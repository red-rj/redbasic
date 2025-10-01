# redbasic AST
import io
from dataclasses import dataclass
from typing import TextIO

# --- base classes ---
class Ast:
    "root of all AST nodes"
    pass

class Stmt(Ast):
    "base statement type"
    pass

class Expr(Ast):
    "base expression type"
    pass

# Interpreter specific Asts
class InteractiveStmt(Stmt):
    pass

class Empty:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

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


@dataclass
class Literal(Expr):
    value:int|float|str

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
    """
    A line of BASIC code.
        10 print "Hello World!"
        goto 10
    """
    statement:Stmt
    linenum:int = 0

@dataclass
class Label(Line):
    """
    A named line
        name: input A
    """
    def __init__(self, statement:Stmt, name:str):
        self.name = name
        super().__init__(statement, hash(name))

@dataclass
class Program(Stmt):
    "top level program"
    body:list[Line]

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

class ReturnStmt(Empty, Stmt):
    pass

class ClearStmt(Empty, InteractiveStmt):
    pass

class EndStmt(Empty, InteractiveStmt):
    pass

@dataclass
class RunStmt(InteractiveStmt):
    arguments:list[Expr]

@dataclass
class ListStmt(InteractiveStmt):
    arguments:list[Expr]
    mode:str

# reconstruct util

def reconstruct_expr(expr, ss:TextIO):
    match expr:
        case list(): #TODO: SequenceExpr
            for e in expr:
                reconstruct_expr(e, ss)
                ss.write(',')
            pos = ss.tell()
            ss.seek(pos-1) # remove last ,
        case Identifier():
            ss.write(expr.name)
        case Func():
            ss.write(f'{expr.name}(')
            reconstruct_expr(expr.arguments, ss)
            ss.write(')')
        case Literal():
            if isinstance(expr.value, str):
                ss.write(f'"{expr.value}"')
            else:
                ss.write(f'{expr.value}')
        case UnaryExpr():
            ss.write(expr.operator)
            reconstruct_expr(expr.argument, ss)
        case BinaryExpr():
            reconstruct_expr(expr.left, ss)
            ss.write(expr.operator)
            reconstruct_expr(expr.right, ss)
        case _:
            raise RuntimeError(f"cannot recontruct {expr!r}")


def reconstruct(program:Program):
    "reconstruct an aproximation of source code from an AST tree"
    ss = io.StringIO()
    recon = lambda e: reconstruct_expr(e, ss)

    for a in program.body:
        stmt = a.statement
        if isinstance(a, Label):
            ss.write(f'{a.name}: ')
        else:
            ss.write(f'{a.linenum:<4d} ')

        match stmt:
            case PrintStmt():
                ss.write('print ')
                for pi in stmt.printlist:
                    recon(pi.expression)
                    if pi.sep:
                        ss.write(pi.sep)
            case InputStmt():
                ss.write("input ")
                recon(stmt.varlist)
            case GotoStmt():
                ss.write("goto ")
                recon(stmt.destination)
            case GosubStmt():
                ss.write("gosub ")
                recon(stmt.destination)
            case VariableDecl():
                ss.write('let ')
                recon(stmt.iden)
                ss.write('=')
                recon(stmt.init)
            case IfStmt():
                ss.write('if ')
                recon(stmt.test)
                ss.write(' then')
                recon(stmt.consequent)
                if stmt.alternate:
                    ss.write(' else ')
                    recon(stmt.alternate)
            case ExpressionStmt():
                recon(stmt.expression)
            case ReturnStmt():
                ss.write('return')
            case ClearStmt():
                ss.write('clear')
            case EndStmt():
                ss.write('end')
            case RunStmt():
                ss.write('run')
            case ListStmt():
                ss.write('list ')
                recon(stmt.arguments)
                ss.write(stmt.mode)
            case _:
                raise RuntimeError(f"cannot recontruct {stmt!r}")
        ss.write('\n')
    return ss.getvalue()