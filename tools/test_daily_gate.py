"""The once-a-day gate of "Deploy site" (queue block 50, 20 Nov 2026). Run: python3 tools/test_daily_gate.py"""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_gate as g  # noqa: E402
import tier1_guard as t  # noqa: E402

NOW = datetime(2026, 11, 21, 6, 2, tzinfo=timezone.utc)


def run(i, event, at, conclusion="success", status="completed"):
    return {"id": i, "run_number": i, "event": event, "status": status, "conclusion": conclusion,
            "created_at": f"2026-11-21T{at}:00Z", "run_started_at": f"2026-11-21T{at}:00Z"}


class Gate(unittest.TestCase):
    def test_push_and_manual_always_build(self):
        self.assertEqual(g.decide("push", False, NOW, [run(1, "schedule", "06:00")], 9), (True, None))
        self.assertEqual(g.decide("workflow_dispatch", False, NOW, [run(1, "schedule", "06:00")], 9), (True, None))

    def test_first_daily_run_builds(self):
        self.assertEqual(g.decide("workflow_dispatch", True, NOW, [], 9), (True, None))

    def test_the_run_itself_does_not_count(self):
        self.assertTrue(g.decide("workflow_dispatch", True, NOW, [run(9, "workflow_dispatch", "06:00", None, "in_progress")], 9)[0])

    def test_late_schedule_skips_after_a_good_trigger_run(self):
        build, line = g.decide("schedule", False, NOW.replace(hour=14, minute=58), [run(5, "workflow_dispatch", "06:00")], 9)
        self.assertFalse(build)
        self.assertIn("already succeeded today at 06:00 UTC", line)

    def test_a_merge_today_counts_as_the_daily_run(self):
        self.assertFalse(g.decide("schedule", False, NOW, [run(5, "push", "05:45")], 9)[0])

    def test_a_merge_before_the_window_does_not(self):
        self.assertTrue(g.decide("schedule", False, NOW, [run(5, "push", "05:10")], 9)[0])

    def test_a_stopped_daily_run_is_not_tried_again(self):
        build, line = g.decide("schedule", False, NOW, [run(5, "workflow_dispatch", "06:00", "failure")], 9)
        self.assertFalse(build)
        self.assertIn("stopped", line)

    def test_a_failed_merge_does_not_stop_the_daily_run(self):
        self.assertTrue(g.decide("schedule", False, NOW, [run(5, "push", "05:50", "failure")], 9)[0])

    def test_a_cancelled_run_does_not_count(self):
        self.assertTrue(g.decide("schedule", False, NOW, [run(5, "workflow_dispatch", "06:00", "cancelled")], 9)[0])

    def test_before_the_window_skips(self):
        build, line = g.decide("schedule", False, NOW.replace(hour=0, minute=40), [], 9)
        self.assertFalse(build)
        self.assertIn("before 05:30 UTC", line)


class StopLine(unittest.TestCase):
    def test_text_change(self):
        self.assertEqual(t.stop_line(["/a/", "/b/"], [], False), "Stopped: text/price change waits for approval: /a/, /b/")

    def test_many_pages_are_cut(self):
        self.assertTrue(t.stop_line([f"/p{i}/" for i in range(12)], [], False).endswith("/p9/ and 2 more"))

    def test_network(self):
        self.assertEqual(t.stop_line([], ["/404.html"], False), f"Stopped: network: {t.LIVE}/404.html after {t.TRIES} tries")

    def test_sitemap(self):
        self.assertIn("sitemap.xml", t.stop_line([], [], True))

    def test_no_stop(self):
        self.assertIsNone(t.stop_line([], [], False))


if __name__ == "__main__":
    unittest.main()
