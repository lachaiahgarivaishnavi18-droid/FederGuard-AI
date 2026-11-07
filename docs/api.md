# API guide

Interactive OpenAPI is `/docs`; machine-readable schemas are `/openapi.json`. Routes require an opaque session cookie except health, registration and login. Login with `POST /api/auth/login {email,password}`. State-changing browser requests must use the configured origin. Logout revokes the current cookie token. Errors use FastAPI's `detail` field (string for application errors, structured details for schema errors). Rate-limit response is HTTP 429.

| Workflow | Routes / permissions |
| --- | --- |
| Identity | `POST /api/auth/register` with bank-specific `X-Registration-Invite`; login/logout; `GET /api/auth/me`; `POST /api/users` administrator creates analyst/reviewer in own bank |
| Banks | `/api/banks` GET/POST, `/{id}` GET/PUT, `/{id}/enroll-client` POST; mutations require administrator |
| Local client | `/api/bank-client/status`, `/dataset-status`, `/training-history`; `/train-local` POST reviewer; no raw dataset response |
| Federation | `POST /api/federated/rounds/start` administrator; rounds/list/detail, clients/models/metrics GET; asynchronous status 202 |
| Privacy | config GET/PUT (admin mutation), accounting/status/audit GET; protected bank-local accounting returned as minimized metadata |
| Detection | `POST /api/fraud/detect` six bounded synthetic features, local scoring; alerts list/detail and metrics GET; alerts private to bank |
| Intelligence | contribute POST; list/detail/trends GET; `/{id}/review` POST owner-bank reviewer, separate from author |
| Knowledge | `POST /api/rag/ingest` multipart `file,title,sharing`; `/documents` GET; `/documents/{id}/review` POST second reviewer; `/query` POST question; `/evidence/{query_id}` GET owner only and current permissions rechecked |
| AI | chat/explain/report POST a question; same evidence-grounded engine; UI exports returned report as text |
| Graph | entities/relationships/patterns GET; permission-scoped evidence graph |
| Cases | investigations POST/GET, `/{id}` GET, `/{id}/notes` POST, `/{id}/status` PUT reviewer; own bank only |
| Agents | `/api/agents/run` POST question; executions list/detail GET owner-bank scoped |
| Analytics | dashboard/fraud-trends/federated-performance/privacy-utility GET; institution-scoped sensitive resources, public model metrics |
| Governance | `/api/audit` GET reviewer, institution-scoped audit trail |

List endpoints for alerts/cases/intelligence/audit support bounded `offset` and `limit`. Some global metadata lists are capped at 100 rather than exposing a complete pagination contract. Bank/node schemas reject unexpected fields. Coordinator model update envelopes are checked against an exact allowlist before use. Native Flower transport is a separate CLI runner and not these REST endpoints.

Create a bank, configure its `<BANK_ID>_ENDPOINT` and `<BANK_ID>_CLIENT_KEY`, restart the coordinator environment and enroll it. An administrator may revoke participation using `active:false`, or withdraw future consortium retrieval with `consent:false`. Cross-bank source consent is checked at retrieval time; approval does not override it. No arbitrary user-supplied outbound endpoint is accepted through the API.
