# Architecture

```mermaid
flowchart LR
  UI[React analyst console] --> API[FastAPI / tenant-scoped authorization]
  API --> DB[(Central metadata, approved intelligence, evidence, cases)]
  API --> C[Federated coordinator / Flower FedAvg]
  C <-->|Parameters and bounded metadata only| A[Bank A process]
  C <-->|Parameters and bounded metadata only| B[Bank B process]
  C <-->|Parameters and bounded metadata only| D[Bank C process]
  A --> AD[(A-only synthetic data / models / privacy journal)]
  B --> BD[(B-only synthetic data / models / privacy journal)]
  D --> DD[(C-only synthetic data / models / privacy journal)]
  API --> R[Permission filter / hybrid retrieval / citations]
  R --> L[Demo extraction or configured LLM]
  API --> G[NetworkX evidence graph]
  API --> H[Human investigation / audit]
```

```mermaid
sequenceDiagram
  actor Analyst
  participant Coordinator
  participant Bank as Each eligible bank node
  participant Accountant as Bank-local Opacus accountant
  Analyst->>Coordinator: Start round, strategy, dropout scenario
  Coordinator->>Bank: Authenticated model/version/privacy request
  Bank->>Bank: Load local synthetic data, fixed public transforms
  Bank->>Accountant: Replay protected release history + proposed steps
  Accountant-->>Bank: Composed epsilon at configured delta
  alt Budget exhausted or unprotected history
    Bank-->>Coordinator: Reject before releasing an update
  else Eligible
    Bank->>Bank: Per-record clipped gradients + Gaussian noise
    Bank->>Bank: Journal spending before response
    Bank-->>Coordinator: Parameters + allowed metadata (no rows)
  end
  Coordinator->>Coordinator: Validate shape/version/participants, require quorum
  Coordinator->>Coordinator: Flower FedAvg / plaintext academic aggregation
  Coordinator->>Coordinator: Public synthetic holdout evaluation, model version
  Coordinator-->>Analyst: Round results, failures and accounting reports
```

The native Flower runner is a separate optional transport experiment. The default dashboard workflow uses Flower's aggregation function with authenticated REST dispatch. The coordinator knows each client's update in both supplied modes. Docker enforces separate data mounts, while local processes share a host administrator; neither represents independent bank infrastructure.

Global evaluation uses generated public synthetic data, never client validation rows. All tree model benchmarks and centralized training occur in the explicitly synthetic-only evaluation script, outside the deployed coordinator path. Fixed feature scaling and missing-value defaults use public constants, never fitted local statistics. Client weights are equal public cohort weights, not hidden private sample counts.
