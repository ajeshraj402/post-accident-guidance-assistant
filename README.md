# Post-Accident Guidance Assistant

An AI-powered tool that helps drivers decide whether to file an insurance claim or pay out of pocket after a car accident — built as a portfolio project targeting AI Engineering roles.

**Live Demo:** https://post-accident-guidance-assistant.vercel.app  
**Analytics Dashboard:** https://charmingalbacore3550.grafana.net/public-dashboards/eb471985a7344aed9cc029587b51bf75

---

## What It Does

Enter your accident details — repair cost, deductible, annual premium, state, fault, injuries, prior claims — and the system returns a structured recommendation: **CLAIM**, **DO_NOT_CLAIM**, or **CONSULT_AGENT**, with a plain-English explanation of the math and relevant state law.

---

## Architecture

```
User (Next.js frontend)
        │
        ▼
FastAPI Backend (Railway)
        │
        ├── Rule Engine      → deterministic math (deductible check, net vs 3yr premium cost)
        ├── RAG              → Pinecone vector search on 60 chunks, 15 state insurance laws
        └── LLM (Groq)       → explanation generation only, never recalculates math
                │
                ├── ClickHouse   → analytics logging (decision, latency, confidence)
                └── Grafana      → live monitoring dashboard
```

**Key design decision:** The LLM is not the decision maker. A deterministic rule engine handles all financial math and hard rules (injuries → always CLAIM, repair ≤ deductible → always DO_NOT_CLAIM, rideshare → always CONSULT_AGENT). The LLM only generates the natural language explanation using pre-computed numbers.

---

## Eval Results

Evaluated using 18 golden test cases across 7 categories with an LLM-as-judge scorer.

| Metric | Score |
|---|---|
| Decision Accuracy | **18/18 (100%)** |
| Reasoning Quality (LLM-as-Judge) | **4.82 / 5** |
| Accuracy Score | 4.78 / 5 |
| Clarity Score | 4.94 / 5 |
| Completeness Score | 4.72 / 5 |
| Avg Latency | ~13s |

**Categories tested:** repair below deductible · injuries present · rideshare vehicle · prior claims · math-based CLAIM · math-based DO_NOT_CLAIM · no-fault states (MI, NJ, FL)

---

## Tech Stack

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)
![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?style=for-the-badge&logo=clickhouse&logoColor=black)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, Tailwind CSS v4, TypeScript |
| Backend | FastAPI, Python 3.13, Pydantic v2 |
| LLM | Groq (`llama-3.3-70b-versatile`), temp=0.1, JSON mode |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Vector DB | Pinecone serverless (`insurance-laws` index, 60 chunks) |
| Analytics | ClickHouse Cloud (MergeTree), Grafana Cloud |
| Eval | LLM-as-judge pipeline (Groq), pandas scorecard |
| Deployment | Vercel (frontend), Railway (backend) |

---

## Project Structure

```
├── backend/
│   ├── main.py          # FastAPI app, /chat, /conversation, /feedback endpoints
│   ├── rule_engine.py   # Deterministic math: deductible check, net vs 3yr cost
│   ├── rag.py           # Pinecone retrieval, lazy singleton embed model
│   ├── llm.py           # Groq LLM, system prompt, JSON response parsing
│   ├── analytics.py     # ClickHouse logging, silent failure pattern
│   ├── models.py        # Pydantic v2 models
│   └── config.py        # Env var loading
├── frontend/
│   └── app/
│       ├── page.tsx     # Accident form + recommendation results UI
│       └── globals.css
├── eval/
│   ├── llm_judge_eval.ipynb   # Colab-ready eval notebook
│   └── run_eval.py            # CLI eval runner
└── scripts/
    ├── seed_data.py     # 25 curated test scenarios
    └── seed_bulk.py     # 250 randomized scenarios for load testing
```

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY, PINECONE_API_KEY, CLICKHOUSE_* vars
uvicorn main:app --reload

# Frontend
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

**Required environment variables:**
```
GROQ_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=insurance-laws
CLICKHOUSE_HOST=
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
```

---

## Key Engineering Decisions

**Hybrid decision engine over pure LLM** — LLMs hallucinate math. All financial calculations are deterministic Python; the LLM only touches natural language generation. This is why decision accuracy is 100%.

**Silent analytics failure** — ClickHouse logging is wrapped in try/except with no re-raise. Analytics failure never breaks the user-facing API response.

**Lazy singleton for embeddings** — The sentence-transformers model loads once on first request and is reused. Cold start adds ~3s; subsequent requests are fast.

**RAG with metadata filtering** — Pinecone queries filter by `state` metadata before similarity search, so a California user never gets Michigan no-fault law context.
