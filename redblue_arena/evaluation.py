"""Fixture evaluation, not a production efficacy estimate."""

from .core import run, validate


def evaluate(config: dict) -> dict:
    validate(config)
    cases = (
        ("failed-logins", True),
        ("threshold-logins", True),
        ("benign-logins", False),
        ("spread-logins", False),
    )
    matrix = {"true_positive": 0, "false_positive": 0, "true_negative": 0, "false_negative": 0}
    results = []
    for scenario, expected in cases:
        report = run({**config, "scenario": scenario})
        actual = bool(report["findings"])
        key = ("true_" if expected == actual else "false_") + ("positive" if actual else "negative")
        matrix[key] += 1
        results.append(
            {
                "scenario": scenario,
                "expected_detection": expected,
                "detected": actual,
                "event_count": len(report["events"]),
            }
        )
    negatives = matrix["false_positive"] + matrix["true_negative"]
    positives = matrix["true_positive"] + matrix["false_negative"]
    return {
        "schema_version": 1,
        "mode": "fixture-evaluation",
        "cases": results,
        "confusion_matrix": matrix,
        "false_positive_rate": matrix["false_positive"] / negatives,
        "recall": matrix["true_positive"] / positives,
        "limitation": "Synthetic fixtures only; labels assume the default rule v2",
    }
