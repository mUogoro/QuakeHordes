#*************************************************
# parser.py
#
# Parser for the Hordes Definition Language
#*************************************************
import types
import logging
from ply import yacc as yacc

# Get the tokens from the lexer
from lexer import tokens
from parser_internals import *


class QHDLSyntaxError(Exception):

    def __init__(self, token, lineno, linepos):
        super(QHDLSyntaxError, self).__init__()
        self.token = token
        self.lineno = lineno
        self.linepos = linepos

    
    def __str__(self):
        return "Syntax error on %d:%d: unexpected token [%s] of value [%s]" % \
            (self.lineno, self.linepos,
             self.token.type, self.token.value)


# Global variables
ENV = Env()


# Return the column position for symbol p
def _retRuleLinepos(p, i):
    # fix for the parsing of the first line of code
    try:
        return p.lexpos(i)-p.lexer.startLinePos-1
    except AttributeError:
        return p.lexpos(i)

#************************************
# Grammar productions definition
#************************************
precedence = (('left', 'OR'),
              ('left', 'AND'),
              ('nonassoc', 'NOT'),
              ('left', 'SUB'),
              ('left', 'ADD'),
              ('left', 'MULT'),
              ('left', 'DIV'),
              ('nonassoc', 'O_ROUND'))

def p_start_rule(p):
    '''start_rule : code_lines'''
    p[0] = ProgramNode(0, 0, p[1])

def p_code_lines(p):
    '''code_lines : code_lines code_line
                  | code_line'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]
    

def p_code_line(p):
    '''code_line : declaration
                 | statement'''
    p[0] = p[1]


def p_declaration(p):
    '''declaration : TYPE ID SEMICOLON
                   | TYPE ID O_SQUARE C_SQUARE SEMICOLON'''
    if len(p) == 4:
        childs = [p[1], p[2], None]
    else:
        childs = [p[1], p[2], 0]
    p[0] = DeclNode(p.lineno(0), _retRuleLinepos(p, 1),
                    childs)
    
    

def p_statement(p):
    '''statement : assign_stmt
                 | methcall_stmt
                 | print_stmt
                 | for_stmt
                 | if_stmt'''
    p[0] = p[1]


def p_assign_stmt(p):
    '''assign_stmt : lval EQUAL rval SEMICOLON'''
    lval = p[1]
    rval = p[3]
    #childs = [p[1], p[3]]
    childs = [lval, rval]
    #p[0] = AssignNode(p.lineno(0), p.lexpos(0), childs)
    p[0] = AssignNode(p.lineno(0), _retRuleLinepos(p, 0),
                      childs)


def p_lval(p):
    '''lval : attr_lookup'''
    #p[0] = LvalNode(p.lineno(0), p.lexpos(0), p[1])
    p[0] = LvalNode(p.lineno(0), 
                    _retRuleLinepos(p, 0), p[1])


def p_rval(p):
    #'''rval : const_val
    #        | attr_lookup
    #        | exp'''
    '''rval : exp'''
        
   #p[0] = RvalNode(p.lineno(0), p.lexpos(0), p[1])
    p[0] = RvalNode(p.lineno(0), 
                    _retRuleLinepos(p, 0), [p[1]])


def p_const_val(p):
    '''const_val : INT_VAL
                 | REAL_VAL
                 | QUOTED_STRING
    '''
    p[0] = p[1]


def p_exp(p):
    '''exp : exp ADD exp
           | exp SUB exp
           | exp MULT exp
           | exp DIV exp
           | O_ROUND exp O_ROUND
           | attr_lookup
           | const_val
    '''
    if len(p) == 2:
        try:
            # attr_lookup or string
            if type(p[1]) is str:
                p[0] = p[1]
            else:
                p[0] = p[1][0]
        except TypeError:
            # const_val
            p[0] = p[1]

    # Hack for position of operand: add them as childs
    elif p[2] == '+':
        op = operator.add
        childs = [p[1], p[3], op,
                  p.lineno(1), 
                  _retRuleLinepos(p, 1),
                  p.lineno(3), 
                  _retRuleLinepos(p, 3)]
        p[0] = ExpNode(p.lineno(0), 
                       _retRuleLinepos(p, 0), childs)
    elif p[2] == '-':
        op = operator.sub
        childs = [p[1], p[3], op,
                  p.lineno(1), 
                  _retRuleLinepos(p, 1),
                  p.lineno(3), 
                  _retRuleLinepos(p, 3)]
        p[0] = ExpNode(p.lineno(0), 
                       _retRuleLinepos(p, 0), childs)
    elif p[2] == '/':
        op = operator.div
        childs = [p[1], p[3], op,
                  p.lineno(1), 
                  _retRuleLinepos(p, 1),
                  p.lineno(3), 
                  _retRuleLinepos(p, 3)]
        p[0] = ExpNode(p.lineno(0), 
                       _retRuleLinepos(p, 0), childs)

    elif p[2] == '*':
        op = operator.mul
        childs = [p[1], p[3], op,
                  p.lineno(1), 
                  _retRuleLinepos(p, 1),
                  p.lineno(3), 
                  _retRuleLinepos(p, 3)]
        p[0] = ExpNode(p.lineno(0), 
                       _retRuleLinepos(p, 0), childs)


def p_attr_lookup(p):
    '''attr_lookup : attr_lookup DOT ID item
                   | ID item'''
    if len(p) == 3:
        varName = p[1]
        varOffset = p[2]
        childs = [varName, varOffset, None]
        p[0] = [VarNode(p.lineno(0),
                        _retRuleLinepos(p, 0), childs)]
    else:
        attrName = p[3]
        attrOffset = p[4]
        childs = [attrName, attrOffset, None]
        attrNode = AttrNode(p.lineno(3),
                            _retRuleLinepos(p, 3), childs)
        p[1][-1].childs[-1] = attrNode
        p[1].append(attrNode)
        p[0] = p[1]


def p_item(p):
    '''item : O_SQUARE INT_VAL C_SQUARE
            |'''
    if len(p) > 1:
        p[0] = p[2]


def p_methcall_stmt(p):
    #'methcall_stmt : attr_lookup DOT METHOD O_ROUND args C_ROUND SEMICOLON'
    'methcall_stmt : attr_lookup DOT ID O_ROUND args C_ROUND SEMICOLON'
    var = p[1]
    funcName = p[3]
    args = p[5]
    childs = [funcName, var, args]
    methNode = MethodCallNode(p.lineno(0),
                              _retRuleLinepos(p, 1), childs)
    p[0] = methNode


def p_print_stmt(p):
    'print_stmt : PRINT args SEMICOLON'
    p[0] = PrintNode(p.lineno(0), _retRuleLinepos(p, 0),
                     p[2])


def p_for_stmt(p):
    '''for_stmt : for_stmt_start code_lines END FOR'''
    iterName = p[1][0]
    iterator = p[1][1]
    childs = [iterName, iterator]
    childs.extend(p[2])
    p[0] = ForNode(p.lineno(0), _retRuleLinepos(p, 0),
                   childs)


def p_for_stmt_start(p):
    '''for_stmt_start : FOR EACH ID IN range COLON
                      | FOR EACH iter AS ID COLON'''
    
    # TODO: avoid type checking
    if type(p[3]) is AstNode:
        p[0] = (p[5], p[3])
    else:
        p[0] = (p[3], p[5])


def p_range(p):
    '''range : O_ROUND INT_VAL COMMA INT_VAL C_ROUND'''
    p[0] = range(p[2], p[4])


def p_if_stmt(p):
    '''if_stmt : IF cond COLON code_lines ELSE COLON code_lines END IF
               | IF cond COLON code_lines END IF'''
    if len(p) == 7:
        childs = [p[2], p[4], None]
    else:
        childs = [p[2], p[4], p[7]]
    p[0] = IfNode(p.lineno(0), _retRuleLinepos(p, 0),
                  childs)


def p_cond(p):
    '''cond : NOT cond
            | cond AND cond
            | cond OR cond
            | O_ROUND cond C_ROUND
            | comparison
    '''
    # TODO: only comparison now
    if len(p) == 2:
        childs = p[1]
        p[0] = CondNode(p.lineno(0), 
                        _retRuleLinepos(p, 0), childs)
    elif len(p) == 3:
        op = operator.not_
        childs = [p[2], None, op]
        p[0] = CondNode(p.lineno(0),
                        _retRuleLinepos(p, 0), childs)
    elif p[1] == '(':
        p[0] = p[2]
    elif p[2] == 'and':
        op = operator.and_
        childs = [p[1], p[3], op]
        p[0] = CondNode(p.lineno(0),
                        _retRuleLinepos(p, 0), childs)
    else:
        op = operator.or_
        childs = [p[1], p[3], op]
        p[0] = CondNode(p.lineno(0),
                        _retRuleLinepos(p, 0), childs)
    
        
def p_comparison(p):
    'comparison : rval relop rval'
    if p[2] == '==':
        relop = operator.eq
    elif p[2] == '!=':
        relop = operator.ne
    elif p[2] == '>':
        relop = operator.gt
    elif p[2] == '>=':
        relop = operator.ge
    elif p[2] == '<':
        relop = operator.lt
    else:
        relop = operator.le
    
    p[0] = [p[1], p[3], relop]


def p_relop(p):
    '''relop : EQ
             | NEQ
             | GT
             | GET
             | LT
             | LET '''
    p[0] = p[1]


def p_iter(p):
    'iter : attr_lookup'
    p[0] = p[1][0]


def p_args(p):
    '''args : args COMMA arg
            | arg'''    
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[3])
        p[0] = p[1]


def p_arg(p):
    #'''arg : attr_lookup'''
    '''arg : rval'''
    p[0] = p[1]


def p_error(t):
    raise QHDLSyntaxError(t, t.lineno,
                          t.lexpos-t.lexer.startLinePos-1)


#************************************
# Grammar productions definition end
#************************************

# Build the parser
def BuildQHDLParser(workDir):
    # WARNING: reenable logging if problems occur
    #return yacc.yacc(outputdir=workDir)
    return yacc.yacc(outputdir=workDir,
                     errorlog=yacc.NullLogger())
