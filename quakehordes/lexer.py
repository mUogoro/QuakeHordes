#*************************************************
# lexer.py
#
# Lexer for the Hordes Definition Language
#*************************************************
from ply import lex as lex


# List of tokens used by the language
reserved = {'if':'IF',
            'else':'ELSE',
            'end':'END',
            'for':'FOR',
            'each':'EACH',
            'as':'AS',
            'in':'IN',
            'not':'NOT',
            'and':'AND',
            'or':'OR',
            'print': 'PRINT'}

types = ['Map', 'Horde', 'Monster', 'Item', 'Player']
methods = ['add', 'remove', 'index']

#tokens = list(reserved.values()) + \
#    ['TYPE', 'ID', 'METHOD',
#     'INT_VAL', 'REAL_VAL', 'QUOTED_STRING',
#     'DOT', 'COLON', 'SEMICOLON', 'COMMA', 'EQUAL',
#     'EQ', 'NEQ', 'GT', 'GET', 'LT', 'LET',
#     'O_ROUND', 'C_ROUND', 'O_SQUARE', 'C_SQUARE']

tokens = list(reserved.values()) + \
    ['TYPE', 'ID',
     'INT_VAL', 'REAL_VAL', 'QUOTED_STRING',
     'DOT', 'COLON', 'SEMICOLON', 'COMMA', 'EQUAL',
     'EQ', 'NEQ', 'GT', 'GET', 'LT', 'LET',
     'O_ROUND', 'C_ROUND', 'O_SQUARE', 'C_SQUARE']


# Token definitions

#def t_MAP(t):
#    r'Map'
#    return t

#def t_HORDE(t):
#    r'Horde'
#    return t

#def t_MONSTER(t):
#    r'Monster'
#    return t

#def t_PLAYER(t):
#    r'Player'
#    return t

#t_ID = r'[A-Za-z][A-Za-z0-9_-]*'
#t_TYPE = r'Map|Horde|Monster|Player'

def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_-]*'
    if t.value in reserved.keys():
        t.type = reserved[t.value]
    elif t.value in types:
        t.type = 'TYPE'
    #elif t.value in methods:
    #    t.type = 'METHOD'
    return t

def t_INT_VAL(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

def t_REAL_VAL(t):
    r'[0-9]*\.[0.9]+'
    t.value = float(t.value)
    return t

# TODO: check
def t_QUOTED_STRING(t):
    r'"[^"]*"'
    t.value = str(t.value[1:-1])
    return t

t_DOT = r'\.'
t_COLON = r':'
t_SEMICOLON = r';'
t_COMMA = r','
t_EQUAL = r'='

t_EQ = r'=='
t_NEQ = r'!='
t_GT = r'>'
t_GET = r'>='
t_LT = r'<'
t_LET = r'<='

t_O_ROUND = r'\('
t_C_ROUND = r'\)'
t_O_SQUARE = r'\['
t_C_SQUARE = r'\]'

def t_comment(t):
    r'\#[^\n]*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.startLinePos = t.lexpos

t_ignore = r' '

def t_error(t):
    raise SyntaxError("Error on line %d  on token %s" %
                      (t.lexer.lineno, t.value))

# Build the lexer
#lex.lex(debug=True)
lex.lex()