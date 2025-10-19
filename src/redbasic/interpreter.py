import sys, os, pprint
import math
from typing import TextIO as Stream
from . import ast, error
from .parser import Parser, parse_int

type Error = Exception

def builtin_rnd(min:int, max:int=None):
    import random
    if max is None:
        min, max = 0, min

    return random.randint(min, max)

def builtin_usr(*args):
    raise NotImplementedError("USR func")

def builtin_pow(base, exp):
    return base ** exp


class Interpreter:
    "Redbasic interpreter"

    TEMP_VAR = '_'

    def __init__(self, parser:Parser = None, textout:Stream=sys.stdout, textin:Stream=sys.stdin):
        self.parser = parser if parser is not None else Parser()
        self.output = textout
        self.input = textin
        self.variables = {}
        self.substack = []
        self.ast = ast.Program([])


    def set_source(self, code:str):
        self.ast = self.parser.parse(code)

    def exec_line(self, line:ast.Line|str):
        if isinstance(line, str):
            line = self.parser.parse_line(line)
        self.exec_statement(line.statement)

    def exec_program(self, prog:ast.Program):
        self.ast = prog
        maxcursor = len(self.ast.body)
        self.cursor = 0

        while self.cursor < maxcursor:
            item = self.ast.body[self.cursor]
            self.exec_statement(item.statement)
            self.cursor += 1

    def exec(self):
        self.exec_program(self.ast)

    def exec_statement(self, stmt:ast.Stmt):
        match stmt:
            case ast.VariableDecl():
                name = stmt.iden.name
                if name in self.variables:
                    raise RuntimeError(f"'{name}' already defined")
                value = self.eval(stmt.init)
                self.setvar(name, value)
            case ast.ExpressionStmt():
                val = self.eval(stmt.expression)
                # se for uma expressão solta, salvar em TEMP_VAR
                if not isinstance(stmt.expression, ast.AssignmentExpr):
                    self.setvar(self.TEMP_VAR, val)
            case ast.PrintStmt():
                self._print(stmt)
            case ast.GotoStmt():
                self._goto(stmt)
            case ast.GosubStmt():
                self._gosub(stmt)
            case ast.EndStmt():
                self.cursor = 2**31
            case ast.IfStmt():
                self._if(stmt)
            case ast.InputStmt():
                self._input(stmt)
            case ast.ReturnStmt():
                self._return()
            case ast.ListStmt():
                self._list(stmt)
            case ast.ClearStmt():
                self._clear()
            case ast.RunStmt():
                self.exec()
            case ast.NewStmt():
                self._new()
            case _:
                raise NotImplementedError(f"unsupported statement {stmt}")

    def _list(self, stmt:ast.ListStmt):
        args = self.eval(stmt.arguments) if stmt.arguments else None
        if isinstance(args, list):
            start, end = args
        elif args:
            start, end = args, len(self.ast.body)
        else:
            start = 0
            end = len(self.ast.body)
        
        body = self.ast.body[start:end]
        tmp = ast.Program(body)
        
        if stmt.mode == 'code':
            src = ast.reconstruct(tmp)
            print(src, file=self.output)
        elif stmt.mode == 'ast':
            pprint.pp(tmp, stream=self.output)
        else:
            raise RuntimeError(f"invalid list mode '{stmt.mode}'")

    def _clear(self):
        if self.input.isatty():
            os.system('cls' if os.name=='nt' else 'clear')

    def _new(self):
        self.output.write("New program\n\n")
        self.ast.body.clear()


    def eval(self, expr:ast.Expr) -> int|float|str|list:
        match expr:
            case ast.Literal():
                return expr.value
            case list():# SequenceExpr
                return [self.eval(e) for e in expr] 
            case ast.AssignmentExpr():
                return self._assignment(expr)
            case ast.BinaryExpr():
                return self._binary_expr(expr)
            case ast.UnaryExpr():
                return self._unary_expr(expr)
            case ast.Identifier():
                return self.getvar(expr.name)
            case ast.Func():
                return self._func(expr)
            case _:        
                raise NotImplementedError(f"unsupported expression {expr}")

    def _func(self, func:ast.Func):
        try:
            args = self.eval(func.arguments)

            if func.name == 'rnd':
                return builtin_rnd(*args)
            elif func.name == 'usr':
                return builtin_usr(*args)
            elif func.name == 'pow':
                return pow(*args)
            elif func.name == 'sqrt':
                return math.sqrt(*args)
        except AttributeError as e:
            raise RuntimeError(f"{func.name}: {e}")


    def _print(self, printstmt:ast.PrintStmt):
        for item in printstmt.printlist:
            val = self.eval(item.expression)
            if item.sep == ',':
                string = f"{val:<8}"
            elif item.sep == ';' or item.sep is None:
                string = str(val)
            else:
                raise error.BadSyntax(f"Bad print separator '{item.sep}'", self.cursor)
            
            self.output.write(string)
        self.output.write('\n')

    def _calc_go(self, dest):
        "returns next cursor"
        if isinstance(dest, str):
            dest = hash(dest)

        if dest == 0:
            raise Error("0 is not a valid linenum")

        linenums = (x.linenum for x in self.ast.body)
        i = 0
        for l in linenums:
            if dest == l:
                return i
            else:
                i += 1

        raise Error(f"Unexpected destination {dest!r}")


    def _goto(self, goto:ast.GotoStmt):
        dest = self.eval(goto.destination)
        self.cursor = self._calc_go(dest)

    def _gosub(self, gosub:ast.GosubStmt):
        if len(self.substack) > 255:
            raise RecursionError()

        dest = self.eval(gosub.destination)
        self.substack.append(self.cursor)
        self.cursor = self._calc_go(dest)

    def _return(self):
        self.cursor = self.substack.pop()


    def _if(self, stmt:ast.IfStmt):
        cond = self.eval(stmt.test)
        if cond:
            self.exec_statement(stmt.consequent)
        elif stmt.alternate:
            self.exec_statement(stmt.alternate)

    def _input(self, stmt:ast.InputStmt):
        for var in stmt.varlist:
            line = self.input.readline().strip()

            try:
                value = float(line)
                if value.is_integer():
                    value = int(value)
                self.setvar(var.name, value)
                continue
            except ValueError:
                pass

            try:
                value = parse_int(line)
                self.setvar(var.name, value)
                continue
            except ValueError:
                pass

            # str
            value = line
            self.setvar(var.name, value)


    def _assignment(self, expr:ast.AssignmentExpr):
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
                    
    def _binary_expr(self, expr:ast.BinaryExpr):
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
            case '>':
                return lhs > rhs
            case '>=':
                return lhs > rhs
            case '<':
                return lhs < rhs
            case '<=':
                return lhs <= rhs
            case '<>'|'><':
                return lhs != rhs
            case '==':
                return lhs == rhs
            case '||':
                return lhs or rhs
            case '&&':
                return lhs and rhs
            
        raise RuntimeError(f"bad binary operator '{expr.operator}'")


    def _unary_expr(self, expr:ast.UnaryExpr):
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
            raise error.UndefinedVar(name)
        
    def setvar(self, name:str, value):
        self.variables[name] = value


    def repl(self, welcome, prompt="> "):
        if not self.input.isatty():
            raise RuntimeError("input stream is not interactive")
        
        from functools import partial

        myprint = partial(print, file=self.output)
        
        self.isrepl = 1
        myprint(welcome, "Ctrl+C to exit", sep='\n')
        
        try:
            body = self.ast.body
            while 1:
                myprint(prompt, end='', flush=True)

                code = self.input.readline()
                if not code:
                    myprint()
                    continue
                
                line = self.parser.parse_line(code)

                if isinstance(line.statement, ast.InteractiveStmt):
                    # interactive statements
                    self.exec_line(line)
                else:
                    # code statements
                    # lines that don't start with a linenum are executed
                    # lines that start with a linenum are added to the program
                    ff = [ x for x in body if x.linenum == line.linenum ]
                    if ff:
                        i = body.index(ff[0])
                        # replace line
                        body[i] = line
                    
                    if line.linenum and not ff:
                        # new line
                        body.append(line)
                    else:
                        self.exec_line(line)
        except EOFError:
            pass
        except KeyboardInterrupt:
            pass

        del self.isrepl
        myprint()




def repl(prog:ast.Program = None):
    interp = Interpreter()
    if prog:
        interp.ast = prog
    
    interp.repl("redbasic REPL v0.2", "> ")

