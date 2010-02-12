#*************************************************
# parser_internals.py
#
#*************************************************

#TODO: included only for debug purposes: remove
import traceback
import operator

# Defined types
# TODO: defines basic types to? (maybe useful for type checking... >_>)
TYPES = {'Map': {'name':'string',
                 'introMessage':'string',
                 'difficult':'string',
                 'width':'int',
                 'height':'int',
                 'next':'Map',
                 'hordes':'Horde[]'},
         'Horde':{'id':'string',
                  'x':'int','y':'int',
                  'delay':'real',
                  'fireX':'int',
                  'fireY':'int',
                  'message':'string',
                  'monsters':'Monster[]',
                  'next':'Horde'},
         'Monster':{'id':'string',
                    'type':'string'},
         'Player':{'x':'int',
                   'y':'int'}}


METHODS = {'add':getattr(list, 'append'),
           'remove':getattr(list, 'remove'),
           'index':getattr(list, 'index')}


class Symbol(object):

    def __init__(self, _id, _type, value, dim=None):
        self.id = _id
        self.type = _type
        self.dim = dim
        self.value = value


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
        # TODO: where perform type checking?
        self.currScope[name] = value

    def search(self, name):
        # TODO: better exception 
        i = len(self.scopes)-1
        while i >= 0:
            tmp = self.scopes[i]
            try:
                return tmp[name]
            except Exception:
                i-=1
                continue
        raise AttributeError("Not found %s" % name)
                
    def restore(self, scope):
        while self.currScope != scope:
            self.pop()


class AstNode(object):

    def __init__(self, lineNo, linePos, childs=None):
        self.lineNo = lineNo
        self.linePos = linePos
        if childs is not None:
            self.childs = childs
        else:
            self.childs = []

    def action(self, scope):
        for child in self.childs:
            child.action(scope)


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
        lval.value = rval.value


class LvalNode(AstNode):

    def action(self, scope):
        varNode = self.childs[0]
        var = varNode.action(scope)
        val = var

        # Here a symbol must be returned!!!
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
        val = scope.search(varName)
        if varOffset is not None:
            val = val.value[varOffset]

        # Perform attribute lookup
        if self.childs[2] is not None:
            scope.push(val.value)
            attr = self.childs[2]
            val = attr.action(scope)
            scope.pop()

        return val


class AttrNode(AstNode):

    def action(self, scope):
        attrName = self.childs[0]
        attrOffset = self.childs[1]
        # Get attrName symbol from current scope
        val = scope.get(attrName)
        if attrOffset is not None:
            val = val.value[attrOffset]

        if self.childs[2] is not None:
            # Perform next attribute lookup
            scope.push(val.value)
            attr = self.childs[2]
            val = attr.action(scope)
            # Restore the scope
            scope.pop()
        
        return val


class MethodCallNode(AstNode):

    def action(self, scope):
        methName = self.childs[0]
        methVar = self.childs[1][0]
        methArgs = self.childs[2]
        methVar.action(scope)
        # Retrieve the function
        method = METHODS[methName]
        # Retrieve the variable symbol
        var = methVar.action(scope)
        # Retrive the args
        args = [attr[0].action(scope) for attr in methArgs]
        # Finally, call the method
        return method(var.value,
                      *[arg for arg in args])
    

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
