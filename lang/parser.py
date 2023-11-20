from .lexer import Token, Tokenizer
from .ast import *


def parse_int(string:str):
    "Helper to handle C style octals"
    if string[0] == '0' and len(string) > 1 and string[1] not in 'xX':
        # octal
        o = string[1:]
        return int(o, 8)
    else:
        return int(string, 0)


def check_assignmet_target(e:Expr):
    if isinstance(e, Identifier):
        return e
    raise SyntaxError('Invalid left-hand side in assignment expression')

def is_literal(tok:Token):
    return tok == Token.string_literal or tok == Token.floatingpoint or tok == Token.integer


def is_assignment_op(tok:Token):
    return tok == Token.assignment or tok == Token.assignment_complex

def is_print_sep(tok:Token):
    return tok == Token.comma or tok == Token.semicolon



class Parser:
    def __init__(self):
        self.string = ''
        self.tokenizer = Tokenizer()
    
    def parse(self, textcode):
        self.string = textcode
        self.tokenizer.reset(textcode)

        self.lookahead = self.tokenizer.next_token()

        return self.program()


    def program(self):
        return Program(self.line_list())
    
    def line_list(self):
        lines = []

        self.skip('eol')
        while self.lookahead:
            if self.lookahead.token == Token.named_label:
                lines.append(self.label())
            else:
                linenum = self.line_number()
                s = self.statement()
                lines.append(Line(s, linenum))
            self.skip('eol')

        return lines
    
    def line_number(self):
        try:
            return self.integer().value
        except SyntaxError:
            return 0
        
    # STATEMENTS

    def statement(self):
        match self.lookahead.token:
            case 'eol':
                self.skip('eol')
                return self.statement()
            case 'print':
                return self.print_stmt()
            case 'input':
                return self.input_stmt()
            case 'goto':
                return self.goto_stmt()
            case 'gosub':
                return self.gosub_stmt()
            case 'let':
                return self.let_stmt()
            case 'if':
                return self.if_stmt()
            case 'clear':
                return self.clear_stmt()
            case 'run':
                return self.run_stmt()
            case 'list':
                return self.list_stmt()
            case _:
                return self.expression_stmt()
            
    
    def expression_stmt(self):
        e = self.expression()
        self.skip('eol')
        return ExpressionStmt(e)

    def print_stmt(self):
        self.eat(Token.kw_print)

        # print list
        plist = []
        while self.lookahead.token != 'eol':
            expr = self.expression()
            sep = None
            if self.lookahead.token in (',', ';', ':'):
                sep = self.eat().value
            
            plist.append(PrintItem(expr, sep))

        self.eat('eol')
        return PrintStmt(plist)

    def input_stmt(self):
        self.eat('input')
        varlist = self.var_list()
        return InputStmt(varlist)

    def var_list(self):
        variables = [ self.identifier() ]
        while self.lookahead.token == ',':
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
        self.eat('if')
        test = self.expression()
        
        if self.lookahead.token == 'then':
            self.eat()

        consequent = self.statement()

        if self.lookahead.token == 'else':
            self.eat()
            alt = self.statement()
        else:
            alt = None

        return IfStmt(test, consequent, alt)

    def clear_stmt(self):
        self.eat('clear')
        return ClearStmt()
    
    def run_stmt(self):
        self.eat('run')
        args = self.expression()
        return RunStmt(args)

    def list_stmt(self):
        self.eat('list')

        args = self.expression()
        mode = 'code'

        if self.lookahead.token == Token.identifier:
            mode = self.identifier().name

        return ListStmt(args, mode)
    
    def label(self):
        _, name = self.eat(Token.named_label)
        return Label(name[:-1])

    # EXPRESSIONS

    def expression(self) -> Expr | list[Expr]:
        seq = self.sequence_expr()
        if len(seq) > 1:
            return seq
        else:
            return seq[0]
    
    def sequence_expr(self):
        exprs = [ self.assignment_expr() ]
        while self.lookahead.token == ',':
            self.eat()
            exprs.append(self.assignment_expr())
        
        return exprs
    
    def assignment_expr(self):
        left = self.logical_or_expr()
        if not is_assignment_op(self.lookahead.token):
            return left
        
        # assignment_op
        op = self.eat_first_of(Token.assignment, Token.assignment_complex).value
        return AssignmentExpr(operator=op, left=check_assignmet_target(left), right=self.assignment_expr())

    def logical_or_expr(self) -> LogicalExpr:
        return self._mk_expr(self.logical_and_expr, Token.logical_or, LogicalExpr)
    
    def logical_and_expr(self) -> LogicalExpr:
        return self._mk_expr(self.equality_expr, Token.logical_and, LogicalExpr)
    
    def equality_expr(self) -> BinaryExpr:
        return self._mk_expr(self.relational_expr, Token.equality_op, BinaryExpr)
    
    def relational_expr(self) -> BinaryExpr:
        return self._mk_expr(self.additive_expr, Token.relational_op, BinaryExpr)
    
    def additive_expr(self) -> BinaryExpr:
        return self._mk_expr(self.multiplicative_expr, Token.additive_op, BinaryExpr)
    
    def multiplicative_expr(self) -> BinaryExpr:
        return self._mk_expr(self.unary_expr, Token.multiplicative_op, BinaryExpr)
    
    def unary_expr(self):
        op = None

        if self.lookahead.token in (Token.additive_op, Token.logical_not):
            op = self.eat().value

        if op:
            # allow chaining
            return UnaryExpr(op, self.unary_expr())
        
        return self.primary_expr()

    def primary_expr(self):
        if is_literal(self.lookahead.token):
            return self.literal()
        
        match self.lookahead.token:
            case '(':
                return self.paren_expr()
            case Token.identifier:
                return self.identifier()
            case 'eof':
                return None
            case _:
                raise ValueError(f"unexpected primary_expr {self.lookahead}")


    def paren_expr(self):
        self.eat('(')
        expr = self.expression()
        self.eat(')')
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
        match self.lookahead.token:
            case 'integer':
                return self.integer()
            case 'floatingpoint':
                return  self.floatingpoint()
            case 'string_literal':
                return self.string_literal()

    # ---

    def _mk_expr(self, higher_expr, operator, Cls):
        left = higher_expr()

        while self.lookahead.token == operator:
            op = self.eat().value
            right = higher_expr()
            left = Cls(op, left, right)

        return left


    def eat(self, expected:Token = None):
        if not expected:
            expected = self.lookahead.token
        
        node = self.lookahead
        
        if not node and expected != Token.eof:
            raise SyntaxError(f"Unexpected end of input, {expected=}")
        
        if node.token != expected:
            raise SyntaxError(f"Unexpected token {node.token}, {expected=}")
        
        self.lookahead = self.tokenizer.next_token()
        return node

    def eat_first_of(self, *validTokens:Token):
        for t in validTokens:
            try:
                return self.eat(t)
            except SyntaxError:
                pass

        # no valid tokens found
        if not self.lookahead and Token.eof not in validTokens:
            errmsg = f"Unexpected end of input, expected one of {validTokens}"
        else:
            errmsg = f"Unexpected token {self.lookahead.token}, expected one of {validTokens}"

        raise SyntaxError(errmsg)
    
    def skip(self, tok:Token):
        while self.lookahead.token == tok:
            self.eat()

