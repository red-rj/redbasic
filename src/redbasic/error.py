# TODO: use my own errors

type Err = Exception

class BadSyntax(SyntaxError):
    def __init__(self, msg, line):
        self.msg = msg
        self.lineno = line
        super().__init__(msg)

class UndefinedVar(LookupError):
    def __init__(self, varname):
        super().__init__(f'{varname} is undefined')


