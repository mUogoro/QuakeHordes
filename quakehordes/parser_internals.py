#*************************************************
# parser_internals.py
#
#*************************************************

import operator

# Defined types
TYPES = {'Map': {'name':'string',
                 'introMessage':'string',
                 'difficult':'string',
                 'width':'int',
                 'height':'int',
                 'next':'Map',
                 'players':'Player[]',
                 'hordes':'Horde[]',
                 'items': 'Item[]'},
         'Horde':{'id':'string',
                  'x':'int','y':'int',
                  'delay':'real',
                  'fireX':'int',
                  'fireY':'int',
                  'message':'string',
                  'next':'Horde',
                  'monsters':'Monster[]'},
         'Monster':{'id':'string',
                    'type':'string'},
         'Item':{'type':'string',
                 'subType':'string',
                 'size':'int'},
         'Player':{'x':'int',
                   'y':'int'}}


# Defined methods (work only on lists) 
METHODS = {'add':getattr(list, 'append'),
           'remove':getattr(list, 'remove'),
           'index':getattr(list, 'index')}


# Symbol class
class Symbol(object):

    def __init__(self, _id, _type, value, dim=None):
        self.id = _id
        self.type = _type
        self.dim = dim
        self.value = value


# Class used for implement scopes
class Env(object):

    def __init__(self):
        self.globalScope = {}
        self.currScope = self.globalScope
        self.scopes = []
        self.scopes.append(self.globalScope)


    def push(self, obj=None):
        if obj is not None:
            self.scopes.append(obj)
        else:
            self.scopes.append({})
        self.currScope = self.scopes[-1]
        

    def pop(self):
        if self.currScope is self.globalScope:
            return self.globalScope
        self.currScope = self.scopes[-2]
        return self.scopes.pop()


    def add(self, name, obj):
        self.currScope[name] = obj

    
    def get(self, name):
        return self.currScope[name]


    def set(self, name, value):
        self.currScope[name] = value


    def search(self, name): 
        i = len(self.scopes)-1
        while i >= 0:
            tmp = self.scopes[i]
            try:
                return tmp[name]
            except KeyError:
                i-=1
                continue
        raise KeyError(name)


    # TODO: remove?
    def restore(self, scope):
        while self.currScope != scope:
            self.pop()


# Exceptions raised for execution errors
class HDLTypeError(Exception):

    def __init__(self, typeFound, typeExpected,
                 lineno, linepos):
        super(HDLTypeError, self).__init__()
        self.typeFound = typeFound
        self.typeExpected = typeExpected
        self.lineno = lineno
        self.linepos = linepos


    def __str__(self):
        return "Invalid type on %d:%d: expected %s, found %s" % \
            (self.lineno, self.linepos,
             self.typeExpected, self.typeFound)


class HDLAttrError(Exception):

    def __init__(self, _type, attrName, lineno, linepos,
                 isMethod=False):
        super(HDLAttrError, self).__init__()
        self.type = _type
        self.attrName = attrName
        self.lineno = lineno
        self.linepos = linepos
        self.isMethod = isMethod


    def __str__(self):
        if not self.isMethod:
            return "Invalid attribute on %d:%d: type %s has no attribute %s" % \
                (self.lineno, self.linepos,
                 self.type, self.attrName)
        else:
            return "Invalid method on %d:%d: type %s has no method %s" % \
                (self.lineno, self.linepos,
                 self.type, self.attrName)


class HDLIndexError(Exception):

    def __init__(self, index, lineno, linepos):
        super(HDLIndexError, self).__init__()
        self.index = index
        self.lineno = lineno
        self.linepos = linepos
        

    def __str__(self):
        return "Invalid index on %d:%d" % \
            (self.lineno, self.linepos)


class HDLNameError(Exception):

    def __init__(self, name, lineno, linepos):
        super(HDLNameError, self).__init__()
        self.name = name
        self.lineno = lineno
        self.linepos = linepos

    
    def __str__(self):
        return "Name error on %d:%d: no variable %s declared" % \
            (self.lineno, self.linepos, self.name)



# Abstract Syntax Tree nodes definition
class AstNode(object):

    def __init__(self, lineno, linepos, childs=None):
        self.lineno = lineno
        self.linepos = linepos
        if childs is not None:
            self.childs = childs
        else:
            self.childs = []

    def action(self, scope):
        for child in self.childs:
            child.action(scope)


class ProgramNode(AstNode):
    pass


class DeclNode(AstNode):
    
    def action(self, scope):
        _type = self.childs[0]
        name = self.childs[1]
        dim = self.childs[2]
        if dim is None:
            value = {}
            value.update(TYPES[_type])
            sym = Symbol(name, _type, value, dim)
            # Init fields
            for field,_type in sym.value.items():
                tmp = Symbol(field, _type, None)
                # Array field: init as an empty list
                if _type.endswith('[]'):
                    tmp.value = []
                sym.value[field]=tmp
        else:
            value = []
            _type += '[]'
            sym = Symbol(name, _type, value, dim)

        scope.add(name, sym)
        return sym


class AssignNode(AstNode):
    
    def action(self, scope):
        lvalNode = self.childs[0]
        rvalNode = self.childs[1]
        lval = lvalNode.action(scope)
        rval = rvalNode.action(scope)

        # Assignment as simple symbol-value copy
        if lval.type == rval.type:
            lval.value = rval.value
        else:
            raise HDLTypeError(rval.type, lval.type,
                               rvalNode.lineno,
                               rvalNode.linepos)


class LvalNode(AstNode):

    def action(self, scope):
        varNode = self.childs[0]
        var = varNode.action(scope)
        val = var
        return val


class RvalNode(AstNode):

    def action(self, scope):
        try:
            varNode = self.childs[0]
            var = varNode.action(scope)
            val = var

        except (TypeError, AttributeError):
            # TODO: how to (and where) handle types?
            value = self.childs
            if type(value) is int:
                _type = 'int'
            elif type(value) is float:
                _type = 'real'
            else:
                _type = 'string'

            val = Symbol("tmp", _type, value)
        
        return val


class VarNode(AstNode):

    def action(self, scope):
        varName = self.childs[0]
        varOffset = self.childs[1]
        try:
            val = scope.search(varName)
        except KeyError, e:
            raise HDLNameError(varName, 
                               self.lineno,
                               self.linepos)

        if varOffset is not None:
            try:
                if varOffset >= 0:
                    val = val.value[varOffset]
                else:
                    raise IndexError()
            except IndexError, e:
                raise HDLIndexError(varOffset,
                                    self.lineno,
                                    self.linepos+len(varName)+1)

        # Perform attribute lookup
        if self.childs[2] is not None:
            scope.push(val.value)
            attr = self.childs[2]
            try:
                val = attr.action(scope)
            except KeyError, e:
                raise HDLAttrError(val.type,
                                   attr.childs[0],
                                   attr.lineno,
                                   attr.linepos)
            scope.pop()

        return val


class AttrNode(AstNode):

    def action(self, scope):
        attrName = self.childs[0]
        attrOffset = self.childs[1]
        # Get attrName symbol from current scope
        val = scope.get(attrName)
        if attrOffset is not None:
            try:
                if attrOffset >= 0:
                    val = val.value[attrOffset]
                else:
                    raise IndexError()
            except IndexError, e:
                raise HDLIndexError(attrOffset,
                                    self.lineno,
                                    self.linepos+len(attrName)+1)

        if self.childs[2] is not None:
            # Perform next attribute lookup
            scope.push(val.value)
            attr = self.childs[2]
            try:
                val = attr.action(scope)
            except KeyError, e:
                raise HDLAttrError(val.type,
                                   attr.childs[0],
                                   attr.lineno,
                                   attr.linepos)
            # Restore the scope
            scope.pop()
        
        return val


class MethodCallNode(AstNode):

    def action(self, scope):
        methName = self.childs[0]
        methVar = self.childs[1][0]
        methArgs = self.childs[2]
        # Retrieve the variable symbol
        var = methVar.action(scope)
        # Retrieve the function
        try:
            method = METHODS[methName]
        except KeyError, e:
            methodLinepos = self.childs[1][-1].linepos + \
                len(var.id) + 1
            raise HDLAttrError(var.type, methName,
                               methVar.lineno,
                               #methVar.linepos,
                               methodLinepos,
                               True)
        # Retrive the args
        #args = [attr[0].action(scope) for attr in methArgs]
        # TODO: perform number-of-arguments checks???
        #args = []
        for arg in methArgs:
            argSym = arg.action(scope)
            if argSym.type != var.type[:-2]:
                raise HDLTypeError(argSym.type, var.type,
                                   arg.lineno, arg.linepos)
            #args.append(argSym)
            
            # and call the method for each arg
            method(var.value, argSym)

        # Finally, call the method
        #return method(var.value,
        #              *[arg for arg in args])
    

class PrintNode(AstNode):

    def action(self, scope):
        args = self.childs
        syms = [val.action(scope) for val in args]
        outStr = ''.join([str(sym.value)+' '
                          for sym in syms])[:-1]

        print outStr


class ForNode(AstNode):

    def action(self, scope):
        try:
            # List iterator
            var = self.childs[0].action(scope)
            symName = self.childs[1]
            sym = Symbol(symName, var.type[:-2], None)
            it = [s.value for s in var.value]

        except AttributeError:
            # Integers iterator
            it = self.childs[1]
            symName = self.childs[0]
            sym = Symbol(symName, "int", None)
        
        scope.push({})
        scope.add(symName, sym)
        code = self.childs[2:]
        for i in it:
            scope.get(symName).value = i
            for child in code:
                child.action(scope)

        scope.pop()


class CondNode(AstNode):
    
    def action(self, scope):
        v1 = self.childs[0]
        v2 = self.childs[1]
        op = self.childs[2]
        # Retrieve values
        val1 = v1.action(scope)
        # Apply operator on values
        if v2 is not None:
            # Binary operator
            val2 = v2.action(scope)
            try:
                retVal = op(val1.value, val2.value)
            except AttributeError:
                retVal = op(val1, val2)
        else:
            # Unary operator
            try:
                retVal = op(val1.value)
            except AttributeError:
                retVal = op(val1)

        return retVal


class IfNode(AstNode):

    def action(self, scope):
        cond = self.childs[0]
        trueBlock = self.childs[1]
        falseBlock = self.childs[2]
        if cond.action(scope):
            scope.push({})
            for stmt in trueBlock:
                stmt.action(scope)
            scope.pop()
        else:
            if falseBlock is not None:
                scope.push({})
                for stmt in falseBlock:
                    stmt.action(scope)
                scope.pop()
