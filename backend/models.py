from pydantic import BaseModel, Field
from typing import Literal, Optional


class AccidentScenario(BaseModel):
    repair_cost: float = Field(..., gt=0, description="Estimated repair cost in USD")
    deductible: float = Field(..., ge=0, description="Policy deductible in USD")
    annual_premium: float = Field(..., gt=0, description="Annual premium in USD")
    at_fault: bool = Field(..., description="Was the user at fault?")
    injuries: bool = Field(False, description="Were there any injuries?")
    prior_claims_2yr: int = Field(0, ge=0, description="Claims filed in last 2 years")
    state: str = Field(..., description="US state where accident occurred")
    notes: str = Field("", description="Additional context (rideshare, classic car, etc.)")


class ClaimRecommendation(BaseModel):
    decision: Literal["CLAIM", "DO_NOT_CLAIM", "CONSULT_AGENT", "OUT_OF_SCOPE"]
    confidence: Literal["High", "Medium", "Low"]
    confidence_score: float
    summary: str
    financial_breakdown: str
    key_factors: list[str]
    reasoning: str
    next_steps: list[str]
    disclaimer: str = "This is general guidance, not professional insurance or legal advice."


class ChatRequest(BaseModel):
    user_id: str
    message: str
    scenario: Optional[AccidentScenario] = None


class ChatResponse(BaseModel):
    user_id: str
    recommendation: ClaimRecommendation
    financial_calc: dict
    session_id: str


class FeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    rating: Literal["thumbs_up", "thumbs_down"]
    comment: Optional[str] = None
