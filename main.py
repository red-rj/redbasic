import sys, io
import argparse
import lang.ast as ast
from lang.parser import Parser
from runtime.interpreter import Interpreter

# baseado nesses cursos
# https://www.udemy.com/share/10416o3@N9X6Bjw-H_pG4ToOt2Ziwam5GYDem5TVH65wxJ4zMRYt0RPOS055QUvpe49AeSIW/
# https://youtube.com/playlist?list=PL_2VhOvlMk4UHGqYCLWc6GO8FaPl8fQTh&si=Z6xQIWjwEH5tTdt2

def repl(parser:Parser):
    interp = Interpreter(parser)
    print("redbasic REPL v0.0")
    buffer = io.StringIO()

    while 1:
        code = input("> ")
        buffer.write(code + '\n')

        lineast = parser.parse_line(code)

        if isinstance(lineast.statement, ast.RunStmt):
            prog = parser.parse(buffer.getvalue())
            interp.exec_program(prog)
        

def main():
    pargs = argparse.ArgumentParser()
    pargs.add_argument('-c', dest='code')
    pargs.add_argument('-f', dest='file')
    pargs.add_argument('-i', dest='interactive', action='store_true')

    args = pargs.parse_args()
    p = Parser()

    if args.code:
        ast = p.parse(args.code)
    elif args.file:
        filename = args.file
        if filename == '-':
            filename = sys.stdin.fileno()
        
        with open(filename, 'r', encoding='utf8') as f:
            ast = p.parse(f.read())
    elif args.interactive:
        repl(p)
        exit()
    else:
        print('invalid mode', file=sys.stderr)
        pargs.print_help()
        exit(5)

    #pprint(ast)
    interp = Interpreter(p)
    interp.exec_program(ast)
    print(interp.variables)

if __name__=='__main__':
    main()