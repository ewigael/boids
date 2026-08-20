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

    def get_averages(self):
        if self._avgs_counter is None:
            self._avgs_counter = time.time()

        for name, v in self._get_deltas():
            if name not in self.tags_data:
                self.tags_data[name] = [v]
            else:
                self.tags_data[name].append(v)

        print(time.time() - self._avgs_counter)
        if time.time() - self._avgs_counter >= self.avgs_step:
            print("reset averages")
            self._set_averages()
            self.tags_data.clear()
            self._avgs_counter = time.time()

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
            for name, vs in self.avgs.items()
        ]
        # Black/PEP8 does us dirty here so here's the same return value in more legible code
        # return [
        #     (
        #         name,
        #              f"{vs:.2f}s" if vs >= 1
        #         else f"{vs * 1e3:.2f}ms" if vs >= 1e-3
        #         else f"{vs * 1e6:.2f}μs" if vs >= 1e-6
        #         else f"{vs * 1e9:.2f}ns"
        #     ) for name, vs in self.avgs.items()
        # ]
