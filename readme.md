# RedBasic
## A simple basic implementation

This is a implementation of TinyBasic in python.

## Expr precendence (low to high)
- sequence
- assignment
- logical or
- logical and
- equality
- relational
- additive
- multiplicitave
- unary
- lhs expression
- primary

## Formal definition
    program
        : line_list EOF
        ;

    line_list
        : line line_list
        ;

    line
        : integer statement EOL
        | statement EOL
        ;

    statement 
        : print_stmt
        | input_stmt
        | let_stmt
        | goto_stmt
        | gosub_stmt
        | return_stmt
        | if_stmt
        | comment
        | clear_stmt
        | run_stmt
        | list_stmt
        ;

    print_stmt
        : 'PRINT' printlist
        | 'PR' printlist
        ;

    printlist
        : printitem
        | printitem ':'
        | printitem print_sep printlist
        ;

    print_sep 
        : ','
        | ';'
        ;

    printitem 
        : expression
        | "characterstring"
        ;

    input_stmt
        : 'INPUT' varlist
        ;

    let_stmt
        : 'LET' var = expression
        | var = expression
        ;

    goto_stmt
        : 'GOTO' expression
        ;

    gosub_stmt
        : 'GOSUB' expression
        ;

    return_stmt
        : 'RETURN'
        ;

    if_stmt
        : 'IF' expression relop expression 'THEN' statement
        | 'IF' expression relop expression statement
        | 'IF' expression relop expression 'THEN' statement 'else' statement
        | 'IF' expression relop expression statement 'else' statement
        ;

    comment
        : 'REM' comment_string
        ;

    clear_stmt
        : 'CLEAR'
        ;

    run_stmt
        : 'RUN'
        | 'RUN' exprlist
        ;
    
    list_stmt
        : 'LIST'
        | 'LIST' exprlist
        | 'LIST' 'ast' exprlist
        ;

    
    varlist 
        : var
        | var ',' varlist
        ;

    exprlist 
        : expression
        | expression ',' exprlist
        ;

    expression 
        : unsignedexpr
        | '+' unsignedexpr
        | '-' unsignedexpr
        ;

    unsignedexpr 
        : term
        | term '+' unsignedexpr
        | term '-' unsignedexpr
        ;

    term 
        : factor
        | factor '*' term
        | factor '/' term
        ;

    factor 
        : var
        | number
        | '(' expression ')'
        | function
        ;

    function 
        : 'RND' '(' expression ')'
        | 'USR' '(' exprlist ')'
        ;

    

    var
        : [a-zA-Z_]\w*
        ;
    
    integer
        : \d+
        ;

    relop 
        : '<'
        | '>'
        | '='
        | '<='
        | '>='
        | '<>'
        | '><'
        ;
