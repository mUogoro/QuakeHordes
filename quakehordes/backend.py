#*************************************************
# backend_internals.py
#
#*************************************************
import logging
from sys import stdout, stderr
from math import sin, cos, pi
from backend_internals import *

# CONVERSION FACTOR
qToMeter = 0.0381

def MeterToQuake(x):
    return int(x/qToMeter)

# DEFAULT VALUES
MAP_WIDTH = 666
MAP_HEIGHT = 666
PLAYER_X = 0
PLAYER_Y = 0


# Validation logger
def initLogger(logFileName):
    logging.basicConfig(filename=logFileName,
                        filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s:%(filename)s:%(lineno)d: %(levelname)s - %(message)s')

    
def log(msg, _type='info'):
    logFunc = getattr(logging, _type)
    logFunc(msg)


class ValidationError(Exception):
    pass


class Map(object):

    DEFAULTS = {'type':'walled', 
                'width':666,
                'height':666}
    VALID = {'type':['cage', 'walled']}

    MATERIALS = {'walls_ground':('asphalt1', 8, 8 ),
                 'walls':('tile2', 16, 16),
                 'walls_exit':('metal1', 4, 8),
                 'cage_ground':('grass2', 4, 4),
                 'cage_bar':('wood1', 1, 1),
                 'cage_exit':('metal1', 1, 1)}

    def __init__(self, symbols):
        # Replace spaces with underscores in map names
        self.name = symbols['name'].value.replace(' ', '_')
        self.introMessage = symbols['introMessage'].value
        self.width = MeterToQuake(symbols['width'].value)
        self.height = MeterToQuake(symbols['height'].value)
        self.type = symbols['type'].value
        self.sNext = symbols['next'].value
        self.sHordes = [sym.value
                        for sym in symbols['hordes'].value]
        self.sPlayers = symbols['players'].value
        self.sItems = symbols['items'].value

        self.brushes = []
        self.players = []
        self.hordes = []
        self.items = []
        self.exitTrigger = None
        self.exit = []

    
    # Internals methods for brushes building
    def _buildCage(self):
        self.cage = []
        exitSize = 60
        # Build floor
        floorA = \
            Brush('floorA',
                  material=Map.MATERIALS['cage_ground'][0],
                  texX=Map.MATERIALS['cage_ground'][1],
                  texY=Map.MATERIALS['cage_ground'][2])
        floorA.scale(self.width/2-exitSize, self.height, 1)
        
        floorB = \
            Brush('floorB',
                  material=Map.MATERIALS['cage_ground'][0],
                  texX=Map.MATERIALS['cage_ground'][1],
                  texY=Map.MATERIALS['cage_ground'][2])
        floorB.scale(self.width/2-exitSize, self.height, 1)
        floorB.translate(self.width/2+exitSize, 0, 0)

        floorC = \
            Brush('floorC',
                  material=Map.MATERIALS['cage_ground'][0],
                  texX=Map.MATERIALS['cage_ground'][1],
                  texY=Map.MATERIALS['cage_ground'][2])
        floorC.scale(exitSize*2, self.height/2-exitSize, 1)
        floorC.translate(self.width/2-exitSize, 0, 0)
        
        floorD = \
            Brush('floorD',
                  material=Map.MATERIALS['cage_ground'][0],
                  texX=Map.MATERIALS['cage_ground'][1],
                  texY=Map.MATERIALS['cage_ground'][2])
        floorD.scale(exitSize*2, self.height/2-exitSize, 1)
        floorD.translate(self.width/2-exitSize,
                         self.height/2+exitSize, 0)

        self.cage.extend([floorA, floorB, floorC, floorD])

        # Build walls bars
        step = 32
        barWidth = 16
        barHeight = 16
        barLenght = 256
        n = 0
        for i in range(max(self.width, self.height)/step):
            if n <= self.width:
                brush1a = \
                    Brush('cage_0x_'+str(i),
                          material=Map.MATERIALS['cage_bar'][0],
                          texX=Map.MATERIALS['cage_bar'][1],
                          texY=Map.MATERIALS['cage_bar'][2])
                brush1a.scale(barWidth, barHeight, barLenght)
                brush1a.translate(n, 0, 0)
                brush1b = \
                    Brush('cage_yx_'+str(i),
                          material=Map.MATERIALS['cage_bar'][0],
                          texX=Map.MATERIALS['cage_bar'][1],
                          texY=Map.MATERIALS['cage_bar'][2])
                brush1b.scale(barWidth, barHeight, barLenght)
                brush1b.translate(n, self.height, 0)
                self.cage.append(brush1a)
                self.cage.append(brush1b)
            if n <= self.height:
                brush2a = \
                    Brush('cage_0y_'+str(i),
                          material=Map.MATERIALS['cage_bar'][0],
                          texX=Map.MATERIALS['cage_bar'][1],
                          texY=Map.MATERIALS['cage_bar'][2])
                brush2a.scale(barWidth, barHeight, barLenght)
                brush2a.translate(0, n, 0)
                brush2b = Brush('cage_xy_'+str(i),
                      material=Map.MATERIALS['cage_bar'][0],
                      texX=Map.MATERIALS['cage_bar'][1],
                      texY=Map.MATERIALS['cage_bar'][2])
                brush2b.scale(barWidth, barHeight, barLenght)
                brush2b.translate(self.width, n, 0)
                self.cage.append(brush2a)
                self.cage.append(brush2b)

            n += step
            if n > max(self.width, self.height)+step:
                break

        self.brushes.extend(self.cage)
            

    def _buildWalls(self):
        # Build floor
        self.brushes.append(\
            Brush(self.name+'_main_brush',
                  material=Map.MATERIALS['walls_ground'][0],
                  texX=Map.MATERIALS['walls_ground'][1],
                  texY=Map.MATERIALS['walls_ground'][2]))
        self.mainBrush = self.brushes[0]
        self.mainBrush.scale(self.width, self.height, 1.0)

        # Build walls
        exitSize = 60
        wall1 = Brush('wall_1',
                      material=Map.MATERIALS['walls'][0],
                      texX=Map.MATERIALS['walls'][1],
                      texY=Map.MATERIALS['walls'][2])
        wall1.scale(self.width, 16, 256)
        wall2 = Brush('wall_2',
                      material=Map.MATERIALS['walls'][0],
                      texX=Map.MATERIALS['walls'][1],
                      texY=Map.MATERIALS['walls'][2])
        wall2.scale(self.width, 16, 256)
        wall2.translate(0, self.height, 0)
        wall3 = Brush('wall_3',
                      material=Map.MATERIALS['walls'][0],
                      texX=Map.MATERIALS['walls'][1],
                      texY=Map.MATERIALS['walls'][2])
        wall3.scale(16, self.height/2-exitSize, 256)
        wall3.translate(self.width, 0, 0)
        wall4 = Brush('wall_4',
                      material=Map.MATERIALS['walls'][0],
                      texX=Map.MATERIALS['walls'][1],
                      texY=Map.MATERIALS['walls'][2])
        wall4.scale(16, self.height/2-exitSize, 256)
        wall4.translate(self.width,
                        self.height/2+exitSize , 0)
        wall5 = Brush('wall_5',
                      material=Map.MATERIALS['walls'][0],
                      texX=Map.MATERIALS['walls'][1],
                      texY=Map.MATERIALS['walls'][2])
        wall5.scale(16, self.height, 256)
        self.brushes.extend([wall1, wall2, wall3,
                             wall4, wall5])
           

    def _buildWallsExit(self):
        # Build exit door
        exitSize = 60
        _exit = Door('exit_trigger',
                      material=Map.MATERIALS['walls_exit'][0],
                      texX=Map.MATERIALS['walls_exit'][1],
                      texY=Map.MATERIALS['walls_exit'][2])
        _exit.scale(16, exitSize*2, 256)
        _exit.translate(self.width,
                        self.height/2-exitSize, 0)
        self.exit.append(_exit)

        # Build changelevel trigger
        if self.sNext is not None:
            nextMap = self.sNext
            nextMapName = nextMap['name'].value
        else:
            nextMapName = self.name

        chLevelTrig = ChangeLevelTrigger(nextMapName)
        chLevelTrig.brush.scale(1, exitSize*4, 256)
        chLevelTrig.brush.translate(self.width+25,
                                    self.height/2-exitSize,
                                    -25)
        self.exit.append(chLevelTrig)


    def _buildCageExit(self):
        # Build exit bars
        k = 20
        offset = 5
        exitSize = 60
        for i in range(0, (exitSize*2) / k):
            bar = Door('exit_trigger',
                      material=Map.MATERIALS['cage_exit'][0],
                      texX=Map.MATERIALS['cage_exit'][1],
                      texY=Map.MATERIALS['cage_exit'][2])
            bar.scale(10, exitSize*2, 10)
            bar.translate(self.width/2-exitSize+offset,
                          self.height/2-exitSize,
                          -10)
            offset += k
            self.exit.append(bar)

        # Build changelevel trigger
        if self.sNext is not None:
            nextMap = self.sNext
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
        # Check the map type
        if self.type == '':
            self.type = Map.DEFAULTS['type']
        elif self.type not in Map.VALID['type']:
            log("Invalid map type [%s] for map [%s]" % \
                    (self.type, self.name), 'warning')
            return False

        # Build players start point. If no player start
        # point is specified, define a default one
        if len(self.sPlayers) == 0:
            self.players.append(Player('%s_singleplayer' % \
                                           self.name,
                                       self.width/2,
                                       self.height/2, 25))

        else:
            playerName = self.name + '_singleplayer'
            playerX = MeterToQuake(\
                self.sPlayers[0].value['x'].value)
            playerY = MeterToQuake(\
                self.sPlayers[0].value['y'].value)
            self.players.append(Player(playerName,
                                       playerX,
                                       playerY,
                                       25))
            for playerSym in self.sPlayers[1:]:
                playerName = self.name + '_playercoop'
                playerX = MeterToQuake(\
                    playerSym.value['x'].value)
                playerY = MeterToQuake(\
                    playerSym.value['y'].value)
                self.players.append(Player(playerName,
                                           playerX,
                                           playerY,
                                           25, isCoop=True))

        y = 0
        validHordes = 0
        for hordeSym in self.sHordes:
            # Used for compute the initial position
            # of the horde (which is the horde position
            # first than the horde is teleported into
            # the map)
            x = 0
            y += 200
            z = -800

            if hordeSym is self.sHordes[-1]:
                # The last horde activates the exit doors
                lastHorde = True
            else:
                lastHorde = False

            i = self.sHordes.index(hordeSym)
            # If no id is specified for current horde,
            # define a new one
            if hordeSym['id'].value == '':
            #    hordeId = "%s_horde%d" % (self.name, i)
                log('%d-th horde of map [%s] has no unique id' % \
                        (i+1, self.name), 'error')
                return False
            else:
                hordeId = hordeSym['id'].value

            if i>0 and self.sHordes[i-1]['next'].value \
                    is not None:
                # The horde is not the first horde and
                # it's activated by the previous horde
                nMonst = \
                    len(self.hordes[i-1].monsters)
                horde = Horde(hordeId, hordeSym, self.name,
                              x, y, z,
                              isFired=True,
                              fireCount=nMonst,
                              fireExit=lastHorde)
            else:
                # The horde is activated by a player-touched
                # trigger
                horde = Horde(hordeId, hordeSym, self.name, 
                              x, y, z,
                              fireExit=lastHorde)
            
            if horde.setup(self.width, self.height):
                self.hordes.append(horde)

        if len(self.hordes) == 0:
            log("No valid hordes specified for map [%s]" % \
                    self.name, 'warning')
            return False

        # Add items
        i=0
        for item in self.sItems:
            it = Item('%s_%s%d' % \
                          (self.name,
                           item.value['type'].value, i),
                      item.value)
            if it.setup(self.width, self.height):
                self.items.append(it)

        # Finally, create the map brushes and the exit-door
        if self.type == 'cage':
            self._buildCage()
            self._buildCageExit()
        else:
            self._buildWalls()
            self._buildWallsExit()

        self.exitTrigger = \
            Trigger('exit',
                    self.width/2,
                    self.height/2,
                    isCounter=True,
                    count=len(self.hordes[-1].monsters))
        return True
        
    
    def __str__(self):
        # TODO: print some statistics here
        #       (date, author, etc.)
        retVal = '// Map %s\n{\n' % self.name
        retVal += '"classname" "worldspawn"\n'

        # Generate main brushes
        retVal += ''.join([str(brush)+'\n'
                           for brush in self.brushes])+'\n'
        

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
        
        # Generate items
        retVal += ''.join(str(item)
                          for item in self.items)

        return retVal



class Horde(object):

    def __init__(self, _id, symbols, mapName, x, y, z,
                 isFired=False, fireCount=0,
                 fireExit=False):
        self.id = _id
        self.x = MeterToQuake(symbols['x'].value)
        self.y = MeterToQuake(symbols['y'].value)
        self.fireX = MeterToQuake(symbols['fireX'].value)
        self.fireY = MeterToQuake(symbols['fireY'].value)
        self.message = symbols['message'].value
        self.realX = x
        self.realY = y
        self.realZ= z
        self.sNext = symbols['next'].value
        self.delay = symbols['delay'].value
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
        self.flames = []
        

    def _buildHordeFlames(self, firstHorde = True):
        if firstHorde:
            _type = 'flame_large_yellow'
        else:
            _type = 'flame_small_yellow'
        
        angle = 0.0
        angleStep = 0.52
        radius = 25
        x = self.fireX
        y = self.fireY
        for i in range(0,12):
            flameX = x + radius*cos(angle)
            flameY = y + radius*sin(angle)
            self.flames.append(Flame("%s_flame%d" % \
                                         (self.id, i),
                                     _type, 2, flameX, flameY, 0))
            angle += angleStep


    def setup(self, boundX, boundY):
        # Check if specified position is inside the map area
        if self.x > boundX or \
                self.y > boundY or \
                self.fireX > boundX or \
                self.fireY > boundY:
            log("Invalid position [(%d, %d)] specified for horde [%s]" % (self.x, self.y, self.id),
                'warning')
            return False

        # Set a default name for horde if no name was
        # specified
        if self.message == '':
            self.message = 'Fight the \'%s\' horde!!!' % \
                self.id

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
            # Horde triggered by the previous horde
            hordeTrigger = Trigger(self.id,
                                   self.x, self.y, 10,
                                   delay=self.delay,
                                   message=self.message,
                                   isCounter=True,
                                   count=self.fireCount)
        else:
            # Horde triggered when the player walk upon
            # a specific map position
            hordeTrigger = Trigger(self.id,
                                   delay=self.delay,
                                   message=self.message)
            hordeTrigger.brush.scale(20, 20, 1)
            hordeTrigger.translate(self.fireX,
                                   self.fireY, 1)
            
        self.hordeTrigger = hordeTrigger

        # Create monsters and their destinations
        angle = 0.0
        angleStep = 1.0
        xStep = 180
        yStep = 180
        i = 0

        nextHordeName = ''
        if self.fireExit:
            nextHordeName = 'exit'
        elif self.sNext is not None:
            nextHordeName = self.sNext['id'].value
        
        for monstSym in self.sMonsters:
            # Compute monsters' teleport destination
            x = xStep * cos(angle)
            y = yStep * sin(angle)
            i += 1

            # Get the monster id: if no id is specified,
            # define a unique id for the monster
            if monstSym['id'].value == '':
                monstId = '%s_monst%d' % (self.id, i)
            else:
                monstId = '%s%d' % (monstSym['id'].value, i)
            monster = Monster(monstId, monstSym, self.id,
                              self.x+x, self.y+y, 20,
                              self.realX,
                              self.realY,
                              self.realZ,
                              nextHordeName)

            # Setup the monster and add it to current horde
            if not monster.setup(boundX, boundY):
                continue
            self.monsters.append(monster)

            # Update data for next monster placement
            angle += angleStep
            self.realX += 100
            if angle >= 2*pi:
                angle = 0
                #xStep += xStep
                #yStep += yStep
                xStep += 80
                yStep += 80
                if angleStep != 0:
                    angleStep -= 0.2

        if len(self.monsters) > 0:
            if not self.isFired:
                self._buildHordeFlames()
            return True
        else:
            log("No valid monster specified for horde [%s]" % \
                    self.id, "warning")
            return False



    def __str__(self):
        # Horde trigger
        retVal = str(self.hordeTrigger)
        
        # Generate monsters
        retVal += '\n%s\n' % ''.join(
            [str(monster) for monster in self.monsters])

        # Generate flames
        retVal += ''.join([str(flame)
                           for flame in self.flames])

        return retVal


class Monster(object):

    VALID = {'type':['army', 'demon1', 'dog', 'enforcer',
                     'fish', 'hell_knight', 'knight',
                     'ogre', 'shalrath', 'shambler',
                     'tarbaby', 'wizard', 'zombie']}
    DEFAULTS = {'type':'army'}

    def __init__(self, _id, symbols, hordeName, x, y, z, 
                 realX, realY, realZ, nextHordeName=None):
        self.id = _id
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
        # Check monster type
        if self.type == '':
            # Not specified: init defaults
            self.type = Monster.DEFAULTS['type']
        elif self.type not in Monster.VALID['type']:
            # Wrong tyep specified: warn the user and
            # return false
            log("Invalid type [%s] of monster [%s] on horde [%s]" % \
                    (self.type,
                     self.id,
                     self.hordeName), "warning")
            return False
        return True


    def setup(self, boundX, boundY):
        # Check monster type
        if self.type == '':
            # Not specified: init defaults
            self.type = Monster.DEFAULTS['type']
        elif self.type not in Monster.VALID['type']:
            # Wrong tyep specified: warn the user and
            # return false
            log("Invalid type [%s] of monster [%s] on horde [%s]" % \
                    (self.type,
                     self.id,
                     self.hordeName), 'warning')
            return False

        # Check the monster position
        if self.x > (boundX-32) or \
                self.y > (boundY-32) or \
                self.x < 32 or \
                self.y < 32:
            log("Invalid position specified for monster [%s] of horde [%s]" % \
                    (self.id,
                     self.hordeName), 'warning')
            return False

        # Create the monster
        monster = \
            MonsterEntity(self.id, self.type,
                          self.realX+50,
                          self.realY+50,
                          self.realZ+25,
                          self.nextHordeName+'_fire')
        self.monstEntity = monster
        # Create monster teleport
        teleport = MonsterTeleport(self.id)
        teleport.brush = Brush(teleport.id + \
                                   '_teleport_brush')
        teleport.brush.scale(80, 80, 1)
        teleport.translate(self.realX+10,
                           self.realY+10,
                           self.realZ)
        self.teleport = teleport

        # Create the trigger
        trigger = MonsterTrigger(self.id,
                                 self.hordeName)
        trigger.brush = Brush(trigger.id + \
                                  '_trigger_brush')
        trigger.brush.translate(self.realX+10,
                                self.realY+10,
                                self.realZ + 100)
        self.trigger = trigger

        # Create the destination
        destination = MonsterDestination(self.id,
                                         self.x,
                                         self.y,
                                         self.z)
        self.destination = destination
        
        return True


    def __str__(self):
        retVal = '\n// Monster %s\n' % self.id
        retVal += str(self.teleport)
        retVal += str(self.monstEntity)
        retVal += str(self.trigger)
        retVal += str(self.destination)
        
        return retVal


class Item(object):

    VALID = {'type':{'health':[],
                      'armor':[],
                      'ammo':['cells', 'rockets',
                              'sheels', 'spikes'],
                      'artifact':['invisibility',
                                  'invulnerability',
                                  'super_damage'],
                      'weapon':['grenadelauncher',
                                'lightning',
                                'nailgun',
                                'rocketlauncher',
                                'supernailgun',
                                'supershotgun']},
             'size':['small', 'medium', 'big']}
    DEFAULTS = {'type':'health', 'size':'medium'}

    def __init__(self, _id, symbols):
        self.id = _id
        self.type = symbols['type'].value
        self.subType = symbols['subType'].value
        self.size = symbols['size'].value
        self.x = MeterToQuake(symbols['x'].value)
        self.y = MeterToQuake(symbols['y'].value)
        self.item = None
        

    def setup(self, boundX, boundY):
        # Check position
        if self.x > boundX or \
                self.y > boundY:
            log("Invalid position [(%d, %d)] for item [%s]" % \
                    (self.x, self.y, self.id), 'warning')
            return False

        # Check type, subType and size. If no type is
        # specified, init the item as a medium health-pack
        if self.type == '':
            self.type = 'health'
            self.size = 'medium'
            self.item = Health(self.id, self.size,
                               self.x, self.y, 25)
            return True

        # Setup health item
        elif self.type == 'health':
            if not self.size in Item.VALID['size']:
                log("Invalid size [%s] for health [%s]" % \
                        (self.id, self.size), 'warning')
                return False
            self.item = Health(self.id, self.size,
                               self.x, self.y, 25)

        # Setup armor item
        elif self.type == 'armor':
            if not self.size in Item.VALID['size']:
                log("Invalid size [%s] for ammo [%s]" % \
                        (self.size, self.id), 'warning')
                return False
            self.item = Armor(self.id, self.size,
                              self.x, self.y, 25)
        
        # Setup artifact item
        elif self.type == 'artifact':
            if not self.subType in \
                    Item.VALID['type']['artifact']:
                log("Invalid sub-type [%s] for artifact [%s]" % \
                        (self.subType, self.id), 'warning')
                return False
            self.item = Artifact(self.id, self.subType,
                                 self.x, self.y, 25)

        # Setup ammo item
        elif self.type == 'ammo':
            if self.size == '':
                self.size == 'medium'
            elif not self.size in Item.VALID['size']:
                log("Invalid size [%s] for ammo [%s]" % \
                        (self.size, self.id),
                    'warning')
                return False
            
            if self.subType == '':
                self.subType == 'sheels';
            elif not self.subType in \
                    Item.VALID['type']['ammo']:
                log("Invalid sub-type [%s] for ammo [%s]" %  \
                        (self.subType, self.id), 'warning')
                return False
            self.item = Ammo(self.id, self.subType,         
                             self.size, self.x, self.y, 25)

        # Setup weapon item
        elif self.type == 'weapon':
            if not self.subType in \
                    Item.VALID['type']['weapon']:
                log("Invalid sub-type [%s] for weapon [%s]" % \
                        (self.subType, self.id), 'warning')
                return False
            self.item = Weapon(self.id, self.subType,
                               self.x, self.y, 25)
        
        else:
            log("Invalid type [%s] for item [%s]" % \
                    (self.type, self.id),
                'warning')
            return False

        return True


    def __str__(self):
        return str(self.item)
