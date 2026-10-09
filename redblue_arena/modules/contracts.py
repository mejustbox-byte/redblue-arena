"""Module API v2. Timestamps are deterministic milliseconds relative to a run."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Event:
    sequence: int
    target: str
    kind: str
    outcome: str
    synthetic: bool = True
    timestamp_ms: int = 0


class Scenario(Protocol):
    def generate(self, target: str) -> list[Event]: ...


class Detector(Protocol):
    def detect(self, events: list[Event]) -> list[dict]: ...
