from .lexer import Token, Tokenizer
from .ast import *
from types import SimpleNamespace as AstNode


def parse_int(string:str):
    "Helper to handle C style octals"
    if string[0] == '0' and len(string) > 1 and 'x' not in string and 'X' not in string:
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
    return tok == Token.eq or tok == Token.eq_complex

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
            case 'print':
                return self.print_stmt()
            case 'input':
                return self.input_stmt()
            case 'goto':
                return self.goto_stmt()
            case 'let':
                return self.let_stmt()
            case 'eol':
                self.skip('eol')
                return self.statement()
            case 'identifier':
                return self.variable_declaration()
            case _:
                #return self.expression_stmt()
                raise SyntaxError("unexpected statement")
            
    
    def expression_stmt(self):
        e = self.expression()
        self.eat('eol')
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
        
    def let_stmt(self):
        self.eat('let')
        return self.variable_declaration()

    def variable_declaration(self):
        iden = self.identifier()
        # variable_init
        self.eat('=')
        init = self.assignment_expr()
        return VariableDecl(iden, init)


    # EXPRESSIONS

    def expression(self):
        return self.sequence_expr()
    
    def sequence_expr(self):
        exprs = [ self.assignment_expr() ]
        while self.lookahead.token == ',':
            self.eat()
            exprs.append(self.assignment_expr())
        
        if len(exprs) > 1:
            return exprs
        
        return exprs[0]
    
    def assignment_expr(self):
        left = self.logical_or_expr()
        if not is_assignment_op(self.lookahead.token):
            return left
        
        # assignment_op
        op = self.eat_first_of('=', 'eq_complex').value
        return AssignmentExpr(operator=op, left=check_assignmet_target(left), right=self.assignment_expr())

    def logical_or_expr(self) -> LogicalExpr:
        return self._mk_expr(self.logical_and_expr, 'logical_or', LogicalExpr)
    
    def logical_and_expr(self) -> LogicalExpr:
        return self._mk_expr(self.equality_expr, 'logical_and', LogicalExpr)
    
    def equality_expr(self) -> BinaryExpr:
        left = self.relational_expr()

        while self.lookahead.token in ('=', 'neq'):
            op = self.eat().value
            right = self.relational_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def relational_expr(self) -> BinaryExpr:
        return self._mk_expr(self.additive_expr, 'relational_op', BinaryExpr)
    
    def additive_expr(self) -> BinaryExpr:
        return self._mk_expr(self.multiplicative_expr, Token.additive_op, BinaryExpr)
    
    def multiplicative_expr(self) -> BinaryExpr:
        return self._mk_expr(self.unary_expr, Token.multiplicative_op, BinaryExpr)
    
    def unary_expr(self):
        op = None

        match self.lookahead.token:
            case Token.additive_op | Token.logical_not:
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
