#!/usr/bin/python

import sys
from os import mkdir, chdir, path, environ, listdir
from subprocess import Popen, PIPE
from optparse import OptionParser
from datetime import datetime
from shutil import copy2


#from quakehordes import ENV, parser, Map
from quakehordes import ENV, Map, BuildQHDLParser
from quakehordes import \
    QHDLLexError, QHDLSyntaxError, \
    QHDLTypeError, QHDLAttrError, QHDLIndexError, \
    QHDLNameError
from quakehordes import initLogger, log


def Build(_map):
    # Obtain the .map code
    if not _map.setup():
        return False
    outMap = str(_map)
    
    # Get the current platform and run the appropriate
    # compiler
    platform = sys.platform
    if platform == 'linux2':
        exe = 'hmap2'
    elif platform == 'win32':
        exe = 'hmap2.exe'
    else:
        log('Unknown or unsupported platform [%s]' % \
                platform, 'error')
        return False

    # Save the compiled map
    with open(_map.name+'.map', 'w') as f:
        f.write(outMap)

    # Finally, compile map
    pCompiler = Popen([exe, _map.name+'.map'],
                      stdout=PIPE, stderr=PIPE)
    pCompiler.wait()
    pExit = pCompiler.communicate()

    if pCompiler.returncode != 0:
        # Map compilation fails!!!
        log('Map compilation fails!!! Error:\n\n%s\n' % \
                pExit[1], 'error')
        return False
    else:
        log('Map compilation success!!!', 'info')

    return True


def Install(_map, installPath):
    try:
        stuffsDir = environ['QUAKEHORDES_STUFFS']
        # Create maps and textures directory if it doesn't exist
        texsInstPath = path.join(installPath, 'textures')
        mapInstPath = path.join(installPath, 'maps')
        if not path.exists(texsInstPath):
            mkdir(texsInstaPath)
        if not path.exists(mapInstPath):
            mkdir(mapInstPath)
        
        # Copy textures
        texsDir = path.join(stuffsDir, 'textures')
        for tex in listdir(texsDir):
            if not path.exists(path.join(texsInstPath,
                                         tex)):
                copy2(path.join(texsDir, tex), texsInstPath)

        # Copy map
        copy2(_map.name+'.bsp', mapInstPath)
    
        log('Map [%s] successfully installed on path [%s]' %\
                (_map.name, installPath), 'info')
        return True

    except KeyError, e:
        log('Installation on path [%s] fails (maybe QUAKEHORDES_STUFFS environment variable unset???): %s' %\
                (installPath, e), 'error')
        return False

    except OSError, e:
        log('Installation on path [%s] fails: %s' % \
                (installPath, e), 'error')
        return False


def ParseCmdLine():
    # Init the command-line parser
    usage = 'usage: QuakeHordes.py src.hq'
    cmdlineParser = OptionParser(usage=usage)
    cmdlineParser.add_option('-I', '--install-path',
                             help='installation path',
                             dest='installPath')
    cmdlineParser.add_option('-W', '--work-dir',
                             help='working directory',
                             dest='workDir')
    return cmdlineParser.parse_args()


# TO DO: how manage build errors?
def main():
    cmdLineArgs = ParseCmdLine()
    sources = cmdLineArgs[1]
    installPath = cmdLineArgs[0].installPath
    workDir = cmdLineArgs[0].workDir

    builtMaps = 0
    for src in sources:
        i = 1
        # Parse and execute each specified file
        with open(src, 'r') as f:

            # Move to working dir. If no working dir is
            # specified, create a new one
            currDir = path.realpath(path.curdir)
            if workDir is None:
                workDir = path.join(curdir, 'tmp')
            if not path.exists(workDir):
                mkdir(workDir)
            workDir = path.realpath(workDir)
            chdir(workDir)

            #print "Parse [%s]" % src
            # Start the parsing of the file
            code = ''.join([line for line in f])
            parser = BuildQHDLParser(workDir)
            try:
                ast = parser.parse(code, tracking=True)
                #print "Execute code"
                # Parsing done. Start the program execution
                # (AST traversal)
                ast.action(ENV)
            except (QHDLLexError, QHDLSyntaxError,
                    QHDLTypeError, QHDLAttrError,
                    QHDLIndexError, QHDLNameError), e:
                print e
                #print "Map generation aborted."
                # Error executing the program. Skip to next
                # source file specified
                continue

            #print "Start maps generation"
            
            # Start logging
            d = datetime.now()
            initLogger('%d%d%d-%s-build.log' % \
                           (d.year,
                            d.month,
                            d.day,
                            src[src.rfind(path.sep)+1:]))
            log('Start maps generation for source file [%s]' % \
                    src, 'info')
            
            for key, sym in ENV.globalScope.items():
                if sym.type == 'Map':
                    m = Map(sym.value)
                    if m.name == '':
                        m.name = 'Map%d' % i
                        log('Map with no defined name found. Set name as [%s]' % \
                                m.name, 'debug')

                    #print "Build map [%s]" % m.name
                    log('Map [%s] found. Start the building process' % \
                            m.name, 'info')
                    if not Build(m):
                        #print "Map [%s] building aborted." % \
                        #    m.name
                        log('Map [%s] building aborted.' % \
                            m.name, 'error')
                        continue

                    builtMaps += 1

                    if installPath is not None:
                        Install(m, installPath)
                    i += 1

            # Come back to previous directory
            chdir(currDir)
            log("Done", 'info')

    if builtMaps:
        return 0
    else:
        # No valid maps built!!!
        return 1

if __name__ == '__main__':
    exit(main())
