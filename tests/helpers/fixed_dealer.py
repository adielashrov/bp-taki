# tests/helpers/fixed_dealer.py

from bppy.model.b_thread import b_thread
from bppy.model.sync_statement import sync
from bppy.model.b_priority_event import BPEvent

def ev(name: str, priority: float = 10.0):
    return BPEvent(name=name, data={}, priority=priority)

@b_thread
def fixed_dealer(p0_cards, p1_cards, leading_card):
    yield sync(request=ev("start_dealing_cards_to_players"))

    yield sync(request=ev("deal_cards_to_player_0"))
    for c in p0_cards:
        yield sync(request=ev(f"deal_{c}"))

    yield sync(request=ev("deal_cards_to_player_1"))
    for c in p1_cards:
        yield sync(request=ev(f"deal_{c}"))

    yield sync(request=ev("finished_dealing_cards_to_players"))

    lead_deal = f"deal_{leading_card}"
    yield sync(request=ev("deal_leading_card"))
    yield sync(request=ev(lead_deal))
    yield sync(request=ev(f"leading_{lead_deal}"))
    yield sync(request=ev("finished_leading_card"))
