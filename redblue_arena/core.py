"""Explicit module contracts and an offline orchestration pipeline."""

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class Event:
    sequence: int
    target: str
    kind: str
    outcome: str
    synthetic: bool = True


class Scenario(Protocol):
    def generate(self, target: str) -> list[Event]: ...


class Detector(Protocol):
    def detect(self, events: list[Event]) -> list[dict]: ...


class FailedLogins:
    def generate(self, target: str) -> list[Event]:
        return [Event(i, target, "authentication", "failure") for i in range(1, 7)]


class ThresholdLogins:
    """Positive fixture exactly at the detection threshold."""

    def generate(self, target: str) -> list[Event]:
        return [Event(i, target, "authentication", "failure") for i in range(1, 6)]


class BenignLogins:
    """Negative fixture: four failures mixed with successful logins."""

    def generate(self, target: str) -> list[Event]:
        outcomes = ("failure", "success", "failure", "success", "failure", "failure")
        return [
            Event(i, target, "authentication", outcome) for i, outcome in enumerate(outcomes, 1)
        ]


class RepeatedFailures:
    def detect(self, events: list[Event]) -> list[dict]:
        counts: dict[str, int] = {}
        for event in events:
            if event.kind == "authentication" and event.outcome == "failure":
                counts[event.target] = counts.get(event.target, 0) + 1
        return [
            {
                "rule_id": "auth.repeated_failures",
                "target": target,
                "severity": "medium",
                "count": count,
                "threshold": 5,
            }
            for target, count in sorted(counts.items())
            if count >= 5
        ]


SCENARIOS: dict[str, Scenario] = {
    "failed-logins": FailedLogins(),
    "threshold-logins": ThresholdLogins(),
    "benign-logins": BenignLogins(),
}


def validate(config: dict) -> tuple[str, str]:
    if not isinstance(config, dict) or set(config) != {
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
    return target, scenario


def normalize(events: list[Event], target: str) -> list[Event]:
    for i, event in enumerate(events, 1):
        if (
            not isinstance(event, Event)
            or event.synthetic is not True
            or event.target != target
            or event.sequence != i
            or event.kind != "authentication"
            or event.outcome not in {"failure", "success"}
        ):
            raise ValueError("Invalid synthetic telemetry")
    return events


def run(config: dict) -> dict:
    target, scenario = validate(config)
    events = normalize(SCENARIOS[scenario].generate(target), target)
    findings = RepeatedFailures().detect(events)
    return {
        "schema_version": 1,
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
