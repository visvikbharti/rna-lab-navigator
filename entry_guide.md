Below is a **single, end-to-end guide** you can keep open while you build RNA Lab Navigator from scratch.
It consolidates **every decision, structure, sprint, and code fragment** we designed—so you don’t need to scroll back through the entire chat.
Use it as your living checklist.

---

## 0 Prerequisites

| Tool               | Version / Install          |
| ------------------ | -------------------------- |
| **Python**         | 3.10 +                     |
| **Node**           | 18 +                       |
| **Docker Desktop** | Latest                     |
| **Railway CLI**    | `npm i -g railway`         |
| **Vercel CLI**     | `npm i -g vercel`          |
| **Git**            | Initialized repo on GitHub |

---

## 1 Repo Skeleton (top-level)

```
rna-lab-navigator/
│
├── backend/               # Django + DRF
│   ├── manage.py
│   ├── requirements.txt
│   ├── rna_backend/       # settings, urls, celery.py
│   └── api/               # models, views, serializers, ingestion/
│       ├── ingestion/
│       │   ├── chunking_utils.py
│       │   ├── embeddings_utils.py
│       │   └── ingest_thesis.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── frontend/              # React + Vite + Tailwind
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── components/
│       │   ├── ChatBox.jsx
│       │   ├── AnswerCard.jsx
│       │   ├── ProtocolUploader.jsx
│       │   └── FilterChips.jsx
│       ├── pages/
│       └── api/           # auth.js, query.js …
│
├── vectorstore/           # (optional legacy scripts)
├── docker-compose.yml     # Postgres, Redis, Weaviate local
├── vercel.json            # frontend rewrite → backend
├── railway.yaml           # backend deploy
├── .env.example
├── README.md
└── docs/ (roadmap, architecture diagram, slides, FAQ…)
```

---

### 1.1 Key environment variables (`.env.example`)

```
DEBUG=True
SECRET_KEY=your-secret
POSTGRES_DB=rna_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TIMEOUT=30
```

---

## 2 Set-Up Commands (local)

```bash
# clone and enter
git clone <repo> && cd rna-lab-navigator

# bring up infra
docker-compose up -d               # postgres, redis, weaviate

# backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
celery -A rna_backend worker -l info &   # new shell
celery -A rna_backend beat   -l info &   # schedules

# frontend
cd ../../frontend
npm install
npm run dev
```

*Open `http://localhost:5173` and Django at `http://127.0.0.1:8000`.*

---

## 3 Backend Highlights

### 3.1 Core RAG Endpoint (`/api/query/`)

1. Vector search: top-10 chunks via Weaviate `near_text`.
2. Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`).
3. Take top-3 → build prompt:

   ```
   You must answer strictly from provided documents…
   ```
4. OpenAI GPT-4o call (`temperature 0.2`).
5. Response = `{answer, sources, confidence_score}`.
6. Log every query (`QueryHistory`) with status & confidence.

### 3.2 Celery Beat Task

```python
@shared_task
def fetch_biorxiv_preprints():
    # RNA + Cas13/CRISPR keyword fetch
    # push abstracts into Weaviate with doc_type="paper"
```

Runs daily at 2 AM.

### 3.3 Thesis Ingestion CLI

```bash
cd backend/api/ingestion
python ingest_thesis.py /path/Thesis.pdf "Author Name" 2023
```

* Splits on `CHAPTER X`, windows 400/100.
* Tags: `doc_type:"thesis"`, `author`, `year`, `chapter`.

---

## 4 Frontend Highlights

* **ChatBox**: textarea → `/api/query/`; streams answer.
* **FilterChips**: choose All / Protocol / Paper / Thesis → sends `doc_type` filter.
* Low-confidence (< 0.5) answers get yellow warning.
* **ProtocolUploader** page (Sprint 2) posts PDF to `/api/protocols/`.

---

## 5 Sprint 1 Roadmap (14 days)

| Day | Milestone                             |
| --- | ------------------------------------- |
| 1   | Backend RAG endpoint working locally  |
| 2   | ChatBox wired up                      |
| 3   | Confidence display + logging verified |
| 4   | 15 manual queries tested              |
| 5   | Deploy backend → Railway              |
| 6   | Deploy frontend → Vercel              |
| 7   | Polish buffer                         |
| 8   | Celery + Redis live                   |
| 9   | BioRxiv fetcher verified              |
| 10  | Automatic daily schedule              |
| 11  | Ingest 5 lab SOP PDFs                 |
| 12  | Thesis ingestion test                 |
| 13  | Mini soft-launch to 1–2 labmates      |
| 14  | Sprint review; plan Sprint 2          |

Success ≥ 85 % good/okay answers; <\$10 OpenAI cost.

---

## 6 Data-Collection Strategy

1. **PI announcement** (template provided) asks for:

   * protocol PDFs (titled, versioned),
   * reagent sheets,
   * troubleshooting notes.
2. Drive folder structure:

```
RNA_Lab_Navigator_Data/
├─ Protocols/ (sub-folders by theme)
├─ Theses/
├─ Reagents/
├─ Troubleshooting_Notes/
├─ Templates/
└─ Archive/
```

3. Naming: `Name_Protocol_vX_YYYY-MM-DD.pdf`.

---

## 7 Presentation Deck (7 slides)

1. **Title**
2. The Challenge
3. Our Solution
4. Live Demo
5. How It Works
6. Proposal to Scale (data-collection request)
7. Future Vision

*(Use deck when meeting PI.)*

---

## 8 Testing Sheet Template

| # | Question | Expected | Chunks Y/N | Conf | Grade | Source OK? | Notes |
| - | -------- | -------- | ---------- | ---- | ----- | ---------- | ----- |

—Fill for 15–20 queries; target ≥ 0.70 mean confidence.

---

## 9 Deployment Cheat-Sheet

```bash
# backend
railway up            # follow prompts, set env vars

# frontend
vercel --prod         # vercel.json handles /api rewrite
```

---

## 10 Next Sprint 2 (after PI approval)

* ProtocolUploader + protocol diff viewer
* InventoryPage (Benchling or manual)
* Admin dashboard (query logs)
* Daily digest to Slack/email

---

### Beyond MVP (ideas)

* Cross-encoder BGE reranker
* ElasticSearch BM25 hybrid
* Feedback buttons (👍/👎)
* Knowledge-graph mode (genes ↔ assays ↔ reagents)
* Optional on-prem LLM to cut API cost

---

## 11 Quick Command Reference

| Purpose           | Command                                           |
| ----------------- | ------------------------------------------------- |
| Run local infra   | `docker-compose up -d`                            |
| Django dev server | `python manage.py runserver`                      |
| Celery worker     | `celery -A rna_backend worker -l info`            |
| Celery beat       | `celery -A rna_backend beat -l info`              |
| Thesis ingest     | `python ingest_thesis.py <pdf> "<author>" <year>` |
| Frontend dev      | `npm run dev`                                     |
| Deploy backend    | `railway up`                                      |
| Deploy frontend   | `vercel --prod`                                   |

---

### 🎯 **You are ready to build**

Follow the directory scaffold, run the commands in order, ingest a thesis + a handful of SOP PDFs, and start Sprint 1 day-by-day.

Ping me whenever you hit a blocker or finish Sprint 1—
we’ll tackle Sprint 2 and beyond together.

**Good coding & happy building, Vishal!**
