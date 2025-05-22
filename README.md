Below is a **production-grade `README.md`** you can drop straight into the root of `rna-lab-navigator/`.
It is self-contained, gives full context, setup, operations, sprint roadmap, and contribution guidelines—enough for any competent developer to stand up the project without further explanation.

```markdown
# RNA Lab Navigator  
_A retrieval-augmented knowledge assistant for Dr Debojyoti Chakraborty’s RNA-biology group (CSIR-IGIB)_

---

## 0 | Why we built this

Modern RNA-biology methods evolve weekly.  Protocols, theses, troubleshooting notes and fresh preprints are scattered across e-mails, drives and memories.  New students spend weeks rediscovering details; senior members lose context as projects hand over.  

**RNA Lab Navigator** is a private, in-house platform that turns every validated lab document into a live, query-able knowledge base and couples it to GPT-4-class reasoning—so anyone can ask:

*“What buffer composition did Priya use in Chapter 3?”*  
*“Any recent bioRxiv papers on Cas13 knock-down efficiency?”*  

…and receive a **cited** answer in seconds.

---

## 1 | High-level feature set

* **RAG Chatbot** – instant Q&A with inline citations from internal SOPs, theses, publications and auto-fetched preprints.  
* **Cross-Encoder reranking** – retrieved chunks are re-scored for maximal relevance before the LLM sees them (cuts hallucination).  
* **Daily literature scan** – Celery worker pulls the latest RNA-biology bioRxiv abstracts each night.  
* **Protocol uploader** – drag-and-drop PDFs → ingested and version-tracked (Sprint 2).  
* **Inventory snapshot** – reagent list surfaced in answers (Sprint 2).  
* **Full audit log** – every query, answer, source and confidence stored for reproducibility.  
* **Thesis mode** – whole PhD theses chunked and searchable (opt-in per author).  
* **Multi-tenant ready** – documents tagged by `doc_type`, `author`, `year`, etc.; namespaces possible.  
* **Deploy-anywhere** – dev on Docker; free-tier launch via Railway (backend) + Vercel (frontend).

---

## 2 | System architecture

```

```
     React + Tailwind  (frontend)  ───────────────►  /api/query/
                                                       │
                                                       ▼
```

┌──────────────────────┐    vector search (top-10)   ┌───────────────┐
│  Weaviate vector DB  │◄────────────────────────────┤ Django + DRF  │
│  (doc chunks + meta) │                             └───────────────┘
└──────────────────────┘          ▲                        │
▲                        │rerank                 │OpenAI GPT-4o
│celery beat (2 AM)      │cross-encoder          ▼
│bioRxiv fetch           │MiniLM (CPU)      ┌─────────────┐
┌──────────────────────┐          │                  │  Answer +   │
│  bioRxiv REST API    │──────────┘                  │ Citations   │
└──────────────────────┘                             └─────────────┘

```

_Internal infra (Docker): Postgres 14 • Redis alpine • Weaviate‐latest_

---

## 3 | Repository layout

```

rna-lab-navigator/
├── backend/               Django 4 + DRF
│   ├── rna\_backend/       settings, celery, urls
│   └── api/
│       ├── ingestion/     thesis + protocol import
│       ├── models.py      QueryHistory, ThesisMeta, …
│       ├── views.py       RAG endpoint (+reranker)
│       ├── serializers.py
│       └── urls.py
├── frontend/              React 18 + Vite + Tailwind
│   ├── src/
│   │   ├── components/    ChatBox, FilterChips, …
│   │   └── pages/         Home, Login, Dashboard
├── docker-compose.yml     Postgres • Redis • Weaviate
├── vercel.json            frontend → backend rewrite
├── railway.yaml           Railway deploy cfg
├── .env.example           env-var template
└── docs/                  roadmap, architecture, FAQ

````

---

## 4 | Quick-start (local dev)

```bash
# 1. clone
git clone https://github.com/<you>/rna-lab-navigator.git
cd rna-lab-navigator

# 2. infra
docker-compose up -d           # postgres:5432 • redis:6379 • weaviate:8080

# 3. backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add OpenAI key, etc.
python manage.py migrate
celery -A rna_backend worker -l info  &   # terminal 1
celery -A rna_backend beat   -l info  &   # terminal 2
python manage.py runserver               # terminal 3

# 4. frontend
cd ../frontend
npm install
npm run dev
````

Open [http://localhost:5173](http://localhost:5173), register a user, ask a question.

---

## 5 | Ingesting documents

### 5.1 SOP PDFs

```
python backend/api/ingestion/ingest_thesis.py \
       data/theses/2023_Sharma_Priya_PhD_Thesis.pdf \
       "Priya Sharma" 2023
```

*(For protocols, reuse same script or simpler ad-hoc import; tag `doc_type:"protocol"`)*

### 5.2 Daily bioRxiv fetch

Runs automatically via Celery Beat (2 AM).  Keywords and schedule in `api/tasks.py`.

---

## 6 | Core commands

| Purpose                   | Command                                           |
| ------------------------- | ------------------------------------------------- |
| Bring up infra containers | `docker-compose up -d`                            |
| Django dev server         | `python manage.py runserver`                      |
| Celery worker / beat      | `celery -A rna_backend worker -l info`            |
| Ingest a thesis           | `python ingest_thesis.py <pdf> "<author>" <year>` |
| Frontend dev server       | `npm run dev`                                     |
| Deploy backend (Railway)  | `railway up`                                      |
| Deploy frontend (Vercel)  | `vercel --prod`                                   |
| Deploy to production      | `make deploy`                                     |
| Run tests & linting       | `make test && make lint`                          |
| View production logs      | `make prod-logs`                                  |

---

## 7 | Sprint roadmap

| Sprint            | Goal                           | Key deliverables                                                                                             |
| ----------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| **1** (Weeks 1–2) | Core RAG chatbot live          | Vector + reranker → GPT flow, logging, confidence, deployed on Railway + Vercel, 15 test queries ≥ 85 % good |
| **2** (Weeks 3–4) | Protocol uploader & inventory  | PDF upload → version table, Benchling/CSV reagent list, admin query dashboard, daily digest email            |
| **3** (future)    | Knowledge-graph, feedback loop | Neo4j or Weaviate KG, 👍/👎 buttons ingested for continual eval                                              |
| **4** (optional)  | On-prem LLM, robot hooks       | Mistral-7B server, thermocycler API calls                                                                    |

Full day-by-day checklist for Sprint 1 is in **docs/roadmap.md**.

---

## 8 | Data-collection policy

1. **Each member submits**: final protocols, reagent sheets, troubleshooting notes.
2. **Naming**: `Name_Protocol_vX_YYYY-MM-DD.pdf`.
3. **Drive layout**: `RNA_Lab_Navigator_Data/Protocols/<theme>/…` etc.
4. **Theses**: author consent + confidential appendices removed/redacted.
5. **PI announcement template** + **FAQ** in `docs/`.

---

## 9 | Security & privacy

* All data stays on lab storage / Railway project (private).
* JWT auth + row-level Weaviate filter prevents cross-user leakage.
* LLM prompt forbids non-cited answers; fallback says “I don’t know”.
* Logs kept in Postgres for traceability; redact if future sharing required.

---

## 10 | Deployment guide

### Production deployment

For a complete production deployment:

1. Set up environment variables:
   ```bash
   cp backend/.env.production.example backend/.env.production
   # Edit the file to add your API keys and other configurations
   ```

2. Generate secure values for your environment:
   ```bash
   python scripts/generate_env_values.py
   ```

3. Deploy using the provided Makefile target:
   ```bash
   make deploy
   ```

This will run tests, lint checks, build Docker images, and start all services. For more details, see `docs/DEPLOYMENT.md`.

### Railway & Vercel deployment

For a simpler deployment using Railway (backend) and Vercel (frontend):

1. Deploy backend to Railway:
   ```bash
   cd backend
   railway up
   ```

2. Deploy frontend to Vercel:
   ```bash
   cd frontend
   vercel --prod
   ```

## 11 | Contribution guide (TL;DR)

* Branch off `dev`, open PR to `dev`; only maintainers merge to `main`.
* Python: black + isort; JS: Prettier (configs included).
* Write or update unit tests for new utilities.
* Large media → store in Drive, not Git.
* Detailed doc in `CONTRIBUTING.md`.

---

## 12 | Troubleshooting tips

| Symptom                             | Likely cause                       | Fix                                  |
| ----------------------------------- | ---------------------------------- | ------------------------------------ |
| `OpenAI API error 'context_length'` | Too many tokens in prompt          | reduce chunk size or top-k           |
| No answer + confidence 0.0          | Retrieval returned zero chunks     | check ingest, re-index               |
| Celery beat not triggering          | Timezone mismatch in `settings.py` | set `CELERY_TIMEZONE="Asia/Kolkata"` |

---

## 13 | License & citation

Project released under **MIT** for internal academic use.
If you use RNA Lab Navigator in a publication, cite:

> Vishal Bharti et al. “RNA Lab Navigator: An internal retrieval-augmented assistant for RNA biology workflows.” (software, 2025)

---

## 14 | Acknowledgements

* Built with OpenAI o3, Weaviate, Django REST Framework, Celery, TailwindCSS.
* Supervised & inspired by Dr Debojyoti Chakraborty.
* Special thanks to early testers in the RNA-biology lab (CSIR-IGIB).

---

**Happy experimenting, and may your buffers always hit the right pH!**

```

---

### How to use this README

1. Drop it into `rna-lab-navigator/README.md`.  
2. Update any bracketed placeholders (`<you>`, Drive links, etc.).  
3. Push to GitHub—new contributors can now get up and running end-to-end without talking to you.

That’s your pivot document—comprehensive, actionable, and future-proof.
```
