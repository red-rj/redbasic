# redbasic AST
from dataclasses import dataclass
import typing

# TODO: add precise location to AST nodes
@dataclass
class Location:
    line:int
    column:int

# --- base classes ---

class Stmt:
    "base statement type"
    pass

class Expr(Stmt):
    "base expression type"
    pass


# --- expressions ---

@dataclass
class BinaryExpr(Expr):
    operator:str
    left:Expr
    right:Expr

class LogicalExpr(BinaryExpr):
    pass

class AssignmentExpr(BinaryExpr):
    pass

@dataclass
class Identifier(Expr):
    name:str

@dataclass
class IntLiteral(Expr):
    value: int

@dataclass
class FloatLiteral(Expr):
    value: float

@dataclass
class StringLiteral(Expr):
    value:str

@dataclass
class SequenceExpr(Expr):
    expressions:list[Expr]

@dataclass
class UnaryExpr(Expr):
    operator:str
    argument:Expr

# --- statements ---
@dataclass
class Line(Stmt):
    """ A line of BASIC code.
    Ex: '10 print "Hello World!"' OR 'goto 10'
    """
    statement:Stmt
    linenum:int = 0

@dataclass
class Program(Stmt):
    "top level program"
    body:list[Line]

@dataclass
class VariableDecl(Stmt):
    iden:Identifier
    init:Expr

@dataclass
class VariableStmt(Stmt):
    declarations:list[VariableDecl]

class EmptyStmt(Stmt):
    pass

@dataclass
class BlockStmt(Stmt):
    body:list[Stmt]

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

@dataclass
class VariableDecl(Stmt):
    iden:Identifier
    init:Expr

@dataclass
class LetStmt(Stmt):
    declaration:VariableDecl

@dataclass
class ExpressionStmt(Stmt):
    expression:Expr

    