from .lexer import Token, Tokenizer
from .ast import *


def parse_int(string:str):
    "Helper to handle C style octals"
    if len(string) > 1 and string[0] == '0' and string[1] not in 'xX':
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

def is_operator(tok:Token):
    other_ops = [Token.additive_op, Token.multiplicative_op, Token.relational_op, Token.equality_op, 
                 Token.logical_and, Token.logical_not, Token.logical_or]
    return is_assignment_op(tok) or tok in other_ops

def is_keyword(tok:Token):
    return tok in (kw for kw in Token if kw.name.startswith('kw_'))



class Parser:
    def __init__(self):
        self.tokenizer = Tokenizer()
    
    def set_source(self, code:str):
        self.tokenizer.reset(code)
        self.lookahead = self.tokenizer.next_token()
 
    def parse(self, textcode:str=None):
        if textcode:
            self.set_source(textcode)
        return self.program()
    
    def parse_line(self, code:str):
        self.set_source(code)
        return self.line()

    # -----

    def program(self):
        return Program(self.line_list())
    
    def line(self):
        self.skip('eol')
        if self.lookahead.token == Token.named_label:
            return self.label()
        
        linenum = self.line_number()
        stmt = self.statement()
        self.skip('eol')
        return Line(stmt, linenum)

    
    def line_list(self):
        lines = []
        while self.lookahead:
            lines.append(self.line())

        return lines
    
    def line_number(self):
        try:
            #return self.integer().value

            # the first number found in a line may or may not be a linenum
            # if it's part of an expression, it's not
            # TODO: add proper undo/redo
            prevcursor = self.tokenizer.cursor
            prevnode = self.lookahead

            num = self.integer().value
            if not is_operator(self.lookahead.token):
                return num
            
            self.tokenizer.cursor = prevcursor
            self.lookahead = prevnode
            return 0
        except SyntaxError:
            return 0
        
    # STATEMENTS

    def statement(self):
        match self.lookahead.token:
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
                return self.expression_stmt()
            
    
    def expression_stmt(self):
        e = self.expression()
        return ExpressionStmt(e)

    def print_stmt(self):
        self.eat(Token.kw_print)

        # print list
        plist = []
        while self.lookahead and self.lookahead.token != 'eol':
            # expr = self.expression()
            expr = self.single_expression()
            sep = None
            if self.lookahead.token in ',;:':
                sep = self.eat().value
            
            plist.append(PrintItem(expr, sep))

        #self.eat('eol')
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
        self.eat(Token.kw_if)
        test = self.expression()
        
        if self.lookahead.token == Token.kw_then:
            self.eat()

        consequent = self.statement()

        if self.lookahead.token == Token.kw_else:
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
            self.eat(',')
            args = self.expression()
        except Exception:
            pass
        return RunStmt(args)

    def list_stmt(self):
        self.eat(Token.kw_list)

        args = self.expression()
        mode = 'code'

        if self.lookahead.token == Token.identifier:
            mode = self.identifier().name

        return ListStmt(args, mode)
    
    def label(self):
        _, name = self.eat(Token.named_label)
        return Label(name[:-1])
    
    def builtin_func(self, func):
        name = self.eat(func).value
        self.eat('(')
        args = self.sequence_expr()
        self.eat(')')

        return Func(name.casefold(), args)
    
    def end_stmt(self):
        self.eat('end')
        return EndStmt()
    
    def return_stmt(self):
        self.eat('return')
        return ReturnStmt()

    # EXPRESSIONS

    def expression(self) -> Expr | list[Expr]:
        seq = self.sequence_expr()
        if len(seq) > 1:
            return seq
        
        return seq[0]
            
    
    # TODO: return ast.SequenceExpr
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
    
    # consume only one expression, w/o consuming ','
    single_expression = assignment_expr

    def logical_or_expr(self) -> LogicalExpr:
        left = self.logical_and_expr()

        while self.lookahead.token == Token.logical_or:
            op = self.eat().value
            right = self.logical_and_expr()
            left = LogicalExpr(op, left, right)

        return left
    
    def logical_and_expr(self) -> LogicalExpr:
        left = self.equality_expr()

        while self.lookahead.token == Token.logical_and:
            op = self.eat().value
            right = self.equality_expr()
            left = LogicalExpr(op, left, right)

        return left
    
    def equality_expr(self) -> BinaryExpr:
        left = self.relational_expr()

        while self.lookahead.token == Token.equality_op:
            op = self.eat().value
            right = self.relational_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def relational_expr(self) -> BinaryExpr:
        left = self.additive_expr()

        while self.lookahead.token == Token.relational_op:
            op = self.eat().value
            right = self.additive_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def additive_expr(self) -> BinaryExpr:
        left = self.multiplicative_expr()

        while self.lookahead.token == Token.additive_op:
            op = self.eat().value
            right = self.multiplicative_expr()
            left = BinaryExpr(op, left, right)

        return left
    
    def multiplicative_expr(self) -> BinaryExpr:
        left = self.unary_expr()

        while self.lookahead.token == Token.multiplicative_op:
            op = self.eat().value
            right = self.unary_expr()
            left = BinaryExpr(op, left, right)

        return left
    
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
            case 'rnd' | 'usr':
                return self.builtin_func(self.lookahead.token)
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
            case Token.integer:
                return self.integer()
            case Token.floatingpoint:
                return  self.floatingpoint()
            case Token.string_literal:
                return self.string_literal()


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

    def getloc(self):
        line = column = 0
        cur = self.tokenizer.cursor

        for i in range(cur):
            c = self.string[i]
            if c == '\n':
                line += 1
                column = 0
            else:
                column += 1
            
        return Location(line, column)

