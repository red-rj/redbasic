# TODO: use my own errors

class BasicError(Exception):
    pass

class SyntaxError(BasicError):
    def __init__(self, msg, line=None):
        self.msg = msg
        self.line = line
        super().__init__(msg, line)

class RuntimeError(BasicError):
    pass

class VarLookupError(RuntimeError):
    def __init__(self, varname):
        super().__init__(f'{varname} undefined')
