# Implement Integrated `optimal` BP Taki Strategy

## Summary
- Add a new fully integrated strategy named `optimal` to [bp_taki.py](/C:/Users/adiel/Documents/Research/bp-taki/bp_taki.py) and wire it into [taki_simulation.py](/C:/Users/adiel/Documents/Research/bp-taki/taki_simulation.py).
- Build it as two cooperating strategy b-threads:
  1. a main card-play prioritizer for normal turns and TAKI sequences
  2. a companion color-choice prioritizer for `change_color`
- Reuse and extend the shared state logic in [external_bridge_state.py](/C:/Users/adiel/Documents/Research/bp-taki/external_bridge_state.py) so BP strategies can see top-card state and opponent hand size without using `block=` or owning lifecycle events.
- Validate in two layers: deterministic correctness/regression tests first, then fixed-seed simulation comparisons against `basic`, `taki`, `taki_and_super_taki`, and the external agent.

## Interfaces
- Accept `"optimal"` anywhere `player_0_strategy` / `player_1_strategy` are parsed in simulation helpers.
- Add a new main strategy entrypoint with full lifecycle/state context:
  `optimal_strategy(index, num_of_cards=2, starting_player=0, num_of_players=2)`
- Add a companion color-selection b-thread with the same context:
  `optimal_change_color_strategy(index, num_of_cards=2, starting_player=0, num_of_players=2)`
- Extend shared strategy state to include:
  `hand_counts`, `top_card_color`, `top_card_type`, and a derived 2-player `opponent_card_count`.
- Keep existing strategies and runtime rule-enforcement APIs unchanged.

## Implementation Changes
- Extend state tracking so BP strategies can observe full turn context.
  Add `pending_deal_player` to state so `deal_cards_to_player_X` can be paired with the following `deal_p_*` event.
  Increment `hand_counts[player]` on dealt cards, decrement on actual played hand cards, set to `0` on `p_i_no_more_cards`, and ignore virtual events like `draw_card`, `closed_taki`, `done_post_action`, and `next_turn`.
  Maintain `top_card_color` / `top_card_type` alongside existing top-card fields after leading-card, regular-card, stop, TAKI, super TAKI, selected-color, and post-TAKI resolution updates.

- Implement the main `optimal_strategy` b-thread with external-player-style setup so it can track the leading card before `start_game`.
  Keep `card_events` as the player’s hand only; observe `draw_card` rather than request it.
  When it is not this player’s turn, wait on all events and update shared state.
  At the start of each own turn, rebuild priorities for every card from current hand plus current state.

- Use this priority policy for normal turns.
  `4.0`: any play that empties the hand immediately.
  `4.5`: regular `taki_{color}` when it opens a dump of at least 2 more same-color cards.
  `5.0`: `stop_{color}` when `opponent_card_count <= 2` or when the hand contains a same-color follow-up card for the extra-turn combo.
  `5.5`: `super_taki` when it effectively converts into the largest color cluster in hand.
  `6.0`: `change_color` only when it is the only strong play besides drawing, or when opponent pressure is high and the selected color will favor our remaining hand.
  `7.5`: supported regular cards or non-combo STOP cards.
  `9.5`: ordinary regular cards with weak follow-up value.
  `11.0`: stash-value wilds (`super_taki`, `change_color`) when they are legal but tactically premature.
  `15.0`: `closed_taki`.
  `20.0`: `draw_card` remains last-resort and is still only observed by the strategy.

- Score support value with explicit heuristics.
  Prefer colors with the largest remaining cluster in hand.
  Prefer spending regular TAKI before super TAKI when both are strong.
  Prefer preserving wild cards until they either avoid a draw, create a strong color commitment, or answer opponent low-card pressure.
  When `opponent_card_count == 1`, aggressively promote STOP and strong dump plays before ordinary shedding plays.

- Use this priority policy inside TAKI sequences.
  Request cards rather than only waiting, so the strategy can choose the order of same-color shedding.
  Prefer same-color cards that keep the longest sequence alive.
  Keep `super_taki` below same-color dump cards unless it is part of an immediate-empty-hand line or still preserves the best continuation.
  Put `change_color` below `closed_taki` inside TAKI so the strategy does not rely on ambiguous runtime semantics there.
  Keep looping until `p_{index}_closed_taki`, remove every played event, then wait for `done_post_action`.

- Implement `optimal_change_color_strategy` as a separate b-thread.
  It observes the same shared state and only acts when this player has played `p_{index}_change_color`.
  It requests `selected_red|blue|green` with priorities based on remaining hand composition.
  Choose the majority color in hand first.
  Break ties by preferring colors that contain STOP or TAKI support.
  Use stable fallback order `red`, `blue`, `green`.
  After selection, wait for `done_post_action`.

- Wire the strategy into simulation builders.
  In both self-play and basic-vs-external builders, append both `optimal_strategy(...)` and `optimal_change_color_strategy(...)` when the selected strategy name is `"optimal"`.
  Pass `starting_player` and `NUM_OF_PLAYERS` into the new strategy only.
  Update strategy docstrings/messages so `"optimal"` is treated as a first-class option everywhere.

## Test Plan
- Extend bridge-state tests under `tests/` to cover:
  initial `hand_counts`
  deal-target pairing via `deal_cards_to_player_X` + `deal_p_*`
  hand-count decrement on regular/action plays
  draw/deal count updates
  `p_i_no_more_cards` zeroing
  `top_card_color` / `top_card_type` updates across regular cards, STOP, selected-color, and TAKI completion

- Add deterministic strategy tests for:
  STOP preferred over a regular card when opponent pressure is high and a same-color follow-up exists
  regular TAKI preferred over super TAKI when it opens the longer dump
  `closed_taki` chosen over `change_color` inside TAKI when no profitable extension remains
  selected color after `change_color` matches the dominant remaining color in hand

- Add regression tests for:
  `"optimal"` completing the current historical deadlock/leading-card seeds without deadlock or draw
  no premature `next_turn` during an `"optimal"` TAKI sequence, mirroring the existing TAKI regression test style

- Run an empirical fixed-seed comparison after correctness tests.
  Compare `"optimal"` against `basic`, `taki`, `taki_and_super_taki`, and the external agent on a balanced schedule of 200 seeds.
  Acceptance rule: zero deadlocks/draws on the comparison set, and no aggregate matchup worse than `taki_and_super_taki`; if needed, adjust only scoring constants, not lifecycle/control-flow logic.

## Assumptions
- The target game remains 2-player for strategy evaluation, even though shared state may still store counts generically.
- Strategy code will not use `block=` and will not request lifecycle events such as `next_turn`, `done_post_action`, or `end_game`.
- Existing rule-enforcement behavior is left intact; this work changes only strategy priorities and color-choice requests.
- Because `change_color` legality inside TAKI is ambiguous between the prompt and current runtime behavior, the new strategy will deliberately avoid preferring it inside TAKI and let `closed_taki` win instead.
