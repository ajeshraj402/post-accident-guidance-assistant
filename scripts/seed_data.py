"""Send synthetic accident scenarios to the live API to populate ClickHouse."""
import uuid
import time
import random
import requests

API_URL = "https://post-accident-guidance-assistant-production.up.railway.app/chat"

SCENARIOS = [
    # Clear DO_NOT_CLAIM: repair < deductible
    {"repair_cost": 300, "deductible": 500, "annual_premium": 1200, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "CA", "notes": "Minor fender bender in parking lot"},
    {"repair_cost": 200, "deductible": 1000, "annual_premium": 1800, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "TX", "notes": "Small scratch on bumper"},
    {"repair_cost": 400, "deductible": 500,  "annual_premium": 1400, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "FL", "notes": "Parking lot ding, other driver left"},
    # Clear CLAIM: injuries
    {"repair_cost": 5000, "deductible": 500,  "annual_premium": 1600, "at_fault": True,  "injuries": True,  "prior_claims_2yr": 0, "state": "NY", "notes": "Rear-ended at stop sign, neck pain"},
    {"repair_cost": 8000, "deductible": 1000, "annual_premium": 2000, "at_fault": False, "injuries": True,  "prior_claims_2yr": 1, "state": "CA", "notes": "T-bone intersection crash, passenger injured"},
    {"repair_cost": 3000, "deductible": 500,  "annual_premium": 1500, "at_fault": True,  "injuries": True,  "prior_claims_2yr": 0, "state": "IL", "notes": "Ran red light, airbags deployed"},
    # CLAIM: repair well above deductible, no prior claims
    {"repair_cost": 7500, "deductible": 500,  "annual_premium": 1200, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "WA", "notes": "Hit guardrail on highway"},
    {"repair_cost": 4200, "deductible": 1000, "annual_premium": 1600, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "TX", "notes": "Other driver sideswiped me"},
    {"repair_cost": 9000, "deductible": 500,  "annual_premium": 1800, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "GA", "notes": "Total loss, deer strike at night"},
    # CONSULT_AGENT: prior claims or rideshare
    {"repair_cost": 3500, "deductible": 500,  "annual_premium": 1400, "at_fault": True,  "injuries": False, "prior_claims_2yr": 2, "state": "CA", "notes": "Third accident in two years"},
    {"repair_cost": 2000, "deductible": 500,  "annual_premium": 1200, "at_fault": True,  "injuries": False, "prior_claims_2yr": 1, "state": "FL", "notes": "Was driving for Uber when accident happened"},
    {"repair_cost": 6000, "deductible": 1000, "annual_premium": 2200, "at_fault": True,  "injuries": False, "prior_claims_2yr": 2, "state": "NY", "notes": "Multiple prior claims, unsure about coverage"},
    # Borderline cases
    {"repair_cost": 1800, "deductible": 1000, "annual_premium": 1400, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "OH", "notes": "Rear-ended someone at low speed"},
    {"repair_cost": 2500, "deductible": 500,  "annual_premium": 2400, "at_fault": True,  "injuries": False, "prior_claims_2yr": 1, "state": "MI", "notes": "No-fault state, minor collision"},
    {"repair_cost": 1200, "deductible": 500,  "annual_premium": 1000, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "NJ", "notes": "Hit from behind, small damage"},
    # No-fault states
    {"repair_cost": 4000, "deductible": 1000, "annual_premium": 1800, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "MI", "notes": "Michigan no-fault collision"},
    {"repair_cost": 3000, "deductible": 500,  "annual_premium": 1600, "at_fault": True,  "injuries": True,  "prior_claims_2yr": 0, "state": "NJ", "notes": "New Jersey PIP claim situation"},
    {"repair_cost": 5500, "deductible": 500,  "annual_premium": 1400, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "FL", "notes": "Florida no-fault fender bender"},
    # High premium sensitivity
    {"repair_cost": 2000, "deductible": 500,  "annual_premium": 3600, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "CA", "notes": "Already paying high premium in CA"},
    {"repair_cost": 1500, "deductible": 500,  "annual_premium": 800,  "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "TN", "notes": "Low premium, small repair needed"},
    # More varied states
    {"repair_cost": 6000, "deductible": 1000, "annual_premium": 1600, "at_fault": False, "injuries": False, "prior_claims_2yr": 0, "state": "AZ", "notes": "Not at fault, significant damage"},
    {"repair_cost": 3500, "deductible": 500,  "annual_premium": 1200, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "CO", "notes": "Black ice caused slide into barrier"},
    {"repair_cost": 800,  "deductible": 1000, "annual_premium": 1400, "at_fault": True,  "injuries": False, "prior_claims_2yr": 0, "state": "OR", "notes": "Shopping cart dented door"},
    {"repair_cost": 12000,"deductible": 500,  "annual_premium": 1800, "at_fault": True,  "injuries": True,  "prior_claims_2yr": 0, "state": "TX", "notes": "Major crash on freeway, multiple vehicles"},
    {"repair_cost": 4500, "deductible": 1000, "annual_premium": 2000, "at_fault": False, "injuries": False, "prior_claims_2yr": 1, "state": "VA", "notes": "Not at fault but have prior claim"},
]

def send_scenario(scenario: dict, index: int) -> None:
    user_id = f"seed-agent-{str(uuid.uuid4())[:8]}"
    payload = {"user_id": user_id, "message": "Please analyze my accident scenario.", "scenario": scenario}

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        decision = data["recommendation"]["decision"]
        confidence = data["recommendation"]["confidence"]
        print(f"[{index+1:02d}] {scenario['state']:2s} | ${scenario['repair_cost']:>6,.0f} | {decision:<15} | {confidence}")
    except Exception as e:
        print(f"[{index+1:02d}] FAILED: {e}")


if __name__ == "__main__":
    print(f"Sending {len(SCENARIOS)} scenarios to {API_URL}\n")
    print(f"{'#':>4}  {'State':<5} {'Repair':>8}  {'Decision':<15}  Confidence")
    print("-" * 55)

    for i, scenario in enumerate(SCENARIOS):
        send_scenario(scenario, i)
        time.sleep(random.uniform(0.5, 1.5))  # polite pacing

    print(f"\nDone. Check ClickHouse for {len(SCENARIOS)} new rows.")
