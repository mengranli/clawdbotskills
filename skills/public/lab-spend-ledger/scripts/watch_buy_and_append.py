#!/usr/bin/env python3
"""Watch a Clawdbot Telegram group session transcript for new "buy" messages and append them to Excel.

This script is meant to be invoked by a cron agent turn via `exec`.
It is deterministic (no LLM needed) once invoked.

State is stored under ~/.clawdbot/lab_spend_ledger_watch_buy_state.json by default.

It scans the Clawdbot session JSONL files under ~/.clawdbot/agents/main/sessions/
for messages that contain the given Telegram group id.

We rely on the injected `[message_id: N]` suffix that Clawdbot adds to group
message text.

Output: JSON summary on stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GROUP_ID_RE = re.compile(r"Telegram [^\]]* id:(-?\d+)")
MSG_ID_RE = re.compile(r"\[message_id:\s*(\d+)\]")
AUTHOR_RE = re.compile(r"\]\s*([^\[]+?)\s*\((\d+)\):\s*")


def utc_iso_from_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_state(path: Path) -> dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def dedupe_check(key: str) -> bool:
    """Return True if already seen."""
    p = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("ledger_dedupe.py")), "check", "--key", key],
        capture_output=True,
        text=True,
    )
    return p.returncode == 10


def dedupe_mark(key: str, meta: dict[str, Any]) -> None:
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("ledger_dedupe.py")),
            "mark",
            "--key",
            key,
            "--meta",
            json.dumps(meta, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))


def find_group_session_files(group_id: str) -> list[Path]:
    root = Path(os.path.expanduser("~/.clawdbot/agents/main/sessions"))
    if not root.exists():
        return []

    out: list[Path] = []
    # Only scan .jsonl files.
    for p in root.glob("*.jsonl"):
        try:
            # Quick tail read (avoid full scan): last 64KB.
            b = p.read_bytes()
            tail = b[-65536:] if len(b) > 65536 else b
            if group_id.encode("utf-8") in tail:
                out.append(p)
        except Exception:
            continue

    # Fallback: include all files if we couldn't detect (better to be slow than miss).
    if not out:
        out = list(root.glob("*.jsonl"))

    return sorted(out, key=lambda x: x.stat().st_mtime)


def iter_messages(jsonl_path: Path):
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") != "message":
                continue
            msg = o.get("message") or {}
            if msg.get("role") != "user":
                continue
            yield o


def extract_text(msg_obj: dict[str, Any]) -> str:
    msg = msg_obj.get("message") or {}
    content = msg.get("content") or []
    parts = []
    for c in content:
        if c.get("type") == "text":
            parts.append(c.get("text") or "")
    return "\n".join(parts)


def parse_candidate(text: str, group_id: str) -> dict[str, Any] | None:
    if f"id:{group_id}" not in text:
        return None

    m_mid = MSG_ID_RE.search(text)
    if not m_mid:
        return None
    message_id = int(m_mid.group(1))

    # Try to capture the last author header in the text.
    author_name = ""
    author_id = ""
    for m in AUTHOR_RE.finditer(text):
        author_name = (m.group(1) or "").strip()
        author_id = (m.group(2) or "").strip()

    # Raw message is after the last ": " up to the [message_id: ...] tag.
    # Works for both injected single-line and multi-line blocks.
    raw = text
    raw = raw.split("[message_id:")[0]
    if ":" in raw:
        raw = raw.rsplit(":", 1)[1]
    raw = raw.strip()

    # Strip leading bot mention(s)
    raw = re.sub(r"^@\w+\s+", "", raw)

    if "buy" not in raw.lower():
        return None

    return {
        "message_id": message_id,
        "author_name": author_name,
        "author_id": author_id,
        "raw_text": raw,
    }


def run_parser(raw_text: str) -> dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("parse_purchase_message.py"))],
        input=raw_text,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)


def run_append(
    ts_iso: str,
    chat_id: str,
    message_id: int,
    author_id: str,
    author_name: str,
    item: str,
    price: float,
    currency: str,
    category: str,
    project_code: str,
    raw_text: str,
):
    script = Path(__file__).with_name("log_spend_to_excel.py")
    receipt = f"telegram:{chat_id}:{message_id}"

    cmd = [
        sys.executable,
        str(script),
        "--ts-iso",
        ts_iso,
        "--chat-id",
        str(chat_id),
        "--message-id",
        str(message_id),
        "--author-id",
        str(author_id or ""),
        "--author-name",
        str(author_name or ""),
        "--item",
        item,
        "--price",
        str(price),
        "--currency",
        currency,
        "--category",
        category,
        "--project-code",
        project_code,
        "--notes",
        "",
        "--raw-text",
        raw_text,
        "--receipt",
        receipt,
    ]

    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group-id", required=True, help="Telegram group chat id (e.g., -1003711269809)")
    ap.add_argument(
        "--state", default=os.path.expanduser("~/.clawdbot/lab_spend_ledger_watch_buy_state.json"), help="State json path"
    )
    ap.add_argument("--max", type=int, default=50, help="Max new messages to process per run")
    ap.add_argument(
        "--init-only",
        action="store_true",
        help="Initialize state to latest observed message_id and exit without appending (safe first run)",
    )

    args = ap.parse_args()

    group_id = str(args.group_id)
    state_path = Path(args.state)
    state = load_state(state_path)

    # Safe default: if we've never seen this group before, initialize to latest and do nothing.
    first_run = "last_message_id" not in state
    last_mid = int(state.get("last_message_id", 0) or 0)

    files = find_group_session_files(group_id)

    appended = []
    seen_max_mid = last_mid

    # Pass 1: discover max message id (for safe initialization).
    for f in files:
        for o in iter_messages(f):
            text = extract_text(o)
            cand = parse_candidate(text, group_id)
            if not cand:
                continue
            mid = int(cand["message_id"])
            seen_max_mid = max(seen_max_mid, mid)

    if args.init_only or (first_run and seen_max_mid > 0):
        state["last_message_id"] = seen_max_mid
        save_state(state_path, state)
        print(
            json.dumps(
                {
                    "ok": True,
                    "group_id": group_id,
                    "state": str(state_path),
                    "initialized": True,
                    "last_message_id": seen_max_mid,
                    "appended": [],
                },
                ensure_ascii=False,
            )
        )
        return 0

    # Pass 2: process new messages only.
    for f in files:
        for o in iter_messages(f):
            text = extract_text(o)
            cand = parse_candidate(text, group_id)
            if not cand:
                continue
            mid = int(cand["message_id"])
            if mid <= last_mid:
                continue

            # Local idempotency: never log the same Telegram message twice.
            dedupe_key = f"telegram:{group_id}:message:{mid}"
            if dedupe_check(dedupe_key):
                last_mid = max(last_mid, mid)
                continue

            raw_text = cand["raw_text"]
            try:
                draft = run_parser(raw_text)
            except Exception:
                continue

            # Only auto-log when required fields are present.
            if draft.get("needs_clarification"):
                continue

            ts_ms = int((o.get("message") or {}).get("timestamp") or 0)
            ts_iso = utc_iso_from_ms(ts_ms) if ts_ms else datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

            try:
                res = run_append(
                    ts_iso=ts_iso,
                    chat_id=group_id,
                    message_id=mid,
                    author_id=cand.get("author_id") or "",
                    author_name=cand.get("author_name") or "",
                    item=draft["item"],
                    price=float(draft["total"]),
                    currency=draft["currency"],
                    category=draft["category"],
                    project_code=draft["project_code"],
                    raw_text=raw_text,
                )
            except Exception:
                continue

            appended.append({"message_id": mid, "receipt": res.get("receipt"), "excel_index": res.get("excel_index")})
            dedupe_mark(dedupe_key, {"receipt": res.get("receipt"), "excel_index": res.get("excel_index")})

            last_mid = max(last_mid, mid)
            if len(appended) >= args.max:
                break
        if len(appended) >= args.max:
            break

    if last_mid != int(state.get("last_message_id", 0) or 0):
        state["last_message_id"] = last_mid
        save_state(state_path, state)

    out = {
        "ok": True,
        "group_id": group_id,
        "state": str(state_path),
        "last_message_id": state.get("last_message_id", last_mid),
        "appended": appended,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
