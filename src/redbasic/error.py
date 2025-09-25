# TODO: use my own errors

class BasicError(Exception):
    pass

class SyntaxError(BasicError):
    def __init__(self, msg, line=None):
        self.msg = msg
        self.line = line

class RuntimeError(BasicError):
    def __init__(self, msg):
        self.msg = msg
