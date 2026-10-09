"""Policy, normalization and orchestration. Public compatibility imports remain here."""

from dataclasses import asdict

from .modules.contracts import Detector, Event, Scenario
from .modules.detections import RepeatedFailures, Rule
from .modules.scenarios import SCENARIOS, BenignLogins, FailedLogins, ThresholdLogins

__all__ = [
    "Detector",
    "Event",
    "Scenario",
    "RepeatedFailures",
    "Rule",
    "SCENARIOS",
    "BenignLogins",
    "FailedLogins",
    "ThresholdLogins",
    "validate",
    "normalize",
    "run",
]


def validate(config: dict) -> tuple[str, str]:
    if not isinstance(config, dict) or set(config) - {"rule"} != {
        "authorized",
        "allowed_targets",
        "target",
        "scenario",
    }:
        raise ValueError(
            "Config must contain exactly authorized, allowed_targets, target, scenario"
        )
    if config["authorized"] is not True:
        raise ValueError("Explicit laboratory authorization is required")
    allowed = config["allowed_targets"]
    if not isinstance(allowed, list) or not allowed or len(allowed) > 100:
        raise ValueError("allowed_targets must contain 1–100 lab identifiers")
    if any(
        not isinstance(t, str)
        or not t.startswith("lab://")
        or not t[6:]
        or len(t) > 128
        or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in t[6:])
        for t in allowed
    ):
        raise ValueError("Targets must be lab:// identifiers, not network addresses")
    target = config["target"]
    if not isinstance(target, str) or target not in allowed:
        raise ValueError("Target is outside the allowlist")
    scenario = config["scenario"]
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    if "rule" in config:
        rule_from_config(config["rule"])
    return target, scenario


def rule_from_config(value: dict) -> Rule:
    if not isinstance(value, dict) or set(value) != {
        "rule_id",
        "version",
        "threshold",
        "window_ms",
    }:
        raise ValueError("Rule must contain rule_id, version, threshold, window_ms")
    return Rule(**value)


def normalize(events: list[Event], target: str) -> list[Event]:
    if not isinstance(events, list) or not 1 <= len(events) <= 10000:
        raise ValueError("Telemetry must contain 1–10000 events")
    previous_time = -1
    for i, event in enumerate(events, 1):
        if (
            not isinstance(event, Event)
            or event.synthetic is not True
            or event.target != target
            or type(event.sequence) is not int
            or event.sequence != i
            or type(event.timestamp_ms) is not int
            or not 0 <= event.timestamp_ms <= 86400000
            or event.timestamp_ms < previous_time
            or not isinstance(event.kind, str)
            or event.kind != "authentication"
            or not isinstance(event.outcome, str)
            or event.outcome not in {"failure", "success"}
        ):
            raise ValueError("Invalid synthetic telemetry")
        previous_time = event.timestamp_ms
    return events


def run(config: dict) -> dict:
    target, scenario = validate(config)
    events = normalize(SCENARIOS[scenario].generate(target), target)
    rule = rule_from_config(config["rule"]) if "rule" in config else Rule()
    findings = RepeatedFailures(rule).detect(events)
    return {
        "schema_version": 2,
        "rule": rule.as_dict(),
        "mode": "synthetic-offline",
        "scenario": scenario,
        "target": target,
        "events": [asdict(e) for e in events],
        "findings": findings,
        "audit": [
            {"sequence": 1, "action": "authorization.accepted", "target": target},
            {"sequence": 2, "action": "scenario.completed", "event_count": len(events)},
            {"sequence": 3, "action": "detection.completed", "finding_count": len(findings)},
        ],
    }
