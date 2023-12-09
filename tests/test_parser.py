import unittest
from lang.parser import Parser, parse_int, is_keyword
from lang.lexer import Token
from lang.ast import *

# --- PARSER TESTS ---
parser = Parser()

class parserTestCase(unittest.TestCase):
    def assertAst(tc, code:str, expected):
        ast = parser.parse(code)
        tc.assertEqual(ast, expected, f"""'{code.strip()}' didn't produce the expected ast:
     {ast=}
{expected=}""")
        
class parserHelpers(unittest.TestCase):
    def test_parse_int(tc):
        tc.assertEqual(0o77, parse_int('077'))
        tc.assertEqual(0xc00ffee, parse_int('0xC00FFEE'))
        tc.assertEqual(1, parse_int('1'))

    def test_is_keyword(tc):
        tc.assertTrue(is_keyword(Token.kw_print))
        tc.assertTrue(is_keyword(Token.kw_false))
        tc.assertFalse(is_keyword(Token.eol))
        tc.assertFalse(is_keyword(Token.semicolon))

class mathTests(parserTestCase):
    def test_addition(tc):
        tc.assertAst(
            "10  2 + 2",
            Program([Line(ExpressionStmt(BinaryExpr('+', IntLiteral(2), IntLiteral(2))), 10)])
        )
        
    def test_nested_add_subtract(tc):
        tc.assertAst(
            "  3 + 2 - 2",
            Program([Line(ExpressionStmt(
                    BinaryExpr('-', 
                               BinaryExpr('+', IntLiteral(3), IntLiteral(2)), 
                               IntLiteral(2)
                               )
                    )
                )])
        )
    
    def test_multiplication(tc):
        tc.assertAst(
            "  2 * 2",
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='*',
                                                                  left=IntLiteral(value=2),
                                                                  right=IntLiteral(value=2))),
                   linenum=0)])
        )

    def test_multiplication_nested(tc):
        tc.assertAst(
            '  2 * 2 * 2',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='*',
                                                                  left=BinaryExpr(operator='*',
                                                                                  left=IntLiteral(value=2),
                                                                                  right=IntLiteral(value=2)),
                                                                  right=IntLiteral(value=2))),
                   linenum=0)])
        )

        tc.assertAst(
            '0  29 * 3 / (1+9-9/3)',
            Program(body=[Line(statement=
                               ExpressionStmt(expression=
                                              BinaryExpr(operator='/',
                                                        left=BinaryExpr(operator='*',
                                                                        left=IntLiteral(value=29),
                                                                        right=IntLiteral(value=3)),
                                                        right=BinaryExpr(operator='-',
                                                                        left=BinaryExpr(operator='+',
                                                                                        left=IntLiteral(value=1),
                                                                                        right=IntLiteral(value=9)),
                                                                        right=BinaryExpr(operator='/',
                                                                                        left=IntLiteral(value=9),
                                                                                        right=IntLiteral(value=3))))),
                   linenum=0)])

        )
    
    def test_operator_precedence(tc):
        tc.assertAst(
            '  2 + 2 * 2',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='+',
                                                                  left=IntLiteral(value=2),
                                                                  right=BinaryExpr(operator='*',
                                                                                   left=IntLiteral(value=2),
                                                                                   right=IntLiteral(value=2)))),
                   linenum=0)])
        )

        tc.assertAst(
            '  (2 + 2) * 2',
            Program(body=[Line(statement=ExpressionStmt(expression=
                                            BinaryExpr(operator='*',
                                                        left=BinaryExpr(operator='+',
                                                                        left=IntLiteral(value=2),
                                                                        right=IntLiteral(value=2)),
                                                        right=IntLiteral(value=2))),
                   linenum=0)])
        )

    def test_variable(tc):
        tc.assertAst(
            "(A+B)/(C+D)",
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='/',
                                                                  left=BinaryExpr(operator='+',
                                                                                  left=Identifier(name='A'),
                                                                                  right=Identifier(name='B')),
                                                                  right=BinaryExpr(operator='+',
                                                                                   left=Identifier(name='C'),
                                                                                   right=Identifier(name='D')))),
                   linenum=0)])
        )

        tc.assertAst(
            "B-14*C",
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='-',
                                                                  left=Identifier(name='B'),
                                                                  right=BinaryExpr(operator='*',
                                                                                   left=IntLiteral(value=14),
                                                                                   right=Identifier(name='C')))),
                   linenum=0)])
        )

    def test_nested_params(tc):
        tc.assertAst("((((42))))", Program([ Line(ExpressionStmt(IntLiteral(42))) ]))
        tc.assertAst("(((((Q)))))", Program([ Line(ExpressionStmt(Identifier('Q'))) ]))

        
class assignmentTests(parserTestCase):
    def test_simple_assignment(tc):
        tc.assertAst(
            'var = 42',
            Program(body=[Line(statement=ExpressionStmt(expression=AssignmentExpr(operator='=', left=Identifier(name='var'), right=IntLiteral(value=42))), linenum=0)])
        )

        tc.assertAst(
            'var = x',
            Program(body=[Line(statement=ExpressionStmt(expression=AssignmentExpr(operator='=', left=Identifier(name='var'), right=Identifier('x'))), linenum=0)])
        )

    def test_chained_assignment(tc):
        tc.assertAst('y = x = 42',
            Program(body=[Line(statement=ExpressionStmt(expression=AssignmentExpr(operator='=', left=Identifier(name='y'), right=AssignmentExpr(operator='=', left=Identifier(name='x'), right=IntLiteral(value=42)))), linenum=0)])
        )
    
    def test_complex_assignment(tc):
        tc.assertAst('a += 1',
                     Program(body=[Line(statement=ExpressionStmt(expression=AssignmentExpr(operator='+=',
                                                                      left=Identifier(name='a'),
                                                                      right=IntLiteral(value=1))),
                   linenum=0)])
        )


class unaryTests(parserTestCase):
    def test_unary_minus(tc):
        tc.assertAst("-x",
            Program(body=[Line(statement=ExpressionStmt(expression=UnaryExpr(operator='-',
                                                                 argument=Identifier(name='x'))),
                   linenum=0)])
        )
    
    def test_unary_not(tc):
        tc.assertAst("!var",
            Program(body=[Line(statement=ExpressionStmt(expression=UnaryExpr(operator='!',
                                                                 argument=Identifier(name='var'))),
                   linenum=0)])
        )

    def test_unary_chaining(tc):
        tc.assertAst("--pedro",
            Program(body=[Line(statement=ExpressionStmt(expression=UnaryExpr(operator='-',
                                                                 argument=UnaryExpr(operator='-',
                                                                                    argument=Identifier(name='pedro')))),
                   linenum=0)])
        )
        tc.assertAst("-!pedro",
            Program(body=[Line(statement=ExpressionStmt(expression=UnaryExpr(operator='-',
                                                                 argument=UnaryExpr(operator='!',
                                                                                    argument=Identifier(name='pedro')))),
                   linenum=0)])
        )
        tc.assertAst("+-pedro",
            Program(body=[Line(statement=ExpressionStmt(expression=UnaryExpr(operator='+',
                                                                 argument=UnaryExpr(operator='-',
                                                                                    argument=Identifier(name='pedro')))),
                   linenum=0)])
        )
    
class comparisonTests(parserTestCase):
    def test_greater_then(tc):
        tc.assertAst(
            'x > 0',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='>',
                                                                  left=Identifier(name='x'),
                                                                  right=IntLiteral(value=0))),
                   linenum=0)])
        )

    def test_equality(tc):
        tc.assertAst(
            'x == 0',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='==',
                                                                  left=Identifier(name='x'),
                                                                  right=IntLiteral(value=0))),
                   linenum=0)])
        )
        tc.assertAst(
            'x <> 0',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='<>',
                                                                  left=Identifier(name='x'),
                                                                  right=IntLiteral(value=0))),
                   linenum=0)])
        )

class logicalTests(parserTestCase):
    def test_and(tc):
        tc.assertAst(
            'x > 0 && y < 1',
            Program(body=[Line(statement=ExpressionStmt(expression=LogicalExpr(operator='&&',
                                                                   left=BinaryExpr(operator='>',
                                                                                   left=Identifier(name='x'),
                                                                                   right=IntLiteral(value=0)),
                                                                   right=BinaryExpr(operator='<',
                                                                                    left=Identifier(name='y'),
                                                                                    right=IntLiteral(value=1)))),
                   linenum=0)])
        )

    def test_or(tc):
        tc.assertAst(
            'z >= 69 || a <= 13.37',
            Program(body=[Line(statement=ExpressionStmt(expression=LogicalExpr(operator='||',
                                                                   left=BinaryExpr(operator='>=',
                                                                                   left=Identifier(name='z'),
                                                                                   right=IntLiteral(value=69)),
                                                                   right=BinaryExpr(operator='<=',
                                                                                    left=Identifier(name='a'),
                                                                                    right=FloatLiteral(value=13.37)))),
                   linenum=0)])
        )

class statmentTests(parserTestCase):
    def test_let_stmt(tc):
        tc.assertAst('let x = 420',
            Program(body=[Line(statement=VariableDecl(iden=Identifier(name='x'),
                                        init=IntLiteral(value=420)),
                linenum=0)])
        )

    def test_list_stmt(tc):
        tc.assertAst('list', Program([Line(ListStmt(None))]))
        tc.assertAst('list 1,5',  Program([Line(ListStmt([IntLiteral(1), IntLiteral(5)]))]))
        tc.assertAst('list 1,5 ast',  Program([Line(ListStmt([IntLiteral(1), IntLiteral(5)], 'ast'))]))


    def test_clear_stmt(tc):
        tc.assertAst('clear', Program([Line(ClearStmt())]))
    
    def test_run_stmt(tc):
        tc.assertAst('run', Program([Line(RunStmt(None))]))

    def test_if_stmt(tc):
        tc.assertAst(
        """
        10 if i < 10 then a = 10
        """,
        Program(body=[
            Line(statement=
                IfStmt(test=BinaryExpr(operator='<',    
                                        left=Identifier(name='i'),
                                        right=IntLiteral(value=10)), 
                        consequent=ExpressionStmt(expression=AssignmentExpr(operator='=', left=Identifier(name='a'), right=IntLiteral(value=10))), 
                        alternate=None), 
            linenum=10)
            ])        
        )
        
    def test_if_stmt_short(tc):
        "If statement w/o 'then'"

        tc.assertAst(
        """
        20 if i == 10  a = 13.37
        """,
        Program(body=[Line(statement=IfStmt(test=BinaryExpr(operator='==',
                                                    left=Identifier(name='i'),
                                                    right=IntLiteral(value=10)),
                                    consequent=ExpressionStmt(expression=AssignmentExpr(operator='=',
                                                                                        left=Identifier(name='a'),
                                                                                        right=FloatLiteral(value=13.37))),
                                    alternate=None),
                   linenum=20)])       
        )

    def test_if_else_stmt(tc):
        tc.assertAst(
            """
            30 if i == 10 then a = 13.37 else a += 1
            """,
            Program(body=[Line(statement=IfStmt(test=BinaryExpr(operator='==',
                                                    left=Identifier(name='i'),
                                                    right=IntLiteral(value=10)),
                                    consequent=ExpressionStmt(expression=AssignmentExpr(operator='=',
                                                                                        left=Identifier(name='a'),
                                                                                        right=FloatLiteral(value=13.37))),
                                    alternate=ExpressionStmt(expression=AssignmentExpr(operator='+=',
                                                                                       left=Identifier(name='a'),
                                                                                       right=IntLiteral(value=1)))),
                   linenum=30)])
        )
    
class labelTests(parserTestCase):
    def test_label(tc):
        tc.assertAst(
            """
            name:
            let i = 1
            """,
            Program(body=[Label(name='name'), Line(statement=VariableDecl(iden=Identifier(name='i'), init=IntLiteral(value=1)), linenum=0)])
        )
        tc.assertAst(
            """
            name: let i = 1
            """,
            Program(body=[Label(name='name'), Line(statement=VariableDecl(iden=Identifier(name='i'), init=IntLiteral(value=1)), linenum=0)])
        )
    
class functionTests(parserTestCase):
    def test_rnd(tc):
        tc.assertAst(
            '42  RND (1,10)',
            Program(body=[Line(statement=ExpressionStmt(expression=Func(name='rnd',
                                                            arguments=[IntLiteral(value=1),
                                                                       IntLiteral(value=10)])),
                   linenum=42)])
        )

    def test_usr(tc):
        tc.assertAst(
            '42  USR(0x7fff, 0, 1)',
            Program(body=[Line(statement=ExpressionStmt(expression=Func(name='usr',
                                                            arguments=[IntLiteral(value=0x7fff),
                                                                       IntLiteral(value=0),
                                                                       IntLiteral(value=1)])),
                   linenum=42)])
        )

# --- exec ---
if __name__=='__main__':
    unittest.main()
