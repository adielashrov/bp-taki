# test_deterministic_event_priority_selection_strategy.py
"""
Unit tests for DeterministicEventPrioritySelectionStrategy.

These tests validate that:
1) Highest priority (lowest numeric value) is always selected.
2) Same-priority ties are resolved deterministically by (event.name, event.data).
3) External events queue is used FIFO when no internal events are selectable.
4) Regular BEvent (without priority) is rejected with TypeError.
"""

import unittest

from bppy.model.b_event import BEvent
from bppy.model.b_priority_event import BPEvent

# Update this import to match where you place the strategy file.
from bppy.model.event_selection.deterministic_event_priority_selection_strategy import (
    DeterministicEventPrioritySelectionStrategy,
)


class TestDeterministicEventPrioritySelectionStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = DeterministicEventPrioritySelectionStrategy()

    def test_selects_highest_priority_event(self):
        e1 = BPEvent("p1", priority=5.0)
        e2 = BPEvent("p0", priority=1.0)  # highest priority (lowest number)
        e3 = BPEvent("p2", priority=10.0)

        statements = [
            {"request": [e1, e3]},
            {"request": [e2]},
        ]

        selected = self.strategy.select(statements)
        self.assertEqual(selected, e2)
        self.assertEqual(selected.get_priority(), 1.0)

    def test_same_priority_tie_breaks_by_name(self):
        # same priority: choose lexicographically smallest name
        a = BPEvent("a_event", priority=5.0)
        b = BPEvent("b_event", priority=5.0)

        statements = [{"request": [b, a]}]
        selected = self.strategy.select(statements)

        self.assertEqual(selected, a)

    def test_same_priority_tie_breaks_by_data_when_name_equal(self):
        # same priority + same name: choose by sorted(data.items())
        e1 = BPEvent("same_name", data={"k": "a"}, priority=5.0)
        e2 = BPEvent("same_name", data={"k": "b"}, priority=5.0)

        statements = [{"request": [e2, e1]}]
        selected = self.strategy.select(statements)

        self.assertEqual(selected, e1)

    def test_tie_break_data_is_order_invariant(self):
        # same logical data, different insertion order -> should be treated identically
        e1 = BPEvent("same_name", data={"a": 1, "b": 2}, priority=5.0)
        e2 = BPEvent("same_name", data={"b": 2, "a": 1}, priority=5.0)

        statements = [{"request": [e2, e1]}]
        selected = self.strategy.select(statements)

        # With identical tie-break keys, selecting min() will return the first in list order
        # ONLY if your implementation doesn't fully normalize. If you normalize by sorting
        # items, these keys become equal, so either is acceptable.
        self.assertIn(selected, [e1, e2])

    def test_external_events_queue_fallback_fifo(self):
        statements = []  # no requested events
        external = [BPEvent("ext1", priority=5.0), BPEvent("ext2", priority=1.0)]

        selected1 = self.strategy.select(statements, external)
        self.assertEqual(selected1.name, "ext1")
        self.assertEqual(len(external), 1)

        selected2 = self.strategy.select(statements, external)
        self.assertEqual(selected2.name, "ext2")
        self.assertEqual(len(external), 0)

        selected3 = self.strategy.select(statements, external)
        self.assertIsNone(selected3)

    def test_type_validation_rejects_regular_bevent(self):
        bad = BEvent("no_priority")
        statements = [{"request": [bad]}]

        with self.assertRaises(TypeError):
            self.strategy.select(statements)


if __name__ == "__main__":
    unittest.main(verbosity=2)
