import bppy as bp
import random
from bppy.model.b_priority_event import BPriorityEvent

random.seed(10)

@bp.thread
def first_b_thread():
    i = 0
    while i < 3:
        lastEvent = yield bp.sync(request=BPriorityEvent("Event_A", data={"content" : "test_data"}, priority=1.0))
        # print(lastEvent)
        i = i + 1

def init_b_program():
    b_program = bp.BProgram(bthreads=[  first_b_thread() ],
                         event_selection_strategy=bp.SimpleEventSelectionStrategy(),
                         listener=bp.PrintBProgramRunnerListener())
    return b_program

def regular_execution_of_bp_program():
    b_program = init_b_program()
    b_program.run()

if __name__ == '__main__':
    regular_execution_of_bp_program()
