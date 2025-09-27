import os, sys
import argparse
import pprint
from . import ast, Parser, Interpreter

# baseado nesses cursos
# https://www.udemy.com/share/10416o3@N9X6Bjw-H_pG4ToOt2Ziwam5GYDem5TVH65wxJ4zMRYt0RPOS055QUvpe49AeSIW/
# https://youtube.com/playlist?list=PL_2VhOvlMk4UHGqYCLWc6GO8FaPl8fQTh&si=Z6xQIWjwEH5tTdt2

def repl(parser:Parser, prog:ast.Program):
    interp = Interpreter(parser)
    print("redbasic REPL v0.1")
    print("Ctrl+C to exit")
    body = prog.body

    while 1:
        code = input("> ")
        lineast = parser.parse_line(code)

        if isinstance(lineast, ast.Line):
            stmt = lineast.statement
            if isinstance(stmt, ast.RunStmt):
                interp.ast = prog
                interp.exec()
            elif isinstance(stmt, ast.ClearStmt):
                os.system('cls' if os.name == 'nt' else 'clear')
            elif isinstance(stmt, ast.ListStmt):
                interp.ast = prog
                args = stmt.arguments
                limits = interp.eval(args) if args else None
                # TODO: respect limit arguments
                if stmt.mode == 'code':
                    src = ast.reconstruct(interp.ast)
                    print(src)
                elif stmt.mode == 'ast':
                    pprint.pp(interp.ast)
            else:
                replaced = False
                if lineast.linenum:
                    numbered_lines = enumerate(body)
                    numbered_lines = [e for e in numbered_lines if isinstance(e[1], ast.Line)]
                    for i, a in numbered_lines:
                        if a.linenum == lineast.linenum:
                            # replace line
                            body[i] = lineast
                            replaced = True
                            break
                # in repl mode, append only if there's a line number
                # else execute
                if not replaced and lineast.linenum:
                    body.append(lineast)
                else:
                    interp.exec_line(lineast)

        elif isinstance(lineast, ast.Label):
            body.append(lineast)


        

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
        repl(p, prog)
        exit()

    interp = Interpreter(p)

    if args.dump and 'ast' in args.dump:
        pprint.pp(Ast)

    interp.exec_program(Ast)

    if args.dump and 'vars' in args.dump:
        pprint.pp(interp.variables)


if __name__=='__main__':
    main()