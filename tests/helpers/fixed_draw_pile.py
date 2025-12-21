from collections import deque

from bppy.model.b_thread import b_thread
from bppy.model.sync_statement import sync
from bppy.model.b_priority_event import BPEvent


def ev(name: str, priority: float = 10.0):
    return BPEvent(name=name, data={}, priority=priority)


@b_thread
def fixed_draw_pile(p0_draws, p1_draws):
    """
    Deterministic draw pile.

    When 'p_0_draw_card' is selected -> request next 'deal_<card>' from p0_draws.
    When 'p_1_draw_card' is selected -> request next 'deal_<card>' from p1_draws.

    Arguments:
        p0_draws: list[str] like ["p_card_7_red", "p_stop_green", ...]
        p1_draws: list[str] like ["p_card_9_red", ...]
    """
    p0q = deque(p0_draws)
    p1q = deque(p1_draws)

    while True:
        chosen = yield sync(waitFor=[ev("p_0_draw_card"), ev("p_1_draw_card")])

        if chosen.name == "p_0_draw_card":
            if not p0q:
                raise AssertionError("Test draw pile empty for player 0")
            next_card = p0q.popleft()
            yield sync(request=ev(f"deal_{next_card}"))

        elif chosen.name == "p_1_draw_card":
            if not p1q:
                raise AssertionError("Test draw pile empty for player 1")
            next_card = p1q.popleft()
            yield sync(request=ev(f"deal_{next_card}"))
