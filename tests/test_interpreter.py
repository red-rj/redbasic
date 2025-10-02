import unittest, io, random
from unittest.mock import Mock, patch
# HACK: fix path and imports
import pathlib, sys
sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent/'src'))

from redbasic import Interpreter

# predictible seed for testing rnd()
random.seed(1993)


class Test(unittest.TestCase):
    testdir = pathlib.Path(__file__).parent
    
    def setUp(self):
        self.input = io.StringIO()
        self.output = io.StringIO()
        self.interp = Interpreter(out=self.output, in_=self.input)
        

    def tearDown(self):
        self.input.truncate(0)
        self.output.truncate(0)
        self.input.seek(0)
        self.output.seek(0)

    def setInput(self, *lines):
        self.input.truncate(0)
        self.input.seek(0)
        for a in lines:
            self.input.write(str(a)+'\n')
        self.input.seek(0)
  
    def execScript(self, script):
        with open(self.testdir/script, encoding='utf-8') as f:
            code = f.read()
            self.interp.set_source(code)
            self.interp.exec()


class ScriptTests(Test):
    def test_print(tc):
        code = "print \"olá\""
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertEqual("olá\n", tc.output.getvalue())

    def test_input(tc):
        code = "10 input name, age"
        tc.setInput("Pedro", 32)
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertDictEqual({'name':'Pedro', 'age':32}, tc.interp.variables)

    def test_read_sum_ints(tc):
        tc.setInput(35)
        tc.execScript("sum-ints.bas")
        tc.assertEqual("Result = 69\n", tc.output.getvalue())
        tc.assertEqual(tc.interp.variables["result"], 69)

    def test_rnd(tc):
        code = "69 let r = rnd(1, 100)"
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertEqual(tc.interp.variables['r'], 62)

    def test_pow(tc):
        code = '10 let p = pow(2, 10)'
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertEqual(tc.interp.variables['p'], 1024)
