# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1 | Project mission 🎯
Build a **private, retrieval-augmented assistant** for Dr Debojyoti Chakraborty’s 21-member RNA-biology lab (CSIR-IGIB) that can, in <5 s, answer protocol / thesis / paper questions **with citations**—preserving institutional memory and accelerating experiments.

## 2 | Prototype “definition of done” (v1, June 2025)

| Metric                                   | Target                              |
| ---------------------------------------- | ----------------------------------- |
| Answer quality (Good + Okay)             | ≥ 85 % on 20-question test bank     |
| Median end-to-end latency                | ≤ 5 s                               |
| Documents ingested                       | ≥ 10 SOPs + 1 thesis + daily preprints |
| First-month OpenAI spend                 | ≤ $30                               |
| Active internal users                    | ≥ 5 lab members                     |

These KPIs are your guard-rails.

## 3 | High-level stack
* **Backend**  Django 4 + DRF + Celery        → `backend/`
* **Frontend** React 18 + Vite + Tailwind    → `frontend/`
* **Vector DB** Weaviate (HNSW + BM25 hybrid)
* **LLM** OpenAI GPT-4o for answers, Ada-002 for embeddings
* **Infra** Docker (Postgres | Redis | Weaviate), deployed on Railway + Vercel

_Need details?_—see `README.md` (user-facing) and `docs/developer_facing_design_dossier.md`.

## 4 | Canonical dev workflow

```bash
docker-compose up -d                 # pg + redis + weaviate
cd backend && make dev               # venv, deps, migrate, runserver
# in two extra terminals
celery -A rna_backend worker -l info
celery -A rna_backend beat   -l info
cd ../frontend && npm i && npm run dev
````

### One-liners you’ll call often

| Task             | Command                                                           |
| ---------------- | ----------------------------------------------------------------- |
| Ingest thesis    | `python backend/api/ingestion/ingest_thesis.py PDF "Author" 2024` |
| RAG smoke test   | `pytest tests/test_rag_smoke.py`                                  |
| Deploy back-end  | `railway up`                                                      |
| Deploy front-end | `vercel --prod`                                                   |

## 5 | Golden technical rules

1. **Chunking** = 400 ± 50 words, 100-word overlap; split theses by `CHAPTER`.
2. Prompt **must** start with:

   > “Answer only from the provided sources; if unsure, say ‘I don’t know.’”
3. Enforce citation tokens; drop answers whose `confidence_score < 0.45`.
4. Celery tasks must respect `CELERY_TIMEZONE="Asia/Kolkata"`.
5. No key/secret may appear in logs or test fixtures.

*Extended tribal lore*: `docs/DEVELOPER_NOTE.md`.

## 6 | File-map for Claude

| Need this?                 | Open this file first                      |
| -------------------------- | ----------------------------------------- |
| Full repo setup & commands | `entry_guide.md`                          |
| Production README          | `README.md`                               |
| Deep system architecture   | `docs/developer_facing_design_dossier.md` |
| Nuances / pitfalls         | `docs/DEVELOPER_NOTE.md`                  |
| Stretch-goal ideas         | `docs/next-level_ideas.md`                |
| UI inspiration             | `docs/visual_ideas.md`                    |

## 7 | When generating code

* Follow repo skeleton—don’t invent new top-level dirs without reason.
* Conform to **black + isort** and **Prettier**.
* Every new ingestion script needs at least one pytest.

###  Demo corpus for local runs
The folder `data/sample_docs/` contains public or dummy files (papers, one thesis, community protocols, inventory CSV).  
The ingestion scripts must automatically load these on `make dev` so a fresh clone produces a working demo without lab-private data.

---

*If anything is unclear, open a GitHub Discussion or ask Vishal Bharti directly.*
Now go build something that will make future lab members wonder how anyone worked without it!

```

This version:

* Leads with the **purpose** and measurable goals.  
* Points Claude to the correct companion docs.  
* Summarises the strict rules it must not break.  

Drop it into your root and Claude Code will “know the mission” the moment it loads the repo.
```
