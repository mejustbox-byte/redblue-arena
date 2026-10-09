"""Versioned threshold rule with an inclusive sliding time window."""

from collections import deque
from dataclasses import asdict, dataclass

from .contracts import Event


@dataclass(frozen=True)
class Rule:
    rule_id: str = "auth.repeated_failures"
    version: int = 2
    threshold: int = 5
    window_ms: int = 60000

    def __post_init__(self):
        if (
            self.rule_id != "auth.repeated_failures"
            or type(self.version) is not int
            or self.version != 2
        ):
            raise ValueError("Unknown rule/version")
        if type(self.threshold) is not int or not 2 <= self.threshold <= 100:
            raise ValueError("Rule threshold must be 2–100")
        if type(self.window_ms) is not int or not 1000 <= self.window_ms <= 3600000:
            raise ValueError("Rule window_ms must be 1000–3600000")

    def as_dict(self) -> dict:
        return asdict(self)


class RepeatedFailures:
    def __init__(self, rule: Rule | None = None):
        self.rule = rule or Rule()

    def detect(self, events: list[Event]) -> list[dict]:
        windows: dict[str, deque] = {}
        peaks: dict[str, tuple[int, int, int]] = {}
        for event in sorted(events, key=lambda e: (e.timestamp_ms, e.sequence)):
            if event.kind != "authentication" or event.outcome != "failure":
                continue
            window = windows.setdefault(event.target, deque())
            while window and event.timestamp_ms - window[0] > self.rule.window_ms:
                window.popleft()
            window.append(event.timestamp_ms)
            if len(window) > peaks.get(event.target, (0, 0, 0))[0]:
                peaks[event.target] = (len(window), window[0], event.timestamp_ms)
        return [
            {
                "rule_id": self.rule.rule_id,
                "rule_version": self.rule.version,
                "target": target,
                "severity": "medium",
                "count": peak[0],
                "threshold": self.rule.threshold,
                "window_ms": self.rule.window_ms,
                "window_start_ms": peak[1],
                "window_end_ms": peak[2],
            }
            for target, peak in sorted(peaks.items())
            if peak[0] >= self.rule.threshold
        ]
