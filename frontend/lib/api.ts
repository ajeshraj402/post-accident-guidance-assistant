const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export interface AccidentScenario {
  repair_cost: number
  deductible: number
  annual_premium: number
  at_fault: boolean
  injuries: boolean
  prior_claims_2yr: number
  state: string
  notes: string
}

export interface ClaimRecommendation {
  decision: 'CLAIM' | 'DO_NOT_CLAIM' | 'CONSULT_AGENT' | 'OUT_OF_SCOPE'
  confidence: 'High' | 'Medium' | 'Low'
  confidence_score: number
  summary: string
  financial_breakdown: string
  key_factors: string[]
  reasoning: string
  next_steps: string[]
  disclaimer: string
}

export interface ChatResponse {
  user_id: string
  recommendation: ClaimRecommendation
  financial_calc: Record<string, unknown>
  session_id: string
}

export async function getRecommendation(scenario: AccidentScenario): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: 'web-user-' + Date.now(),
      message: 'Should I claim?',
      scenario,
    }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Something went wrong. Please try again.')
  }
  return res.json()
}

export async function submitFeedback(
  userId: string,
  sessionId: string,
  rating: 'thumbs_up' | 'thumbs_down'
): Promise<void> {
  await fetch(`${API_URL}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, rating }),
  })
}
