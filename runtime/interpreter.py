import io
import sys
import typing
import lang.ast as ast
from lang.parser import Parser
from enum import Enum, auto


number = typing.TypeVar('number', int, float)
TextIO = io.TextIOBase


class Interpreter:
    "Redbasic interpreter"

    def __init__(self, parser:Parser, out:TextIO=sys.stdout):
        self.parser = parser
        self.out = out
        self.idx = 0
        self.variables = {}
        self.labels:dict[str,int] = {}


    def exec_program(self, prog:ast.Program):
        for i, item in enumerate(prog.body):
            self.idx = i
            if isinstance(item, ast.Line):
                self.exec_statement(item.statement)
            elif isinstance(item, ast.Label):
                self.labels[item.name] = self.idx + 1
            else:
                raise RuntimeError("Bad Program body")
            
    def exec(self, code:str):
        prog = self.parser.parse(code)
        self.exec_program(prog)

    def exec_statement(self, stmt:ast.Stmt):
        if isinstance(stmt, ast.VariableDecl):
            name = stmt.iden.name
            value = self.eval(stmt.init)
            self.setvar(name, value)
        elif isinstance(stmt, ast.ExpressionStmt):
            val = self.eval(stmt.expression)
            self.setvar("_", val)
        else:
            raise NotImplementedError(f"unsupported statement {stmt}")


    def eval(self, expr:ast.Expr) -> ast.literal_t:
        if isinstance(expr, ast.Literal):
            return expr.value
        elif isinstance(expr, list): # SequenceExpr
            return [self.eval(e) for e in expr]
        elif isinstance(expr, ast.AssignmentExpr):
            return self.eval_assignment(expr)
        elif isinstance(expr, ast.LogicalExpr):
            return self.eval_logical_expr(expr)
        elif isinstance(expr, ast.BinaryExpr):
            return self.eval_binary_expr(expr)
        elif isinstance(expr, ast.UnaryExpr):
            return self.eval_unary_expr()
        elif isinstance(expr, ast.Identifier):
            return self.getvar(expr.name)
        
        
        raise NotImplementedError(f"unsupported expression {expr}")


    def eval_assignment(self, expr:ast.AssignmentExpr):
        name = expr.left.name
        value = self.eval(expr.right)

        # simple assignment
        if expr.operator == '=':
            self.setvar(name, value)
            return value
        
        # complex assignment
        assert len(expr.operator) == 2
        var = self.getvar(name)

        match expr.operator[0]:
            case '+':
                var += value
            case '-':
                var -= value
            case '*':
                var *= value
            case '/':
                var /= value

        self.setvar(name, var)
        return var
                    
    def eval_binary_expr(self, expr:ast.BinaryExpr):
        lhs = self.eval(expr.left)
        rhs = self.eval(expr.right)

        match expr.operator:
            case '+':
                return lhs + rhs
            case '-':
                return lhs - rhs
            case '*':
                return lhs * rhs
            case '/':
                return lhs / rhs
            case _:
                raise RuntimeError(f"bad binary operator '{expr.operator}'")

    def eval_logical_expr(self, expr:ast.LogicalExpr):
        lhs = self.eval(expr.left)
        rhs = self.eval(expr.right)

        match expr.operator:
            case '||':
                return lhs or rhs
            case '&&':
                return lhs and rhs
            
        raise RuntimeError(f"bad binary operator '{expr.operator}'")


    def eval_unary_expr(self, expr:ast.UnaryExpr):
        arg = self.eval(expr.argument)

        match expr.operator:
            case '+':
                arg = +arg
            case '-':
                arg = -arg
            case '!':
                arg = not arg
            case _:
                raise RuntimeError(f"bad unary operator '{expr.operator}'")
        
        return arg
    
    def getvar(self, name:str):
        try:
            var = self.variables[name]
            return var
        except KeyError:
            raise LookupError(f"undefined variable {name}")
        
    def setvar(self, name:str, value):
        self.variables[name] = value



