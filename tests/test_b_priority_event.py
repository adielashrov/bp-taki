import unittest
import math
from bppy.model.b_event import BEvent
from bppy.model.b_priority_event import BPEvent

class TestBPriorityEvent(unittest.TestCase):

    def test_equality_same_priority(self):
        e1 = BPEvent("tick", {"round": 1}, priority=10)
        e2 = BPEvent("tick", {"round": 1}, priority=10)
        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))

    def test_equality_different_priority(self):
        e1 = BPEvent("tick", {"round": 1}, priority=10.0)
        e2 = BPEvent("tick", {"round": 1}, priority=10.1)
        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))

    def test_noequality_with_bevent(self):
        e1 = BPEvent("start", {"level": 2})
        e2 = BEvent("start", {"level": 2})
        self.assertNotEqual(e1, e2)
        self.assertNotEqual(e2, e1)
        self.assertEqual(hash(e1), hash(e2))

    def test_inequality_with_different_name(self):
        e1 = BPEvent("start", {"level": 2.0})
        e2 = BEvent("begin", {"level": 2.0})
        self.assertNotEqual(e1, e2)

    def test_inequality_with_different_data(self):
        e1 = BPEvent("start", {"level": 2})
        e2 = BEvent("start", {"level": 3})
        self.assertNotEqual(e1, e2)

    def test_repr_and_str(self):
        e = BPEvent("move", {"x": 10, "y": 5}, priority=1)
        expected = "BPEvent(name=move,data={'x': 10, 'y': 5}, priority=1)"
        self.assertEqual(repr(e), expected)
        self.assertEqual(str(e), expected)

if __name__ == "__main__":
    unittest.main()
