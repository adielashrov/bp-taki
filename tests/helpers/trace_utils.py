# tests/helpers/trace_utils.py

from datetime import datetime
from pathlib import Path


def write_trace_to_file(test_name: str, events: list[str], directory: str = "test_traces"):
    """
    Writes the event trace to a uniquely named file:
    <directory>/<test_name>_<YYYY-MM-DD_HH-MM-SS>.trace
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{test_name}_{timestamp}.trace"
    path = Path(directory) / filename

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Test: {test_name}\n")
        f.write(f"# Timestamp: {timestamp}\n")
        f.write("# -------------------------\n")
        for e in events:
            f.write(e + "\n")

    return path
