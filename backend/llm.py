import json
from groq import Groq
from models import ClaimRecommendation
from config import GROQ_API_KEY, LLM_MODEL

_groq_client = None

SYSTEM_PROMPT = """You are an expert post-accident insurance guidance assistant. Your sole purpose
is to help people decide whether they should file an auto insurance claim or pay out of pocket
after a car accident.

You have access to:
1. STATE-SPECIFIC INSURANCE LAWS: provided in the user message as RAG_CONTEXT
2. FINANCIAL CALCULATION: provided in the user message as FINANCIAL_CALC (pre-computed — do NOT recalculate)
3. USER SCENARIO: the accident details

DECISION FRAMEWORK:
- ALWAYS recommend CLAIM if injuries are involved (liability risk overrides all math)
- ALWAYS recommend DO_NOT_CLAIM if repair cost <= deductible (nothing to gain)
- ALWAYS use CONSULT_AGENT for: rideshare/delivery vehicles, 2+ claims in 2 years, collectible cars
- For everything else: if net_claim_value > three_year_cost → CLAIM, else DO_NOT_CLAIM
- If force_decision is set in FINANCIAL_CALC, use that decision — do not override it

YOUR RESPONSE MUST:
1. State the decision clearly
2. Explain the math in plain English (use numbers from FINANCIAL_CALC, do not compute yourself)
3. Reference the state law context naturally
4. List 2-4 key factors that drove the decision
5. Be calm, clear, and empathetic — user is stressed

YOUR RESPONSE MUST NOT:
- Perform any financial calculations yourself
- Discuss health, life, or non-auto insurance
- Give legal advice beyond "consult an attorney"
- Make up state laws not in the provided RAG_CONTEXT
- Exceed 300 words in the reasoning field

TONE: Calm, direct, empathetic. Get to the point fast.

OUTPUT: Return ONLY valid JSON matching this exact schema:
{
  "decision": "CLAIM" | "DO_NOT_CLAIM" | "CONSULT_AGENT" | "OUT_OF_SCOPE",
  "confidence": "High" | "Medium" | "Low",
  "confidence_score": 0.0 to 1.0,
  "summary": "One sentence summary of the recommendation",
  "financial_breakdown": "Plain-English explanation of the math",
  "key_factors": ["factor 1", "factor 2", "factor 3"],
  "reasoning": "Full explanation referencing state laws and financial calc",
  "next_steps": ["step 1", "step 2", "step 3"],
  "disclaimer": "This is general guidance, not professional insurance or legal advice."
}"""


def _get_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def get_llm_recommendation(
    scenario: dict,
    financial_calc: dict,
    rag_context: str,
) -> ClaimRecommendation:
    user_content = (
        "ACCIDENT SCENARIO:\n"
        + json.dumps(scenario, indent=2)
        + "\n\nFINANCIAL_CALC (pre-computed — use these numbers, do not recalculate):\n"
        + json.dumps(financial_calc, indent=2)
        + "\n\nRAG_CONTEXT (state insurance laws):\n"
        + rag_context
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1024,
    )

    data = json.loads(response.choices[0].message.content)
    return ClaimRecommendation(**data)
