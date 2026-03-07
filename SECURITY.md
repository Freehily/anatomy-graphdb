# Security Policy

## Supported versions

Security updates are currently provided for the latest version on `main`.

## Reporting a vulnerability

Please do not open public GitHub issues for suspected vulnerabilities.

Report privately to:

- `tomrfreeman3@gmail.com`

Include:

- a clear description of the issue
- reproduction steps or proof of concept
- potential impact
- any suggested mitigation

You should receive an acknowledgment within 5 business days.

## Sensitive data and secrets

- Never commit `.env` files, credentials, or API tokens.
- Rotate secrets immediately if exposed in logs, screenshots, or chat transcripts.
- Use least-privilege credentials for Neo4j instances where possible.

## Dependency and runtime hygiene

- Keep Python dependencies up to date.
- Run tests/validation before release:
  - `poetry run pytest`
  - `poetry run stronger-anatomy --region all --validate-only`
