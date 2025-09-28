import os, sys
import argparse
import pprint
from . import ast, Parser, Interpreter, repl

# baseado nesses cursos
# https://www.udemy.com/share/10416o3@N9X6Bjw-H_pG4ToOt2Ziwam5GYDem5TVH65wxJ4zMRYt0RPOS055QUvpe49AeSIW/
# https://youtube.com/playlist?list=PL_2VhOvlMk4UHGqYCLWc6GO8FaPl8fQTh&si=Z6xQIWjwEH5tTdt2

def main():
    pargs = argparse.ArgumentParser()
    pargs.add_argument('-c', dest='code')
    pargs.add_argument('-f', dest='file', type=argparse.FileType())
    pargs.add_argument('-i', dest='interactive', action='store_true')
    pargs.add_argument('--dump', action='append', choices=('ast', 'vars'))

    args = pargs.parse_args()
    p = Parser()

    if args.code:
        Ast = p.parse(args.code)
    elif args.file:
        text = args.file.read()
        Ast = p.parse(text)
    else:
        print('invalid mode', file=sys.stderr)
        pargs.print_help()
        exit(5)

    if args.interactive:
        prog = Ast if (args.code or args.file) else ast.Program([])
        repl(prog)
        exit()

    interp = Interpreter(p)

    if args.dump and 'ast' in args.dump:
        pprint.pp(Ast)

    interp.exec_program(Ast)

    if args.dump and 'vars' in args.dump:
        pprint.pp(interp.variables)


if __name__=='__main__':
    main()