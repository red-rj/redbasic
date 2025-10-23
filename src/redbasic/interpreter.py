import sys, os, pprint
import math
from typing import TextIO as Stream
from . import ast, error
from .parser import Parser, parse_int

type Error = error.Err

def builtin_rnd(min:int, max:int=None):
    import random
    if max is None:
        min, max = 0, min

    return random.randint(min, max)

def builtin_usr(*args):
    raise NotImplementedError("USR func")

def find_index_of(item, sequence, attr=None):
    if attr:
        item = getattr(item, attr, item)
        sequence = ( getattr(o, attr) for o in sequence )

    for i,v in enumerate(sequence):
        if v == item:
            return i
    return -1

VAR_NOT_FOUND = object()

class Interpreter:
    "Redbasic interpreter"

    TEMP_VAR = '_'

    def __init__(self, textout:Stream=sys.stdout, textin:Stream=sys.stdin):
        assert textout.writable()
        assert textin.readable()

        self.parser = Parser()
        self.output = textout
        self.input = textin
        self.variables = {}
        self.substack = []
        self.ast:ast.Program = None


    def set_source(self, code:str):
        self.ast = self.parser.parse(code)

    def exec(self):
        maxcursor = len(self.ast.body)
        self.cursor = 0

        while self.cursor < maxcursor:
            item = self.ast.body[self.cursor]
            self.exec_statement(item.statement)
            if isinstance(item.statement, (ast.GotoStmt, ast.ReturnStmt, ast.EndStmt)):
                continue
            self.cursor += 1

    def exec_script(self, path):
        with open(path) as s:
            code = s.read()
        self.set_source(code)
        self.exec()

    def exec_src(self, code):
        self.set_source(code)
        self.exec()

    def exec_line(self, line:ast.Line|str):
        if isinstance(line, str):
            line = self.parser.parse_line(line)
        self.exec_statement(line.statement)

    # ---

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

    # ---

    def _list(self, stmt:ast.ListStmt):
        args = self.eval(stmt.arguments) if stmt.arguments else None
        if isinstance(args, list):
            sl = slice(*args)
        elif args:
            sl = slice(args, args+1)
        else:
            sl = slice(0, None)
        
        body = self.ast.body[sl]
        tmp = ast.Program(body)
        
        if stmt.mode == 'code':
            src = ast.reconstruct(tmp)
            print(src, file=self.output)
        elif stmt.mode == 'ast':
            pprint.pp(tmp, stream=self.output)
        else:
            raise RuntimeError(f"invalid list mode '{stmt.mode}'")

    def _clear(self):
        if self.output.isatty():
            os.system('cls' if os.name=='nt' else 'clear')

    def _new(self):
        self.output.write("New program\n\n")
        self.ast.body.clear()

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


    def _eval_dest(self, destination):
        if isinstance(destination, ast.Identifier):
            return self.variables.get(destination.name, VAR_NOT_FOUND)
        else:
            return self.eval(destination)

    def _calc_go(self, dest):
        "returns next cursor"
        if isinstance(dest, str):
            dest = hash(dest)

        if dest == 0:
            raise Error("0 is not a valid linenum")

        idx = find_index_of(dest, (x.linenum for x in self.ast.body))
        if idx > -1:
            return idx
        else:
            raise RuntimeError(f"Unexpected destination {dest}")

    def _goto(self, goto:ast.GotoStmt):
        if isinstance(goto, ast.GosubStmt):
            if len(self.substack) > 255:
                raise RecursionError()
            self.substack.append(self.cursor+1)
        
        dest = self._eval_dest(goto.destination)
        if dest is VAR_NOT_FOUND:
            # try to find label
            dest = goto.destination.name

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
    
    # ---

    def getvar(self, name:str):
        try:
            return self.variables[name]
        except KeyError:
            raise error.UndefinedVar(name)
        
    def setvar(self, name:str, value):
        self.variables[name] = value


    def repl(self, welcome, prompt="> "):
        from functools import partial
        
        if not self.input.isatty():
            raise RuntimeError("input stream is not interactive")
        
        myprint = partial(print, file=self.output)

        self.isrepl = 1
        myprint(welcome)
        
        try:
            body = self.ast.body
            while 1:
                myprint(prompt, end='', flush=True)

                code = self.input.readline()
                if not code.strip():
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
                    if line.linenum:
                        idx = find_index_of(line, body, "linenum")
                        if idx != -1:
                            body[idx] = line
                        else:
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
    basic = Interpreter()
    if prog:
        basic.ast = prog
    
    basic.repl("redbasic REPL v0.2", "> ")
