from bppy.model.b_thread import b_thread
from bppy.model.sync_statement import sync
from bppy.model.b_priority_event import BPEvent


def ev(name: str, priority: float = 10.0):
    return BPEvent(name=name, data={}, priority=priority)


@b_thread
def fixed_alternating_dealer(p0_cards, p1_cards, leading_card):
    if len(p0_cards) != len(p1_cards):
        raise ValueError("p0_cards and p1_cards must have the same length")

    yield sync(request=ev("start_dealing_cards_to_players"))

    for p0_card, p1_card in zip(p0_cards, p1_cards):
        yield sync(request=ev("deal_cards_to_player_0"))
        yield sync(request=ev(f"deal_{p0_card}"))
        yield sync(request=ev("deal_cards_to_player_1"))
        yield sync(request=ev(f"deal_{p1_card}"))

    yield sync(request=ev("finished_dealing_cards_to_players"))

    lead_deal = f"deal_{leading_card}"
    yield sync(request=ev("deal_leading_card"))
    yield sync(request=ev(lead_deal))
    yield sync(request=ev(f"leading_{lead_deal}"))
    yield sync(request=ev("finished_leading_card"))
