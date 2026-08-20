"""Simple Performance Logger class"""

import weakref
import time


class PerformanceLogger:

    loggers = weakref.WeakSet()

    def __init__(self, name, tick_func=time.perf_counter):
        """Simple interface for logging time deltas between computations"""
        PerformanceLogger.loggers.add(self)

        self.name = name
        self.tick = tick_func

        self.tags = []

    def start(self):
        self.clear()
        self.add("start")

    def add(self, name):
        self.tags.append((name, self.tick()))

    def clear(self):
        self.tags.clear()

    def _get_deltas(self):
        return [
            (name, v - prev_v)
            for (_, prev_v), (name, v) in zip(self.tags, self.tags[1:])
        ]

    def get_deltas(self):
        # Black/PEP8 does us dirty here so here's the same code in a more leggible format
        # return [
        #     (
        #         name,
        #              f"{vs:.2f}s" if vs >= 1
        #         else f"{vs * 1e3:.2f}ms" if vs >= 1e-3
        #         else f"{vs * 1e6:.2f}μs" if vs >= 1e-6
        #         else f"{vs * 1e9:.2f}ns"
        #     ) for name, vs in self._get_deltas()
        # ]
        return [
            (
                name,
                (
                    f"{vs:.2f}s"
                    if vs >= 1
                    else (
                        f"{vs * 1e3:.2f}ms"
                        if vs >= 1e-3
                        else f"{vs * 1e6:.2f}μs" if vs >= 1e-6 else f"{vs * 1e9:.2f}ns"
                    )
                ),
            )
            for name, vs in self._get_deltas()
        ]
