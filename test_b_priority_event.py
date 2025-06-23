import unittest
import math
from bppy.model.b_event import BEvent
from bppy.model.b_priority_event import BPriorityEvent

class TestBPriorityEvent(unittest.TestCase):

    def test_equality_same_priority(self):
        e1 = BPriorityEvent("tick", {"round": 1}, priority=10)
        e2 = BPriorityEvent("tick", {"round": 1}, priority=10)
        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))

    def test_inequality_different_priority(self):
        e1 = BPriorityEvent("tick", {"round": 1}, priority=10.0)
        e2 = BPriorityEvent("tick", {"round": 1}, priority=10.1)
        self.assertNotEqual(e1, e2)
        self.assertNotEqual(hash(e1), hash(e2))

    def test_equality_with_bevent(self):
        e1 = BPriorityEvent("start", {"level": 2})
        e2 = BEvent("start", {"level": 2})
        self.assertEqual(e1, e2)
        self.assertEqual(e2, e1)
        # What do we expect the behavior to be in this case? open question.??
        # Consult with Tom.
        # self.assertEqual(hash(e1), hash(e2))

    def test_inequality_with_different_name(self):
        e1 = BPriorityEvent("start", {"level": 2.0})
        e2 = BEvent("begin", {"level": 2.0})
        self.assertNotEqual(e1, e2)

    def test_inequality_with_different_data(self):
        e1 = BPriorityEvent("start", {"level": 2})
        e2 = BEvent("start", {"level": 3})
        self.assertNotEqual(e1, e2)

    def test_repr_and_str(self):
        e = BPriorityEvent("move", {"x": 10, "y": 5}, priority=1)
        expected = "BPriorityEvent(name=move,data={'x': 10, 'y': 5}, priority=1)"
        self.assertEqual(repr(e), expected)
        self.assertEqual(str(e), expected)

if __name__ == "__main__":
    unittest.main()
