from bppy.model.event_selection.simple_event_selection_strategy import SimpleEventSelectionStrategy
from bppy.model.b_priority_event import BPEvent
import random


class EventPrioritySelectionStrategy(SimpleEventSelectionStrategy):
    """
    An EventSelectionStrategy that selects events based on priority.
    Events with lower priority values have higher priority (are selected first).
    For events with the same priority, selection is arbitrary/random.

    This strategy is specifically designed to work with BPEvent instances.
    Inherits from SimpleEventSelectionStrategy and only overrides the select method
    to implement priority-based event selection.
    """

    def select(self, statements, external_events_queue=[]):
        """
        Selects the next event from the given statements and external events queue based on priority.

        This method selects the event with the highest priority (lowest priority value) from the set of
        selectable events. Only BPEvent instances are considered for priority-based selection.
        If multiple events have the same priority, one is chosen arbitrarily.
        If no events can be selected from the statements, an event from the external events queue
        will be selected (or `None` is returned if the queue is empty).

        Parameters
        ----------
        statements : list
            A list of bthreads sync statements from which an event will be selected.
        external_events_queue : list, optional
            A list of external events that may be selected.

        Returns
        -------
        BPEvent or `None`
            The selected BPEvent with the highest priority, or `None` if no event can be selected.

        Raises
        ------
        TypeError
            If selectable events contain non-BPEvent instances.
        """
        # Use the inherited method to get selectable events
        selectable_events = self.selectable_events(statements)

        if selectable_events:
            # Convert to list for easier manipulation
            events_list = list(selectable_events)

            # Validate that all events are BPEvent instances
            for event in events_list:
                if not isinstance(event, BPEvent):
                    raise TypeError(
                        f"EventPrioritySelectionStrategy requires BPEvent instances, got {type(event)}: {event}")

            # Sort events by priority (lower number = higher priority)
            events_list.sort(key=lambda event: event.get_priority())

            # Get the highest priority value
            highest_priority = events_list[0].get_priority()

            # Collect all events with the highest priority
            highest_priority_events = [
                event for event in events_list
                if event.get_priority() == highest_priority
            ]

            # If multiple events have the same highest priority, choose randomly
            return random.choice(highest_priority_events)
        else:
            if len(external_events_queue) > 0:
                return external_events_queue.pop(0)
            else:
                return None