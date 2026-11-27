import json
import unittest

from run_benchmark import BENCH, FIX, stack_preprocess


class PreprocessTests(unittest.TestCase):
    def test_public_fixtures_match_ground_truth(self):
        scenarios = json.loads((BENCH / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]
        self.assertTrue(scenarios)
        for scenario in scenarios:
            with self.subTest(scenario=scenario["id"]):
                fixture = FIX / scenario["fixture"]
                raw = fixture.read_text(encoding="utf-8")
                truth_file = fixture.with_suffix(".ground_truth.json")
                expected = json.loads(truth_file.read_text(encoding="utf-8"))
                summary, _, _ = stack_preprocess(fixture.name, raw)
                actual = json.loads(summary)
                for field in scenario["quality_checks"]:
                    self.assertEqual(actual[field], expected[field], field)

    def test_access_log_ignores_non_object_and_invalid_lines(self):
        raw = "\n".join([
            '{"level":"ERROR"}',
            "null",
            "[]",
            "0",
            '"text"',
            "false",
            "{invalid",
            "",
            '{"level":"FATAL"}',
            '{"level":"WARN"}',
        ])
        summary, _, _ = stack_preprocess("access_log_example.jsonl", raw)
        self.assertEqual(json.loads(summary), {"error_count": 2, "lines": 10})

    def test_git_summary_uses_utf8_byte_counts(self):
        raw = "commit abc\nAuthor: Zo\u00eb <author@example.com>\n"
        summary, raw_bytes, summary_bytes = stack_preprocess("git_log_example.txt", raw)
        self.assertEqual(json.loads(summary), {
            "commit_count": 1,
            "top_author": "Zo\u00eb",
            "unique_authors": 1,
        })
        self.assertEqual(raw_bytes, len(raw.encode("utf-8")))
        self.assertEqual(summary_bytes, len(summary.encode("utf-8")))
        self.assertGreater(raw_bytes, len(raw))
        self.assertGreater(summary_bytes, len(summary))
