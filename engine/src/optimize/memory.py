"""Cooperative CP-SAT memory stop, including native allocations in process RSS."""
import os
import resource
from threading import Event, Thread


def resident_memory_mb():
    # tracemalloc cannot see the solver's C++ allocations. statm reports current
    # RSS rather than the high-water mark left by an earlier invocation.
    try:
        with open("/proc/self/statm") as file:
            pages = int(file.read().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") / (1024 * 1024)
    except (OSError, ValueError, IndexError):
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


class MemoryGuard:
    def __init__(self, solver, max_memory_mb):
        self.solver = solver
        self.max_memory_mb = max_memory_mb
        self.finished = Event()
        self.thread = Thread(target=self._watch, name="solver-memory", daemon=True)
        self.exceeded = False

    def check(self):
        if resident_memory_mb() >= self.max_memory_mb:
            self.exceeded = True
        return self.exceeded

    def _watch(self):
        while not self.finished.wait(0.1):
            if self.check():
                # Repeat until Solve returns: a stop during solver startup can
                # otherwise arrive before OR-Tools installs its stop handle.
                self.solver.StopSearch()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.finished.set()
        self.thread.join()
