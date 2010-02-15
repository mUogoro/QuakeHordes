#*************************************************
# backend_internals.py
#
#*************************************************
from math import sin, cos, pi
from backend_internals import *


class Map(object):

    def __init__(self, symbols):
        self.name = symbols['name'].value
        self.introMessage = symbols['introMessage'].value
        self.difficult = symbols['difficult'].value
        self.width = symbols['width'].value
        self.height = symbols['height'].value
        self.sNext = symbols['next'].value
        self.sHordes = [sym.value
                        for sym in symbols['hordes'].value]
        self.sPlayers = symbols['players'].value

        self.brushes = []
        self.players = []
        self.hordes = []


    def validate(self):
        return True


    def setup(self):
        self.brushes.append(Brush(self.name+'_main_brush'))
        self.mainBrush = self.brushes[0]
        self.mainBrush.scale(self.width, self.height, 1.0)

        for playerSym in self.sPlayers:
            playerName = self.name + '_player1'
            playerX = playerSym.value['x'].value
            playerZ = playerSym.value['z'].value
            self.players.append(Player(playerName,
                                       playerX,
                                       playerZ,
                                       25))

        y = 0
        for hordeSym in self.sHordes:
            #hordeName = '%s_%s' % \
            #    (self.name, hordeSym.value['id'].value)
            x = 0
            y += 200
            z = -400
            
            i = self.sHordes.index(hordeSym)
            if i>0 and \
                    self.sHordes[i-1]['next'].value is not None:
                count = len(self.sHordes[i-1]['monsters'].value)
                horde = Horde(hordeSym, self.name, x, y, z,
                              isFired=True,
                              fireCount=count)
            else:
                horde = Horde(hordeSym, self.name, x, y, z)
            horde.setup()
            self.hordes.append(horde)
        
    
    def __str__(self):
        # TODO: print some statistics here
        #       (date, author, etc.)
        retVal = '// Map %s\n{\n' % self.name
        retVal += '"classname" "worldspawn"\n'

        # Generate main brush
        retVal += ''.join([str(brush)
                           for brush in self.brushes])
        # Generate all hordes support brushes
        retVal += \
            ''.join(['\n// %s support brush\n%s' % 
                     (horde.id, str(horde.supBrush))
                     for horde in self.hordes])
        retVal += '\n}\n'

        # Generate hordes
        retVal += \
            ''.join([str(horde) for horde in self.hordes])
        retVal += '\n'

        # Generate player start points
        retVal += ''.join([str(player)
                           for player in self.players])
        retVal += '\n'
        
        return retVal



class Horde(object):

    def __init__(self, symbols, mapName, x, y, z,
                 isFired=False, fireCount=0):
        self.id = symbols['id'].value
        self.x = symbols['x'].value
        self.z = symbols['z'].value
        self.realX = x
        self.realY = y
        self.realZ = z
        self.sNext = symbols['next'].value
        self.delay = symbols['delay'].value
        self.fireX = symbols['fireX'].value
        self.fireZ = symbols['fireZ'].value
        self.sMonsters = \
            [sym.value
             for sym in symbols['monsters'].value]
        self.isFired = isFired
        self.fireCount = fireCount

        self.nMonsters = len(self.sMonsters)
        self.monsters = []
        self.supBrush = None
        self.hordeTrigger = None
        
    
    def validate(self):
        return True


    def setup(self):
        # Create the supporting surface
        supBrush = Brush(self.id + '_brush')
        # Each monster has a 100x100 support area
        supBrush.scale(self.nMonsters*100, 100, 1)
        supBrush.translate(self.realX,
                           self.realY,
                           self.realZ)
        self.supBrush = supBrush

        # Create the horde trigger
        if self.isFired:
            hordeTrigger = HordeTrigger(self.id,
                                        isCounter=True,
                                        count=self.fireCount)
        else:
            hordeTrigger = HordeTrigger(self.id)
            hordeTrigger.brush.scale(20, 20, 1)
        hordeTrigger.translate(self.x, self.z, 1)
        self.hordeTrigger = hordeTrigger

        # Create monsters and their destinations
        angle = 0.0
        angleStep = 0.8
        xStep = 100
        yStep = 100

        i = 0

        nextHordeName = ''
        if self.sNext is not None:
            nextHordeName = self.sNext['id'].value
        for monstSym in self.sMonsters:
            # TODO: compute here monster destination
            #       (teleport) coordinates based on
            #       a user specified formation (triangular,
            #       circular etc.)

            x = xStep * cos(angle)
            y = yStep * sin(angle)
            
            #print "monst:", x, y

            angle += angleStep
            if angle >= 2*pi:
                angle = 0
                xStep += xStep
                yStep += yStep

            # TODO: how to manage monsters with same name
            monstSym['id'].value += str(i)
            monster = Monster(monstSym, self.id,
                              self.x+x, self.z+y, 20,
                              self.realX,
                              self.realY,
                              self.realZ,
                              nextHordeName)
            
            i += 1
            self.realX += 100

            monster.setup()
            self.monsters.append(monster)


    def __str__(self):
        # Horde trigger
        retVal = str(self.hordeTrigger)
        
        # Generate monsters
        retVal += '\n%s\n' % ''.join(
            [str(monster) for monster in self.monsters])

        return retVal


class Monster(object):

    def __init__(self, symbols, hordeName, x, y, z, 
                 realX, realY, realZ, nextHordeName=None):
        self.id = symbols['id'].value
        self.type = symbols['type'].value
        self.hordeName = hordeName
        self.x = x
        self.y = y
        self.z = z
        self.realX = realX
        self.realY = realY
        self.realZ = realZ
        self.nextHordeName = nextHordeName
        
        self.trigger = None
        self.teleport = None
        self.destination = None
        self.monstEntity = None


    def validate(self):
        return True


    def setup(self):
        # Create the monster
        monsterName = '%s_%s' % (self.hordeName, self.id)
        monster = MonsterEntity(monsterName, self.type,
                                self.realX+50,
                                self.realY+50,
                                self.realZ+25,
                                self.nextHordeName)
        self.monstEntity = monster
        # Create monster teleport
        teleport = MonsterTeleport(monsterName)
        teleport.brush = Brush(teleport.id + \
                                   '_teleport_brush')
        teleport.brush.scale(80, 80, 1)
        teleport.translate(self.realX+10,
                           self.realY+10,
                           self.realZ)
        self.teleport = teleport

        # Create the trigger
        trigger = MonsterTrigger(monsterName,
                                 self.hordeName)
        trigger.brush = Brush(trigger.id + \
                                  '_trigger_brush')
        trigger.brush.translate(self.realX+10,
                                self.realY+10,
                                self.realZ + 100)
        self.trigger = trigger

        # Create the destination
        destination = MonsterDestination(monsterName,
                                         self.x,
                                         self.y,
                                         self.z)
        self.destination = destination
        


    def __str__(self):
        retVal = '\n// Monster %s\n' % self.id
        retVal += str(self.teleport)
        retVal += str(self.monstEntity)
        retVal += str(self.trigger)
        retVal += str(self.destination)
        
        return retVal

