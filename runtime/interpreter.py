import io
import sys
import typing
import lang.ast as ast
from lang.ast import literal_t
from lang.parser import Parser
import random


number = typing.TypeVar('number', int, float)
TextIO = io.TextIOBase

def builtin_rnd(min:int, max:int=None):
    if max is None:
        min, max = 0, min

    return random.randint(min, max)

def builtin_usr(out:TextIO, *args):
    out.write(f"<usr func {args=}\n")



class Interpreter:
    "Redbasic interpreter"

    def __init__(self, parser:Parser, out:TextIO=sys.stdout, in_:TextIO=sys.stdin):
        self.parser = parser
        self.output = out
        self.input = in_
        self.idx = 0
        self.cur_linenum = 0
        self.variables = {}
        self.labels:dict[str,int] = {}
        self.ast = ast.Program([])

    
    def add_line(self, astLine):
        self.ast.body.append(astLine)


    def exec_program(self, prog:ast.Program):
        self.ast = prog
        maxidx = len(prog.body)
        
        while self.idx < maxidx:
            item = prog.body[self.idx]

            if isinstance(item, ast.Line):
                self.cur_linenum = item.linenum
                self.exec_statement(item.statement)
            elif isinstance(item, ast.Label):
                self.labels[item.name] = self.idx + 1
            else:
                raise RuntimeError("Bad Program body")
            
            self.idx += 1

            
    def exec(self):
        self.exec_program(self.ast)

    def exec_statement(self, stmt:ast.Stmt):
        match stmt:
            case ast.VariableDecl():
                name = stmt.iden.name
                value = self.eval(stmt.init)
                self.setvar(name, value)
            case ast.ExpressionStmt():
                val = self.eval(stmt.expression)
                self.setvar("_", val)
            case ast.PrintStmt():
                self.print_stmt(stmt)
            case ast.GotoStmt():
                self.goto_stmt(stmt)
            case ast.EndStmt():
                self.idx = float('inf')
            case _:
                raise NotImplementedError(f"unsupported statement {stmt}")


    def eval(self, expr:ast.Expr) -> literal_t:
        match expr:
            case ast.Literal():
                return expr.value
            case list():
                return [self.eval(e) for e in expr] # SequenceExpr
            case ast.AssignmentExpr():
                return self.eval_assignment(expr)
            case ast.LogicalExpr():
                return self.eval_logical_expr(expr)
            case ast.BinaryExpr():
                return self.eval_binary_expr(expr)
            case ast.UnaryExpr():
                return self.eval_unary_expr()
            case ast.Identifier():
                return self.getvar(expr.name)
            case ast.Func():
                return self.func(expr)
            case _:        
                raise NotImplementedError(f"unsupported expression {expr}")

    def func(self, func:ast.Func):
        if func.name == 'rnd':
            error = ''
            args = self.eval(func.arguments)          

            if len(func.arguments) > 2:
                error = "too many arguments"
            elif len(func.arguments) == 0:
                error = "not enough arguments"
            elif not all(isinstance(t, (int, float)) for t in args):
                error = 'invalid argument type'
            
            if error:
                raise RuntimeError("rnd: "+error)
            
            return builtin_rnd(*args)
        elif func.name == 'usr':
            args = self.eval(func.arguments)
            builtin_usr(self.output, *args)


    def print_stmt(self, printstmt:ast.PrintStmt):
        for item in printstmt.printlist:
            val = self.eval(item.expression)
            if item.sep == ',':
                string = f"{val}{' '*8}"
            else:
                string = str(val)
            
            self.output.write(string)
        self.output.write('\n')


    def goto_stmt(self, goto:ast.GotoStmt):
        dest = self.eval(goto.destination)

        if isinstance(dest, int):
            for i, line in enumerate(self.ast.body):
                if isinstance(line, ast.Label):
                    continue

                if line.linenum == dest:
                    self.idx = i
                    break
        elif isinstance(dest, str):
            self.idx = self.labels[dest]


        


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



