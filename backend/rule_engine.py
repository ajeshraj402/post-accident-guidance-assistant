NO_FAULT_STATES = {
    "michigan", "new york", "florida", "new jersey", "pennsylvania",
    "hawaii", "kansas", "kentucky", "massachusetts", "minnesota",
    "north dakota", "utah"
}


def check_special_cases(scenario: dict) -> dict | None:
    notes = scenario.get("notes", "").lower()
    prior = scenario.get("prior_claims_2yr", 0)

    if prior >= 1:
        return {
            "force_decision": "CONSULT_AGENT",
            "force_reason": (
                "You have a prior claim in the last 2 years. Filing again makes 2 claims "
                "in 2 years, which statistically triggers non-renewal or significant "
                "rate increases. Consult your agent before filing."
            ),
        }

    rideshare_keywords = ["uber", "lyft", "doordash", "rideshare", "grubhub", "instacart", "delivery app"]
    if any(k in notes for k in rideshare_keywords):
        return {
            "force_decision": "CONSULT_AGENT",
            "force_reason": (
                "Rideshare/delivery app accidents involve complex coverage gaps between "
                "personal and commercial policies. Your personal policy may exclude this. "
                "Consult your agent and the app's insurance team."
            ),
        }

    collectible_keywords = ["classic", "collectible", "antique", "vintage", "custom"]
    if any(k in notes for k in collectible_keywords):
        return {
            "force_decision": "CONSULT_AGENT",
            "force_reason": (
                "Classic/collectible vehicles require agreed-value or stated-value policies. "
                "A standard policy pays Actual Cash Value, which may be far below market value. "
                "Consult a specialist insurer."
            ),
        }

    return None


def calculate_financial_impact(
    repair_cost: float,
    deductible: float,
    annual_premium: float,
    at_fault: bool,
    prior_claims_2yr: int = 0,
    injuries: bool = False,
    state: str = "",
) -> dict:
    is_no_fault = state.strip().lower() in NO_FAULT_STATES

    if injuries:
        return {
            "force_decision": "CLAIM",
            "force_reason": (
                "Injuries are present. Always file a claim when injuries are involved — "
                "medical costs and liability exposure far outweigh premium considerations."
            ),
        }

    if is_no_fault:
        net = repair_cost - deductible
        if net <= 0:
            return {
                "force_decision": "DO_NOT_CLAIM",
                "force_reason": (
                    f"Repair cost (${repair_cost:,.0f}) is at or below your deductible "
                    f"(${deductible:,.0f}). You would receive nothing from the insurer."
                ),
            }
        annual_increase = round(annual_premium * 0.10, 2)
        three_year_cost = round(annual_increase * 3, 2)
        return {
            "force_decision": "CLAIM",
            "force_reason": f"{state.title()} is a no-fault state. File with your own insurer.",
            "net_claim_value": round(net, 2),
            "annual_premium_increase": annual_increase,
            "three_year_cost": three_year_cost,
            "is_no_fault_state": True,
            "math_summary": (
                f"Net claim value: ${net:,.0f}. "
                f"Estimated premium increase: ${annual_increase:,.0f}/yr (${three_year_cost:,.0f} over 3 years)."
            ),
        }

    if repair_cost <= deductible:
        return {
            "force_decision": "DO_NOT_CLAIM",
            "force_reason": (
                f"Repair cost (${repair_cost:,.0f}) is at or below your deductible "
                f"(${deductible:,.0f}). Filing would cost you more than not filing."
            ),
        }

    net = repair_cost - deductible
    pct = 0.40 if at_fault else 0.15
    if prior_claims_2yr >= 1:
        pct += 0.10

    annual_increase = round(annual_premium * pct, 2)
    three_year_cost = round(annual_increase * 3, 2)
    financially_worth = net > three_year_cost

    return {
        "force_decision": None,
        "net_claim_value": round(net, 2),
        "annual_premium_increase": annual_increase,
        "three_year_cost": three_year_cost,
        "financially_worth_claiming": financially_worth,
        "premium_increase_pct": round(pct * 100, 1),
        "math_summary": (
            f"Net claim value: ${net:,.0f}. "
            f"Premium increase: ${annual_increase:,.0f}/yr ({pct*100:.0f}%), "
            f"${three_year_cost:,.0f} over 3 years. "
            f"Financially {'worth' if financially_worth else 'NOT worth'} claiming."
        ),
    }
