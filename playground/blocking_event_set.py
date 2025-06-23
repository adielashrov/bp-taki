import bppy as bp
from bppy.model.event_selection.statement_priority_event_selection_strategy import StatementPriorityBasedEventSelectionStrategy

event_set = bp.EventSet(lambda e: e.name.startswith('first'))

@bp.thread
def blocking_event_set():
    while True:
        # yield bp.sync(hardBlock=bp.BEvent("first_event"))
        #yield bp.sync(hardBlock=event_set)
        yield bp.sync(block=event_set)

@bp.thread
def request_events():
    while True:
        yield bp.sync(request=bp.BEvent("first_event"))


if __name__ == "__main__":
    b_program = bp.BProgram(bthreads=[request_events(), blocking_event_set()],
                            event_selection_strategy=StatementPriorityBasedEventSelectionStrategy(),
                            listener=bp.PrintBProgramRunnerListener())
    b_program.run()