from log_b_program_runner_listener import LogBProgramRunnerListener
from debug_blocking import debug_who_blocks
from bppy.model.b_priority_event import BPEvent

class DebugBlockersListener(LogBProgramRunnerListener):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.logger = logger
        self._saw_end_game = False
    
    def event_selected(self, b_program, event):
        super().event_selected(b_program, event)
        if event.name == "end_game":
            self._saw_end_game = True

    def ended(self, b_program):
        super().ended(b_program)
        # At this point, bthreads have already advanced past `end_game`.
        if self._saw_end_game:
            debug_who_blocks(b_program, BPEvent("p_1_card_4_blue", priority=10.0), logger=self.logger)
