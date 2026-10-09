"""Small deterministic fixtures, with no network or process operations."""

from .contracts import Event, Scenario


class FailedLogins:
    def generate(self, target: str) -> list[Event]:
        return [
            Event(i, target, "authentication", "failure", timestamp_ms=i * 1000)
            for i in range(1, 7)
        ]


class ThresholdLogins:
    def generate(self, target: str) -> list[Event]:
        return [
            Event(i, target, "authentication", "failure", timestamp_ms=i * 1000)
            for i in range(1, 6)
        ]


class BenignLogins:
    def generate(self, target: str) -> list[Event]:
        outcomes = ("failure", "success", "failure", "success", "failure", "failure")
        return [
            Event(i, target, "authentication", outcome, timestamp_ms=i * 1000)
            for i, outcome in enumerate(outcomes, 1)
        ]


class SpreadLogins:
    def generate(self, target: str) -> list[Event]:
        return [
            Event(i, target, "authentication", "failure", timestamp_ms=i * 61000)
            for i in range(1, 7)
        ]


SCENARIOS: dict[str, Scenario] = {
    "failed-logins": FailedLogins(),
    "threshold-logins": ThresholdLogins(),
    "benign-logins": BenignLogins(),
    "spread-logins": SpreadLogins(),
}
