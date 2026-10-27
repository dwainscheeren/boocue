"""Absolute-time, coalescing light scheduler; no Home Assistant dependency."""

from __future__ import annotations

import asyncio
from bisect import bisect_right
from collections.abc import Awaitable, Callable

from .models import Cue, Effect


async def play_timeline(
    effect: Effect,
    emit: Callable[[Cue, int], Awaitable[None]],
    progress: Callable[[float, int], None],
    *,
    start_delay: float,
    speed: float,
    interval: float,
    repeat: bool,
) -> None:
    """Use the latest due cue; never replay a backlog after a slow device call."""
    loop = asyncio.get_running_loop()
    epoch = loop.time() + start_delay
    times = [c.at for c in effect.cues]
    cycle = 0
    index = -1
    emitted = 0
    next_dispatch = epoch
    while True:
        now = loop.time()
        elapsed = max(0.0, (now - epoch) * speed)
        if now < epoch:
            await asyncio.sleep(min(epoch - now, 0.1))
            continue
        if elapsed >= effect.duration:
            if not repeat:
                progress(effect.duration, cycle)
                return
            skipped_cycles = max(1, int(elapsed / effect.duration))
            cycle += skipped_cycles
            epoch += effect.duration * skipped_cycles / speed
            elapsed = (now - epoch) * speed
            index = -1
        progress(elapsed, cycle)
        due = bisect_right(times, elapsed) - 1
        if due >= 0 and due != index and now >= next_dispatch:
            await emit(effect.cues[due], emitted)
            emitted += 1
            index = due
            next_dispatch = loop.time() + interval
        await asyncio.sleep(min(interval, 0.1))
