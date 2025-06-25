import math
from bppy.model.b_event import BEvent

class BPEvent(BEvent):
    """
    A class to represent a Behavioral Event (BEvent) object with priorities.

    Attributes
    ----------
    name : str
        The name of the event.
    data : dict
        Additional data associated with the event.
    priority : float
        The priority of the event, which is math.inf by default.
    """
    def __init__(self, name="", data=None, priority=math.inf):
        """
        Constructs all the necessary attributes for the BPEvent object.

        Parameters
        ----------
        name : str
            The name of the event.
        data : dict
            Additional data associated with the event.
        priority : float
            The priority of the event, which is math.inf by default.
        """
        super().__init__(name, data)
        self.priority = priority

    def __key(self):
        # Add priority only for full BPEvent-to-BPEvent comparison
        return (self.name, tuple(sorted(self.data.items())), self.priority)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, BPEvent) and self.__key() == other.__key()

    def __repr__(self):
        return "{}(name={},data={}, priority={})".format(
            self.__class__.__name__, self.name, self.data, self.priority)

    def __str__(self):
        return self.__repr__()
