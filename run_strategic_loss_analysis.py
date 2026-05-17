import sys
import os
import logging

sys.path.insert(0, ".")

from taki_simulation import run_single_game, SimulationListener, create_simulation_bprogram


class TracingListener(SimulationListener):
    """SimulationListener that writes each selected event and debug logs to a file."""

    def __init__(self, file_path: str):
        super().__init__()
        self._fh = open(file_path, "w", encoding="utf-8")
        self._log_handler = logging.StreamHandler(self._fh)
        self._log_handler.setLevel(logging.DEBUG)
        self._log_handler.setFormatter(logging.Formatter("%(message)s"))
        self._taki_logger = logging.getLogger("TakiGame")
        self._taki_logger.addHandler(self._log_handler)

    def event_selected(self, b_program, event):
        super().event_selected(b_program, event)
        self._fh.write(f"{event}\n")
        self._fh.flush()

    def close(self):
        self._taki_logger.removeHandler(self._log_handler)
        self._log_handler.close()
        self._fh.close()
 
 
def run_strategic_loss_analysis(num_seeds: int = 100):
    """
    Phase 1: sweep seeds 0..(num_seeds-1), basic (P0) vs strategic (P1).
    Phase 2: replay each losing seed, writing only the event trace to a file.
    """
 
    # ── Phase 1: sweep ────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"Phase 1: basic (P0) vs strategic (P1) — {num_seeds} games")
    print("=" * 60)
 
    losses, wins, errors = [], [], []
 
    for seed in range(num_seeds):
        result = run_single_game(
            game_number=seed,
            seed=seed,
            player_0_strategy="basic",
            player_1_strategy="strategic",
            player_1_win_now=True,
            starting_player=-1,
            silent=True,
        )
 
        if result is None:
            errors.append(seed)
            print(f"  seed={seed:3d}: ERROR")
            continue
 
        if result.ended_in_deadlock or result.ended_in_draw:
            errors.append(seed)
            tag = "DEADLOCK" if result.ended_in_deadlock else "DRAW"
            print(f"  seed={seed:3d}: {tag}")
            continue
 
        tag = "STRATEGIC LOSES <<<" if result.winner == 0 else "strategic wins"
        print(f"  seed={seed:3d}: {tag}  | start_player={result.starting_player} | events={result.event_count}")
 
        if result.winner == 0:
            losses.append(seed)
        else:
            wins.append(seed)
 
    print()
    print("=" * 60)
    print(f"Strategic WINS  : {len(wins)}")
    print(f"Strategic LOSSES: {len(losses)}  ->  seeds: {losses}")
    print(f"Errors/draws    : {len(errors)}")
    print("=" * 60)
 
    # ── Phase 2: replay completed seeds (losses and wins), write event traces ─
    if not (losses or wins):
        print("\nNo completed games — nothing to replay.")
        return

    os.makedirs("traces", exist_ok=True)
    total = len(losses) + len(wins)
    print(f"\nPhase 2: writing event traces for {total} completed game(s) …\n")

    # Replay losses first, then wins. Tag files accordingly.
    seeds_to_replay = [("loss", s) for s in losses] + [("win", s) for s in wins]

    for tag, seed in seeds_to_replay:
        trace_path = f"traces/{tag}_seed_{seed:03d}.log"
        print(f"  seed={seed} ({tag}) -> {trace_path}")

        listener = TracingListener(trace_path)

        b_program, _ = create_simulation_bprogram(
            seed=seed,
            listener=listener,
            player_0_strategy="basic",
            player_1_strategy="strategic",
            player_1_win_now=True,
            starting_player=-1,
        )

        try:
            b_program.run()
        except AssertionError:
            if not (listener.get_deadlock() or listener.get_draw()):
                raise
        finally:
            listener.close()

    print("\nDone. Event traces written to ./traces/")

def replay_seed(seed: int = 3, output_path: str = None):
    """Replay a single seed and write its event trace to a file.
    Defaults to traces/replay_seed_NNN.log (separate from the sweep output)
    so you can diff the two files to validate they are identical."""
    os.makedirs("traces", exist_ok=True)
    trace_path = output_path if output_path is not None else f"traces/replay_seed_{seed:03d}.log"
 
    listener = TracingListener(trace_path)
    b_program, starting_player = create_simulation_bprogram(
        seed=seed,
        listener=listener,
        player_0_strategy="basic",
        player_1_strategy="strategic",
        starting_player=-1,
    )
 
    try:
        b_program.run()
    except AssertionError:
        if not (listener.get_deadlock() or listener.get_draw()):
            raise
    finally:
        listener.close()
 
    print(f"seed={seed} | winner={listener.get_winner()} | starting_player={starting_player} | events={listener.get_event_count()}")
    print(f"Trace written to: {trace_path}")
 
if __name__ == "__main__":
    run_strategic_loss_analysis()
    # replay_seed(seed=3, output_path="traces/replay_seed_003.log")