#!/usr/bin/python

import sys
from os import mkdir, chdir, path, uname
from subprocess import Popen, PIPE
from optparse import OptionParser

#from quakehordes import ENV, parser, Map
from quakehordes import ENV, Map, BuildQHDLParser
from quakehordes import \
    QHDLLexError, QHDLSyntaxError, \
    QHDLTypeError, QHDLAttrError, QHDLIndexError, \
    QHDLNameError


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
    #pCompiler = Popen(exe,
    #                  stdout=PIPE, stderr=PIPE)
    if pCompiler.returncode != 0:
        # Map compilation fails!!! 
        return False
    else:
        # TO DO: what to do with output?
        pExit = pCompiler.communicate()

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

            print "Parse [%s]" % src
            code = ''.join([line for line in f])
            parser = BuildQHDLParser(workDir)

            try:
                ast = parser.parse(code, tracking=True)
                print "Execute code"
                ast.action(ENV)
            except (QHDLLexError, QHDLSyntaxError,
                    QHDLTypeError, QHDLAttrError,
                    QHDLIndexError, QHDLNameError), e:
                print e
                print "Map generation aborted."
                continue

            print "Start maps generation"
            for key, sym in ENV.globalScope.items():
                if sym.type == 'Map':
                    m = Map(sym.value)
                    if m.name == '':
                        m.name = 'Map%d' % i
                    print "Build map [%s]" % m.name
                    if not Build(m):
                        print "Map [%s] building aborted." % \
                            m.name
                    if installPath is not None:
                        Install(m, installPath)
                    i += 1

            # Come back to previous directory
            chdir(currDir)
            print "Done"

if __name__ == '__main__':
    exit(main())
