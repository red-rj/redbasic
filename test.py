import unittest
from lang.parser import Parser
from lang.ast import *

parser = Parser()

class mathTests(unittest.TestCase):
    
    def test_addition(tc):
        code = "2 + 2"
        ast = parser.parse(code)
        expected = Program([ BinaryExpr('+', IntLiteral(2), IntLiteral(2)) ])
        tc.assertEqual(ast, expected)

    def test_nested_add_subtract(tc):
        code = '3 + 2 -2'
        ast = parser.parse(code)
        expected = Program(body=[BinaryExpr(operator='-',
                         left=BinaryExpr(operator='+',
                                         left=IntLiteral(value=3),
                                         right=IntLiteral(value=2)),
                         right=IntLiteral(value=2))])
        tc.assertEqual(ast, expected)

    def test_multiplication(tc):
        code = '2 * 2'
        ast = parser.parse(code)
        expected = Program(body=[BinaryExpr(operator='*',
                         left=IntLiteral(value=2),
                         right=IntLiteral(value=2))])
        tc.assertEqual(ast, expected)

    def test_multiplication_nested(tc):
        code = '2 * 2 * 2'
        ast = parser.parse(code)
        expected = Program(body=[BinaryExpr(operator='*',
                         left=BinaryExpr(operator='*',
                                         left=IntLiteral(value=2),
                                         right=IntLiteral(value=2)),
                         right=IntLiteral(value=2))])
        tc.assertEqual(ast, expected)

        code = '29 * 3 / (1+9-9/3)'
        ast = parser.parse(code)
        expected = Program(body=[BinaryExpr(operator='/',
                         left=BinaryExpr(operator='*',
                                         left=IntLiteral(value=29),
                                         right=IntLiteral(value=3)),
                         right=BinaryExpr(operator='-',
                                          left=BinaryExpr(operator='+',
                                                          left=IntLiteral(value=1),
                                                          right=IntLiteral(value=9)),
                                          right=BinaryExpr(operator='/',
                                                           left=IntLiteral(value=9),
                                                           right=IntLiteral(value=3))))])
        tc.assertEqual(ast, expected)
        

    def test_operator_precedence(tc):
        code = '2 + 2 * 2'
        ast = parser.parse(code)
        expected = Program(body=[BinaryExpr(operator='+',
                         left=IntLiteral(value=2),
                         right=BinaryExpr(operator='*',
                                          left=IntLiteral(value=2),    
                                          right=IntLiteral(value=2)))])
        tc.assertEqual(ast, expected)

        code = '(2 + 2) * 2;'
        ast = parser.parse(code)
        expected = Program(body=[BinaryExpr(operator='*',
                         left=BinaryExpr(operator='+',
                                         left=IntLiteral(value=2),  
                                         right=IntLiteral(value=2)),
                         right=IntLiteral(value=2))])
        tc.assertEqual(ast, expected)
        
    
class assignmentTests(unittest.TestCase):
    def test_simple_assignment(tc):
        code = 'var = 42'
        ast = parser.parse(code)
        expected = Program(body=[AssignmentExpr(operator='=',
                             left=Identifier(name='var'),
                             right=IntLiteral(value=42))])
        tc.assertEqual(ast, expected)

        code = 'var = x'
        ast = parser.parse(code)
        expected = Program(body=[AssignmentExpr(operator='=',
                             left=Identifier(name='var'),
                             right=Identifier('x'))])
        tc.assertEqual(ast, expected)

    def test_chained_assignment(tc):
        code = 'y = x = 42'
        ast = parser.parse(code)
        expected = Program(body=[AssignmentExpr(operator='=',
                             left=Identifier(name='y'),
                             right=AssignmentExpr(operator='=',
                                                  left=Identifier(name='x'),
                                                  right=IntLiteral(value=42)))])
        tc.assertEqual(ast, expected)
        

class variableTests(unittest.TestCase):
    def test_simple_variable_assignment(tc):
        code = 'let x = 420;'
        ast = parser.parse(code)
        expected = Program([VariableStmt([VariableDecl(Identifier('x'), IntLiteral(420))])])
        tc.assertEqual(ast, expected)
    
    def test_variable_declaration_no_init(tc):
        code = 'let x;'
        ast = parser.parse(code)
        expected = Program([VariableStmt(declarations=[VariableDecl(iden=Identifier(name='x'), init=None)])])
        tc.assertEqual(ast, expected)

    def test_multiple_variable_declaration(tc):
        code = 'let pedro, lila = 23;'
        ast = parser.parse(code)
        expected = Program([
            VariableStmt(declarations=[VariableDecl(iden=Identifier(name='pedro'),
                                                      init=None),
                                         VariableDecl(iden=Identifier(name='lila'),
                                                      init=IntLiteral(value=23))])
                                                      ])
        tc.assertEqual(ast, expected)

        code = 'let pedro = 30, lila = 23;'
        ast = parser.parse(code)
        expected = Program([
            VariableStmt(declarations=[VariableDecl(iden=Identifier(name='pedro'),
                                                      init=IntLiteral(value=30)),
                                         VariableDecl(iden=Identifier(name='lila'),
                                                      init=IntLiteral(value=23))])
                                                      ])
        tc.assertEqual(ast, expected)

    def test_multiple_variable_declaration_no_init(tc):
        code = 'let pedro, lila;'
        ast = parser.parse(code)
        expected = Program([VariableStmt(declarations=[VariableDecl(iden=Identifier(name='pedro'),
                                                      init=None),
                                         VariableDecl(iden=Identifier(name='lila'),
                                                      init=None)])])
        tc.assertEqual(ast, expected)

    
class statementListTests(unittest.TestCase):
    def test_statement_list(tc):
        code = """
        "hello";

        42;
        """
        ast = parser.parse(code)
        expected = Program(body=[StringLiteral(value='hello'), IntLiteral(value=42)])
        tc.assertEqual(ast, expected)


    



# --- exec ---

if __name__=='__main__':
    unittest.main()
