Below is a **developer-only cheat sheet**—the “tribal knowledge” and subtle rules that aren’t obvious from the public README but make the project run smoothly.
---

## RNA Lab Navigator – Internal Dev Notes & Nuances

### 1  Chunking matters more than you think

| Rule                                          | Rationale                                                            |
| --------------------------------------------- | -------------------------------------------------------------------- |
| **Window ≈ 400 ± 50 words, overlap ≈ 100**    | keeps context under \~3 k tokens when k=3                            |
| **Split theses at CHAPTER first**             | avoids cross-chapter bleed; improves reranker scores                 |
| **Do not chunk reagent tables** as plain text | they balloon tokens. Convert to Markdown table if useful; else skip. |

### 2  Embedding hygiene

1. **Always trim text to 8,191 chars** before Ada-002 call (`input[:8191]`).
2. **Cache embeddings** (Weaviate stores vectors; never re-embed same hash).
3. Use the *same* embedding model for query and docs; do **not** mix BGE + Ada until you introduce hybrid mode deliberately.

### 3  Cross-encoder tips

* `ms-marco-MiniLM-L-6-v2` ≈ 70 ms on laptop CPU for 10 pairs—acceptable.
* Score range isn’t \[0,1]—normalize via `torch.sigmoid` if you want strict thresholds.
* Average top-k score = cheap confidence metric; < 0.45 means answer likely shaky.

### 4  Prompt guard-rails

* **First system line** (non-negotiable):

  > “Answer only from provided sources; if uncertain, say ‘I don’t know.’”
* Add `"citation-required"` rule: if GPT output lacks “Source \d” token, discard and retry with temperature 0.
* Keep temperature ≤ 0.3; higher values hallucinate citations.

### 5  OpenAI cost control

| Trick                                                          | Impact                                             |
| -------------------------------------------------------------- | -------------------------------------------------- |
| Use `gpt-3.5-turbo` for *summarising* preprints before storage | 10× cheaper than GPT-4-class                       |
| Limit prompt context to **top-3** chunks                       | linear token growth; chunk 4 rarely changes answer |
| Set hard monthly cap in dashboard (`Usage > hard limit`)       | avoids surprise bills                              |

### 6  Operational logging

* Store every request/response in `QueryHistory` – but **truncate answer to 4 k chars** to avoid Postgres bloat.
* For privacy review, you can anonymise question text older than 6 months (`answer` and `sources` stay).

### 7  Celery quirks

* Railway free tier sleeps → beat tasks pause. Keep beat on a cheap always-on box or change schedule to “run on first query of day.”
* Set `CELERY_TIMEZONE="Asia/Kolkata"` to align logs with IST.

### 8  Weaviate schema tweaks (future)

* If ingest explodes beyond 1 M chunks, create separate **classes** (`ProtocolChunk`, `ThesisChunk`, `PaperChunk`) instead of one megaclass.
* Turn on HNSW `efConstruction=128` and `M=32` for latency < 50 ms at scale.

### 9  Testing discipline

* Keep `docs/test_queries.xlsx` with expected answer snippets—CI can do fuzz-matching.
* `pytest` smoke test hits `/api/query/` with fixed seed question to catch OpenAI key expiry or infra drift.

### 10  Deployment gotchas

* Railway: add `RAILWAY_STATIC_URL` to Django `ALLOWED_HOSTS`.
* Vercel rewrite path must **not** include trailing slash by default (`/api/(.*)` not `/api/(.*)/`).
* When upgrading Weaviate, run `docker pull semitechnologies/weaviate:latest` locally first—rare schema-breaking releases.

### 11  Security corner-cases

* Enforce file-size limit (e.g., 30 MB) on protocol uploads; a malicious 1 GB PDF will kill memory.
* Strip **embedded JS / macros** from Word docs if you ever support `.docx` ingestion.
* Never echo `OPENAI_API_KEY` in logs—mask using `log_filter` middleware.

### 12  Future feature staging

1. **Hybrid BM25+vector** – add ElasticSearch or Weaviate’s hybrid search once doc count > 20 k.
2. **Feedback loop** – store thumbs-down answers; nightly script re-queries with different prompt/chunk sizes to self-improve.
3. **On-prem LLM** – run Mistral-7B or Mixtral-8x7B in vLLM with quantization; route low-risk queries there, fallback to GPT-4-class for complex ones.

---

**Golden rule:** *If you change chunking, retrain your intuition*—re-run accuracy test-sheet before deploying to users.

Happy shipping,
—Core dev team
