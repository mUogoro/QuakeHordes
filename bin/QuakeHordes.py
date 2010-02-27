#!/usr/bin/python

import sys
from os import mkdir, chdir, path, uname
from subprocess import Popen, PIPE
from optparse import OptionParser
from datetime import datetime

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
    platform = uname()[0]
    if platform == 'Linux':
        exe = 'hmap2'
    elif platform == 'Windows':
        exe = 'hmap2.exe'
    else:
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
    print "Install on [%s]" % installPath


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

    for src in sources:
        i = 1
        # Parse and execute each specified file
        with open(src, 'r') as f:

            # Move to working dir. If no working dir is
            # specified, create a new one
            if workDir is None:
                workDir = 'tmp'
                if not path.exists('tmp'):
                    mkdir(workDir)
            workDir = path.realpath(workDir)
            currDir = path.realpath(path.curdir)
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

                    if installPath is not None:
                        Install(m, installPath)
                    i += 1

            # Come back to previous directory
            chdir(currDir)
            log("Done", 'info')

if __name__ == '__main__':
    exit(main())
