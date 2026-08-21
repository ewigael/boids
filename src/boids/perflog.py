"""Simple Performance Logger class"""

import weakref
import time


class PerformanceLogger:

    loggers = weakref.WeakSet()

    def __init__(self, name, tick_func=time.perf_counter, avgs_step=1):
        """Simple interface for logging time deltas between computations"""
        PerformanceLogger.loggers.add(self)

        self.name = name
        self.tick = tick_func
        self.avgs_step = avgs_step

        self.tags = []
        self.tags_data = {}
        self.avgs = {}
        self._avgs_counter = None

    def start(self):
        self.clear()
        self.tags = [("start", self.tick())]

    def add(self, name):
        now = self.tick()
        self.tags_data.setdefault(name, []).append(now - self.tags[-1][1])
        self.tags.append((name, now))

    def clear(self):
        self.tags.clear()

    def _set_averages(self):
        """Compute averages from stored data"""
        self.avgs.clear()
        for name, data in self.tags_data.items():
            self.avgs[name] = sum(data) / len(data)

    def get_deltas(self):
        # Black/PEP8 does us dirty here so here's the same code in a more leggible format
        # return [
        #     (
        #         name,
        #              f"{vs:.2f}s" if vs >= 1
        #         else f"{vs * 1e3:.2f}ms" if vs >= 1e-3
        #         else f"{vs * 1e6:.2f}μs" if vs >= 1e-6
        #         else f"{vs * 1e9:.2f}ns",
        #         vs
        #     ) for name, vs in self._get_deltas()
        # ]
        return [
            (
                name,
                (
                    f"{vs[-1]:.2f}s"
                    if vs[-1] >= 1
                    else (
                        f"{vs[-1] * 1e3:.2f}ms"
                        if vs[-1] >= 1e-3
                        else (
                            f"{vs[-1] * 1e6:.2f}μs"
                            if vs[-1] >= 1e-6
                            else f"{vs[-1] * 1e9:.2f}ns"
                        )
                    )
                ),
                vs[-1],
            )
            for name, vs in self.tags_data.items()
        ]

    def get_averages(self):
        if self._avgs_counter is None:
            self._avgs_counter = self.tick()

        if self.tick() - self._avgs_counter >= self.avgs_step:
            self._set_averages()
            self.tags_data.clear()
            self._avgs_counter = self.tick()

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
                vs,
            )
            for name, vs in self.avgs.items()
        ]
        # Black/PEP8 does us dirty here so here's the same return value in more legible code
        # return [
        #     (
        #         name,
        #              f"{vs:.2f}s" if vs >= 1
        #         else f"{vs * 1e3:.2f}ms" if vs >= 1e-3
        #         else f"{vs * 1e6:.2f}μs" if vs >= 1e-6
        #         else f"{vs * 1e9:.2f}ns",
        #         vs
        #     ) for name, vs in self.avgs.items()
        # ]
