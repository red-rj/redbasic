from typing import Any
import unittest
from lang.parser import Parser
from lang.ast import *

# --- PARSER TESTS ---
parser = Parser()

class parserTestCase(unittest.TestCase):
    def assertAst(tc, code:str, expected:Program):
        ast = parser.parse(code)
        tc.assertEqual(ast, expected)
        



    
# --- exec ---

if __name__=='__main__':
    unittest.main()
