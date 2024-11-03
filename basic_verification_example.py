from bppy.analysis.symbolic_bprogram_verifier import SymbolicBProgramVerifier

import bppy as bp
from bppy import *

# Control events
all_events = [
    BEvent("Hello"),
    BEvent("World")
]


@bp.thread
def hello():  # requests "Hello" once
    while True:
        yield bp.sync(request=bp.BEvent("Hello"))


@bp.thread
def world():  # requests "World" once
    while True:
        yield bp.sync(request=bp.BEvent("World"))


def init_bprogram():
    b_program = bp.BProgram(
        bthreads=[
           hello(), world()
        ],
        event_selection_strategy=bp.SimpleEventSelectionStrategy(),
        listener=bp.PrintBProgramRunnerListener()
    )
    return b_program

if __name__ == "__main__":

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

