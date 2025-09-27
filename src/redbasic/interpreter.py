import sys
from typing import TextIO as Stream
from . import ast, error
from .parser import Parser, parse_int


def builtin_rnd(min:int, max:int=None):
    from random import randint
    if max is None:
        min, max = 0, min

    return randint(min, max)

def builtin_usr(out:Stream, *args):
    raise NotImplementedError("USR func")



class Interpreter:
    "Redbasic interpreter"

    TEMP_VAR = '_'

    def __init__(self, parser:Parser = None, out:Stream=sys.stdout, in_:Stream=sys.stdin):
        self.parser = parser if parser is not None else Parser()
        self.output = out
        self.input = in_
        self.idx = 0
        self.cur_linenum = 0
        self.variables = {}
        self.labels:dict[str,int] = {}
        self.ast:ast.Program = None
        self.substack = []

    
    def add_line(self, astLine:str):
        tp = Parser()
        l = tp.parse_line(astLine)
        if self.ast:
            self.ast.body.append(l)
        else:
            self.ast = ast.Program([l])

    def set_source(self, code:str):
        self.ast = self.parser.parse(code)


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
                raise error.RuntimeError("Bad Program body")
            
            self.idx += 1

            
    def exec(self):
        self.exec_program(self.ast)

    # ---

    def exec_statement(self, stmt:ast.Stmt):
        match stmt:
            case ast.VariableDecl():
                name = stmt.iden.name
                value = self.eval(stmt.init)
                self.setvar(name, value)
            case ast.ExpressionStmt():
                val = self.eval(stmt.expression)
                # se for uma expressão solta, salvar em TEMP_VAR
                if not isinstance(stmt.expression, ast.AssignmentExpr):
                    self.setvar(self.TEMP_VAR, val)
            case ast.PrintStmt():
                self.eval_print(stmt)
            case ast.GotoStmt():
                self.eval_goto(stmt)
            case ast.EndStmt():
                self.idx = float('inf')
            case ast.IfStmt():
                self.eval_if(stmt)
            case ast.InputStmt():
                self.eval_input(stmt)
            case ast.InteractiveStmt():
                pass
            case _:
                raise NotImplementedError(f"unsupported statement {stmt}")

    def eval(self, expr:ast.Expr) -> int|float|str|list:
        match expr:
            case ast.Literal():
                return expr.value
            case list():# SequenceExpr
                return [self.eval(e) for e in expr] 
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
                return self.eval_func(expr)
            case _:        
                raise NotImplementedError(f"unsupported expression {expr}")

    def eval_func(self, func:ast.Func):
        if func.name == 'rnd':
            args = self.eval(func.arguments)

            try:
                n = builtin_rnd(*args)
                return n
            except Exception as e:
                raise error.RuntimeError('rnd: '+str(e))
            
        elif func.name == 'usr':
            args = self.eval(func.arguments)
            builtin_usr(self.output, *args)


    def eval_print(self, printstmt:ast.PrintStmt):
        for item in printstmt.printlist:
            val = self.eval(item.expression)
            if item.sep == ',':
                string = f"{val}{' '*8}"
            elif item.sep == ';' or item.sep is None:
                string = str(val)
            else:
                raise error.SyntaxError(f"Bad print separator '{item.sep}'", self.idx)
            
            self.output.write(string)
        self.output.write('\n')

    def _calc_go(self, dest):
        if isinstance(dest, int):
            indexedbody = ( x for x in enumerate(self.ast.body) if hasattr(x[1], 'linenum') )
            theresult = [x[0] for x in indexedbody if x[1].linenum==dest][0]
            return theresult
        if isinstance(dest, str):
            return self.labels[dest]
        
        raise error.RuntimeError(f"Unexpected destination {dest!r}")


    def eval_goto(self, goto:ast.GotoStmt):
        dest = self.eval(goto.destination)
        newidx = self._calc_go(dest)
        self.idx = newidx

    def _gosub(self, gosub:ast.GosubStmt):
        dest = self.eval(gosub.destination)
        pos = self.idx+1
        self.substack.append(pos)
        if len(self.substack) > 1024:
            raise RuntimeError("recursion limit")

        newidx = self._calc_go(dest)
        self.idx = newidx

    def _return(self):
        pos = self.substack[-1]
        self.substack.pop()
        self.idx = pos


    def eval_if(self, stmt:ast.IfStmt):
        cond = self.eval(stmt.test)
        if cond:
            self.exec_statement(stmt.consequent)
        elif stmt.alternate:
            self.exec_statement(stmt.alternate)

    def eval_input(self, stmt:ast.InputStmt):
        for var in stmt.varlist:
            line = self.input.readline().strip()

            converters = parse_int, float, str
            value = None

            for conv in  converters:
                try:
                    value = conv(line)
                    break
                except ValueError:
                    continue

            if value is None:
                raise error.RuntimeError("Bad input")
            
            self.setvar(var.name, value)


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
        rhs = self.eval(expr.right)
        lhs = self.eval(expr.left)

        match expr.operator:
            case '+':
                return lhs + rhs
            case '-':
                return lhs - rhs
            case '*':
                return lhs * rhs
            case '/':
                return lhs / rhs
            
        raise error.RuntimeError(f"bad binary operator '{expr.operator}'")

    def eval_logical_expr(self, expr:ast.LogicalExpr):
        rhs = self.eval(expr.right)
        lhs = self.eval(expr.left)

        match expr.operator:
            case '||':
                return lhs or rhs
            case '&&':
                return lhs and rhs
            
        raise error.RuntimeError(f"bad binary operator '{expr.operator}'")


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
                raise error.RuntimeError(f"bad unary operator '{expr.operator}'")
        
        return arg
    
    def getvar(self, name:str):
        try:
            var = self.variables[name]
            return var
        except KeyError:
            raise error.VarLookupError(name)
        
    def setvar(self, name:str, value):
        self.variables[name] = value
