import unittest

from redblue_arena.core import Event, RepeatedFailures, Rule, normalize, run
from redblue_arena.evaluation import evaluate

CONFIG = {
    "authorized": True,
    "allowed_targets": ["lab://training"],
    "target": "lab://training",
    "scenario": "failed-logins",
}


class RuleTests(unittest.TestCase):
    def test_inclusive_window_boundary(self):
        detector = RepeatedFailures(Rule(threshold=2, window_ms=1000))

        def events(delta):
            return [
                Event(1, "lab://a", "authentication", "failure", timestamp_ms=0),
                Event(2, "lab://a", "authentication", "failure", timestamp_ms=delta),
            ]

        self.assertEqual(detector.detect(events(1000))[0]["count"], 2)
        self.assertEqual(detector.detect(events(1001)), [])

    def test_spread_fixture_and_quality(self):
        report = run({**CONFIG, "scenario": "spread-logins"})
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["findings"], [])
        quality = evaluate(CONFIG)
        self.assertEqual(
            quality["confusion_matrix"],
            {"true_positive": 2, "false_positive": 0, "true_negative": 2, "false_negative": 0},
        )
        self.assertEqual(quality["recall"], 1)

    def test_custom_rule_and_rejected_types(self):
        report = run({**CONFIG, "rule": Rule(threshold=7).as_dict()})
        self.assertEqual(report["findings"], [])
        for value in [True, 0, 101, "5"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Rule(threshold=value)
        for rule in [{}, {**Rule().as_dict(), "command": "x"}, {**Rule().as_dict(), "version": 1}]:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                run({**CONFIG, "rule": rule})

    def test_telemetry_numeric_and_order_boundaries(self):
        for events in [
            [],
            [Event(True, "lab://training", "authentication", "failure")],
            [Event(1, "lab://training", "authentication", "failure", timestamp_ms=True)],
            [Event(1, "lab://training", "authentication", "failure", timestamp_ms=-1)],
            [
                Event(1, "lab://training", "authentication", "failure", timestamp_ms=2),
                Event(2, "lab://training", "authentication", "failure", timestamp_ms=1),
            ],
        ]:
            with self.subTest(events=events), self.assertRaises(ValueError):
                normalize(events, "lab://training")
