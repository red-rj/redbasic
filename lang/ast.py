# redbasic AST
from dataclasses import dataclass, field

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
class AssignmentExpr(Expr):
    operator:str
    left:Expr
    right:Expr


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