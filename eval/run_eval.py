"""Run the eval pipeline directly (no Jupyter needed)."""
import os, json, time, requests
from groq import Groq
import pandas as pd

import os
from dotenv import load_dotenv
load_dotenv("backend/.env")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL      = "https://post-accident-guidance-assistant-production.up.railway.app/chat"
JUDGE_MODEL  = "llama-3.3-70b-versatile"

groq_client = Groq(api_key=GROQ_API_KEY)

GOLDEN_CASES = [
    {"id": "DNF-001", "category": "repair_below_deductible", "description": "Repair ($200) < deductible ($500)",
     "scenario": {"repair_cost": 200, "deductible": 500, "annual_premium": 1200, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "CA", "notes": "Small scratch on bumper"},
     "expected_decision": "DO_NOT_CLAIM"},
    {"id": "DNF-002", "category": "repair_below_deductible", "description": "Repair ($300) < deductible ($1000)",
     "scenario": {"repair_cost": 300, "deductible": 1000, "annual_premium": 1800, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "TX", "notes": "Parking lot dent"},
     "expected_decision": "DO_NOT_CLAIM"},
    {"id": "DNF-003", "category": "repair_below_deductible", "description": "Repair ($500) == deductible ($500)",
     "scenario": {"repair_cost": 500, "deductible": 500, "annual_premium": 1400, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "OH", "notes": "Shopping cart damage"},
     "expected_decision": "DO_NOT_CLAIM"},
    {"id": "CLM-001", "category": "injuries_present", "description": "Injuries override everything -> CLAIM",
     "scenario": {"repair_cost": 1500, "deductible": 2000, "annual_premium": 1200, "at_fault": True, "injuries": True, "prior_claims_2yr": 0, "state": "CA", "notes": "Passenger complained of neck pain"},
     "expected_decision": "CLAIM"},
    {"id": "CLM-002", "category": "injuries_present", "description": "Injuries even when repair < deductible -> CLAIM",
     "scenario": {"repair_cost": 300, "deductible": 500, "annual_premium": 1600, "at_fault": False, "injuries": True, "prior_claims_2yr": 0, "state": "NY", "notes": "Rear-ended, driver has back pain"},
     "expected_decision": "CLAIM"},
    {"id": "CLM-003", "category": "injuries_present", "description": "Serious injuries, major repair -> CLAIM",
     "scenario": {"repair_cost": 12000, "deductible": 1000, "annual_premium": 2000, "at_fault": True, "injuries": True, "prior_claims_2yr": 0, "state": "TX", "notes": "Multi-car freeway accident, ambulance called"},
     "expected_decision": "CLAIM"},
    {"id": "CA-001", "category": "rideshare_vehicle", "description": "Uber mention -> CONSULT_AGENT",
     "scenario": {"repair_cost": 3000, "deductible": 500, "annual_premium": 1400, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "CA", "notes": "Was driving for Uber when accident happened"},
     "expected_decision": "CONSULT_AGENT"},
    {"id": "CA-002", "category": "rideshare_vehicle", "description": "Lyft mention -> CONSULT_AGENT",
     "scenario": {"repair_cost": 5000, "deductible": 500, "annual_premium": 1200, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "FL", "notes": "Lyft driver, had passenger in car"},
     "expected_decision": "CONSULT_AGENT"},
    {"id": "CA-003", "category": "rideshare_vehicle", "description": "Classic car -> CONSULT_AGENT",
     "scenario": {"repair_cost": 4000, "deductible": 500, "annual_premium": 1800, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "TX", "notes": "1969 classic Mustang, restored"},
     "expected_decision": "CONSULT_AGENT"},
    {"id": "CA-004", "category": "prior_claims", "description": "1 prior claim -> CONSULT_AGENT",
     "scenario": {"repair_cost": 5000, "deductible": 500, "annual_premium": 1600, "at_fault": True, "injuries": False, "prior_claims_2yr": 1, "state": "GA", "notes": "Second accident this year"},
     "expected_decision": "CONSULT_AGENT"},
    {"id": "CA-005", "category": "prior_claims", "description": "2 prior claims -> CONSULT_AGENT",
     "scenario": {"repair_cost": 8000, "deductible": 1000, "annual_premium": 2200, "at_fault": True, "injuries": False, "prior_claims_2yr": 2, "state": "NY", "notes": "Third incident in two years"},
     "expected_decision": "CONSULT_AGENT"},
    {"id": "MC-001", "category": "math_claim", "description": "net=$6500 >> 3yr=$1440 -> CLAIM",
     "scenario": {"repair_cost": 7000, "deductible": 500, "annual_premium": 1200, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "WA", "notes": "Hit guardrail on highway"},
     "expected_decision": "CLAIM"},
    {"id": "MC-002", "category": "math_claim", "description": "Not at fault: net=$4000 >> 3yr=$810 -> CLAIM",
     "scenario": {"repair_cost": 5000, "deductible": 1000, "annual_premium": 1800, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "AZ", "notes": "Other driver ran red light"},
     "expected_decision": "CLAIM"},
    {"id": "MC-003", "category": "math_claim", "description": "Major repair: net=$8500 >> 3yr=$2400 -> CLAIM",
     "scenario": {"repair_cost": 9500, "deductible": 1000, "annual_premium": 2000, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "CO", "notes": "Deer collision, significant body damage"},
     "expected_decision": "CLAIM"},
    {"id": "MNC-001", "category": "math_no_claim", "description": "High premium: net=$1500 << 3yr=$4800 -> DO_NOT_CLAIM",
     "scenario": {"repair_cost": 2000, "deductible": 500, "annual_premium": 4000, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "CA", "notes": "Minor fender bender, already paying high premium"},
     "expected_decision": "DO_NOT_CLAIM"},
    {"id": "MNC-002", "category": "math_no_claim", "description": "High premium: net=$1000 << 3yr=$3600 -> DO_NOT_CLAIM",
     "scenario": {"repair_cost": 1500, "deductible": 500, "annual_premium": 3000, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "IL", "notes": "Backed into a pole"},
     "expected_decision": "DO_NOT_CLAIM"},
    {"id": "NF-001", "category": "no_fault_state", "description": "Michigan no-fault: net=$3500 >> 3yr=$540 -> CLAIM",
     "scenario": {"repair_cost": 4000, "deductible": 500, "annual_premium": 1800, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "MI", "notes": "Intersection collision in Detroit"},
     "expected_decision": "CLAIM"},
    {"id": "NF-002", "category": "no_fault_state", "description": "New Jersey no-fault: net=$2500 >> 3yr=$420 -> CLAIM",
     "scenario": {"repair_cost": 3000, "deductible": 500, "annual_premium": 1400, "at_fault": True, "injuries": False, "prior_claims_2yr": 0, "state": "NJ", "notes": "Rear-ended at traffic light"},
     "expected_decision": "CLAIM"},
]

JUDGE_SYSTEM = """You are an expert evaluator assessing AI-generated auto insurance guidance.
Score the response on three dimensions (1-5 each):
1. ACCURACY: Does the financial breakdown correctly explain the math?
2. CLARITY: Is it easy for a non-expert driver to understand?
3. COMPLETENESS: Does it address key factors (state law, financial math, special circumstances)?
Return ONLY valid JSON:
{"accuracy_score": <1-5>, "clarity_score": <1-5>, "completeness_score": <1-5>, "overall_score": <avg, 1 decimal>, "strengths": "<one sentence>", "weaknesses": "<one sentence or None>"}"""


def call_api(case):
    payload = {"user_id": f"eval-{case['id']}", "message": "Please analyze my accident scenario.", "scenario": case["scenario"]}
    start = time.time()
    resp = requests.post(API_URL, json=payload, timeout=30)
    latency = round((time.time() - start) * 1000)
    resp.raise_for_status()
    data = resp.json()["recommendation"]
    return {**data, "latency_ms": latency}


def judge_response(result):
    content = (
        f"SCENARIO: {json.dumps(result['scenario'], indent=2)}\n\n"
        f"EXPECTED: {result['expected']}  ACTUAL: {result['actual']}  CORRECT: {result['passed']}\n\n"
        f"FINANCIAL BREAKDOWN:\n{result['financial_breakdown']}\n\n"
        f"REASONING:\n{result['reasoning']}\n\n"
        f"KEY FACTORS: {result['key_factors']}"
    )
    resp = groq_client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": content}],
        response_format={"type": "json_object"},
        temperature=0.0, max_tokens=256,
    )
    return json.loads(resp.choices[0].message.content)


# ── Phase 1: Run API calls ───────────────────────────────────────────────────
print(f"Running {len(GOLDEN_CASES)} test cases against live API...\n")
results = []
for i, case in enumerate(GOLDEN_CASES):
    try:
        api = call_api(case)
        passed = api["decision"] == case["expected_decision"]
        results.append({
            "id": case["id"], "category": case["category"], "description": case["description"],
            "expected": case["expected_decision"], "actual": api["decision"], "passed": passed,
            "confidence": api["confidence"], "confidence_score": api["confidence_score"],
            "latency_ms": api["latency_ms"], "reasoning": api["reasoning"],
            "financial_breakdown": api["financial_breakdown"],
            "key_factors": api["key_factors"], "next_steps": api["next_steps"],
            "scenario": case["scenario"],
        })
        print(f"  [{i+1:02d}] {case['id']:<8} {'PASS' if passed else 'FAIL'}  {case['expected_decision']:<15} -> {api['decision']:<15} ({api['latency_ms']}ms)")
    except Exception as e:
        print(f"  [{i+1:02d}] {case['id']:<8} ERROR: {e}")
        results.append({"id": case["id"], "category": case["category"], "description": case["description"],
                        "expected": case["expected_decision"], "actual": "ERROR", "passed": False,
                        "confidence": None, "confidence_score": None, "latency_ms": None,
                        "reasoning": "", "financial_breakdown": "", "key_factors": [], "next_steps": [],
                        "scenario": case["scenario"]})
    time.sleep(0.8)

# ── Phase 2: LLM-as-Judge ────────────────────────────────────────────────────
print(f"\nRunning LLM-as-Judge scoring...\n")
for i, result in enumerate(results):
    if result["actual"] == "ERROR":
        result.update({"accuracy_score": 0, "clarity_score": 0, "completeness_score": 0, "overall_score": 0, "strengths": "N/A", "weaknesses": "API error"})
        continue
    try:
        scores = judge_response(result)
        result.update(scores)
        print(f"  [{i+1:02d}] {result['id']:<8} acc={scores['accuracy_score']} clarity={scores['clarity_score']} complete={scores['completeness_score']} -> {scores['overall_score']}")
    except Exception as e:
        print(f"  [{i+1:02d}] {result['id']:<8} JUDGE ERROR: {e}")
        result.update({"accuracy_score": 0, "clarity_score": 0, "completeness_score": 0, "overall_score": 0, "strengths": "N/A", "weaknesses": str(e)})
    time.sleep(0.5)

# ── Scorecard ────────────────────────────────────────────────────────────────
df = pd.DataFrame(results)
total        = len(df)
passed_count = df["passed"].sum()
accuracy_pct = passed_count / total * 100

print("\n" + "=" * 55)
print("  POST-ACCIDENT GUIDANCE ASSISTANT — EVAL SCORECARD")
print("=" * 55)
print(f"  Test Cases          : {total}")
print(f"  Decision Accuracy   : {passed_count}/{total} ({accuracy_pct:.1f}%)")
print()
print(f"  Reasoning Quality (LLM-as-Judge, out of 5):")
print(f"    Accuracy          : {df['accuracy_score'].mean():.2f}")
print(f"    Clarity           : {df['clarity_score'].mean():.2f}")
print(f"    Completeness      : {df['completeness_score'].mean():.2f}")
print(f"    Overall           : {df['overall_score'].mean():.2f}")
print()
print(f"  Avg Latency         : {df['latency_ms'].dropna().mean():.0f}ms")
print("=" * 55)

print("\nAccuracy by Category:")
cat = df.groupby("category").agg(correct=("passed","sum"), total=("passed","count"), avg_quality=("overall_score","mean"))
cat["accuracy"] = (cat["correct"] / cat["total"] * 100).map("{:.0f}%".format)
cat["avg_quality"] = cat["avg_quality"].map("{:.2f}".format)
print(cat[["correct","total","accuracy","avg_quality"]].to_string())

failed = df[~df["passed"]][["id","category","expected","actual"]]
print(f"\nFailed cases: {'None' if failed.empty else ''}")
if not failed.empty:
    print(failed.to_string(index=False))

export_cols = ["id","category","description","expected","actual","passed","confidence","confidence_score",
               "latency_ms","accuracy_score","clarity_score","completeness_score","overall_score","strengths","weaknesses"]
df[export_cols].to_csv("eval/eval_results.csv", index=False)
print("\nResults saved to eval/eval_results.csv")
