# Security Policy

Do not submit real secrets, production credentials, private source code, or personal data to an AI provider unless your organization has approved that data flow.

## Reporting
Report vulnerabilities privately to the repository maintainer. Do not open a public issue containing exploitable details.

## Security boundaries
- Submitted code is analyzed as text and is not intentionally executed by the application.
- AI provider output is untrusted and schema-validated.
- GitHub webhook requests are authenticated with HMAC SHA-256 before acceptance.
- Review history is scoped to the authenticated user.
- Production deployments should enforce HTTPS, rate limits, secret rotation, backups, monitoring, and least-privilege infrastructure permissions.
