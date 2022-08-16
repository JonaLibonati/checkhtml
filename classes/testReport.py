from __future__ import annotations

class TestReport:
    def __init__(self, name: str) -> None:
        self.name = name
        self.data = [{"type": 'title', "data": self.name}]
        self.sections = []
        self.lines = []
        self._firstLine()

    def _firstLine(self) -> None:
        if len(self.name) <= 60:
            self.lines.append(f"\n-------------------- {self.name.upper()} --------------------\n")
        else: self.lines.append(f"\n{self.name.upper()}\n")

    def addSection(self, *args: Section) -> Section:
        for arg in args:
            self.sections.append(arg)
            for data in arg.data:
                self.data.append(data)
            for line in arg.lines:
                self.lines.append(line)
        return self

    def setName(self, new_name: str) -> None:
        self.name = new_name
        self.data[0] = {"type": 'title', "data": self.name}
        if len(self.name) <= 60:
            self.lines[0] = f"\n---------------------- {self.name.upper()} ----------------------\n"
        else: self.lines[0] = f"\n{self.name.upper()}\n"

    def print(self) -> None:
        for line in self.lines:
            print(line)

    #def printHtml(self) -> None:
    #    pass

    #def printTxt(self) -> None:
    #    pass

class Section:
    def __init__(self, name: str) -> None:
        self.name = name
        self.data = [{"type": 'subtitle', "data": self.name}]
        self.subsection = []
        self.results = []
        self.lines = []
        self._firstLine()

    def _firstLine(self) -> None:
        if len(self.name) <= 60:
            self.lines.append(f"\n------------ {self.name.upper()} ------------\n")
        else: self.lines.append(f"\n{self.name.upper()}\n")

    def addResult(self, *args: Result) -> Section:
        for arg in args:
            self.results.append(arg)
            self.data.append(arg.data)
            self.lines.append(arg.line)
        return self

    def addSubSection(self, *args: Subsection) -> Section:
        for arg in args:
            if len(self.lines) == 1:
                if len(arg.name) <= 60: arg.lines[0] = f"--- {arg.name.upper()} ---\n"
                else: arg.lines[0] = f"{arg.name.upper()}\n"
            self.subsection.append(arg)
            for data in arg.data:
                self.data.append(data)
            for line in arg.lines:
                    self.lines.append(line)
        return self

    def setName(self, new_name: str) -> None:
        self.name = new_name
        self.data[0] = {"type": 'title', "data": self.name}
        if len(self.name) <= 60:
            self.lines[0] = f"\n------------ {self.name.upper()} ------------\n"
        else: self.lines[0] = f"\n{self.name.upper()}\n"

    def print(self) -> None:
        for line in self.lines:
            print(line)

class Subsection(Section):
    def _firstLine(self) -> None:
        if len(self.name) <= 60:
            self.lines.append(f"\n-- {self.name.upper()} --\n")
        else: self.lines.append(f"\n{self.name.upper()}\n")

class Result:
    def __init__(self, description: str, result = 'comment') -> None:
        self.description = description
        self.result = result
        self.data = {"type": 'result', "data": self.description, "result": result}
        self.line = ''
        self._writeLine()

    def _writeLine(self) -> None:
        if self.result == "success":
            self.line = f"🟢 - {self.description}"
        elif self.result == "fail":
            self.line = f"🔴 - {self.description}"
        elif self.result == "warning":
            self.line = f"🟡 - {self.description}"
        elif self.result == "comment":
            self.line = f"{self.description}"
        else:
            self.line = 'CODE ERROR: Invalid result. Please use ["success", "fail, "warning" or "comment"(default)]'

    def print(self) -> None:
        print(self.line)