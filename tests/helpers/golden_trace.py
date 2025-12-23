# tests/helpers/golden_trace.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple


def _read_lines(path: Path) -> List[str]:
    lines: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue  # skip metadata and blank lines
        lines.append(stripped)
    return lines


def assert_trace_exact(
    test_name: str,
    actual_events: List[str],
    golden_dir: str = "tests/golden_traces",
) -> Path:
    """
    Strict golden: actual trace must exactly equal golden trace (line-by-line).
    """
    golden_path = Path(golden_dir) / f"{test_name}.trace"
    if not golden_path.exists():
        raise AssertionError(
            f"Missing golden trace file: {golden_path}\n"
            f"Create it by saving a known-good run to that path."
        )

    expected = _read_lines(golden_path)

    if actual_events != expected:
        # Small diff-style output (first mismatch + some context)
        mismatch_idx = next((i for i, (a, e) in enumerate(zip(actual_events, expected)) if a != e), None)
        if mismatch_idx is None and len(actual_events) != len(expected):
            mismatch_idx = min(len(actual_events), len(expected))

        context_from = max(0, mismatch_idx - 5)
        context_to = mismatch_idx + 5

        exp_slice = expected[context_from:context_to]
        act_slice = actual_events[context_from:context_to]

        raise AssertionError(
            f"[{test_name}] Trace differs from golden!\n"
            f"Golden: {golden_path}\n"
            f"First mismatch index: {mismatch_idx}\n"
            f"Expected (context): {exp_slice}\n"
            f"Actual   (context): {act_slice}\n"
            f"Lengths: expected={len(expected)} actual={len(actual_events)}"
        )

    return golden_path


def assert_trace_contains_subsequence(
    test_name: str,
    actual_events: List[str],
    required_events: List[str],
) -> None:
    """
    Flexible golden: required_events must appear in actual_events in order (not necessarily contiguous).
    """
    it = iter(actual_events)
    missing_at = None

    for req in required_events:
        for a in it:
            if a == req:
                break
        else:
            missing_at = req
            break

    if missing_at is not None:
        raise AssertionError(
            f"[{test_name}] Trace missing required event in-order: '{missing_at}'\n"
            f"Required subsequence: {required_events}\n"
            f"Trace tail (last 50): {actual_events[-50:]}"
        )
