"""Prints the simulation to the terminal, one line per turn."""


class TerminalOutput:
    """Shows the trace of the simulation as plain text.

    Attributes:
        trace: One string per turn, like "D1-roof1 D2-goal".
    """

    def __init__(self, trace: list[str]) -> None:
        """Stores the trace so it can be shown later.

        Args:
            trace: The turns from Simulation.run().
        """
        self.trace = trace

    def show(self) -> None:
        """Prints every turn on its own line."""
        for line in self.trace:
            print(line)
