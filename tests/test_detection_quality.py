"""Deterministic regression cases for detection quality and target isolation."""

import unittest

from redblue_arena.core import Event, RepeatedFailures, run


class DetectionQualityTests(unittest.TestCase):
    def test_scenario_matrix(self):
        for scenario, event_count, findings, failures in (
            ("failed-logins", 6, 1, 6),
            ("threshold-logins", 5, 1, 5),
            ("benign-logins", 6, 0, 4),
        ):
            with self.subTest(scenario=scenario):
                config = {
                    "authorized": True,
                    "allowed_targets": ["lab://quality"],
                    "target": "lab://quality",
                    "scenario": scenario,
                }
                report = run(config)
                self.assertEqual(len(report["events"]), event_count)
                self.assertEqual(len(report["findings"]), findings)
                self.assertEqual(report["audit"][-1]["finding_count"], findings)
                self.assertEqual(sum(e["outcome"] == "failure" for e in report["events"]), failures)
                self.assertEqual(report, run(config))
                if findings:
                    self.assertEqual(report["findings"][0]["count"], failures)
                    self.assertEqual(report["findings"][0]["threshold"], 5)

    def test_successes_and_other_event_kinds_do_not_count(self):
        events = [Event(i, "lab://quality", "authentication", "success") for i in range(6)]
        events += [Event(i, "lab://quality", "other", "failure") for i in range(6)]
        self.assertEqual(RepeatedFailures().detect(events), [])

    def test_targets_are_never_aggregated(self):
        events = [
            Event(i, target, "authentication", "failure")
            for target in ("lab://a", "lab://b")
            for i in range(4)
        ]
        self.assertEqual(RepeatedFailures().detect(events), [])
        events.append(Event(9, "lab://b", "authentication", "failure"))
        findings = RepeatedFailures().detect(events)
        self.assertEqual([(f["target"], f["count"]) for f in findings], [("lab://b", 5)])

    def test_new_scenarios_require_authorization(self):
        for scenario in ("threshold-logins", "benign-logins"):
            with self.subTest(scenario=scenario), self.assertRaises(ValueError):
                run(
                    {
                        "authorized": False,
                        "allowed_targets": ["lab://quality"],
                        "target": "lab://quality",
                        "scenario": scenario,
                    }
                )
