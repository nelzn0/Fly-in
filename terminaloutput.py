class TerminalOutput:

    def __init__(self, trace: list[str]) -> None:
        self.trace = trace

    def show(self) -> None:
        for line in self.trace:
            print(line)
