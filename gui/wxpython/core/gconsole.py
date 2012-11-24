"""!
@package core.gconsole

@brief Command output widgets

Classes:
 - goutput::CmdThread
 - goutput::GStdout
 - goutput::GStderr
 - goutput::GConsole

(C) 2007-2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Michael Barton (Arizona State University)
@author Martin Landa <landa.martin gmail.com>
@author Vaclav Petras <wenzeslaus gmail.com> (refactoring)
@author Anna Kratochvilova <kratochanna gmail.com> (refactoring)
"""

import os
import sys
import re
import time
import threading
import Queue
import codecs
import locale

import wx
from wx.lib.newevent import NewEvent

import grass.script as grass
from   grass.script import task as gtask

from core import globalvar
from core.gcmd import CommandThread, GError, GException
from core.events import gMapCreated
from gui_core.forms import GUI
from core.debug import Debug
from core.settings import UserSettings


wxCmdOutput, EVT_CMD_OUTPUT = NewEvent()
wxCmdProgress, EVT_CMD_PROGRESS = NewEvent()
wxCmdRun, EVT_CMD_RUN = NewEvent()
wxCmdDone, EVT_CMD_DONE = NewEvent()
wxCmdAbort, EVT_CMD_ABORT = NewEvent()
wxCmdPrepare, EVT_CMD_PREPARE = NewEvent()


def GrassCmd(cmd, env=None, stdout=None, stderr=None):
    """!Return GRASS command thread"""
    return CommandThread(cmd, env=env,
                         stdout=stdout, stderr=stderr)


class CmdThread(threading.Thread):
    """!Thread for GRASS commands"""
    requestId = 0

    def __init__(self, receiver, requestQ=None, resultQ=None, **kwds):
        """!
        @param receiver event receiver (used in PostEvent)
        """
        threading.Thread.__init__(self, **kwds)

        if requestQ is None:
            self.requestQ = Queue.Queue()
        else:
            self.requestQ = requestQ

        if resultQ is None:
            self.resultQ = Queue.Queue()
        else:
            self.resultQ = resultQ

        self.setDaemon(True)

        self.receiver = receiver
        self._want_abort_all = False

        self.start()

    def RunCmd(self, *args, **kwds):
        """!Run command in queue

        @param args unnamed command arguments
        @param kwds named command arguments

        @return request id in queue
        """
        CmdThread.requestId += 1

        self.requestCmd = None
        self.requestQ.put((CmdThread.requestId, args, kwds))

        return CmdThread.requestId

    def SetId(self, id):
        """!Set starting id"""
        CmdThread.requestId = id

    def run(self):
        os.environ['GRASS_MESSAGE_FORMAT'] = 'gui'
        while True:
            requestId, args, kwds = self.requestQ.get()
            for key in ('callable', 'onDone', 'onPrepare', 'userData'):
                if key in kwds:
                    vars()[key] = kwds[key]
                    del kwds[key]
                else:
                    vars()[key] = None

            if not vars()['callable']:
                vars()['callable'] = GrassCmd

            requestTime = time.time()

            # prepare
            event = wxCmdPrepare(cmd=args[0],
                                 time=requestTime,
                                 pid=requestId,
                                 onPrepare=vars()['onPrepare'],
                                 userData=vars()['userData'])
            wx.PostEvent(self.receiver, event)

            # run command
            event = wxCmdRun(cmd=args[0],
                             pid=requestId)

            wx.PostEvent(self.receiver, event)

            time.sleep(.1)
            self.requestCmd = vars()['callable'](*args, **kwds)
            if self._want_abort_all:
                self.requestCmd.abort()
                if self.requestQ.empty():
                    self._want_abort_all = False

            self.resultQ.put((requestId, self.requestCmd.run()))

            try:
                returncode = self.requestCmd.module.returncode
            except AttributeError:
                returncode = 0  # being optimistic

            try:
                aborted = self.requestCmd.aborted
            except AttributeError:
                aborted = False

            time.sleep(.1)

            # set default color table for raster data
            if UserSettings.Get(group='rasterLayer',
                                key='colorTable', subkey='enabled') and \
                    args[0][0][:2] == 'r.':
                colorTable = UserSettings.Get(group='rasterLayer',
                                              key='colorTable',
                                              subkey='selection')
                mapName = None
                if args[0][0] == 'r.mapcalc':
                    try:
                        mapName = args[0][1].split('=', 1)[0].strip()
                    except KeyError:
                        pass
                else:
                    moduleInterface = GUI(show=None).ParseCommand(args[0])
                    outputParam = moduleInterface.get_param(value='output',
                                                            raiseError=False)
                    if outputParam and outputParam['prompt'] == 'raster':
                        mapName = outputParam['value']

                if mapName:
                    argsColor = list(args)
                    argsColor[0] = ['r.colors',
                                    'map=%s' % mapName,
                                    'color=%s' % colorTable]
                    self.requestCmdColor = vars()['callable'](*argsColor, **kwds)
                    self.resultQ.put((requestId, self.requestCmdColor.run()))

            event = wxCmdDone(cmd=args[0],
                              aborted=aborted,
                              returncode=returncode,
                              time=requestTime,
                              pid=requestId,
                              onDone=vars()['onDone'],
                              userData=vars()['userData'])

            # send event
            wx.PostEvent(self.receiver, event)

    def abort(self, abortall=True):
        """!Abort command(s)"""
        if abortall:
            self._want_abort_all = True
        self.requestCmd.abort()
        if self.requestQ.empty():
            self._want_abort_all = False


class GStdout:
    """!GConsole standard output

    Based on FrameOutErr.py

    Name:      FrameOutErr.py
    Purpose:   Redirecting stdout / stderr
    Author:    Jean-Michel Fauth, Switzerland
    Copyright: (c) 2005-2007 Jean-Michel Fauth
    Licence:   GPL
    """
    def __init__(self, receiver):
        """!
        @param receiver event receiver (used in PostEvent)
        """
        self.receiver = receiver

    def write(self, s):
        if len(s) == 0 or s == '\n':
            return

        for line in s.splitlines():
            if len(line) == 0:
                continue

            evt = wxCmdOutput(text=line + '\n',
                              type='')
            wx.PostEvent(self.receiver, evt)


class GStderr:
    """!GConsole standard error output

    Based on FrameOutErr.py

    Name:      FrameOutErr.py
    Purpose:   Redirecting stdout / stderr
    Author:    Jean-Michel Fauth, Switzerland
    Copyright: (c) 2005-2007 Jean-Michel Fauth
    Licence:   GPL
    """
    def __init__(self, receiver):
        """!
        @param receiver event receiver (used in PostEvent)
        """
        self.receiver = receiver
        self.type = ''
        self.message = ''
        self.printMessage = False

    def flush(self):
        pass

    def write(self, s):
        if "GtkPizza" in s:
            return

        # remove/replace escape sequences '\b' or '\r' from stream
        progressValue = -1

        for line in s.splitlines():
            if len(line) == 0:
                continue

            if 'GRASS_INFO_PERCENT' in line:
                value = int(line.rsplit(':', 1)[1].strip())
                if value >= 0 and value < 100:
                    progressValue = value
                else:
                    progressValue = 0
            elif 'GRASS_INFO_MESSAGE' in line:
                self.type = 'message'
                self.message += line.split(':', 1)[1].strip() + '\n'
            elif 'GRASS_INFO_WARNING' in line:
                self.type = 'warning'
                self.message += line.split(':', 1)[1].strip() + '\n'
            elif 'GRASS_INFO_ERROR' in line:
                self.type = 'error'
                self.message += line.split(':', 1)[1].strip() + '\n'
            elif 'GRASS_INFO_END' in line:
                self.printMessage = True
            elif self.type == '':
                if len(line) == 0:
                    continue
                evt = wxCmdOutput(text=line,
                                  type='')
                wx.PostEvent(self.receiver, evt)
            elif len(line) > 0:
                self.message += line.strip() + '\n'

            if self.printMessage and len(self.message) > 0:
                evt = wxCmdOutput(text=self.message,
                                  type=self.type)
                wx.PostEvent(self.receiver, evt)

                self.type = ''
                self.message = ''
                self.printMessage = False

        # update progress message
        if progressValue > -1:
            # self.gmgauge.SetValue(progressValue)
            evt = wxCmdProgress(value=progressValue)
            wx.PostEvent(self.receiver, evt)


# events related to messages
# TODO: create separete class for handling messages?
gWriteLog, EVT_WRITE_LOG = NewEvent()
gWriteCmdLog, EVT_WRITE_CMD_LOG = NewEvent()
gWriteWarning, EVT_WRITE_WARNING = NewEvent()
gWriteError, EVT_WRITE_ERROR = NewEvent()

# Occurs when an ignored command is called.
# Attribute cmd contains command (as a list).
gIgnoredCmdRun, EVT_IGNORED_CMD_RUN = NewEvent()

# Occurs when important command is called.
# Determined by switchPage and priority parameters of GConsole.RunCmd()
# currently used only for Layer Manager
# because others (forms and gmodeler) just wants to see all commands
# (because commands are the main part of their work)
gImportantCmdRun, EVT_IMPORTANT_CMD_RUN = NewEvent()


class GConsole(wx.EvtHandler):
    """!
    """
    def __init__(self, guiparent=None, giface=None, ignoredCmdPattern=None):
        """!
        @param guiparent parent window for created GUI objects
        @param lmgr layer manager window (TODO: replace by giface)
        @param ignoredCmdPattern regular expression specifying commads
        to be ignored (e.g. @c '^d\..*' for display commands)
        """
        wx.EvtHandler.__init__(self)

        self._guiparent = guiparent
        self._giface = giface
        self._ignoredCmdPattern = ignoredCmdPattern

        # create queues
        self.requestQ = Queue.Queue()
        self.resultQ = Queue.Queue()

        self.cmdOutputTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnProcessPendingOutputWindowEvents)
        self.Bind(EVT_CMD_RUN, self.OnCmdRun)
        self.Bind(EVT_CMD_DONE, self.OnCmdDone)
        self.Bind(EVT_CMD_ABORT, self.OnCmdAbort)

        # stream redirection
        self.cmdStdOut = GStdout(receiver=self)
        self.cmdStdErr = GStderr(receiver=self)

        # thread
        self.cmdThread = CmdThread(self, self.requestQ, self.resultQ)

    def Redirect(self):
        """!Redirect stdout/stderr
        """
        if Debug.GetLevel() == 0 and int(grass.gisenv().get('DEBUG', 0)) == 0:
            # don't redirect when debugging is enabled
            sys.stdout = self.cmdStdOut
            sys.stderr = self.cmdStdErr
        else:
            enc = locale.getdefaultlocale()[1]
            if enc:
                sys.stdout = codecs.getwriter(enc)(sys.__stdout__)
                sys.stderr = codecs.getwriter(enc)(sys.__stderr__)
            else:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__

    def WriteLog(self, text, style=None, wrap=None,
                 switchPage=False, priority=1):
        """!Generic method for writing log message in
        given style

        @param line text line
        @param switchPage for backward compatibility
        (replace by priority: False=1, True=2)
        @param priority priority of this message
        (0=no priority, 1=normal, 2=medium, 3=high)
        """
        event = gWriteLog(text=text, wrap=wrap,
                          switchPage=switchPage, priority=priority)
        wx.PostEvent(self, event)

    def WriteCmdLog(self, line, pid=None, switchPage=True):
        """!Write message in selected style

        @param line message to be printed
        @param pid process pid or None
        @param switchPage True to switch page
        """
        event = gWriteCmdLog(line=line, pid=pid,
                             switchPage=switchPage)
        wx.PostEvent(self, event)

    def WriteWarning(self, line):
        """!Write message in warning style"""
        event = gWriteWarning(line=line)
        wx.PostEvent(self, event)

    def WriteError(self, line):
        """!Write message in error style"""
        event = gWriteError(line=line)
        wx.PostEvent(self, event)

    def RunCmd(self, command, compReg=True, switchPage=False, skipInterface=False,
               onDone=None, onPrepare=None, userData=None, priority=1):
        """!Run command typed into console command prompt (GPrompt).

        @todo Document the other event.
        @todo Solve problem with the other event
        (now uses gOutputText event but there is no text,
        use onPrepare handler instead?)

        Posts event EVT_IGNORED_CMD_RUN when command which should be ignored
        (according to ignoredCmdPattern) is run.
        For example, see layer manager which handles d.* on its own.

        @todo replace swichPage and priority by parameter 'silent' or 'important'
        also possible solution is RunCmdSilently and RunCmdWithoutNotifyingAUser

        @param command command given as a list (produced e.g. by utils.split())
        @param compReg True use computation region
        @param switchPage switch to output page
        @param priority command importance - possible replacement for switchPage
        @param skipInterface True to do not launch GRASS interface
        parser when command has no arguments given
        @param onDone function to be called when command is finished
        @param onPrepare function to be called before command is launched
        @param userData data defined for the command
        """
        if len(command) == 0:
            Debug.msg(2, "GPrompt:RunCmd(): empty command")
            return

        # update history file
        env = grass.gisenv()
        try:
            filePath = os.path.join(env['GISDBASE'],
                                    env['LOCATION_NAME'],
                                    env['MAPSET'],
                                    '.bash_history')
            fileHistory = codecs.open(filePath, encoding='utf-8', mode='a')
        except IOError, e:
            GError(_("Unable to write file '%(filePath)s'.\n\nDetails: %(error)s") % 
                    {'filePath': filePath, 'error': e},
                   parent=self._guiparent)
            fileHistory = None

        if fileHistory:
            try:
                fileHistory.write(' '.join(command) + os.linesep)
            finally:
                fileHistory.close()

        if command[0] in globalvar.grassCmd:
            # send GRASS command without arguments to GUI command interface
            # except ignored commands (event is emitted)

            if self._ignoredCmdPattern and \
              re.compile(self._ignoredCmdPattern).search(' '.join(command)) and \
              '--help' not in command:
                event = gIgnoredCmdRun(cmd=command)
                wx.PostEvent(self, event)
                return

            else:
                # other GRASS commands (r|v|g|...)
                try:
                    task = GUI(show=None).ParseCommand(command)
                except GException, e:
                    GError(parent=self._guiparent,
                           message=unicode(e),
                           showTraceback=False)
                    return

                hasParams = False
                if task:
                    options = task.get_options()
                    hasParams = options['params'] and options['flags']
                    # check for <input>=-
                    for p in options['params']:
                        if p.get('prompt', '') == 'input' and \
                                p.get('element', '') == 'file' and \
                                p.get('age', 'new') == 'old' and \
                                p.get('value', '') == '-':
                            GError(parent=self._guiparent,
                                   message=_("Unable to run command:\n%(cmd)s\n\n"
                                             "Option <%(opt)s>: read from standard input is not "
                                             "supported by wxGUI") % {'cmd': ' '.join(command),
                                                                      'opt': p.get('name', '')})
                            return

                if len(command) == 1 and hasParams and \
                        command[0] != 'v.krige':
                    # no arguments given
                    try:
                        GUI(parent=self._guiparent, giface=self._giface).ParseCommand(command)
                    except GException, e:
                        print >> sys.stderr, e
                    return

                # documenting old behavior/implementation:
                # switch and focus if required
                # important commad
                # TODO: add also user data, cmd, ... to the event?
                importantEvent = gImportantCmdRun()
                wx.PostEvent(self, importantEvent)

                # activate computational region (set with g.region)
                # for all non-display commands.
                if compReg:
                    tmpreg = os.getenv("GRASS_REGION")
                    if "GRASS_REGION" in os.environ:
                        del os.environ["GRASS_REGION"]

                # process GRASS command with argument
                self.cmdThread.RunCmd(command,
                                      stdout=self.cmdStdOut,
                                      stderr=self.cmdStdErr,
                                      onDone=onDone, onPrepare=onPrepare,
                                      userData=userData,
                                      env=os.environ.copy())
                self.cmdOutputTimer.Start(50)

                # deactivate computational region and return to display settings
                if compReg and tmpreg:
                    os.environ["GRASS_REGION"] = tmpreg
        else:
            # Send any other command to the shell. Send output to
            # console output window
            if len(command) == 1 and not skipInterface:
                try:
                    task = gtask.parse_interface(command[0])
                except:
                    task = None
            else:
                task = None

            if task:
                # process GRASS command without argument
                GUI(parent=self._guiparent, giface=self._giface).ParseCommand(command)
            else:
                self.cmdThread.RunCmd(command,
                                      stdout=self.cmdStdOut,
                                      stderr=self.cmdStdErr,
                                      onDone=onDone, onPrepare=onPrepare,
                                      userData=userData)
            self.cmdOutputTimer.Start(50)

    def GetLog(self, err=False):
        """!Get widget used for logging

        @todo what's this?

        @param err True to get stderr widget
        """
        if err:
            return self.cmdStdErr

        return self.cmdStdOut

    def GetCmd(self):
        """!Get running command or None"""
        return self.requestQ.get()

    def OnCmdAbort(self, event):
        """!Abort running command"""
        self.cmdThread.abort()
        event.Skip()

    def OnCmdRun(self, event):
        """!Run command"""
        self.WriteCmdLog('(%s)\n%s' % (str(time.ctime()), ' '.join(event.cmd)))
        event.Skip()

    def OnCmdDone(self, event):
        """!Command done (or aborted)

        Posts event EVT_MAP_CREATED.
        """
        # Process results here
        try:
            ctime = time.time() - event.time
            if ctime < 60:
                stime = _("%d sec") % int(ctime)
            else:
                mtime = int(ctime / 60)
                stime = _("%(min)d min %(sec)d sec") % {'min': mtime,
                                                        'sec': int(ctime - (mtime * 60))}
        except KeyError:
            # stopped deamon
            stime = _("unknown")

        if event.aborted:
            # Thread aborted (using our convention of None return)
            self.WriteWarning(_('Please note that the data are left in'
                                ' inconsistent state and may be corrupted'))
            msg = _('Command aborted')
        else:
            msg = _('Command finished')

        self.WriteCmdLog('(%s) %s (%s)' % (str(time.ctime()), msg, stime))

        if event.onDone:
            event.onDone(cmd=event.cmd, returncode=event.returncode)

        self.cmdOutputTimer.Stop()

        if event.cmd[0] == 'g.gisenv':
            Debug.SetLevel()
            self.Redirect()

        # do nothing when no map added
        if event.returncode != 0 or event.aborted:
            event.Skip()
            return

        # find which maps were created
        try:
            task = GUI(show=None).ParseCommand(event.cmd)
        except GException, e:
            print >> sys.stderr, e
            task = None
            return

        for p in task.get_options()['params']:
            prompt = p.get('prompt', '')
            if prompt in ('raster', 'vector', '3d-raster') and \
                    p.get('age', 'old') == 'new' and \
                    p.get('value', None):
                name = p.get('value')
                if '@' not in name:
                    name = name + '@' + grass.gisenv()['MAPSET']
                mapEvent = gMapCreated(wx.ID_ANY,
                                       name=name, ltype=prompt, add=None)
                wx.PostEvent(self, mapEvent)

        event.Skip()

    def OnProcessPendingOutputWindowEvents(self, event):
        wx.GetApp().ProcessPendingEvents()