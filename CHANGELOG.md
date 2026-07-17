# Changelog

## 0.5.0 - 2026-07-17

- Replace unkeyed receipt digests with HMAC-SHA256 signatures backed by a 256-bit key stored outside the workspace.
- Preserve opt-in migration support for legacy StartQ 0.4 SHA-256 receipts while blocking downgrade by default.
- Move optional cloud API keys out of `config.json` into a protected key file or environment variable.
- Avoid duplicate transcript capture during `startq shutdown`.
- Use Markdown package metadata and standard contribution and security documents.
- Add Linux and Windows CI across Python 3.10 and 3.12.

## 0.4.0 - 2026-05-20

- Add EndQ transcript capture and session receipts.
- Add optional cloud Brain synchronization.
- Add the StartQ, AutoQ, and EndQ command workflow.
