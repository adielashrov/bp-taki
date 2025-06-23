# Your code will work with this modification:
def test_your_code():
    import bppy as bp

    event_set = bp.EventSet(lambda e: e.name.startswith('first'))

    @bp.thread
    def blocking_event_set():
        while True:
            # This will now work with our enhanced strategy
            yield bp.sync(block=event_set)

    @bp.thread
    def request_events():
        while True:
            yield bp.sync(request=bp.BEvent("first_event"))

    # Use the enhanced strategy
    b_program = bp.BProgram(
        bthreads=[request_events(), blocking_event_set()],
        event_selection_strategy=Connect4EnhancedEventSelectionStrategy(),
        listener=bp.PrintBProgramRunnerListener()
    )
    b_program.run()