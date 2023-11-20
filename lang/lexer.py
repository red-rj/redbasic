import re
from enum import Enum, StrEnum, auto
from typing import NamedTuple


class Token(StrEnum):
    # literals
    string_literal = auto()
    integer = auto()
    floatingpoint = auto()

    comment = auto()
    identifier = auto()
    named_label = auto()

    # arithimatic operators
    additive_op = auto()
    multiplicative_op = auto()

    # relational operators
    relational_op = auto()

    # equality
    #eq
    neq = auto()

    # assignment
    #eq
    eq_complex = auto()

    # logical operators
    logical_not = auto()
    logical_and = auto()
    logical_or = auto()

    eol = auto()
    eof = auto()

    # manual values
    #   keywords
    kw_print = 'print'
    kw_input = 'input'
    kw_let = 'let'
    kw_goto = 'goto'
    kw_gosub = 'gosub'
    kw_return = 'return'
    kw_if = 'if'
    kw_then = 'then'
    kw_else = 'else'
    kw_end = 'end'
    kw_clear = 'clear'
    kw_list = 'list'
    kw_run = 'run'
    kw_rem = 'rem'
    kw_true = 'true'
    kw_false = 'false'
    #   symbols
    eq = '='
    l_paren = '('
    r_paren = ')'
    comma = ','
    semicolon = ';'



# lang spec definition
rxc = re.compile
basic_spec = {
    rxc(r"\r\n|\n"): Token.eol,
    rxc(r'^\s+'): None,
    
    # Numbers
    #   floating point w/ scientific exponents
    rxc(r"(\d+\.\d*)([Ee][-+]?\d+)?"): Token.floatingpoint,
    #   integers, in HEX, OCTAL and DECIMAL respectivly. TODO: support oldschool $90 hex
    rxc(r"(0[xX][a-fA-F\d]+)|(0[0-7]+)|(\d+)"): Token.integer,
    rxc(r'"[^"]*"'): Token.string_literal,

    # math operations
    rxc(r"[+\-]"): Token.additive_op,
    rxc(r"[*/]"): Token.multiplicative_op,

    # keywords
    rxc(r"^\b(PRINT|PR)\b", re.IGNORECASE): Token.kw_print,
    rxc(r"^\bIF\b", re.IGNORECASE): Token.kw_if,
    rxc(r"^\bTHEN\b", re.IGNORECASE): Token.kw_then,
    rxc(r"^\bELSE\b", re.IGNORECASE): Token.kw_else,
    rxc(r"^\bINPUT\b", re.IGNORECASE): Token.kw_input,
    rxc(r"^\bLET\b", re.IGNORECASE): Token.kw_let,
    rxc(r"^\bGOTO\b", re.IGNORECASE): Token.kw_goto,
    rxc(r"^\bGOSUB\b", re.IGNORECASE): Token.kw_gosub,
    rxc(r"^\bRETURN\b", re.IGNORECASE): Token.kw_return,
    rxc(r"^\bEND\b", re.IGNORECASE): Token.kw_end,
    rxc(r"^\bCLEAR\b", re.IGNORECASE): Token.kw_clear,
    rxc(r"^\bLIST\b", re.IGNORECASE): Token.kw_list,
    rxc(r"^\bRUN\b", re.IGNORECASE): Token.kw_run,
    rxc(r"^REM .*", re.IGNORECASE): Token.comment,

    # identifiers
    #   named labels
    rxc(r"^[a-zA-Z_]\w*:"): Token.named_label,
    #   variables
    rxc(r"[a-zA-Z_]\w*"): Token.identifier,

    rxc(r"\("): Token.l_paren,
    rxc(r"\)"): Token.r_paren,
    
    rxc(r','): Token.comma,
    rxc(r';'): Token.semicolon,

    # assignment
    # rxc(''): Token.eq
    rxc(r'[+\-*/]='): Token.eq_complex,

    # relational
    rxc(r'[><]=?'): Token.relational_op,

    # equality
    rxc(r'='): Token.eq,
    rxc(r'<>|><'): Token.neq,
}


class TokenNode(NamedTuple):
    token:Token = Token.eof
    value:str = None

    def __bool__(self):
        return self.token != Token.eof
    
    def __repr__(self) -> str:
        return f"{TokenNode.__name__}({self.token!s}, {self.value!r})"


class Tokenizer:
    def __init__(self, string:str = None):
        self.reset(string)

    def reset(self, string:str = None):
        self.string = string
        self.cursor = 0

    def has_more_tokens(self):
        return self.cursor < len(self.string)
    
    def is_eof(self):
        return self.cursor == len(self.string)
    
    def next_token(self):
        if not self.has_more_tokens():
            return TokenNode()
        
        code = self.string[self.cursor:]

        for pattern, token in basic_spec.items():
            matched = pattern.match(code)
            if not matched:
                continue
            
            token_value = matched.group(0)
            self.cursor += len(token_value)

            if not token or token == Token.comment:
                return self.next_token()

            return TokenNode(token, token_value)
        
        raise SyntaxError(f"Unexpected token: '{code[0]}'")
    

    def __iter__(self):
        return self
    
    def __next__(self):
        n = self.next_token()
        if not n:
            raise StopIteration
        return n
    
    def __bool__(self):
        return self.has_more_tokens()

