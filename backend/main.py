import uuid
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from models import AccidentScenario, ChatRequest, ChatResponse, FeedbackRequest, ClaimRecommendation
from rule_engine import check_special_cases, calculate_financial_impact
from rag import retrieve_state_context
from llm import get_llm_recommendation
from analytics import log_recommendation, log_feedback

app = FastAPI(
    title="Post-Accident Guidance Assistant",
    description="AI-powered claim vs. no-claim decision engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_pipeline(scenario: AccidentScenario) -> tuple[dict, ClaimRecommendation]:
    scenario_dict = scenario.model_dump()

    special = check_special_cases(scenario_dict)
    if special and special.get("force_decision") == "CONSULT_AGENT":
        financial_calc = special
    else:
        financial_calc = calculate_financial_impact(
            repair_cost=scenario.repair_cost,
            deductible=scenario.deductible,
            annual_premium=scenario.annual_premium,
            at_fault=scenario.at_fault,
            prior_claims_2yr=scenario.prior_claims_2yr,
            injuries=scenario.injuries,
            state=scenario.state,
        )

    rag_context = retrieve_state_context(scenario.state)
    recommendation = get_llm_recommendation(scenario_dict, financial_calc, rag_context)

    return financial_calc, recommendation


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/health/clickhouse")
def health_clickhouse():
    try:
        from analytics import get_client
        client = get_client()
        result = client.query("SELECT 1").result_set[0][0]
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if request.scenario is None:
        raise HTTPException(
            status_code=400,
            detail="Scenario data is required. Please provide accident details.",
        )

    start = time.time()
    try:
        financial_calc, recommendation = run_pipeline(request.scenario)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    latency_ms = int((time.time() - start) * 1000)
    session_id = str(uuid.uuid4())

    log_recommendation(
        session_id=session_id,
        user_id=request.user_id,
        scenario=request.scenario.model_dump(),
        decision=recommendation.decision,
        confidence=recommendation.confidence,
        confidence_score=recommendation.confidence_score,
        latency_ms=latency_ms,
    )

    return ChatResponse(
        user_id=request.user_id,
        recommendation=recommendation,
        financial_calc=financial_calc,
        session_id=session_id,
    )


@app.get("/conversation/{user_id}")
def get_conversation(user_id: str):
    return {
        "user_id": user_id,
        "conversations": [],
        "note": "Conversation memory not yet implemented (Phase 6).",
    }


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    log_feedback(session_id=request.session_id, rating=request.rating)
    return {"status": "received", "session_id": request.session_id}


handler = Mangum(app)
