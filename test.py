from typing import Any
import unittest
from lang.parser import Parser, parse_int
from lang.ast import *

# --- PARSER TESTS ---
parser = Parser()

class parserTestCase(unittest.TestCase):
    def assertAst(tc, code:str, expected):
        ast = parser.parse(code)
        tc.assertEqual(ast, expected, f"""
     {ast=}
{expected=}""")
        
class parserHelpers(unittest.TestCase):
    def test_parse_int(tc):
        tc.assertEqual(0o77, parse_int('077'))
        tc.assertEqual(0xc00ffee, parse_int('0xC00FFEE'))
        tc.assertEqual(1, parse_int('1'))

class mathTests(parserTestCase):
    def test_addition(tc):
        tc.assertAst(
            "10  2 + 2",
            Program([Line(ExpressionStmt(BinaryExpr('+', IntLiteral(2), IntLiteral(2))), 10)])
        )
        
    def test_nested_add_subtract(tc):
        tc.assertAst(
            "3 + 2 - 2",
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
            "2 * 2",
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='*',
                                                                  left=IntLiteral(value=2),
                                                                  right=IntLiteral(value=2))),
                   linenum=0)])
        )

    def test_multiplication_nested(tc):
        tc.assertAst(
            '2 * 2 * 2',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='*',
                                                                  left=BinaryExpr(operator='*',
                                                                                  left=IntLiteral(value=2),
                                                                                  right=IntLiteral(value=2)),
                                                                  right=IntLiteral(value=2))),
                   linenum=0)])
        )

        tc.assertAst(
            '29 * 3 / (1+9-9/3)',
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
            '2 + 2 * 2',
            Program(body=[Line(statement=ExpressionStmt(expression=BinaryExpr(operator='+',
                                                                  left=IntLiteral(value=2),
                                                                  right=BinaryExpr(operator='*',
                                                                                   left=IntLiteral(value=2),
                                                                                   right=IntLiteral(value=2)))),
                   linenum=0)])
        )

        tc.assertAst(
            ' (2 + 2) * 2',
            Program(body=[Line(statement=ExpressionStmt(expression=
                                            BinaryExpr(operator='*',
                                                        left=BinaryExpr(operator='+',
                                                                        left=IntLiteral(value=2),
                                                                        right=IntLiteral(value=2)),
                                                        right=IntLiteral(value=2))),
                   linenum=0)])
        )
        
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
        tc.assertAst('1  a += 1',
                     Program(body=[Line(statement=ExpressionStmt(expression=AssignmentExpr(operator='+=',
                                                                      left=Identifier(name='a'),
                                                                      right=IntLiteral(value=1))),
                   linenum=1)])
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

    @unittest.expectedFailure
    def test_if_else_stmt(tc):
        tc.assertAst(
            """
            30 if i == 10 then a = 13.37 else a += 1
            """,
            
        )
    
    
# --- exec ---

if __name__=='__main__':
    unittest.main()
