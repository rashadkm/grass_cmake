"""
@package utils.py

@brief Misc utilities for GRASS wxPython GUI

(C) 2007-2008 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Martin Landa, Jachym Cepicky

@date 2007-2008
"""

import os
import sys

try:
    import subprocess
except:
    compatPath = os.path.join(globalvar.ETCWXDIR, "compat")
    sys.path.append(compatPath)
    import subprocess

def GetTempfile(pref=None):
    """
    Creates GRASS temporary file using defined prefix.

    @param pref prefer the given path

    @return Path to file name (string) or None
    """
    import gcmd
    tempfileCmd = gcmd.Command(["g.tempfile",
                                "pid=%d" %
                                os.getpid()])

    tempfile = tempfileCmd.ReadStdOutput()[0].strip()

    try:
        path, file = os.path.split(tempfile)
        if pref:
            file = "%s%s" % (pref, file)
        return os.path.join(path, file)
    except:
        return Node

def GetLayerNameFromCmd(dcmd):
    """Get layer name from GRASS command

    @param dcmd GRASS command (given as list)

    @return map name
    @return '' if no map name found in command
    """
    mapname = ''
    for item in dcmd:
        if 'map=' in item:
            mapname = item.split('=')[1]
        elif 'input=' in item:
            mapname = item.split('=')[1]
        elif 'red=' in item:
            mapname = item.split('=')[1]
        elif 'h_map=' in item:
            mapname = item.split('=')[1]
        elif 'reliefmap' in item:
            mapname = item.split('=')[1]
        elif 'd.grid' in item:
            mapname = 'grid'
        elif 'd.geodesic' in item:
            mapname = 'geodesic'
        elif 'd.rhumbline' in item:
            mapname = 'rhumb'
        elif 'labels=' in item:
            mapname = item.split('=')[1]+' labels'
            
        if mapname != '':
            break
        
    return mapname

def ListOfCatsToRange(cats):
    """Convert list of category number to range(s)

    Used for example for d.vect cats=[range]

    @param cats category list

    @return category range string
    @return '' on error
    """

    catstr = ''

    try:
        cats = map(int, cats)
    except:
        return catstr

    i = 0
    while i < len(cats):
        next = 0
        j = i + 1
        while j < len(cats):
            if cats[i + next] == cats[j] - 1:
                next += 1
            else:
                break
            j += 1

        if next > 1:
            catstr += '%d-%d,' % (cats[i], cats[i + next])
            i += next + 1
        else:
            catstr += '%d,' % (cats[i])
            i += 1
        
    return catstr.strip(',')

def CheckForWx():
    """Try to import wx module and check its version"""
    majorVersion = 2.8
    minorVersion = 1.1
    try:
        import wx
        version = wx.__version__
        if float(version[:3]) < majorVersion:
            raise ValueError('You are using wxPython version %s' % str(version))
        if float(version[:3]) == 2.8 and \
                float(version[4:]) < minorVersion:
            raise ValueError('You are using wxPython version %s' % str(version))

    except (ImportError, ValueError), e:
        print >> sys.stderr, 'ERROR: ' + str(e) + \
            '. wxPython >= %s.%s is required. Detailed information in README file.' % \
            (str(majorVersion), str(minorVersion))
        sys.exit(1)

def ListOfMapsets():
    """Get list of available/accessible mapsets

    @return ([available mapsets], [accessible mapsets]) 
    """
    import gcmd
    all_mapsets = []
    accessible_mapsets = []

    ### FIXME
    # problem using Command here (see preferences.py)
    # cmd = gcmd.Command(['g.mapsets', '-l'])
    cmd = subprocess.Popen(['g.mapsets', '-l'],
                           stdout=subprocess.PIPE)
    
    try:
        # for mset in cmd.ReadStdOutput()[0].split(' '):
        for mset in cmd.stdout.readlines()[0].strip('%s' % os.linesep).split(' '):
            if len(mset) > 0:
                all_mapsets.append(mset)
    except:
        raise gcmd.CmdError('Unable to get list of available mapsets.')
    
    # cmd = gcmd.Command(['g.mapsets', '-p'])
    cmd = subprocess.Popen(['g.mapsets', '-p'],
                           stdout=subprocess.PIPE)
    try:
        # for mset in cmd.ReadStdOutput()[0].split(' '):
        for mset in cmd.stdout.readlines()[0].strip('%s' % os.linesep).split(' '):
            if len(mset) > 0:
                accessible_mapsets.append(mset)
    except:
        raise gcmd.CmdError('Unable to get list of accessible mapsets.')

    return (all_mapsets, accessible_mapsets)
