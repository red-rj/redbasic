import re
from .spec import Token, basic_spec
from .ast import *
from . import error

def parse_int(string:str):
    "Helper to handle C style octals"
    if len(string) > 1 and string[0] == '0' and string[1] not in 'xX':
        # octal
        o = string[1:]
        return int(o, 8)
    else:
        return int(string, 0)


def is_literal(tok:Token):
    return tok == Token.string_literal or tok == Token.floatingpoint or tok == Token.integer


def is_assignment_op(tok:Token):
    return tok == Token.assignment or tok == Token.assignment_complex

def is_operator(tok:Token):
    other_ops = [Token.additive_op, Token.multiplicative_op, Token.relational_op, Token.equality_op, 
                 Token.logical_and, Token.logical_not, Token.logical_or]
    return is_assignment_op(tok) or tok in other_ops

def is_keyword(tok:Token):
    return tok in (kw for kw in Token if kw.name.startswith('kw_'))


# TODO: find a way to do better tokenization
# maybe with a mode variable?
# Spec = { MODE_ROOT: basic_spec, MODE_LIST: { mode: r"code|ast" }, ... }

class Parser:
    def __init__(self):
        self.stack = []
        self.lookahead:tuple[Token,str] = Token.eof, None

    def set_source(self, code:str):
        self.cursor = 0
        self.linenum = 1
        self.code = code
        self.stack.clear()
        self.lookahead = self.next_token()
 
    def parse(self, textcode:str=None):
        self.set_source(textcode)
        return self.program()
    
    def parse_line(self, code:str):
        self.set_source(code)
        return self.line_stmt()
    
    # --Tokenize--

    def next_token(self) -> tuple[Token, str]:
        if self.cursor >= len(self.code):
            return Token.eof, None
        
        for tok, pattern in basic_spec.items():
            m = pattern.match(self.code, self.cursor)
            if not m:
                continue
            
            tvalue = m.group(0)
            self.cursor += len(tvalue)

            if tok == Token.eol:
                self.linenum += 1

            if tok in (None, Token.comment, Token.eol):
                return self.next_token()
            
            return tok, tvalue
        
        raise error.BadSyntax(f"Unexpected '{self.code[self.cursor]}'", self.linenum)
    

    def eat(self, expected:Token = None) -> tuple[Token, str]:
        if not expected:
            expected = self.lookahead[0]
        
        node = self.lookahead
        errmsg = None
        
        if node[0] == Token.eof and expected != Token.eof:
            errmsg = "Unexpected end of input"
        
        if node[0] != expected:
            errmsg = "Unexpected token"

        if errmsg:
            err = self._bad_syntax(errmsg)
            err.add_note(f'expected {expected}')
            err.add_note(f'got {node[0]}')
            raise err
        
        self.push_undo()
        self.lookahead = self.next_token()
        return node
    
    # ----

    def program(self):
        return Program(self.line_list())
    
    def line_stmt(self):
        token, _ = self.lookahead
        if token == Token.named_label:
            _, name = self.eat()
            # statements are optional in labels
            stmt = None
            try:
                stmt = self.statement()
            except Exception:
                pass

            return Label(stmt, name[:-1])
        
        # get line number
        # line numbers are optional, don't confuse a line number for an expression
        linenum = 0
        try:
            n = self.integer().value
            if not is_operator(self.lookahead[0]):
                linenum = n
            else:
                self.undo()
        except Exception:
            pass

        stmt = self.statement()
        return Line(stmt, linenum)

    def line_list(self):
        lines = []
        while self.lookahead[0] != Token.eof:
            lines.append(self.line_stmt())

        return lines
            
    # STATEMENTS

    def statement(self):
        match self.lookahead[0]:
            case Token.kw_print:
                return self.print_stmt()
            case Token.kw_input:
                return self.input_stmt()
            case Token.kw_goto:
                return self.goto_stmt()
            case Token.kw_gosub:
                return self.gosub_stmt()
            case Token.kw_let:
                return self.let_stmt()
            case Token.kw_if:
                return self.if_stmt()
            case Token.kw_clear:
                return self.clear_stmt()
            case Token.kw_run:
                return self.run_stmt()
            case Token.kw_list:
                return self.list_stmt()
            case Token.kw_end:
                return self.end_stmt()
            case Token.kw_return:
                return self.return_stmt()
            case _:
                e = self.expression_stmt()
                if e.expression is None:
                    return None
                else:
                    return e

    
    def expression_stmt(self):
        e = self.expression()
        return ExpressionStmt(e)

    def print_stmt(self):
        self.eat(Token.kw_print)

        # print list
        # TODO: Tokenize separetor as print_sep: r"[,;]"
        plist = []
        while self.lookahead[0] not in (Token.eol, Token.eof):
            expr = self.single_expression()
            if self.lookahead[0] in (Token.comma, Token.semicolon):
                _, sep = self.eat()
            else:
                sep = None
            plist.append(PrintItem(expr, sep))

        return PrintStmt(plist)

    def input_stmt(self):
        self.eat('input')
        varlist = self.var_list()
        return InputStmt(varlist)

    def var_list(self):
        variables = [ self.identifier() ]
        while self.lookahead[0] == Token.comma:
            self.eat()
            variables.append(self.identifier())
        
        return variables
    
    def goto_stmt(self):
        self.eat('goto')
        dest = self.expression()
        return GotoStmt(dest)
    
    def gosub_stmt(self):
        self.eat('gosub')
        dest = self.expression()
        return GosubStmt(dest)
        
    def let_stmt(self):
        self.eat('let')
        return self.variable_decl()
    
    def variable_decl(self):
        iden = self.identifier()
        # variable_init
        self.eat(Token.assignment)
        init = self.assignment_expr()
        return VariableDecl(iden, init)

    def if_stmt(self):
        self.eat(Token.kw_if)
        test = self.expression()
        
        if self.lookahead[0] == Token.kw_then:
            self.eat()

        consequent = self.statement()

        if self.lookahead[0] == Token.kw_else:
            self.eat()
            alt = self.statement()
        else:
            alt = None

        return IfStmt(test, consequent, alt)

    def clear_stmt(self):
        self.eat(Token.kw_clear)
        return ClearStmt()
    
    def run_stmt(self):
        self.eat(Token.kw_run)
        args = None
        try:
            self.eat(Token.comma)
            args = self.expression()
        except Exception:
            pass
        return RunStmt(args)

    def list_stmt(self):
        # list MODE or list EXPRLIST MODE
        self.eat(Token.kw_list)
        mode = 'code'
        args = None

        # list MODE or list NUM,NUM MODE
        # TODO: Tokenize as list_mode: r"code|ast"
        if self.lookahead[0] == Token.identifier:
            mode = self.identifier().name
        else:
            args = self.expression()
            if self.lookahead[0] == Token.identifier:
                mode = self.identifier().name

        return ListStmt(args, mode)
    
    def builtin_func(self, func):
        _, name = self.eat(func)
        self.eat(Token.l_paren)
        args = self.sequence_expr()
        self.eat(Token.r_paren)

        return Func(name.casefold(), args)
    
    def end_stmt(self):
        self.eat(Token.kw_end)
        return EndStmt()
    
    def return_stmt(self):
        self.eat(Token.kw_return)
        return ReturnStmt()

    # EXPRESSIONS

    def expression(self) -> Expr | list[Expr]:
        seq = self.sequence_expr()
        if len(seq) > 1:
            return seq
        
        return seq[0]
            
    
    # TODO: return ast.SequenceExpr
    def sequence_expr(self) -> list[AssignmentExpr|LogicalExpr]:
        exprs = [ self.assignment_expr() ]
        while self.lookahead[0] == Token.comma:
            self.eat()
            exprs.append(self.assignment_expr())
        
        return exprs
    
    def assignment_expr(self) -> AssignmentExpr|LogicalExpr:
        left = self.logical_or_expr()
        if not is_assignment_op(self.lookahead[0]):
            return left
        
        # assignment_op
        refrigirator = (Token.assignment, Token.assignment_complex)
        for food in refrigirator:
            try:
                node = self.eat(food)
                if not isinstance(left, Identifier):
                    raise self._bad_syntax('Invalid left-hand side in assignment expression')
                return AssignmentExpr(operator=node[1], left=left, right=self.assignment_expr())
            except error.BadSyntax:
                pass
        
        raise self._bad_syntax(f"expected one of {refrigirator}, got {self.lookahead}")

    # consume only one expression, w/o consuming ','
    single_expression = assignment_expr

    def logical_or_expr(self) -> LogicalExpr:
        left = self.logical_and_expr()

        while self.lookahead[0] == Token.logical_or:
            _, op = self.eat()
            right = self.logical_and_expr()
            left = LogicalExpr(op, left, right)

        return left
    
    def logical_and_expr(self) -> LogicalExpr:
        left = self.equality_expr()

        while self.lookahead[0] == Token.logical_and:
            _, op = self.eat()
            right = self.equality_expr()
            left = LogicalExpr(op, left, right)

        return left
    
    def equality_expr(self) -> BinaryExpr:
        left = self.relational_expr()

        while self.lookahead[0] == Token.equality_op:
            _, op = self.eat()
            right = self.relational_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def relational_expr(self) -> BinaryExpr:
        left = self.additive_expr()

        while self.lookahead[0] == Token.relational_op:
            _, op = self.eat()
            right = self.additive_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def additive_expr(self) -> BinaryExpr:
        left = self.multiplicative_expr()

        while self.lookahead[0] == Token.additive_op:
            _, op = self.eat()
            right = self.multiplicative_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def multiplicative_expr(self) -> BinaryExpr:
        left = self.unary_expr()

        while self.lookahead[0] == Token.multiplicative_op:
            _, op = self.eat()
            right = self.unary_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def unary_expr(self):
        op = None

        if self.lookahead[0] in (Token.additive_op, Token.logical_not):
            _, op = self.eat()

        if op:
            # allow chaining
            return UnaryExpr(op, self.unary_expr())
        
        return self.primary_expr()

    def primary_expr(self):
        if is_literal(self.lookahead[0]):
            return self.literal()
        
        match self.lookahead[0]:
            case Token.l_paren:
                return self.paren_expr()
            case Token.identifier:
                return self.identifier()
            case Token.eof | Token.eol:
                return None
            case Token.f_builtin:
                return self.builtin_func(self.lookahead[0])
            case _:
                raise self._bad_syntax(f"unexpected primary_expr {self.lookahead}")


    def paren_expr(self):
        self.eat(Token.l_paren)
        expr = self.expression()
        self.eat(Token.r_paren)
        return expr
    
    def identifier(self):
        _, name = self.eat(Token.identifier)
        return Identifier(name)
    
    # LITERALS

    def integer(self):
        _, i = self.eat(Token.integer)
        return IntLiteral(parse_int(i))
    
    def floatingpoint(self):
        _, f = self.eat(Token.floatingpoint)
        return FloatLiteral(float(f))
    
    def string_literal(self):
        _, string = self.eat(Token.string_literal)
        return StringLiteral(string[1:-1])
    
    def literal(self):
        match self.lookahead[0]:
            case Token.integer:
                return self.integer()
            case Token.floatingpoint:
                return  self.floatingpoint()
            case Token.string_literal:
                return self.string_literal()
            case _:
                e = self._bad_syntax("Expected literal (int, float, str)")
                e.add_note(self.lookahead)
                raise e


    def push_undo(self):
        return self.stack.append((self.lookahead, self.cursor, self.linenum))

    def undo(self, n=1):
        assert len(self.stack) >= n
        while n:
            look,cursor,line = self.stack[-1]
            self.lookahead = look
            self.cursor = cursor
            self.linenum = line
            self.stack.pop()
            n -= 1

    def _bad_syntax(self, msg):
        return error.BadSyntax(msg, self.linenum)
