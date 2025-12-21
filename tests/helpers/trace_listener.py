# tests/helpers/trace_listener.py

class TraceListener:
    def __init__(self):
        self.events = []

    def starting(self, b_program): pass
    def started(self, b_program): pass
    def super_step_done(self, b_program): pass
    def ended(self, b_program): pass
    def assertion_failed(self, b_program): pass
    def halted(self, b_program): pass

    def event_selected(self, b_program, event):
        self.events.append(event.name)

    def winner(self):
        for name in self.events:
            if name.startswith("p_") and name.endswith("_no_more_cards"):
                return int(name.split("_")[1])
        return None

    def tail(self, n: int = 30):
        return self.events[-n:]
