import os, sys
import pathlib
from lang.lexer import Tokenizer
from lang.parser import Parser
from pprint import pprint

# baseado nesses cursos
# https://www.udemy.com/share/10416o3@N9X6Bjw-H_pG4ToOt2Ziwam5GYDem5TVH65wxJ4zMRYt0RPOS055QUvpe49AeSIW/
# https://youtube.com/playlist?list=PL_2VhOvlMk4UHGqYCLWc6GO8FaPl8fQTh&si=Z6xQIWjwEH5tTdt2


def getprogram()->str:
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = sys.stdin.fileno()

    with open(filename, 'r') as f:
        return f.read()



def main():
    # src = getprogram()
    src = """
10 print "hello"
goto 10
let x = 1
20 y = 2
rem run
"""
    p = Parser()
    ast = p.parse(src)
    pprint(ast)
    


if __name__=='__main__':
    main()