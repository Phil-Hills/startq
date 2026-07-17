# Contributing to StartQ

StartQ is intentionally small: a standard-library session journal with optional cloud sync. Focused bug fixes, portability improvements, tests, and documentation corrections are welcome.

## Development

```bash
git clone https://github.com/Phil-Hills/startq.git
cd startq
python -m unittest discover -v
python -m build
```

## Pull requests

- Keep each pull request focused on one concern.
- Add or update tests for behavior changes.
- Preserve backward compatibility for existing `.startq/brain/*.json` receipts when practical.
- Do not commit `.startq/`, transcripts, signing keys, cloud keys, credentials, or customer data.
- Document the checks you ran and any platform behavior you could not verify.

Report suspected vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
