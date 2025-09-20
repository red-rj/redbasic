import os, sys, io
import argparse
from . import ast, Parser, Interpreter
import pprint

# baseado nesses cursos
# https://www.udemy.com/share/10416o3@N9X6Bjw-H_pG4ToOt2Ziwam5GYDem5TVH65wxJ4zMRYt0RPOS055QUvpe49AeSIW/
# https://youtube.com/playlist?list=PL_2VhOvlMk4UHGqYCLWc6GO8FaPl8fQTh&si=Z6xQIWjwEH5tTdt2

def repl(parser:Parser):
    interp = Interpreter(parser)
    print("redbasic REPL v0.0")
    buffer = io.StringIO()
    body = []

    while 1:
        code = input("> ")
        buffer.write(code + '\n')

        lineast = parser.parse_line(code)
        body.append(lineast)

        if isinstance(lineast.statement, ast.RunStmt):
            #prog = parser.parse(buffer.getvalue())
            prog = ast.Program(body)
            interp.exec_program(prog)
        elif isinstance(lineast.statement, ast.ClearStmt):
            os.system('cls' if os.name == 'nt' else 'clear')
        

def main():
    pargs = argparse.ArgumentParser()
    pargs.add_argument('-c', dest='code')
    pargs.add_argument('-f', dest='file', type=argparse.FileType('r'))
    pargs.add_argument('-i', dest='interactive', action='store_true')
    pargs.add_argument('--dump', action='append', choices=('ast', 'vars'))

    args = pargs.parse_args()
    p = Parser()

    if args.code:
        ast = p.parse(args.code)
    elif args.file:
        text = args.file.read()
        ast = p.parse(text)
    elif args.interactive:
        repl(p)
        exit()
    else:
        print('invalid mode', file=sys.stderr)
        pargs.print_help()
        exit(5)

    interp = Interpreter(p)

    if args.dump and 'ast' in args.dump:
        pprint.pp(ast)

    interp.exec_program(ast)

    if args.dump and 'vars' in args.dump:
        pprint.pp(interp.variables)


if __name__=='__main__':
    main()