Below is a **single, developer-facing design dossier**: it contains four complementary views that together describe the entire platform, from browser to GPU and from nightly ETL to audit dashboard.  Any engineer familiar with modern Python/JS stacks can build, operate, and extend the system from these specs alone.

---

## 1 | Physical / Deployment Diagram

```
║  Browser (React) ║────────HTTPS────────►║  Vercel Edge Proxy  ║──────►  Railway Back-end  ─┐
║                  ║                      ║  (rewrite /api)     ║                          │
╚══════════════════╝                      ╚═════════════════════╝                          │
                                                                                           │
                     ┌──────────────────────────────────────────────────────────────────────┤
                     │                                    Gunicorn (ASGI)                  │
📦  VPC :  Railway    │   Django + DRF + Celery worker + Beat (+ Cross-Encoder in RAM)      │
                     └──────────────────────────────────────────────────────────────────────┘
                             │  ▲                         │▲
                Postgres     │  │ ORM                    Redis
           (query logs, auth)│  │                         │ celery broker / cache
                             │  │                         │
                             ▼  │                         ▼
                       ╔══════════════════════════════════════════╗
                       ║   Weaviate Cloud (vector + hybrid)       ║
                       ║   Class: Document (≈ 400-word chunks)    ║
                       ╚══════════════════════════════════════════╝
                             │                             ▲
              nightly ETL    │ REST w/ vectors             │ near_text search
             (Celery Beat)   ▼                             │
     bioRxiv API  •  protocol PDFs  •  theses PDF pipeline  │
                                                       OpenAI HTTPS
                                                        (GPT-4o)
```

*All network hops TLS-encrypted; Weaviate, Postgres and Redis run in Railway’s private network; only Vercel edge exposes public HTTPS.*

---

## 2 | Detailed Component / Service Breakdown

| Component           | Tech                                              | Key Responsibilities                                                                                                                      | Scaling Knob                                |
| ------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| **Frontend**        | React 18 + Vite + Tailwind                        | • Chat UI & streamed answers<br>• Filter chips (All/Protocol/Paper/Thesis)<br>• Protocol upload page<br>• Confidence & citation rendering | Edge-cached static bundle; SSR not required |
| **API Layer**       | Django 4 + DRF                                    | • `/api/query/` RAG endpoint<br>• `/api/protocols/` CRUD<br>• JWT auth                                                                    | Horizontal via gunicorn workers             |
| **RAG Engine**      | Same container                                    | • 10-NN vector search via Weaviate<br>• Cross-Encoder `ms-marco-MiniLM-L-6-v2` rerank<br>• Prompt builder & policy guard rails            | Cross-Encoder kept in memory; 2–4 vCPU fine |
| **Task Queue**      | Celery + Redis                                    | • Nightly `fetch_biorxiv_preprints`<br>• Large-file protocol ingestion<br>• Future fine-tune jobs                                         | Add more workers if ingest >5 GB/day        |
| **Vector Store**    | Weaviate Cloud (HNSW)                             | • Stores ≈ 400-word chunks w/ metadata<br>• Hybrid BM25 toggle on<br>• Multi-tenant ready                                                 | `efConstruction`, `M` tune when >1 M chunks |
| **Structured DB**   | Postgres 14                                       | • Users, QueryHistory, ThesisMeta<br>• Audit + feedback tables                                                                            | Railway Postgres 1 GB ⇒ upgrade when needed |
| **LLM Gateway**     | OpenAI GPT-4o                                     | • Completion for answers<br>• Embedding (`text-embedding-ada-002`)                                                                        | Call concurrency limited by API key QPS     |
| **Secrets & CI/CD** | Railway env-vars, Vercel env-vars, GitHub Actions | • Build → test → deploy manifests                                                                                                         | Add staging branch for pre-prod             |

---

## 3 | Sequence Flow (Query Path)

```mermaid
sequenceDiagram
  participant U as User (React)
  participant F as Frontend (Vercel)
  participant A as Django API
  participant V as Weaviate
  participant X as Cross-Encoder
  participant O as OpenAI

  U->>F: POST /api/query {Q, doc_type?}
  F->>A: same JWT token
  A->>V: near_text (Q) limit 10 [where doc_type?]
  V-->>A: top-10 chunks + meta
  A->>X: (Q,chunk) pairs
  X-->>A: relevance scores
  A: sort, keep top-3
  A->>O: GPT-4o prompt (Q + 3 chunks)
  O-->>A: answer text
  A->>Postgres: insert QueryHistory (Q,A,sources,conf,status)
  A-->>F: {answer, sources, conf}
  F-->>U: stream answer + citations
```

*Timeouts* — vector search 500 ms, rerank <100 ms, GPT 2–5 s.
*Guard rail* — if `conf < 0.45 OR no citation token`, API downgrades `status="low_confidence"` and warns front-end.

---

## 4 | Data-Ingestion Pipelines

### 4.1 Protocol / Paper

```
PDF → PyMuPDF text → chunk (400/100) → embed (Ada-002) → Weaviate {doc_type:"protocol"/"paper"}
```

### 4.2 Thesis (author-approved)

```
PDF → detect CHAPTER regex → chapter_split → chunk 400/100
     → store meta {author, year, chapter, filename, doc_type:"thesis"}
```

### 4.3 bioRxiv nightly

```
Celery beat cron → bioRxiv REST window (yesterday) → filter keywords
     → abstract + title chunk → embed → Weaviate {doc_type:"paper", source:"bioRxiv"}
```

*All embeddings cached by SHA-256(document\_id + chunk\_index).*

---

## 5 | Security & Compliance

1. **Auth** – JWT (`djangorestframework-simplejwt`); token forwarded by React; API checks tenant ID against vector filter.
2. **Least privilege** – lab members: upload & query; only Maintainers can delete / re-index.
3. **Secrets** – `.env` in Railway/Vercel; never in Git.
4. **Data privacy** – raw patient data pages must be redacted before ingestion.
5. **OpenAI policy** – prompt forbids export of lab IP unless citation is public.

---

## 6 | Ops & Observability

| Signal               | Where                        | Alert threshold   |
| -------------------- | ---------------------------- | ----------------- |
| API 5xx rate         | Railway metrics + Sentry     | >1 % in 5 min     |
| OpenAI latency       | custom histogram in Postgres | P95 > 15 s        |
| Celery task failures | Flower dashboard             | >2 failures / day |
| Postgres size        | Railway                      | 85 % of plan      |
| Weaviate RAM         | Cloud dashboard              | >70 % mem         |

---

## 7 | Sprint-1 Milestones (14-day Gantt)

```
D1-3   Backend RAG + Chat UI
D4     15 manual QA
D5-6   Railway + Vercel deploy
D8-10  Celery + bioRxiv fetcher
D11-12 Ingest SOPs + 1 thesis
D13    Soft-launch to 2 users
D14    Review, plan Sprint-2
```

---

## 8 | Extensibility Hooks

* **Hybrid retrieval** – set `hybridSearch:true` in Weaviate or route to ElasticSearch.
* **Feedback loop** – `POST /api/feedback/` → nightly fine-tune cross-encoder or prompt.
* **Alternate LLM** – add vLLM endpoint; in `views.py` route low-risk queries when `tokens_total < 250` and `conf >= 0.8`.
* **Graph mode** – build Neo4j ingestion from SOP reagent tables → graph-RAG.

---

## 8.1 | Advanced Architecture Enhancements (Post-MVP)

| Category | Enhancement | Implementation Approach | Priority |
|----------|------------|--------------------------|----------|
| **Retrieval Quality** | Hybrid Vector + BM25 Search | Fully enable Weaviate's hybrid search with proper weights tuning | High |
| | Sparse-Dense Fusion | Implement ColBERT or sparse retrieval alongside embeddings | Medium |
| | Cross-Encoder Fine-tuning | Collect user feedback to create training data for reranker | Medium |
| **Performance** | Streaming Response | Implement SSE for streaming in Django view and React | High |
| | Response Caching | Redis cache for frequently asked questions with TTL | Medium |
| | Batch Embedding Processing | Queue and process embeddings in batches to reduce API costs | Medium |
| **Resilience** | Local Model Fallback | Add Ollama with Mistral/Llama for when OpenAI is unavailable | Medium |
| | Tiered Model Selection | Route simpler queries to smaller models based on complexity | High |
| | Embedding Caching | Implement robust SHA-based embedding cache with Redis | High |
| **Quality Metrics** | User Feedback System | Add 👍/👎 feedback buttons and comments field | High |
| | Automated Evaluation | Create test suite with golden dataset for retrieval quality | Medium |
| | Confidence Score Tuning | Improve confidence calculation with ML-based approach | Low |
| **Advanced Features** | Knowledge Graph | Extract entities from docs and build relationships in Neo4j | Medium |
| | Figure Extraction | Extract, index, and link figures from PDFs | High |
| | Multi-modal Support | Enable image queries and results where applicable | Low |

*Implementation Sequence*: Focus on high-priority items after MVP is stable, with retrieval quality improvements first, followed by performance optimizations.

---

## 9 | On-boarding checklist for new devs

1. **Clone & run** `docker-compose up -d`.
2. Create `.env` (copy sample).
3. `python manage.py createsuperuser`.
4. Run `python ingest_thesis.py sample.pdf "Test User" 2024`.
5. `npm run dev` → ask a question.
6. Read `docs/DEVELOPER_NOTE.md` for edge-cases and internal conventions.

Welcome aboard!

---

*This design document together with the repo ensures the project is reproducible by any competent full-stack developer without additional oral knowledge.*
