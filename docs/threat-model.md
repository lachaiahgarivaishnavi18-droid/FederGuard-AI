# Threat model

Assets: bank-local datasets, client credentials, model updates, evidence permissions, analyst sessions, investigation records, privacy journals, model registry integrity.

| Threat | Implemented control | Residual risk / further work |
| --- | --- | --- |
| Curious coordinator / gradient leakage | No raw-record training endpoints; clipped/noised gradients; bounded update envelopes | Individual model updates remain visible; cryptographic secure aggregation absent |
| Compromised bank / poisoning | Known configured endpoint + bank-specific credential, model version, finite tensor/shape/norm checks, quorum | No Byzantine-robust defense, attestation or independent verification of local accounting |
| Sybil / enrollment | Administrator enrollment, environment-configured endpoint and credential | Native Flower compatibility runner does not authenticate membership; admin provisioning requires institutional process |
| Replay / duplicate releases | Bank-local round cache, sequential coordinator lock, unique participation constraint | Durable distributed leader election absent; run one API worker; changed requests with the same round reuse cached output |
| Cross-tenant access | Server-side bank scope on cases, alerts, queries, executions; permission-filtered shared records | PostgreSQL row-level security not configured; privileged DB operator is trusted |
| Revoked sharing / stale evidence | Active bank/consent/approval/expiry checked before retrieval and evidence access | Already downloaded reports cannot be recalled |
| Prompt injection | Retrieval scope fixed before LLM; documents described as untrusted data; no model tools; citation references validated | Semantic truth/entailment not mechanically guaranteed; extractive fallback can quote malicious text as evidence |
| Session theft / credential guessing | HttpOnly opaque sessions, scrypt, expiry, logout revocation, origin checks, rate limits | Demo lacks MFA/SSO, distributed rate limits, account lockout or password reset |
| Malicious upload | Extension allowlist, file/expanded DOCX/text/page limits, parser error handling | Parser sandboxing, malware scanning and comprehensive decompression/CPU protections absent |
| Data leakage through logs | No input datasets, password or API key logging in application; minimized metadata | Access logging, exception infrastructure and external LLM providers need independent review |
| Artifact compromise | SHA256 recorded with model parameters | No signing key management, trusted model delivery or verified registry chain |
| Privacy-budget reset | Local persistent ledger, conservative spending before release, budget rejection | Local administrator can delete/roll back journals; no remote attestation |
| Infrastructure compromise | Separate Docker bank volumes/networks, non-root Python containers, no coordinator bank-data mounts | Local process simulation shares one host; at-rest encryption and institution-owned infrastructure remain deployment work |

Only synthetic data is authorized in this prototype. Access controls do not substitute for institutional consent or legal review. No security audit or penetration test has been performed. HTTP local links, self-hosted developer secrets, mutable audit rows and the absence of authenticated secure aggregation make this unsuitable for production bank data.
