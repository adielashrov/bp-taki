from bppy.analysis.symbolic_bprogram_verifier import SymbolicBProgramVerifier
from bppy.model.event_selection.connect4_event_priority_based_event_selection_strategy import Connect4PriorityBasedEventSelectionStrategy
import random
import bppy as bp
from bppy import *

random.seed(10)

# Control events
all_events = [
    BEvent("Hello"),
    BEvent("World")
]


@bp.thread
def hello():  # requests "Hello" once
    for i in range(1):
        yield bp.sync(request=bp.BEvent("World_0"))


@bp.thread
def world():  # requests "World" once
    sync_statements = [
        {
            'request': bp.BEvent("World_1"),
            'requestPriority': 10
        },
        {
            'request': [ bp.BEvent("World_2") ],
            'requestPriority': 20
        }
    ]
    for i in range(2):
        yield bp.sync(multiSync=sync_statements)

@bp.thread
def simulate_block():
    # print("simulate_block before first sync")
    yield bp.sync(waitFor=bp.BEvent("World_2"))
    # print("simulate_block after first sync")
    yield bp.sync(waitFor=bp.BEvent("World_1"), hardBlock=bp.BEvent("World_2"))
    # print("simulate_block after second sync")
    yield bp.sync(waitFor=bp.BEvent("Hello"), hardBlock=[bp.BEvent("World_1"), bp.BEvent("World_2")])
    # print("simulate_block after third sync")


def init_bprogram():
    b_program = bp.BProgram(
        bthreads=[
           hello(), world(), simulate_block()
        ],
        event_selection_strategy=Connect4PriorityBasedEventSelectionStrategy(),
        listener=bp.PrintBProgramRunnerListener()
    )
    return b_program

def verify_example():
    # Initialize verifier and check that the program does not end using the BPROGRAM_DONE flag.
    # The verifier will use BDDs to check the property.
    verifier = SymbolicBProgramVerifier(init_bprogram, all_events)
    result, explanation_str = verifier.verify(spec="G (!(event = BPROGRAM_DONE))", type="BDD", find_counterexample=True,
                                              print_info=False)

    if result:
        print("OK")
    else:
        print("Violation Found")
        print("Counterexample:")
        print(explanation_str)


if __name__ == "__main__":
    bprogram = init_bprogram()
    bprogram.run()

