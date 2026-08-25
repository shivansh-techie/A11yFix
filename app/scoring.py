# weights loosely based on axe-core's own severity definitions
IMPACT_WEIGHTS = {
    "critical": 10,
    "serious": 7,
    "moderate": 4,
    "minor": 2,
}


def compute_score(violations: list) -> float:
    if not violations:
        return 100.0
    deduction = sum(IMPACT_WEIGHTS.get(v.get("impact", "minor"), 2) for v in violations)
    return round(max(0.0, 100.0 - deduction), 1)
