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
    test_codes = [
"2 * 2",
"2 * 2 * 2",
'29 * 3 / (1+9-9/3)',
'2 + 2 * 2',
'(2 + 2) * 2',
'var = 42',
'var = x',
'y = x = 42',
'let x = 420',
'let pedro = 30, lila = 23',
"""
10 if i < 10 then a = 10
""",
"""
20 if i == 10 a = 13.37
""",
"""
30 if i == 10 then a = 13.37 else a += 1
""",
"a += 1"
    ]

    p = Parser()

    for code in test_codes:
        try:
            print(code, end=' :: ')
            ast = p.parse(code)
            pprint(ast)
        except Exception as e:
            print(e)

        print('-'*25)
    


if __name__=='__main__':
    main()