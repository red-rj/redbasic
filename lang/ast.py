# redbasic AST
from dataclasses import dataclass, field
import typing

# TODO: add precise location to AST nodes
@dataclass
class Location:
    line:int
    column:int

# --- base classes ---
@dataclass
class Ast:
    "root of all AST nodes"

class Stmt(Ast):
    "base statement type"
    pass

class Expr(Ast):
    "base expression type"
    pass

class EmptyNode:
    "for stateless nodes"
    __instance = None

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __repr__(self):
        return f"{self.__class__.__name__}()"

# --- expressions ---
@dataclass
class Identifier(Expr):
    name:str

@dataclass
class BinaryExpr(Expr):
    operator:str
    left:Expr
    right:Expr

class LogicalExpr(BinaryExpr):
    pass

class AssignmentExpr(BinaryExpr):
    left:Identifier


literal_t = typing.TypeVar('literal_t', int, float, str)

@dataclass
class Literal(Expr):
    value:literal_t

@dataclass
class IntLiteral(Literal):
    value: int

@dataclass
class FloatLiteral(Literal):
    value: float

@dataclass
class StringLiteral(Literal):
    value:str

@dataclass
class SequenceExpr(Expr):
    expressions:list[Expr]

@dataclass
class UnaryExpr(Expr):
    operator:str
    argument:Expr

@dataclass
class Func(Expr):
    name:str
    arguments:list[Expr]

# --- statements ---
@dataclass
class Line(Stmt):
    """ A line of BASIC code.
    Ex: '10 print "Hello World!"' OR 'goto 10'
    """
    statement:Stmt
    linenum:int = 0

@dataclass
class Label(Stmt):
    name:str

content_t = typing.TypeVar('content_t', Line, Label)

@dataclass
class Program(Stmt):
    "top level program"
    body:list[content_t]

@dataclass
class VariableDecl(Stmt):
    iden:Identifier
    init:AssignmentExpr

@dataclass
class IfStmt(Stmt):
    test:Expr
    consequent:Stmt
    alternate:Stmt

@dataclass
class PrintItem:
    expression:Expr
    sep:str

@dataclass
class PrintStmt(Stmt):
    printlist:list[PrintItem]

@dataclass
class InputStmt(Stmt):
    varlist:list[Identifier]

@dataclass
class GotoStmt(Stmt):
    destination:Expr

class GosubStmt(GotoStmt):
    pass

@dataclass
class VariableDecl(Stmt):
    iden:Identifier
    init:Expr

# @dataclass
# class LetStmt(Stmt):
#     declarations:list[VariableDecl]

@dataclass
class ExpressionStmt(Stmt):
    expression:Expr

@dataclass
class IfStmt(Stmt):
    test:Expr
    consequent:Stmt
    alternate:Stmt

class ReturnStmt(Stmt):
    pass

class InteractiveStmt(EmptyNode, Stmt):
    pass

class ClearStmt(InteractiveStmt):
    pass

class EndStmt(InteractiveStmt):
    pass

@dataclass
class RunStmt(Stmt):
    arguments:list[Expr]

@dataclass
class ListStmt(Stmt):
    arguments:list[Expr]
    mode:str = 'code'

