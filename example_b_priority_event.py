import bppy as bp
import random
from bppy.model.b_priority_event import BPEvent
from bppy.model.event_selection.event_priority_selection_strategy import EventPrioritySelectionStrategy

random.seed(10)

NUM_OF_ITERATIONS = 2

@bp.thread
def first_b_thread():
    for i in range(NUM_OF_ITERATIONS):
        last_event = yield bp.sync(waitFor=[BPEvent("Event_C", data={"content" : "test_data_3_" + str(i)}, priority=3.0)])
        print("first_b_thread was notified on ", last_event)

@bp.thread
def second_b_thread():
    for i in range(NUM_OF_ITERATIONS):
        yield bp.sync(request=BPEvent("Event_B", data={"content" : "test_data_2_" + str(i)}, priority=5.0))


@bp.thread
def third_b_thread():
    for i in range(NUM_OF_ITERATIONS):
        last_event = yield bp.sync(request=BPEvent("Event_C", data={"content" : "test_data_3_" + str(i)}, priority=2.0))
        print("third_b_thread was notified on ", last_event)

@bp.thread
def fourth_b_thread():
    for i in range(NUM_OF_ITERATIONS):
        last_event = yield bp.sync(request=BPEvent("Event_C", data={"content" : "test_data_3_" + str(i)}, priority=2.0))
        print("fourth_b_thread was notified on ", last_event)

@bp.thread
def fifth_b_thread():
    for i in range(NUM_OF_ITERATIONS):
        last_event = yield bp.sync(block=BPEvent("Event_C", data={"content" : "test_data_3_" + str(i)}, priority=5.0))
        print("fifth_b_thread was notified on ", last_event)


@bp.thread
def sixth_b_thread():
    for i in range(NUM_OF_ITERATIONS):
        last_event = yield bp.sync(request=BPEvent("Event_D", data={"content" : "test_data_6_" + str(i)}, priority=3.0))
        # print("sixth_b_thread was notified on ", last_event)



def init_b_program():
    b_program = bp.BProgram(bthreads=[  first_b_thread() , second_b_thread(), third_b_thread() , fourth_b_thread(), fifth_b_thread(), sixth_b_thread() ],
                         event_selection_strategy=EventPrioritySelectionStrategy(),
                         listener=bp.PrintBProgramRunnerListener())
    return b_program

def regular_execution_of_bp_program():
    b_program = init_b_program()
    b_program.run()

if __name__ == '__main__':
    regular_execution_of_bp_program()
