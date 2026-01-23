from typing import Callable, Optional
from enum import IntEnum

class VerbosityLevel(IntEnum):
    NONE = 0
    PROG = 1
    INFO = 2


class Reporter:
    def __init__(self, verbosity: int):
        if verbosity < 0:
            raise ValueError("verbosity must be >= 0")

        self.verbosity = verbosity

    def report(self, verbosity_level: VerbosityLevel, message):
        if self.verbosity >= verbosity_level:
            print(message)

    def run_if(self, verbosity_level: VerbosityLevel, fn: Callable[[], None]):
        if self.verbosity >= verbosity_level:
            fn()