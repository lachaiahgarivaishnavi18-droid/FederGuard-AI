# Honest scope and remaining integrations

This repository is a functional academic vertical slice across the requested domains, **not an exhaustive production implementation of every item in the master brief**.

Implemented: local model training and scores, three isolated process datasets, actual Flower aggregation plus native Flower transport runner, FedProx option in web training, per-record Gaussian mechanism with Opacus accounting, permission-aware intelligence and document retrieval, provider abstraction/demo, graph analysis, LangGraph workflow, human cases/audit, frontend, tests and evaluation reports.

Remaining or explicitly limited:

- Cryptographic secure aggregation is not implemented. Plaintext aggregation is labeled throughout. SecAgg+ is not enabled, and no cryptographic security review has occurred.
- Formal DP proof/security validation, cryptographic RNG, institution-scale overlapping-person accounting, DP evaluation metrics and production PrivacyEngine deployment remain work. Reported epsilon applies only under the documented synthetic research mechanism assumptions.
- Native Flower compatibility transport uses legacy APIs and needs authenticated membership/attestation, approved modern SuperLink/ClientApp deployment and integration with the web model registry. TLS is configurable but not tested here.
- Semantic models and FAISS/cross-encoder integrations require extra dependencies, model weights and configuration. Default retrieval is explicitly BM25 + TF-IDF. Indexes are in memory per query, not durable incremental vector indexes. OCR, Chroma and Neo4j are not integrated.
- External OpenAI-compatible, Gemini, Anthropic and local-provider adapters are present but were not exercised against real providers. No API keys were available. Citation IDs are checked; semantic faithfulness and contradictory-evidence handling require independent evaluation. The local fallback is extractive, not a generative model.
- Agent stages inspect authorized metadata and support investigations. Local schema inspection uses a bank endpoint; local scoring/training require explicit operations. They do not invent or autonomously execute transactions, retrain models, or make case outcomes. Dependency failures remain visible in typed traces. There are no autonomous institution-deployed agent workers.
- Additive logistic explanations are displayed operationally; actual SHAP artifacts are generated in the synthetic evaluation CLI. Tree baselines are experimental centralized synthetic comparisons, not federated tree merging. No production calibration, fairness, drift monitoring, robust poisoning mitigation or real-bank performance validation is claimed.
- Database persistence is real, but much domain data uses typed JSON resource records rather than all proposed normalized domain tables. Full permission matrices, database RLS, per-entity migrations/version histories and dedicated graph/vector storage are future extensions.
- User identity has administrator/reviewer/analyst roles, bank membership, bank invitations and reviewer creation. SSO, MFA, credential reset, fine-grained permission administration and signed client/model artifacts remain extensions. Reviewer creation is API-only; demo Bank A can create a second reviewer. The current UI only offers bank settings to administrators.
- Case assignment is set on creation; reassignment and a full evidence attachment editor are not implemented. Notes and reviewer outcomes are functional; alert outcome synchronization and richer priority queues remain extensions.
- Global lists are capped; selected bank-local lists are paginated. Rate limits/round lock are single-process. Durable task queues, multi-worker coordinator, distributed locking and observability stack are absent.
- Docker, PostgreSQL, TLS/mTLS, encrypted storage and recovery procedures are prepared/documented but not executed or independently validated here. Local-only deployment shares one host and administrative secret file.
- No independent penetration test, legal assessment, privacy proof, cryptographic review, availability review or production readiness claim.

The measured reports intentionally preserve weak early-round results, false negatives and the privacy/utility tradeoff. Synthetic labels and public holdout data do not establish fitness for any real institution.
