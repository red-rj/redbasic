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
    return tok == Token.string_lit or tok == Token.floatingpoint or tok == Token.integer

def is_keyword(tok:Token):
    return tok.value >= Token.kw_print.value and tok.value <= Token.kw_rem.value

def is_assignment_op(tok:Token):
    return tok == Token.eq or tok == Token.eq_complex

def is_print_sep(tok:Token):
    return tok == Token.comma or tok == Token.semicolon

# helper for iterating through all keywords
def iter_keywords():
    begin = Token.kw_print.value
    end = Token.kw_rem.value + 1
    for i in range(begin, end):
        yield Token(i)



class Parser:
    def __init__(self):
        self.string = ''
        self.tokenizer = Tokenizer()
    
    def parse(self, textcode):
        self.string = textcode
        self.tokenizer.reset(textcode)

        self.lookahead = self.tokenizer.next_token()

        return self.program()

    
    # cada entrada na definição BNF deve ser uma função
    
    def integer(self):
        _, i = self.eat(Token.integer)
        return IntLiteral(parse_int(i))
    
    def floatingpoint(self):
        _, value = self.eat(Token.floatingpoint)
        return FloatLiteral(float(value))
    
    def string_lit(self):
        _, string = self.eat(Token.string_lit)
        return StringLiteral(string[1:-1])
    
    
    # main entry point
    """
    program
        : line+ EOF
        ;
    """
    def program(self):
        # lines = []
        # while self.tokenizer:
        #     #lines.append(self.line())
        #     lines.append(self.statement())
        return Program(self.statement_list())
    
    def literal(self):
        match self.lookahead.token:
            case Token.integer:
                return self.integer()
            case Token.floatingpoint:
                return self.floatingpoint()
            case Token.string_lit:
                return self.string_lit()

        raise SyntaxError(f"literal: unexpected literal '{self.lookahead.value}'")

    """
    line
        : integer statement eol
        | statement eol
        ;
    """
    def line(self):
        linenum = 0
        try:
            linenum = self.integer().value
        except SyntaxError:
            pass

        return Line(self.statement(), linenum)


    """
    statement
        : expression_stmt
        | block_stmt
        | empty_stmt
        | variable_stmt
        | if_stmt
        ;
    """
    def statement(self):
        # ignore empty lines
        if self.lookahead.token == Token.eol:
            self.eat()
            return self.statement()

        match self.lookahead.token:
            case Token.kw_let:
                return self.variable_stmt()
            case Token.kw_if:
                return self.if_stmt()
            case Token.block_begin:
                return self.block_stmt()
            case Token.semicolon:
                return self.empty_stmt()
            case _:
                return self.expression_stmt()
    
    def statement_list(self, stop:Token = None):
        stmts = [self.statement()]

        while self.lookahead:
            # ignore empty lines
            if self.lookahead.token == Token.eol:
                self.eat()
                continue

            if self.lookahead.token == stop:
                break

            stmts.append(self.statement())

        return stmts
    
    def expression_stmt(self):
        s = self.expression()
        self.eat_first_of(Token.eol, Token.eof, Token.semicolon)
        return s
    
    """
    block_stmt
        : '{' opt_stmt_list '}'
        ;
    """
    def block_stmt(self):
        self.eat(Token.block_begin)
        # opt_stmt_list
        body = []
        if self.lookahead.token != Token.block_end:
            body = self.statement_list(Token.block_end)
        
        self.eat(Token.block_end)
        return BlockStmt(body)

    def empty_stmt(self):
        self.eat(Token.semicolon)
        return EmptyStmt()

    """
    variable_stmt
        : 'let' identifier '=' expression
        | identifier '=' expression
        ;
    """
    def variable_stmt_simple(self):
        "simple ver. only one assignment per line"
        try:
            self.eat(Token.kw_let)
        except SyntaxError:
            pass
        iden = self.identifier()
        self.eat(Token.eq)
        val = self.expression()
        return VariableStmt(iden, val)

    """
    variable_stmt
        : 'let' variable_decl_list (';' | EOL)
        ;
    """
    def variable_stmt(self):
        "complex ver. (from course) allows multiple var declarations per line, separated by commas"
        self.eat(Token.kw_let)
        decls = self.variable_decl_list()
        self.eat_first_of(Token.semicolon, Token.eol)
        return VariableStmt(decls)

    """
    variable_decl_list
        : variable_decl
        | variable_decl_list ',' variable_decl
        ;
    """
    def variable_decl_list(self):
        decls = [self.variable_decl()]
        while self.lookahead.token == Token.comma:
            self.eat(Token.comma)
            decls.append(self.variable_decl())

        return decls
    
    """
    variable_decl
        : identifier optional_variable_init
        ;
    """
    def variable_decl(self):
        iden = self.identifier()
        lookahead = self.lookahead.token
        # optional_variable_init
        if lookahead != Token.comma and lookahead != Token.semicolon:
            init = self.variable_init()
        else:
            init = None

        return VariableDecl(iden, init)

    def variable_init(self):
        self.eat(Token.eq)
        return self.assignment_expr()

    """
    if_stmt
        : 'if' expression statement
        | 'if' expression statement 'else' statement
        ;
    """
    def if_stmt(self):
        self.eat(Token.kw_if)
        test = self.expression()
        consequent = self.statement()

        if self.lookahead and self.lookahead.token == Token.kw_else:
            alternate = self.statement()
        else:
            alternate = None
        
        return IfStmt(test, consequent, alternate)

    """
    precedence:
    - assignment
    - relational
    - additive
    - multiplicitave
    - primary

    expression
        : assignment_expr
        ;
    """
    def expression(self):
        return self.assignment_expr()
    
    """
    assignment_expr
        : relational_expr
        | lhs_expr ASSIGNMENT_OP assignment_expr
        ;
    """
    def assignment_expr(self):
        left = self.relational_expr()
        if not is_assignment_op(self.lookahead.token):
            return left

        # assignment_op() must run b4 assignment_expr()
        return AssignmentExpr(operator=self.assignment_op().value, left=check_assignmet_target(left), right=self.assignment_expr())

    def assignment_op(self):
        if self.lookahead.token == Token.eq:
            return self.eat(Token.eq)
        
        return self.eat(Token.eq_complex)

    
    """
    lhs_expr
        : identifier
        ;
    """
    def lhs_expr(self):
        return self.identifier()
    
    """
    identifier
        : VARNAME
        ;
    """
    def identifier(self):
        name = self.eat(Token.identifier).value
        return Identifier(name)

    
    # generic binary expression factory
    def _binary_expr(this, builder, operator) -> BinaryExpr:
        left = builder()

        while this.lookahead.token == operator:
            op = this.eat(operator).value
            right = builder()
            left = BinaryExpr(op, left, right)

        return left


    """
    RELOP: >, >=, <, <=

    relational_expr
        ; additive_expr 
        | additive_expr RELOP relational_expr
        ;
    """
    def relational_expr(self):
        return self._binary_expr(self.additive_expr, Token.relational_op)    
    

    """
    EQUALITY_OP: =, <>, ><
        x = y
        x <> y; x >< y

    equality_expr
        : relational_expr
        | equality_expr EQUALITY_OP relational_expr
        ;
    """
    def equality_expr(self):
        return self._binary_expr(self.relational_expr, Token.equality_op)
    

    """
    ADDITIVE_OP: +, -
    
    additive_expr
        : multiplicative_expr
        | additive_expr ADDITIVE_OP multiplicative_expr
        ;
    """
    def additive_expr(self):
        return self._binary_expr(self.multiplicative_expr, Token.additive_op)        
        # left = self.multiplicative_expr()
        # while self.lookahead.token == Token.additive_op:
        #     op = self.eat(Token.additive_op).value
        #     right = self.multiplicative_expr()
        #     left = BinaryExpr(left, right, op)
        # return left
    
    """
    MULTIPLICATIVE_OP: *, /

    multiplicative_expr
        : primary_expr
        | multiplicative_expr MULTIPLICATIVE_OP primary_expr
        ;
    """
    def multiplicative_expr(self):
        return self._binary_expr(self.primary_expr, Token.multiplicative_op)
    
    """
    primary_expr
        : literal
        | paren_expr
        | lhs_expr
        ;
    """
    def primary_expr(self):
        if is_literal(self.lookahead.token):
            return self.literal()
        
        match self.lookahead.token:
            case Token.l_paren:
                return self.paren_expr()
            case _:
                return self.lhs_expr()

    """
    paren_expr:
        : '(' expression ')'
        ;
    """
    def paren_expr(self):
        self.eat(Token.l_paren)
        expr = self.expression()
        self.eat(Token.r_paren)
        return expr

    # ---

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
