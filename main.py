import sys
import locale
import argparse
from lang.parser import Parser
from pprint import pprint

# baseado nesses cursos
# https://www.udemy.com/share/10416o3@N9X6Bjw-H_pG4ToOt2Ziwam5GYDem5TVH65wxJ4zMRYt0RPOS055QUvpe49AeSIW/
# https://youtube.com/playlist?list=PL_2VhOvlMk4UHGqYCLWc6GO8FaPl8fQTh&si=Z6xQIWjwEH5tTdt2

def main():
    pargs = argparse.ArgumentParser()
    pargs.add_argument('-c', dest='code')
    pargs.add_argument('-f', dest='file')

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
    else:
        print('invalid mode', file=sys.stderr)
        pargs.print_help()
        exit(5)

    pprint(ast)

if __name__=='__main__':
    main()