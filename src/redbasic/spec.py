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

    # equality operators
    equality_op = auto()

    # assignment
    assignment = auto()
    assignment_complex = auto()

    # logical operators
    logical_not = auto()
    logical_and = auto()
    logical_or = auto()

    eol = auto()
    eof = auto()

    f_builtin = auto()
    # statement specific
    list_mode = auto()
    print_sep = auto()

    # manual values
    # keywords
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
    # symbols
    l_paren = '('
    r_paren = ')'
    comma = ','
    semicolon = ';'

# lang spec definition
rxc = re.compile
basic_spec = {
    # ignorables
    Token.eol: rxc(r"(\r\n|\n)"),
    None: rxc(r'\s+'), 
    Token.comment: rxc(r"\bREM\b.*", re.IGNORECASE),
    
    # Numbers
    #   floating point w/ scientific exponents
    Token.floatingpoint: rxc(r"(\d+\.\d*)([Ee][-+]?\d+)?"),
    #   support oldschool $90 hex: integers, in HEX, OCTAL and DECIMAL respectivly. TODO
    Token.integer: rxc(r"((0[xX][a-fA-F\d]+)|(0[0-7]+)|(\d+))"),
    Token.string_literal: rxc(r'"[^"]*"'),

    # equality
    Token.equality_op: rxc(r'(==|<>|><)'),

    # assignment
    Token.assignment_complex: rxc(r'[-+*/]='),
    Token.assignment: rxc(r'='),

    # relational
    Token.relational_op: rxc(r'[><]=?'),

    # math operations
    Token.additive_op: rxc(r"[+\-]"),
    Token.multiplicative_op: rxc(r"[*/]"),

    Token.l_paren: rxc(r"\("),
    Token.r_paren: rxc(r"\)"),
    Token.comma: rxc(r','),
    Token.semicolon: rxc(r';'),

    Token.logical_not: rxc(r'!'),
    Token.logical_and: rxc(r'&&'),
    Token.logical_or: rxc(r'[|]{2}'),

    # keywords
    Token.kw_print: rxc(r"\b(PRINT|PR)\b", re.IGNORECASE),
    Token.kw_if: rxc(r"\bIF\b", re.IGNORECASE),
    Token.kw_then: rxc(r"\bTHEN\b", re.IGNORECASE),
    Token.kw_else: rxc(r"\bELSE\b", re.IGNORECASE),
    Token.kw_input: rxc(r"\bINPUT\b", re.IGNORECASE),
    Token.kw_let: rxc(r"\bLET\b", re.IGNORECASE),
    Token.kw_goto: rxc(r"\bGOTO\b", re.IGNORECASE),
    Token.kw_gosub: rxc(r"\bGOSUB\b", re.IGNORECASE),
    Token.kw_return: rxc(r"\bRETURN\b", re.IGNORECASE),
    Token.kw_end: rxc(r"\bEND\b", re.IGNORECASE),
    Token.kw_clear: rxc(r"\bCLEAR\b", re.IGNORECASE),
    Token.kw_list: rxc(r"\bLIST\b", re.IGNORECASE),
    Token.kw_run: rxc(r"\bRUN\b", re.IGNORECASE),

    # builtin functions
    Token.f_builtin: rxc(r"\b(USR|RND|POW|SQRT)\b", re.IGNORECASE),

    # identifiers
    #   named labels
    Token.named_label: rxc(r"[a-zA-Z_]\w*:"),
    #   variables
    Token.identifier: rxc(r"[a-zA-Z_]\w*")
}
