import os
import sys
import urllib.request

class CmdArgs:

    def __init__(self) -> None:
        self.argv = sys.argv
        self.script_name = sys.argv[0]
        self.structure = 'SCRIPT_NAME <-OPTIONS or --OPTIONS> [INPUTS]'
        self.options = []
        self.inputs = []
        self._getOpt()
        self._createInputs()

    def _getOpt(self) -> None:
        for i in range(1, len(self.argv)):
            if sys.argv[i][0] == '-' or sys.argv[i][0:1] == '--' and not(os.path.isdir(sys.argv[i]) or os.path.isfile(sys.argv[i])):
                self.options.append(CmdOption(sys.argv[i]))
            else:
                break

    def _createInputs(self) -> None:
        input_name_list = self.argv[(len(self.options) + 1) :]
        for input_name in input_name_list:
            self.inputs.append(CmdInput(input_name))

    def inputsQty(self) -> int:
        return len(self.inputs)

    def optionsQty(self) -> int:
        return len(self.options)

    def isValidInputQty(self, min_input_qty = -1, max_input_qty= -1) -> bool:
        return ((min_input_qty <= self.inputsQty() <= max_input_qty) or (self.inputsQty() >= min_input_qty and max_input_qty == -1))

    def isValidOptQty(self, max_opt_qty = -1) -> bool:
        return (self.optionsQty() <= max_opt_qty and max_opt_qty != -1)

class CmdInput:
    def __init__(self, path: str) -> None:
        self.path = path
        self.name = ''
        self.type = ''
        self._getType()

    def _getType(self) -> None:
        if os.path.exists(self.path):
            if os.path.isdir(self.path):
                self.type = "dir"
            elif os.path.isfile(self.path):
                self.type = os.path.splitext(self.path)[1]
        elif 'http' in self.path:
            if 'https' in self.path:
                self.path = self.path.replace('https', 'http')
            try:
                urllib.request.urlopen(self.path)
                self.type = 'httpUrl'
            except ValueError as e:
                print(f'Error: {e}')
            except urllib.error.URLError as e:
                print(f'Error: {e}')
        else:
            self.type = None

    def isValidInputType(self, *valid_input_types: str) -> bool:
        return self.type in valid_input_types

class CmdOption:
    def __init__(self, name: str) -> None:
        self.name = name

    def isValidOption(self, *valid_options: str) -> bool:
        return self.name in valid_options
