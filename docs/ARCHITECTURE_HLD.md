# High-level design
## Scope and boundaries
One evolving repository; V1 deterministic RAG, V2 tool-using agent. Local FastAPI, embeddings, ingestion, optional UI; cloud Oracle and external generation API. Trust boundaries: browser→API, API→DB over TLS, API→LLM provider (send minimum evidence), ingestion→untrusted corpus. No direct browser access to secrets or Oracle.

```mermaid
flowchart LR
  subgraph Laptop[Local laptop / later app host]
    U[Browser / API client] --> A[FastAPI validation / limits]
    A --> S[Search orchestration]
    S --> E[MiniLM CPU embedding]
    S --> R[Retrieval adapter]
    S --> L[LLM adapter]
    I[Ingestion CLI] --> C[Clean / token chunk / batch embed]
    C --> R
    A --> O[Logs / metrics]
  end
  subgraph Cloud[External services]
    R <-->|TLS / pooled connections| D[(Oracle vector + relational DB)]
    L <-->|HTTPS / bounded calls| M[LLM API]
  end
```

```mermaid
sequenceDiagram
  participant U as Client
  participant A as FastAPI
  participant E as Embedding service
  participant D as Oracle
  participant L as LLM API
  U->>A: query + bounded top_k + optional filters
  A->>E: tokenize and embed
  E-->>A: 384 float vector
  A->>D: bound vector query
  D-->>A: ranked chunks and provenance
  alt retrieval only or insufficient evidence
    A-->>U: results or insufficient evidence
  else answer
    A->>L: bounded context with source IDs
    L-->>A: structured answer + cited IDs
    A-->>U: validated answer or fallback + sources
  end
```

Offline flow: attributed technical sources → validation/dedup → token-aware chunks → local normalized embeddings → transaction/batch insert → counts and retrieval verification. Independent from online path. Exact search first. V2 calls the same retrieval and LLM interfaces; see AI_AGENT_DESIGN.md. No distributed deployment is claimed.
