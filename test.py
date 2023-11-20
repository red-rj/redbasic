from typing import Any
import unittest
from lang.parser import Parser
from lang.ast import *

# --- PARSER TESTS ---
parser = Parser()

class parserTestCase(unittest.TestCase):
    def assertAst(tc, code:str, expected):
        ast = parser.parse(code)
        tc.assertEqual(ast, expected, f"""
     {ast=}
{expected=}""")

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
        


    
# --- exec ---

if __name__=='__main__':
    unittest.main()
