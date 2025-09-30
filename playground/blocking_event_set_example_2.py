import bppy as bp
from bppy.model.event_selection.statement_priority_event_selection_strategy import StatementPriorityBasedEventSelectionStrategy

# Example usage demonstrating the simplified API
def example_usage():
    import bppy as bp

    # Define some useful EventSets
    dangerous_moves = bp.EventSet(lambda e: e.name.startswith('danger'))
    edge_moves = bp.EventSet(lambda e: e.name.endswith('_0') or e.name.endswith('_6'))

    @bp.thread
    def safety_rules():
        # Hard block dangerous moves (absolute - cannot be overridden)
        yield bp.sync(block=dangerous_moves)

    @bp.thread
    def strategy_preferences():
        # Soft block edge moves (can be overridden by higher priority)
        yield bp.sync(softBlock=edge_moves, blockPriority=30)

    @bp.thread
    def normal_moves():
        yield bp.sync(request=bp.BEvent("edge_move_0"), requestPriority=20)  # Will be soft blocked

    @bp.thread
    def urgent_moves():
        yield bp.sync(request=bp.BEvent("edge_move_6"), requestPriority=50)  # Overrides soft block

    @bp.thread
    def dangerous_but_urgent():
        yield bp.sync(request=bp.BEvent("danger_move"), requestPriority=100)  # Still hard blocked

    b_program = bp.BProgram(
        bthreads=[safety_rules(), strategy_preferences(), normal_moves(), urgent_moves(), dangerous_but_urgent()],
        event_selection_strategy=StatementPriorityBasedEventSelectionStrategy(),
        listener=bp.PrintBProgramRunnerListener()
    )
    b_program.run()


if __name__ == "__main__":
    example_usage()