# Runtime config (Aaron)

This skill is currently wired to:

- Excel (OneDrive share link): https://1drv.ms/x/c/f41c1af2eee30a91/IQC57il2jfQ6Q5Idi604SQtNASxT0JypHcP9wVMRddS0PgA?e=n5BjtR
- Excel Table name: `Ledger`
- Columns order:
  `ts_iso,chat_id,message_id,author_id,author_name,item,price,currency,category,project_code,notes,raw_text`
- Azure client id (public client/device code): `b98aa7fe-f1b7-4780-9285-4acf1e25d0e8`
- Tenant: `common`
- Token cache: stored on host in `~/.clawdbot/msal_token_cache_lab_spend_ledger.json`

Telegram group:
- Spend-only group chat id: `-1003711269809`
- Trigger: messages containing `buy` (case-insensitive)
