import unittest

from redblue_arena.core import Event, RepeatedFailures, normalize, run


class PipelineTests(unittest.TestCase):
    def config(self, **changes):
        return dict(
            authorized=True,
            allowed_targets=["lab://training"],
            target="lab://training",
            scenario="failed-logins",
            **changes,
        )

    def test_end_to_end(self):
        result = run(self.config())
        self.assertEqual(len(result["events"]), 6)
        self.assertEqual(result["findings"][0]["count"], 6)
        self.assertEqual(len(result["audit"]), 3)
        self.assertEqual(result, run(self.config()))

    def test_fail_closed(self):
        for key, value in [
            ("authorized", False),
            ("authorized", 1),
            ("target", "lab://other"),
            ("target", []),
            ("allowed_targets", ["https://example.com"]),
            ("scenario", "shell"),
            ("scenario", []),
        ]:
            with self.subTest(key=key, value=value):
                config = self.config()
                config[key] = value
                with self.assertRaises(ValueError):
                    run(config)
        with self.assertRaises(ValueError):
            run({**self.config(), "command": "anything"})

    def test_threshold_and_target_isolation(self):
        detector = RepeatedFailures()
        events = [Event(i, "lab://a", "authentication", "failure") for i in range(4)]
        events += [Event(5, "lab://b", "authentication", "failure")]
        self.assertEqual(detector.detect(events), [])
        events.append(Event(6, "lab://a", "authentication", "failure"))
        self.assertEqual(detector.detect(events)[0]["target"], "lab://a")

    def test_telemetry_boundary(self):
        for event in [
            Event(1, "lab://other", "authentication", "failure"),
            Event(1, "lab://training", "authentication", "failure", False),
            Event(2, "lab://training", "authentication", "failure"),
        ]:
            with self.assertRaises(ValueError):
                normalize([event], "lab://training")
