from .lexer import Token, Tokenizer
from .ast import *
from types import SimpleNamespace as AstNode


def parse_int(string:str):
    "Helper to handle C style octals"
    if string[0] == '0' and len(string) > 1 and 'x' not in string and 'X' not in string:
        # octal
        o = string[1:]
        return int(o, 8)
    else:
        return int(string, 0)


def check_assignmet_target(e:Expr):
    if isinstance(e, Identifier):
        return e
    raise SyntaxError('Invalid left-hand side in assignment expression')

def is_literal(tok:Token):
    return tok == Token.string_lit or tok == Token.floatingpoint or tok == Token.integer

def is_keyword(tok:Token):
    return tok.value >= Token.kw_print.value and tok.value <= Token.kw_rem.value

def is_assignment_op(tok:Token):
    return tok == Token.eq or tok == Token.eq_complex

def is_print_sep(tok:Token):
    return tok == Token.comma or tok == Token.semicolon

# helper for iterating through all keywords
def iter_keywords():
    begin = Token.kw_print.value
    end = Token.kw_rem.value + 1
    for i in range(begin, end):
        yield Token(i)



class Parser:
    def __init__(self):
        self.string = ''
        self.tokenizer = Tokenizer()
    
    def parse(self, textcode):
        self.string = textcode
        self.tokenizer.reset(textcode)

        self.lookahead = self.tokenizer.next_token()

        return self.program()

    
    def program(self):
        lines = []

    # ---

    def eat(self, expected:Token = None):
        if not expected:
            expected = self.lookahead.token
        
        node = self.lookahead
        
        if not node and expected != Token.eof:
            raise SyntaxError(f"Unexpected end of input, {expected=}")
        
        if node.token != expected:
            raise SyntaxError(f"Unexpected token {node.token}, {expected=}")
        
        self.lookahead = self.tokenizer.next_token()
        return node

    def eat_first_of(self, *validTokens:Token):
        for t in validTokens:
            try:
                return self.eat(t)
            except SyntaxError:
                pass

        # no valid tokens found
        if not self.lookahead and Token.eof not in validTokens:
            errmsg = f"Unexpected end of input, expected one of {validTokens}"
        else:
            errmsg = f"Unexpected token {self.lookahead.token}, expected one of {validTokens}"

        raise SyntaxError(errmsg)
