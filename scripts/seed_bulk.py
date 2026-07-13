"""Generate 250 randomized accident scenarios and send to live API."""
import uuid, time, random, requests

API_URL = "https://post-accident-guidance-assistant-production.up.railway.app/chat"

STATES = ["CA", "TX", "FL", "NY", "IL", "WA", "GA", "OH", "MI", "NJ",
          "PA", "AZ", "CO", "OR", "TN", "VA", "NC", "MA", "MN", "MO",
          "NV", "UT", "MD", "WI", "IN"]

DEDUCTIBLES   = [250, 500, 750, 1000, 1500, 2000]
PREMIUMS      = [800, 1000, 1200, 1400, 1600, 1800, 2000, 2400, 2800, 3200, 4000]

STANDARD_NOTES = [
    "Rear-ended at a stop sign",
    "Hit a parked car while reversing",
    "Sideswiped on the highway",
    "Ran a red light, minor collision",
    "Black ice caused slide into barrier",
    "Hail damage on hood and roof",
    "Deer jumped onto road at night",
    "Backed into a pole in parking lot",
    "Shopping cart dented door",
    "Hit guardrail on freeway on-ramp",
    "Other driver merged into my lane",
    "Pothole caused blowout and spin-out",
    "Driver ahead braked suddenly",
    "Collision at roundabout",
    "Hydroplaned and hit median",
    "T-bone at intersection",
    "Sideswipe while changing lanes",
    "Rear-ended on freeway in traffic",
    "Minor fender bender in school zone",
    "Hit a trash can blown into road",
    "Construction zone merge collision",
    "Parking garage pillar scrape",
    "Bicycle hit my door when opening",
    "Rock chip cracked windshield",
    "Animal ran across road, swerved",
]

RIDESHARE_NOTES = [
    "Was driving for Uber when accident happened",
    "Lyft driver, had passenger in car",
    "DoorDash delivery when collision occurred",
    "Rideshare app was active, had a rider",
    "Was on Instacart delivery route",
]

CLASSIC_NOTES = [
    "1969 classic Mustang, fully restored",
    "Vintage 1957 Chevy, custom paint job",
    "Antique 1940 Ford pickup, show vehicle",
    "Classic 1972 Corvette, collector item",
]

INJURY_NOTES = [
    "Passenger complained of neck pain",
    "Driver has back pain after impact",
    "Airbags deployed, head injury possible",
    "Ambulance called at scene",
    "Multiple occupants, hospital visit needed",
    "Whiplash reported by all passengers",
    "Child in backseat, medical check needed",
]


def random_scenario():
    state = random.choice(STATES)
    deductible = random.choice(DEDUCTIBLES)
    premium = random.choice(PREMIUMS)
    at_fault = random.random() < 0.55
    prior_claims = random.choices([0, 1, 2], weights=[70, 22, 8])[0]

    # Injury rate ~15%
    injuries = random.random() < 0.15
    if injuries:
        repair_cost = random.uniform(1500, 14000)
        notes = random.choice(INJURY_NOTES)
    # Rideshare rate ~8%
    elif random.random() < 0.08:
        repair_cost = random.uniform(800, 8000)
        notes = random.choice(RIDESHARE_NOTES)
    # Classic car rate ~5%
    elif random.random() < 0.05:
        repair_cost = random.uniform(2000, 10000)
        notes = random.choice(CLASSIC_NOTES)
    else:
        # Spread: 30% minor (below/near deductible), 70% significant
        if random.random() < 0.30:
            repair_cost = random.uniform(100, deductible * 1.1)
        else:
            repair_cost = random.uniform(deductible * 0.5, 14000)
        notes = random.choice(STANDARD_NOTES)

    return {
        "repair_cost": round(repair_cost, 2),
        "deductible": float(deductible),
        "annual_premium": float(premium),
        "at_fault": at_fault,
        "injuries": injuries,
        "prior_claims_2yr": prior_claims,
        "state": state,
        "notes": notes,
    }


def send(scenario, index, total):
    payload = {
        "user_id": f"bulk-{str(uuid.uuid4())[:8]}",
        "message": "Please analyze my accident scenario.",
        "scenario": scenario,
    }
    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        decision = data["recommendation"]["decision"]
        print(f"[{index:03d}/{total}] {scenario['state']:2s} | ${scenario['repair_cost']:>7,.0f} | {decision}")
    except Exception as e:
        print(f"[{index:03d}/{total}] FAILED: {e}")


if __name__ == "__main__":
    random.seed(42)
    N = 250
    scenarios = [random_scenario() for _ in range(N)]

    print(f"Sending {N} randomized scenarios to {API_URL}\n")

    for i, scenario in enumerate(scenarios, 1):
        send(scenario, i, N)
        time.sleep(random.uniform(0.3, 0.8))

    print(f"\nDone. {N} records sent.")
