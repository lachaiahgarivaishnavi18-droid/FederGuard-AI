# Synthetic data

Each bank node deterministically generates its own local synthetic dataset at first launch:

- bank_a: 4,500 rows, lower typical amount/velocity.
- bank_b: 3,500 rows, different amount/velocity/risk distribution.
- bank_c: 2,000 rows, different distribution plus synthetic concept drift.

Total: 10,000 rows. Arrays contain amount, velocity, device risk, geographic deviation score, account age and hour, with missing feature values and imbalanced fraud labels. No customer names, account numbers, payment credentials, raw locations or device identifiers are generated. Local stores are `runtime/<bank>/transactions.npz` and are ignored by Git. They are created by the bank process, not read by the deployed coordinator. Bank nodes also maintain their local model, replay journal and privacy history there.

Shared approved synthetic intelligence, policy chunks and cases are seeded into the central metadata database separately. `sample_policies/velocity.md` is a synthetic document for the upload CLI. The evaluation script explicitly generates synthetic benchmark cohorts in one process for the permitted centralized experimental comparison; this is separate from the deployed FL path.
