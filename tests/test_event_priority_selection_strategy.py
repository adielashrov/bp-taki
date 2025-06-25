"""
Test suite for EventPrioritySelectionStrategy.

This module contains comprehensive tests to validate the priority-based event selection
behavior, including priority ordering, same-priority handling, type validation, and
integration with the BPpy framework.
"""

import unittest
from unittest.mock import patch
import random
from collections import Counter

from bppy.model.b_event import BEvent
from bppy.model.b_priority_event import BPEvent
from bppy.model.event_set import EmptyEventSet
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy


class TestEventPrioritySelectionStrategy(unittest.TestCase):
    """Test cases for EventPrioritySelectionStrategy"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.strategy = EventPrioritySelectionStrategy()

        # Create test events with different priorities
        self.high_priority_event = BPEvent("high_priority", priority=1.0)
        self.medium_priority_event = BPEvent("medium_priority", priority=5.0)
        self.low_priority_event = BPEvent("low_priority", priority=10.0)
        self.same_priority_event1 = BPEvent("same_priority_1", priority=5.0)
        self.same_priority_event2 = BPEvent("same_priority_2", priority=5.0)

        # Regular BEvent without priority (should cause TypeError)
        self.regular_event = BEvent("regular_event")

    def test_inherits_from_simple_event_selection_strategy(self):
        """Test that EventPrioritySelectionStrategy properly inherits from SimpleEventSelectionStrategy."""
        from bppy.model.event_selection.simple_event_selection_strategy import SimpleEventSelectionStrategy
        self.assertIsInstance(self.strategy, SimpleEventSelectionStrategy)

    def test_selects_highest_priority_event(self):
        """Test that the strategy selects the event with the highest priority (lowest number)."""
        statements = [
            {'request': [self.low_priority_event]},
            {'request': [self.high_priority_event]},
            {'request': [self.medium_priority_event]}
        ]

        selected_event = self.strategy.select(statements)

        self.assertEqual(selected_event, self.high_priority_event)
        self.assertEqual(selected_event.get_priority(), 1.0)

    def test_priority_ordering_multiple_events(self):
        """Test correct priority ordering with multiple events."""
        statements = [
            {'request': [self.low_priority_event, self.medium_priority_event]},
            {'request': [self.high_priority_event]}
        ]

        selected_event = self.strategy.select(statements)

        # Should select the highest priority event
        self.assertEqual(selected_event, self.high_priority_event,
                         "Expected highest priority event to be selected.")

    def test_same_priority_random_selection(self):
        """Test that events with the same priority are selected randomly."""
        statements = [
            {'request': [self.same_priority_event1]},
            {'request': [self.same_priority_event2]}
        ]

        # Run selection multiple times and collect results
        selections = []
        for _ in range(100):
            selected_event = self.strategy.select(statements)
            selections.append(selected_event.name)

        # Both events should be selected at least once (with high probability)
        selection_counts = Counter(selections)
        self.assertIn("same_priority_1", selection_counts)
        self.assertIn("same_priority_2", selection_counts)

        # Both should have roughly equal selection frequency (allowing for randomness)
        total_selections = len(selections)
        for count in selection_counts.values():
            self.assertGreater(count, total_selections * 0.2)  # At least 20% each

    def test_blocks_prevent_event_selection(self):
        """Test that blocked events are not selected even if they have high priority."""
        statements = [
            {'request': [self.high_priority_event]},
            {'request': [self.medium_priority_event]},
            {'block': [self.high_priority_event]}  # Block the high priority event
        ]

        selected_event = self.strategy.select(statements)

        # Should select medium priority event since high priority is blocked
        self.assertEqual(selected_event, self.medium_priority_event,
                         "High-priority event was blocked, expected medium-priority instead.")

    def test_no_selectable_events_returns_none(self):
        """Test that None is returned when no events can be selected."""
        statements = [
            {'request': [self.high_priority_event]},
            {'block': [self.high_priority_event]}  # Block the only requested event
        ]

        selected_event = self.strategy.select(statements)

        self.assertIsNone(selected_event)

    def test_external_events_queue_fallback(self):
        """Test that external events are selected when no internal events are available."""
        statements = []  # No requested events
        external_events = [self.medium_priority_event, self.low_priority_event]

        selected_event = self.strategy.select(statements, external_events)

        # Should return the first event from external queue
        self.assertEqual(selected_event, self.medium_priority_event)
        # Should remove the event from the queue
        self.assertEqual(len(external_events), 1)
        self.assertEqual(external_events[0], self.low_priority_event)

    def test_empty_external_events_queue_returns_none(self):
        """Test that None is returned when no events are available anywhere."""
        statements = []  # No requested events
        external_events = []  # No external events

        selected_event = self.strategy.select(statements, external_events)

        self.assertIsNone(selected_event)

    def test_type_validation_rejects_regular_bevents(self):
        """Test that the strategy raises TypeError for regular BEvent instances."""
        statements = [
            {'request': [self.regular_event]}  # Regular BEvent without priority
        ]

        with self.assertRaises(TypeError) as context:
            self.strategy.select(statements)

        self.assertIn("EventPrioritySelectionStrategy requires BPEvent instances", str(context.exception))
        self.assertIn("BEvent", str(context.exception))

    def test_mixed_bpevent_and_bevent_raises_error(self):
        """Test that mixing BPEvent and regular BEvent instances raises TypeError."""
        statements = [
            {'request': [self.high_priority_event, self.regular_event]}
        ]

        with self.assertRaises(TypeError) as context:
            self.strategy.select(statements)

        self.assertIn("EventPrioritySelectionStrategy requires BPEvent instances", str(context.exception))

    def test_is_satisfied_method_inherited(self):
        """Test that the is_satisfied method works correctly (inherited from parent)."""
        statement = {'request': [self.high_priority_event], 'waitFor': [self.medium_priority_event]}

        # Should be satisfied if event is requested
        self.assertTrue(self.strategy.is_satisfied(self.high_priority_event, statement))

        # Should be satisfied if event is waited for
        self.assertTrue(self.strategy.is_satisfied(self.medium_priority_event, statement))

        # Should not be satisfied for unrelated event
        self.assertFalse(self.strategy.is_satisfied(self.low_priority_event, statement))

    def test_is_satisfied_with_blocked_event(self):
        """Test that blocked events are not satisfied even if requested."""
        statement = {
            'request': [self.high_priority_event],
            'block': [self.high_priority_event]
        }

        # Should not be satisfied because event is blocked
        self.assertFalse(self.strategy.is_satisfied(self.high_priority_event, statement))

    def test_selectable_events_method_inherited(self):
        """Test that the selectable_events method works correctly (inherited from parent)."""
        statements = [
            {'request': [self.high_priority_event, self.medium_priority_event]},
            {'request': [self.low_priority_event]},
            {'block': [self.medium_priority_event]}  # Block medium priority
        ]

        selectable = self.strategy.selectable_events(statements)

        # Should include high and low priority, but not medium (blocked)
        expected = {self.high_priority_event, self.low_priority_event}
        self.assertEqual(selectable, expected)

    def test_deterministic_behavior_with_fixed_seed(self):
        """Test that the strategy behaves deterministically with fixed random seed."""
        statements = [
            {'request': [self.same_priority_event1]},
            {'request': [self.same_priority_event2]}
        ]

        # Test with fixed seed
        random.seed(42)
        result1 = self.strategy.select(statements)

        random.seed(42)
        result2 = self.strategy.select(statements)

        # Results should be identical with same seed
        self.assertEqual(result1, result2)

    def test_complex_priority_scenario(self):
        """Test a complex scenario with multiple priority levels and blocking."""
        # Create events with various priorities
        urgent = BPEvent("urgent", priority=0.5)
        high = BPEvent("high", priority=2.0)
        normal1 = BPEvent("normal1", priority=5.0)
        normal2 = BPEvent("normal2", priority=5.0)
        low = BPEvent("low", priority=10.0)

        statements = [
            {'request': [normal1, low]},
            {'request': [high, urgent]},
            {'request': [normal2]},
            {'block': [urgent]}  # Block the most urgent event
        ]

        selected_event = self.strategy.select(statements)

        # Should select 'high' since 'urgent' is blocked
        self.assertEqual(selected_event, high)
        self.assertEqual(selected_event.get_priority(), 2.0)

    def test_bpevent_get_priority_method(self):
        """Test that BPEvent instances have working get_priority method."""
        event = BPEvent("test", priority=3.14)

        self.assertEqual(event.get_priority(), 3.14)
        self.assertTrue(hasattr(event, 'get_priority'))
        self.assertTrue(callable(getattr(event, 'get_priority')))

    def test_same_priority_random_selection(self):
        """Same-priority events should be selected randomly with uniform distribution"""
        statements = [
            {'request': [self.same_priority_event1]},
            {'request': [self.same_priority_event2]}
        ]

        with patch('random.choice', side_effect=[self.same_priority_event1, self.same_priority_event2] * 50):
            selections = [self.strategy.select(statements).name for _ in range(100)]

        selection_counts = Counter(selections)
        self.assertIn("same_priority_1", selection_counts, "same_priority_1 should be selected at least once.")
        self.assertIn("same_priority_2", selection_counts, "same_priority_2 should be selected at least once.")
        for count in selection_counts.values():
            self.assertGreater(count, 15, "Each event should appear at least 15 times over 100 trials.")

class TestEventPrioritySelectionStrategyIntegration(unittest.TestCase):
    """Integration tests for EventPrioritySelectionStrategy with BPpy framework"""

    def setUp(self):
        """Set up integration test fixtures."""
        self.strategy = EventPrioritySelectionStrategy()

    def test_integration_with_bppy_sync_statements(self):
        """Test integration with typical BPpy sync statement structures."""
        # Simulate typical sync statements from BPpy
        event1 = BPEvent("event1", priority=1.0)
        event2 = BPEvent("event2", priority=2.0)
        event3 = BPEvent("event3", priority=1.0)

        statements = [
            {
                'request': [event2],
                'waitFor': [],
                'block': EmptyEventSet()
            },
            {
                'request': [event1, event3],
                'waitFor': [event2],
                'block': EmptyEventSet()
            }
        ]

        selected_event = self.strategy.select(statements)

        # Should select one of the priority 1.0 events (event1 or event3)
        self.assertIn(selected_event, [event1, event3])
        self.assertEqual(selected_event.get_priority(), 1.0)

    def test_wait_for_only_event_not_selected_if_blocked_elsewhere(self):
        """Event only in waitFor should not be selected if blocked by other b-thread"""
        event = BPEvent("only_waited_event", priority=1.0)
        statements = [
            {'waitFor': [event]},
            {'block': [event]}
        ]
        selected_event = self.strategy.select(statements)
        self.assertIsNone(selected_event, "Blocked event should not be selected even if waited for.")

    def test_performance_with_many_events(self):
        """Stress test: Strategy handles many events and selects the highest priority (lowest number)"""
        many_events = [BPEvent(f"event_{i}", priority=i) for i in range(1000, 0, -1)]
        statements = [{'request': many_events}]
        selected_event = self.strategy.select(statements)
        self.assertEqual(selected_event.name, "event_1", "Expected lowest-numbered (highest-priority) event.")


def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(loader.loadTestsFromTestCase(TestEventPrioritySelectionStrategy))
    test_suite.addTests(loader.loadTestsFromTestCase(TestEventPrioritySelectionStrategyIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()