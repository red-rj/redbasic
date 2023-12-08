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
        for i in range(len(prog.body)):
            item = prog.body[self.idx]
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
            self.variables[stmt.iden.name] = self.eval(stmt.init)
        elif isinstance(stmt, ast.ExpressionStmt):
            val = self.eval(stmt.expression)
            self.variables["_"] = val
        else:
            raise NotImplementedError(f"unsupported statement {stmt}")


    def eval(self, expr:ast.Expr) -> ast.literal_t:
        if isinstance(expr, ast.Literal):
            return expr.value
        elif isinstance(expr, ast.BinaryExpr):
            return self.eval_binary_expr(expr)
        
        raise NotImplementedError(f"unsupported expression {expr}")

                    
    def eval_binary_expr(self, expr:ast.BinaryExpr):
        lhs = self.eval(expr.left)
        rhs = self.eval(expr.right)

        # TODO: this is awful
        result = eval(f'{lhs} {expr.operator} {rhs}')

        return result



