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
        yield bp.sync(request=bp.BEvent("Hello"), priority=30)


@bp.thread
def world():  # requests "World" once
    while True:
        yield bp.sync(request=bp.BEvent("World"), priority=10)


def init_bprogram():
    b_program = bp.BProgram(
        bthreads=[
           hello(), world()
        ],
        event_selection_strategy=bp.PriorityBasedEventSelectionStrategy(default_priority=0),
        listener=bp.PrintBProgramRunnerListener()
    )
    return b_program

if __name__ == "__main__":

    bp_program = init_bprogram()
    bp_program.run()