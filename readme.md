# RedBasic
## A simple basic implementation

This is a implementation of the BASIC programing language in python. It's based on TinyBasic, but not intented to be compatible with it.

## Expression precendence (low to high)
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
        | label line_list
        ;

    line
        : integer? statement EOL
        ;

    label
        : identifier ':' EOL
        : identifier ':' statement EOL
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
        | end_stmt
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
        : single_expression
        | string_literal
        ;

    input_stmt
        : 'INPUT' varlist
        ;

    let_stmt
        : 'LET' identifier = expression
        | identifier = expression
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
        : 'IF' expression relop expression 'THEN'? statement
        | 'IF' expression relop expression 'THEN'? statement 'else' statement
        ;

    comment
        : 'REM' comment_string
        ;

    clear_stmt
        : 'CLEAR'
        ;

    run_stmt
        : 'RUN'
        | 'RUN' ',' exprlist
        ;
    
    list_stmt
        : 'LIST'
        | 'LIST' exprlist
        | 'LIST' exprlist list_mode
        ;

    list_mode
        : 'code'
        | 'ast'
        ;

    end_stmt
        : 'end'
        ;
    
    varlist 
        : identifier
        | identifier ',' varlist
        ;

    exprlist 
        : expression
        | expression ',' exprlist
        ;

    expression 
        : assignment_expr
        | assignment_expr ',' expression
        ;

    assignment_expr
        : logical_or_expr
        | lhs assignment_op assignment_expr
        ;

    single_expression
        : assignment_expr
        ;

    logical_or_expr
        : logical_and_expr
        | logical_and_expr logical_or_op logical_or_expr
        ;

    logical_and_expr
        : equality_expr
        | equality_expr logical_and_op logical_and_expr
        ;

    equality_expr
        : relational_expr
        | relational_expr equality_op equality_expr
        ;

    relational_expr
        : additive_expr
        | additive_expr relational_op relational_expr
        ;

    additive_expr
        : multiplicative_expr
        | multiplicative_expr additive_op additive_expr
        ;

    multiplicative_expr
        : unary_expr
        | unary_expr multiplicative_op multiplicative_expr
        ;

    unary_expr
        : primary_expr
        | additive_op unary_expr
        | logical_not_op unary_expr
        ;

    primary_expr
        : literal
        | paren_expr
        | identifier
        | function
        ;

    lhs
        : identifier
        ;

    function 
        : 'RND' '(' expression ')'
        | 'USR' '(' exprlist ')'
        ;

    number
        : integer
        | float
        ;

    identifier
        : [a-zA-Z_]\w*
        ;
    
    integer
        : \d+
        ;

    float
        : (\d+\.\d*)([Ee][-+]?\d+)?
        ;

    relational_op 
        : '<'
        | '>'
        | '<='
        | '>='
        ;

    equality_op
        : '=='
        | '<>'
        | '><'
        ;

    assignment_op
        : '='
        | '+='
        | '-='
        | '*='
        | '/='
        ;

    additive_op
        : '+'
        | '-'
        ;

    multiplicative_op
        : '*'
        | '/'
        ;

    logical_or_op
        : '||'
        ;
    
    logical_and_op
        : '&&'
        ;
    
    logical_not_op
        : '!'
        ;
    