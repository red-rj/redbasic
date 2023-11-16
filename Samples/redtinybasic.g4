grammar redtinybasic;


// a program is a collection of lines / labels
program
   : (line | label) + EOF
   ;

label
    : varname ':'
    ;

linenumber : NUMBER ;

// a line starts with a INT (optional)
line 
   : linenumber? ((linecontent (':' linecontent?)*) | (COMMENT | REM))
   ;

ampersand_operator
   : '&'
   ;

linecontent
    : (ampersand_operator? statement)
    | (COMMENT | REM)
    ;


// statements
statement
   : printstmt
   | inputstmt
   | amptstmt
   | ifstmt
   | gosubstmt
   | gotostmt
   | letstmt
   | endstmt
   | returnstmt
   ;

printstmt
    : PRINT printlist?
    ;

ifstmt
    : IF expression THEN? statement
    ;

gotostmt
    : GOTO expression
    ;

gosubstmt
   : GOSUB expression
   ;

inputstmt
   : INPUT (STRINGLITERAL (',' | ';'))? varlist
   ;

letstmt
   : LET? variableassignment
   ;

amptstmt
   : '&' expression
   ;

endstmt
   : END
   ;

returnstmt
   : RETURN
   ;


variableassignment
   : vardecl EQ exprlist
   ;

vardecl
   : var ('(' exprlist ')')*
   ;

printlist
   : expression ((',' | ';') expression?)*
   ;

// relop ::= < ! > ! = ! <= ! >= ! <> ! >< 
relop
   : (GTE)
   | (GT EQ)
   | (EQ GT)
   | LTE
   | (LT EQ)
   | (EQ LT)
   | (LT GT) // neq
   | EQ
   | GT
   | LT
   ;

// expressions
number
   :  ('+' | '-')? (NUMBER | FLOAT)
   ;

func 
    : STRINGLITERAL
    | number
    | vardecl
    | usrfunc
    | rndfunc
    | '(' expression ')'
    ;

signExpression
   : NOT? ('+' | '-')? func
   ;

exponentExpression
   : signExpression (EXPONENT signExpression)*
   ;

multiplyingExpression
   : exponentExpression (('*' | '/') exponentExpression)*
   ;

addingExpression
   : multiplyingExpression (('+' | '-') multiplyingExpression)*
   ;

relationalExpression
   : addingExpression ((relop) addingExpression)?
   ;

expression
   : func
   | (relationalExpression ((AND | OR) relationalExpression)*)
   ;


var
   : varname varsuffix?
   ;

varname
   : LETTERS (LETTERS | NUMBER)*
   ;

varsuffix
   : ('$' | '%')
   ;

varlist
   : vardecl (',' vardecl)*
   ;

exprlist
   : expression (',' expression)*
   ;

usrfunc
    : USR '(' exprlist ')'
    ;

rndfunc
    : RND '(' expression ')'
    ;

// keywords
PRINT : 'print' | 'PRINT' ;
IF : 'if' | 'IF' ;
THEN : 'then' | 'THEN' ;
ELSE : 'else' | 'ELSE' ;
GOTO : 'goto' | 'GOTO' ; 
INPUT : 'input' | 'INPUT' ; 
LET : 'let' | 'LET' ;
GOSUB : 'gosub' | 'GOSUB' ;
RETURN : 'return' | 'RETURN' ;
CLEAR : 'clear' | 'CLEAR' ;
LIST : 'list' | 'LIST' ;
RUN : 'run' | 'RUN' ;
END : 'end' | 'END' ;
REM : 'rem' | 'REM' ;

// builtin functions
RND : 'rnd' | 'RND' ;
USR : 'usr' | 'USR' ;

NOT : 'not' | 'NOT' ;
AND : 'AND' | 'and' | '&&' ;
OR : 'OR' | 'or' | '||' ;


// basic stuff
COMMENT : REM ~ [\r\n]* ;

LETTERS : [a-zA-Z]+ ;

NUMBER
   : [0-9]+ (('e' | 'E') NUMBER)*
   ;
FLOAT
   : DIGIT* '.' DIGIT + (('e' | 'E') DIGIT+)*
   ;
STRINGLITERAL
   : '"' ~ ["\r\n]* '"'
   ;

EXPONENT : '^' ;

GTE : '>=' ;
LTE : '<=' ;
GT : '>' ;
LT : '<' ;
EQ : '=' ;
NEQ : (LT GT) ;

DIGIT : [0-9] ;
HEXDIGIT : [a-fA-F0-9] ;