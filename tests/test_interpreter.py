import unittest, io, random
import functools
# HACK: fix path and imports
import pathlib, sys
scriptdir = pathlib.Path(__file__).absolute()
sys.path.append(str(scriptdir.parent.parent/'src'))

from redbasic import Interpreter


class TestCase(unittest.TestCase):
    testdir = scriptdir.parent
            
    def setUp(self):
        self.input = io.StringIO()
        self.output = io.StringIO()
        self.interp = Interpreter(textout=self.output, textin=self.input)
        
    def tearDown(self):
        self.input.truncate(0)
        self.output.truncate(0)
        self.input.seek(0)
        self.output.seek(0)

    def setInput(self, *lines):
        self.input.seek(0)
        for a in lines:
            self.input.write(f'{a}\n')
        self.input.truncate()
        self.input.seek(0)

    def execScript(self, script):
        with open(self.testdir/script, encoding='utf-8') as f:
            code = f.read()
            self.interp.set_source(code)
            self.interp.exec()


class interpreterTests(TestCase):
    def test_print(tc):
        code = "print \"olá\""
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertRegex(tc.output.getvalue(), "olá")

    def test_input(tc):
        code = "10 input name, age"
        tc.setInput("Pedro", 32)
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertDictEqual({'name':'Pedro', 'age':32}, tc.interp.variables)

    def test_rnd(tc):
        random.seed(1993)
        code = "69 let r = rnd(1, 100)"
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertEqual(tc.interp.variables['r'], 62)

    def test_pow(tc):
        code = '10 let p = pow(2, 10)'
        tc.interp.set_source(code)
        tc.interp.exec()
        tc.assertEqual(tc.interp.variables['p'], 1024)

    def test_loose_expr(tc):
        tc.interp.set_source("1  32+1993")
        tc.interp.exec()
        tc.assertEqual(tc.interp.variables["_"], 2025)

    def test_no_repl_on_noninteractive_streams(tc):
        with tc.assertRaises(RuntimeError):
            tc.interp.repl("oh no", "not a tty!")

class ScriptTests(TestCase):
    def test_read_sum_ints(tc):
        tc.setInput(35)
        tc.execScript("sum-ints.bas")
        tc.assertEqual("Result = 69\n", tc.output.getvalue())
        tc.assertEqual(tc.interp.variables["result"], 69)

    def test_math(tc):
        tc.execScript("math.bas")
        var = tc.interp.variables
        results = {
            'R_add':80,
            'R_sub':74,
            'R_div':37,
            'R_mul':111,
        }

        for key in results:
            for n in range(1,3):
                name = f"{key}{n}"
                tc.assertEqual(var[name], results[key])
        
    def test_if(tc):
        tc.execScript("if.bas")
        out = tc.output.getvalue()
        tc.assertRegex(out, r"if ok")
        tc.assertRegex(out, r"else ok")
        tc.assertNotRegex(out, r"error")

    def test_relational(tc):
        tc.execScript("relational.bas")
        out = tc.output.getvalue()
        tc.assertRegex(out, r"if and")
        tc.assertRegex(out, r"else and")
        tc.assertRegex(out, r"if or")
        tc.assertRegex(out, r"else or")
        tc.assertNotRegex(out, r"error")

    def test_goto(tc):
        tc.execScript("goto.bas")
        out = tc.output.getvalue()
        var = tc.interp.variables
        tc.assertRegex(out, "start")
        tc.assertEqual(var["tmp"], 2)

    def test_gosub(tc):
        tc.execScript("gosub.bas")
        out = tc.output.getvalue()
        tc.assertRegex(out, "start")
        tc.assertRegex(out, "lineno")
        tc.assertRegex(out, "label")
        tc.assertRegex(out, "end")


if __name__=='__main__':
    unittest.main()