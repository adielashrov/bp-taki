def _bt_debug_name(bt):
    name = getattr(bt, "name", None)
    if name:
        return name

    # BPpy's @thread decorator wraps generators in a function named `wrapper`.
    # The wrapper keeps the original generator in local var `f`.
    frame = getattr(bt, "gi_frame", None)
    if frame is not None:
        locals_ = getattr(frame, "f_locals", {}) or {}
        inner_bt = locals_.get("f")
        if inner_bt is not None:
            inner_name = getattr(getattr(inner_bt, "gi_code", None), "co_name", None)
            if inner_name:
                return inner_name

    code_name = getattr(getattr(bt, "gi_code", None), "co_name", None)
    if code_name:
        return code_name

    return repr(bt)


def debug_who_blocks(b_program, ev, logger=None):
    blockers = []
    # BPpy 1.x keeps the active sync statements on b_program.tickets (dicts),
    # not on the generator objects in b_program.bthreads.
    tickets = getattr(b_program, "tickets", None) or []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue

        block = ticket.get("block")
        if block is None:
            continue

        bt = ticket.get("bt")
        bt_name = _bt_debug_name(bt)

        try:
            if block.contains(ev):
                blockers.append(bt_name)
                continue
        except Exception:
            pass

        try:
            if ev in block:
                blockers.append(bt_name)
        except Exception:
            pass

    # Fallback for versions/layouts that expose the current statement on bthreads.
    if not blockers:
        for bt in getattr(b_program, "bthreads", []) or []:
            stmt = getattr(bt, "statement", None) or getattr(bt, "stmt", None)
            if stmt is None:
                continue

            block = getattr(stmt, "block", None)
            if block is None:
                continue

            bt_name = _bt_debug_name(bt)

            try:
                if block.contains(ev):
                    blockers.append(bt_name)
                    continue
            except Exception:
                pass

            try:
                if ev in block:
                    blockers.append(bt_name)
            except Exception:
                pass

    message = f"[WHO_BLOCKS] Event {ev.name} is blocked by: {blockers}"
    if logger:
        logger.info(message)
    else:
        print(message)
    return blockers
