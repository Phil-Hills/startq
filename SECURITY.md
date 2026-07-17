# Security Policy

## Reporting

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability reporting for this repository, or contact `contact@a2ac.ai` with the affected version, reproduction steps, and impact. Remove credentials, transcripts, source code, and personal information from reports.

## Local data

The `.startq/` directory can contain AI prompts, session summaries, Git metadata, transcripts, and cloud credentials. Keep it out of source control and restrict access to the operating-system account that runs StartQ. Signing keys are stored separately in the user's config directory by default.

## Integrity boundary

StartQ 0.5 uses HMAC-SHA256 to authenticate local receipts. This detects edits by a process that cannot access the user-config signing key. It does not defend against an administrator or compromised process with access to both the receipt and signing key, and it is not an external timestamp or public-chain anchor.

Legacy StartQ receipts used unkeyed SHA-256. They provide corruption detection but not writer authentication and are rejected unless the operator explicitly uses `--allow-legacy`.

## Cloud sync

Use HTTPS endpoints. Prefer the hidden API-key prompt or `STARTQ_CLOUD_API_KEY`; avoid passing secrets through command-line arguments. StartQ cannot control the security or retention practices of a configured third-party cloud endpoint.
