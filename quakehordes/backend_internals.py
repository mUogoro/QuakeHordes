#*************************************************
# backend_internals.py
#
#*************************************************
from math import sqrt
from numpy import *

class Brush(object):
        
    def __init__(self, _id, material=None, planes=None):
        self.id = _id
        if material is None:
            self.material = "NULL"
        else:
            self.material = material
        if planes is not None:
            self.planes = planes
        else:
            self.planes = [
                [array([1, 1, 1, 1]), array([1, 0, 1, 1]),
                 array([0, 1, 1, 1])],
                [array([1, 1, 1, 1]), array([0, 1, 1, 1]),
                 array([1, 1, 0, 1])],
                [array([1, 1, 1, 1]), array([1, 1, 0, 1]),
                 array([1, 0, 1, 1])],
                [array([0, 0, 0, 1]), array([1, 0, 0, 1]),
                 array([0, 1, 0, 1])],
                [array([0, 0, 0, 1]), array([0, 0, 1, 1]),
                 array([1, 0, 0, 1])],
                [array([0, 0, 0, 1]), array([0, 1, 0, 1]),
                 array([0, 0, 1, 1])]
                ]


    def scale(self, x, y, z):
        scaleMat = array([[x, 0, 0, 0],
                          [0, y, 0, 0],
                          [0, 0, z, 0],
                          [0, 0, 0, 1]])
        for plane in self.planes:
            plane[0] = dot(plane[0], scaleMat)
            plane[1] = dot(plane[1], scaleMat)
            plane[2] = dot(plane[2], scaleMat)

    
    def translate(self, x, y, z):
        transMat = array([[1, 0, 0, 0],
                          [0, 1, 0, 0],
                          [0, 0, 1, 0],
                          [x, y, z, 1]])
        for plane in self.planes:
            plane[0] = dot(plane[0], transMat)
            plane[1] = dot(plane[1], transMat)
            plane[2] = dot(plane[2], transMat)      


    def __str__(self):
        retVal = '{\n'
        for plane in self.planes:
            retVal += ''.join(['( %d %d %d ) ' % (v[0], v[1], v[2])
                               for v in plane])
            retVal += '%s 0 0 0 1 1\n' % self.material
        return retVal + '}'


class MovableEntity(object):

    def __init__(self, _id, x=None, y =None, z=None):
        self.id = _id
        if x is not None and \
                y is not None and z is not None:
            self.pos = array([x, y, z, 1])
        else:
            self.pos = array([25, 25, 25, 1])
        

    def translate(self, x, y, z):
        transMat = array([[1, 0, 0, x],
                          [0, 1, 0, y],
                          [0, 0, 1, z],
                          [0, 0, 0, 1]])
        self.pos = dot(self.pos, transMat)



class Door(Brush):

    def __str__(self):
        retVal = '''
{
"classname" "func_door"
"targetname" "%s"
"angle" "90"
"wait" "-1"
''' % self.id
        retVal += super(Door, self).__str__()
        retVal += '\n}\n'
        return retVal


class Player(MovableEntity):

    def __init__(self, _id, x=None, y=None, z=None,
                 isCoop=False):
        super(Player, self).__init__(_id, x, y, z)
        self.isCoop = isCoop


    def __str__(self):
        if not self.isCoop:
            retVal = '''{
"classname" "info_player_start"
"origin" "%d %d %d"
}
''' % (self.pos[0], self.pos[1], self.pos[2])
        else:
            retVal = '''{
"classname" "info_player_coop"
"origin" "%d %d %d"
}
''' % (self.pos[0], self.pos[1], self.pos[2])            
        return retVal



class Trigger(MovableEntity):

    def __init__(self, _id, x=None, y=None, z=None,
                 isCounter=False, count=0):
        super(Trigger, self).__init__(_id, x, y, z)
        self.brush = Brush(self.id+"_brush")
        self.isCounter = isCounter
        self.count = count


    def translate(self, x, y, z):
        super(Trigger, self).translate(x, y, z)
        self.brush.translate(x, y, z)


    def __str__(self):
        if self.isCounter is False:
            retVal = '''{
"classname" "trigger_once"
"target" "%s_trigger"
%s
}
''' % (self.id, str(self.brush))
        else:
            retVal = '''{
"classname" "trigger_counter"
"origin" "%d %d %d"
"target" "%s_trigger"
"targetname" "%s_fire"
"spawnflags" "1"
"count" "%d"
}
''' % (self.pos[0], self.pos[1], self.pos[2],
       self.id, self.id, self.count)
        return retVal


class ChangeLevelTrigger(MovableEntity):

    def __init__(self, _id, x=None, y=None, z=None):
        super(ChangeLevelTrigger, self).__init__(_id,
                                                 x, y, z)
        self.brush = Brush(self.id+"_brush")


    def translate(self, x, y, z):
        super(ChangeLevelTrigger, self).translate(x, y, z)
        self.brush.translate(x, y, z)


    def __str__(self):
        retVal = '''{
"classname" "trigger_changelevel"
"map" "%s"
%s
}
''' % (self.id, str(self.brush))
        return retVal


class MonsterTrigger(MovableEntity):
    
    def __init__(self, _id, hordeName,
                 x=None, y=None, z=None):
        super(MonsterTrigger, self).__init__(_id, x, y, z)
        self.hordName = hordeName
        self.brush = Brush(self.id+"_brush")
    

    def translate(self, x, y, z):
        super(MonsterTrigger, self).translate(x, y, z)
        self.brush.translate(x, y, z)


    def __str__(self):
        retVal = '''{
"classname" "trigger_once"
"targetname" "%s_trigger"
"target" "%s_teleport"
"spawnflags" "1"
%s
}
''' % (self.hordName, self.id, str(self.brush))
        return retVal



class MonsterTeleport(MovableEntity):

    def __init__(self, _id, x=None, y=None, z=None,
                 brush=None):
        super(MonsterTeleport, self).__init__(_id, x, y, z)
        self.brush = brush

    
    def translate(self, x, y, z):
        super(MonsterTeleport, self).translate(x, y, z)
        self.brush.translate(x, y, z)


    def __str__(self):
        retVal = '''{
"classname" "trigger_teleport"
"target" "%s_destination"
"targetname" "%s_teleport"
// brush
%s
}
''' % (self.id, self.id, str(self.brush))
        return retVal



class MonsterDestination(MovableEntity):

    def __str__(self):
        retVal = '''{
"classname" "info_teleport_destination"
"origin" "%d %d %d"
"angle" "0.0"
"targetname" "%s_destination"
}
''' % (self.pos[0], self.pos[1], self.pos[2], self.id)
        return retVal


class MonsterEntity(MovableEntity):

    def __init__(self, _id, _type, 
                 x=None, y=None, z=None,
                 target=None):
        super(MonsterEntity, self).__init__(_id, x, y, z)
        self.type = _type
        self.target = target
    

    def __str__(self):
        retVal = '''{
"classname" "monster_%s"
"origin" "%s %s %s"
"spawnflags" "1"
"target" "%s"
}
''' % (self.type, self.pos[0], self.pos[1], self.pos[2],
       self.target)
        return retVal

