# Post-Accident Guidance Assistant — Session Memory
> Last updated: June 29, 2026. Share this file with Claude at the start of every session.

---

## What We're Building
An AI-powered web app that tells a person after a car accident: **Should I file an insurance claim or pay out of pocket?**

- **Type:** Portfolio project — live, zero cost
- **Target:** AI Engineering roles (like Jerry.ai)
- **Users:** Regular people (not fleet managers)

---

## Why Jerry.ai
Jerry.ai is an AI auto insurance platform (50k+ chats/month). Their tools: **ClickHouse, Metabase, Python, JupyterHub, GitHub**. Their role focuses on evaluation frameworks, prompt strategies, answer quality improvement, and LLM guardrails. This project mirrors all of that.

---

## Finalized Tech Stack (Zero Cost, All Permanent Free Tiers)

| Layer | Tool | Free? |
|---|---|---|
| Frontend | Next.js | Vercel (free forever) |
| Backend | FastAPI (Python) | AWS Lambda + API Gateway (1M req/month free) |
| LLM | Groq (Llama 3.3 70B) | Free tier, no billing required |
| Structured Output | Pydantic + JSON mode | Free library |
| App Database | AWS DynamoDB | 25 GB free forever |
| Vector DB | Pinecone | Free tier |
| Analytics DB | ClickHouse Cloud | Free tier |
| Evaluation | Google Colab (Jupyter) | Free |
| Dashboard | Metabase on Railway | Free |
| Auth | AWS Cognito | 50k MAU free forever |
| Version Control | GitHub | Free |

**NOT using LangChain** — too rigid, too many abstraction layers, hard to debug. Replaced with direct Groq SDK + manual DynamoDB memory + Pydantic.
**NOT using Gemini** — free tier requires billing setup in some regions (India). Switched to Groq which is truly free with no billing required.

---

## System Architecture (Data Flow)

```
User input
  → Guardrails check (in scope? injury detected?)
  → RAG retrieves state insurance laws (Pinecone)
  → Rule Engine calculates financial impact (pure Python math)
  → Gemini LLM generates plain-English explanation (Instructor/Pydantic)
  → Response returned with confidence score
  → Conversation logged to ClickHouse
  → User feedback captured (thumbs up/down)
  → Weekly: Colab notebook runs LLM-as-judge eval
  → Metabase dashboard updated
```

### Key Design Decision: Hybrid Engine
- **Rule engine (Python):** All math — deductible vs repair cost, premium impact over 3 years
- **LLM (Gemini):** Only natural language — understanding input + explaining output
- LLMs hallucinate math. Rule engines can't talk. Split the responsibility.

---

## Structured Output Model

```python
class ClaimRecommendation(BaseModel):
    decision: Literal["CLAIM", "DO_NOT_CLAIM", "CONSULT_AGENT", "OUT_OF_SCOPE"]
    confidence: Literal["High", "Medium", "Low"]
    confidence_score: float          # 0.0 to 1.0
    summary: str                     # One sentence
    financial_breakdown: str         # Plain-English math
    key_factors: list[str]           # 2-4 factors
    reasoning: str                   # Full explanation
    next_steps: list[str]            # 2-3 action items
    disclaimer: str                  # Always included
```

---

## RAG Pipeline
- **Sources:** iii.org, nolo.com, NAIC, state DOI websites
- **Priority states:** 12 no-fault states + top 5 populous (CA, TX, FL, NY, IL) = ~15 states
- **Two layers:**
  1. Structured JSON per state (no-fault status, min limits, PIP, SOL) → rule engine
  2. Scraped text chunks from iii.org + nolo.com → embedded into Pinecone → RAG context

**Tomorrow's task:** Write the structured JSON for 15 priority states first (most important, powers the rule engine).

---

## Guardrails
- Out-of-scope → return OUT_OF_SCOPE, redirect user
- Injury detected → always force CLAIM (liability risk overrides math)
- confidence_score < 0.65 → override to CONSULT_AGENT
- Suspicious inputs → flag for manual review

---

## 9 Build Phases

| Phase | What | Status |
|---|---|---|
| 1 | Prototype in Colab — 15 test scenarios + system prompt | **DONE — 15/15 passed** |
| 2 | Core decision engine (pure Python math) | **DONE — built inside Phase 1 notebook** |
| 3 | LLM + structured output (Groq + Pydantic) | **DONE — built inside Phase 1 notebook** |
| 4 | RAG pipeline (Pinecone + state laws) | **DONE — 15/15 with RAG, 60 chunks across 15 states** |
| 5 | FastAPI backend | Not started |
| 6 | Memory + DynamoDB | Not started |
| 7 | Next.js frontend | Not started |
| 8 | Evaluation pipeline (ClickHouse + Colab + Metabase) | Not started |
| 9 | Deploy (AWS Lambda + Vercel) | Not started |

---

## 15 Test Scenarios (Eval Baseline)

### Clear: DO NOT CLAIM
1. Repair $650, deductible $500, at-fault, no injuries, Texas → **DO_NOT_CLAIM** (net gain $150 vs $1,440 premium increase over 3yr)
2. Repair $400, deductible $500, at-fault, no injuries, California → **DO_NOT_CLAIM** (repair below deductible, zero net gain)
3. Repair $900, deductible $500, not at-fault, other driver uninsured, UM coverage yes → **CLAIM via UM** (no premium impact, net $400)

### Clear: CLAIM
4. Repair $12,000, deductible $1,000, not at-fault, no injuries, Georgia → **CLAIM** (net $11,000, no fault = low premium impact)
5. Repair $3,500, deductible $500, not at-fault, passenger has neck pain → **CLAIM** (injuries present, always claim)
6. Total loss, car worth $8,000, repair $9,000, deductible $1,000, at-fault → **CLAIM** (nets $7,000 after deductible)

### Edge Cases
7. Repair $2,000, deductible $500, Michigan, no injuries → **CLAIM** (no-fault state, own insurance covers regardless)
8. Repair $1,800, deductible $500, at-fault, 1 prior claim in 18 months → **CONSULT_AGENT** (2 claims in 2yr risks cancellation)
9. Repair $700, deductible $500, other driver fled, no UM coverage → **DO_NOT_CLAIM** (net $200 not worth triggering collision claim)
10. No vehicle damage, medical bills $4,500, not at-fault, injuries → **CLAIM** (always claim for medical costs)
11. Repair $750, deductible $500, at-fault, premium $900/yr → **DO_NOT_CLAIM** (net $250 vs $1,080 over 3yr)
12. Repair $3,000, deductible $500, at-fault, Uber driver, app was on → **CONSULT_AGENT** (rideshare gap complexity)
13. Repair $2,500, deductible $1,000, accident in Florida, home state Ohio → **CLAIM** (Florida no-fault rules apply at scene)
14. Repair $5,000, standard policy, classic car worth $45,000 → **CONSULT_AGENT** (standard policy undervalues collectible)
15. User asks about health insurance → **OUT_OF_SCOPE** (guardrail fires, redirect)

---

## System Prompt v1

```
You are an expert post-accident insurance guidance assistant. Your sole purpose
is to help people decide whether they should file an auto insurance claim or pay
out of pocket after a car accident.

You have access to:
1. STATE-SPECIFIC INSURANCE LAWS: {rag_context}
2. FINANCIAL CALCULATION: {rule_engine_output}
3. USER CONVERSATION HISTORY: {conversation_history}

DECISION FRAMEWORK:
- ALWAYS recommend claiming if injuries are involved (liability risk is too high)
- ALWAYS recommend DO_NOT_CLAIM if repair cost <= deductible
- CONSULT_AGENT for: rideshare/commercial vehicles, 2+ claims in 2 years,
  collectible cars, unclear fault in no-fault states
- For everything else: compare net_claim_value vs three_year_premium_cost

YOUR RESPONSE MUST:
1. State the decision clearly: CLAIM, DO NOT CLAIM, or CONSULT YOUR AGENT
2. Show the math in simple terms (no jargon)
3. Explain WHY in plain English a stressed person can understand
4. List 2-3 key factors that drove the decision
5. Include confidence level (High / Medium / Low)
6. Always end with the disclaimer

YOUR RESPONSE MUST NOT:
- Perform financial calculations yourself (use the provided calculation)
- Discuss health, life, or non-auto insurance topics
- Give legal advice beyond "consult an attorney"
- Make up state laws not in the provided context

TONE: Calm, clear, empathetic. Get to the point fast.
OUTPUT FORMAT: Return structured JSON matching the ClaimRecommendation schema.
```

---

## Current Status & Next Steps
**Phase 1, 2, 3 complete.** Eval baseline: 15/15 passed.

**Next: Phase 5 — FastAPI Backend**
Move the notebook logic into a proper FastAPI app with these endpoints:
- `POST /chat` — main recommendation endpoint
- `GET /conversation/{user_id}` — fetch conversation history
- `POST /feedback` — store thumbs up/down
Deploy to AWS Lambda using Mangum adapter.

**Files:**
- `phase1_prototype.ipynb` — fully working prototype (Phases 1-4 complete)
- RAG: Pinecone index `insurance-laws`, 60 chunks, 15 states, `all-MiniLM-L6-v2` embeddings
- LLM: Groq `llama-3.3-70b-versatile`, JSON mode, Pydantic validation

---

## Reference Files
- `Post_Accident_Guidance_Assistant_Approach.pdf` — full technical approach document (in this folder)
