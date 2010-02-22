#*************************************************
# backend_internals.py
#
#*************************************************
from math import sin, cos, pi
from backend_internals import *

# DEFAULT VALUES
MAP_WIDTH = 666
MAP_HEIGHT = 666
PLAYER_X = 0
PLAYER_Y = 0

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
        self.sItems = symbols['items'].value

        self.brushes = []
        self.players = []
        self.hordes = []
        self.exitTrigger = None
        self.exit = []


    def validate(self):
        # Check if:
        # - almost one horde is specified
        # - almost one specified horde is valid

        # Define default values for undefined attributes
        #if self.width is None:
        #    self.width = MAP_WIDTH
        #if self.height is None:
        #    self.height = MAP_HEIGHT
        #if self.introMessage is None:
        #    pass

        return True

    
    def _buildCage(self):
        self.cage = []
        exitSize = 60
        # Build floor
        floorA = Brush('floorA')
        floorA.scale(self.width/2-exitSize, self.height, 1)
        
        floorB = Brush('floorB')
        floorB.scale(self.width/2-exitSize, self.height, 1)
        floorB.translate(self.width/2+exitSize, 0, 0)

        floorC = Brush('floorC')
        floorC.scale(exitSize*2, self.height/2-exitSize, 1)
        floorC.translate(self.width/2-exitSize, 0, 0)
        
        floorD = Brush('floorD')
        floorD.scale(exitSize*2, self.height/2-exitSize, 1)
        floorD.translate(self.width/2-exitSize,
                         self.height/2+exitSize, 0)

        self.cage.extend([floorA, floorB, floorC, floorD])


        # Build walls bars
        step = 50
        barWidth = 20
        barHeight = 20
        barLenght = 200
        n = 0
        for i in range(max(self.width, self.height)/step):
            if n < self.width:
                brush1a = Brush('cage_0x_'+str(i),
                                material='wood')
                brush1a.scale(barWidth, barHeight, barLenght)
                brush1a.translate(n, 0, 0)
                brush1b = Brush('cage_yx_'+str(i),
                                material='wood')
                brush1b.scale(barWidth, barHeight, barLenght)
                brush1b.translate(n, self.height, 0)
                self.cage.append(brush1a)
                self.cage.append(brush1b)
            if n < self.height:
                brush2a = Brush('cage_0y_'+str(i),
                                material='wood')
                brush2a.scale(barWidth, barHeight, barLenght)
                brush2a.translate(0, n, 0)
                brush2b = Brush('cage_xy_'+str(i),
                                material='wood')
                brush2b.scale(barWidth, barHeight, barLenght)
                brush2b.translate(self.width, n, 0)
                self.cage.append(brush2a)
                self.cage.append(brush2b)

            n += step
            if n > max(self.width, self.height):
                break

        self.brushes.extend(self.cage)
            

    def _buildWalls(self):
        # Build floor
        self.brushes.append(Brush(self.name+'_main_brush',
                                  material='grass2'))
        self.mainBrush = self.brushes[0]
        self.mainBrush.scale(self.width, self.height, 1.0)

        # Build walls
        wall1 = Brush('wall_0x')
        wall1.scale(self.width, 16, 256)
        wall2 = Brush('wall_xx')
        wall2.scale(self.width, 16, 256)
        wall2.translate(0, self.height, 0)
        wall3 = Brush('wall_xy')
        wall3.scale(16, self.height, 256)
        wall3.translate(self.width, 0, 0)
        wall4 = Brush('wall_0y')
        wall4.scale(16, self.height, 256)
        self.brush.extend([wall1, wall2, wall3, wall4])
           

    def _buildWallExit(self):
        pass


    def _buildCageExit(self):
        # Build exit bars
        k = 20
        offset = 5
        exitSize = 60
        for i in range(0, (exitSize*2) / k):
            bar = Door('exit_trigger')
            bar.scale(10, exitSize*2, 10)
            bar.translate(self.width/2-exitSize+offset,
                          self.height/2-exitSize,
                          -10)
            offset += k
            self.exit.append(bar)

        # Build changelevel trigger
        if self.sNext is not None:
            nextMap = self.sNext.value
            nextMapName = nextMap['name'].value
        else:
            nextMapName = self.name

        chLevelTrig = ChangeLevelTrigger(nextMapName)
        chLevelTrig.brush.scale(exitSize*4, exitSize*4, 1)
        chLevelTrig.brush.translate(self.width/2-exitSize,
                                    self.height/2-exitSize,
                                    -25)
        self.exit.append(chLevelTrig)
                                             


    def setup(self):
        # TODO: better map generation?
        self._buildCage()
        self._buildCageExit()
        #self._buildWalls()

        for playerSym in self.sPlayers:
            playerName = self.name + '_player1'
            playerX = playerSym.value['x'].value
            playerY = playerSym.value['y'].value
            self.players.append(Player(playerName,
                                       playerX,
                                       playerY,
                                       25))

        y = 0
        for hordeSym in self.sHordes:
            #hordeName = '%s_%s' % \
            #    (self.name, hordeSym.value['id'].value)
            x = 0
            y += 200
            z = -400

            if hordeSym is self.sHordes[-1]:
                # The last horde activates the 
                # final-level door
                lastHorde = True
            else:
                lastHorde = False

            i = self.sHordes.index(hordeSym)
            if i>0 and \
                    self.sHordes[i-1]['next'].value is not None:
                count = len(self.sHordes[i-1]['monsters'].value)
                horde = Horde(hordeSym, self.name, x, y, z,
                              isFired=True,
                              fireCount=count,
                              fireExit=lastHorde)
            else:
                horde = Horde(hordeSym, self.name, x, y, z,
                              fireExit=lastHorde)
            horde.setup()
            self.hordes.append(horde)

        # Finally, create exit-door
        self.exitTrigger = Trigger('exit',
                                   self.width/2,
                                   self.height/2,
                                   isCounter=True,
                                   count=len(self.sHordes[-1]['monsters'].value))
        
        
    
    def __str__(self):
        # TODO: print some statistics here
        #       (date, author, etc.)
        retVal = '// Map %s\n{\n' % self.name
        retVal += '"classname" "worldspawn"\n'

        # Generate main brush
        retVal += ''.join([str(brush)+'\n'
                           for brush in self.brushes])+'\n'

        # Generate cage
        #retVal += ''.join([str(brush)+'\n'
        #                   for brush in self.cage])
        # Generate walls
        #retVal += ''.join([str(brush)+'\n'
        #                   for brush in self.walls])
        

        # Generate all hordes support brushes
        retVal += \
            ''.join(['\n// %s support brush\n%s' % 
                     (horde.id, str(horde.supBrush))
                     for horde in self.hordes])
        retVal += '\n}\n'

        # Generate exit doors
        retVal += \
            ''.join([str(door)+'\n'
                     for door in self.exit])

        # Generate exit trigger
        retVal += str(self.exitTrigger) + '\n'

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
                 isFired=False, fireCount=0,
                 fireExit=False):
        self.id = symbols['id'].value
        self.x = symbols['x'].value
        self.y = symbols['y'].value
        self.realX = x
        self.realY = y
        self.realZ= z
        self.sNext = symbols['next'].value
        self.delay = symbols['delay'].value
        self.fireX = symbols['fireX'].value
        self.fireY = symbols['fireY'].value
        self.sMonsters = \
            [sym.value
             for sym in symbols['monsters'].value]
        self.isFired = isFired
        self.fireCount = fireCount
        self.fireExit = fireExit

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
            hordeTrigger = Trigger(self.id,
                                   self.x, self.y, 10,
                                   isCounter=True,
                                   count=self.fireCount)
        else:
            hordeTrigger = Trigger(self.id)
            hordeTrigger.brush.scale(20, 20, 1)
            hordeTrigger.translate(self.fireX,
                                   self.fireY, 1)
        self.hordeTrigger = hordeTrigger

        # Create monsters and their destinations
        angle = 0.0
        angleStep = 0.8
        xStep = 100
        yStep = 100

        i = 0

        nextHordeName = ''
        if self.fireExit:
            nextHordeName = 'exit'
        elif self.sNext is not None:
            nextHordeName = self.sNext['id'].value
        
        # Compute monsters' teleport destination
        for monstSym in self.sMonsters:
            x = xStep * cos(angle)
            y = yStep * sin(angle)

            angle += angleStep
            if angle >= 2*pi:
                angle = 0
                #xStep += xStep
                #yStep += yStep
                xStep += 80
                yStep += 80
                if angleStep != 0:
                    angleStep -= 0.2


            # TODO: how to manage monsters with same name
            monstSym['id'].value += str(i)
            monster = Monster(monstSym, self.id,
                              self.x+x, self.y+y, 20,
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
        monster = \
            MonsterEntity(monsterName, self.type,
                          self.realX+50,
                          self.realY+50,
                          self.realZ+25,
                          self.nextHordeName+'_fire')
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

