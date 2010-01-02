#! /usr/bin/python
"""
@brief Construct simple wx.Python GUI from a GRASS command interface
description.

Classes:
 - grassTask
 - processTask
 - helpPanel
 - mainFrame
 - cmdPanel
 - GrassGUIApp
 - GUI

 Copyright (C) 2000-2009 by the GRASS Development Team

 This program is free software under the GPL (>=v2) Read the file
 COPYING coming with GRASS for details.

 This program is just a coarse approach to automatically build a GUI
 from a xml-based GRASS user interface description.

 You need to have Python 2.4, wxPython 2.8 and python-xml.

 The XML stream is read from executing the command given in the
 command line, thus you may call it for instance this way:

 python menuform.py r.basins.fill

 Or you set an alias or wrap the call up in a nice shell script, GUI
 environment ... please contribute your idea.

 Updated to wxPython 2.8 syntax and contrib widgets.  Methods added to
 make it callable by gui.  Method added to automatically re-run with
 pythonw on a Mac.

@author Jan-Oliver Wagner <jan@intevation.de>
@author Bernhard Reiter <bernhard@intevation.de>
@author Michael Barton, Arizona State University
@author Daniel Calvelo <dca.gis@gmail.com>
@author Martin Landa <landa.martin@gmail.com>

@todo
 - verify option value types
"""

import sys
import re
import string
import textwrap
import os
import time
import types
import copy
import locale
import types
from threading import Thread
import Queue

### i18N
import gettext
gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode=True)

import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()

import wx
import wx.html
import wx.lib.flatnotebook as FN
import wx.lib.colourselect as csel
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from wx.lib.newevent import NewEvent

try:
    import xml.etree.ElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree # Python <= 2.4

import utils

gisbase = os.getenv("GISBASE")
if gisbase is None:
    print >>sys.stderr, "We don't seem to be properly installed, or we are being run outside GRASS. Expect glitches."
    gisbase = os.path.join(os.path.dirname( sys.argv[0] ), os.path.pardir)
    wxbase = gisbase
else:
    wxbase = os.path.join(globalvar.ETCWXDIR)

sys.path.append( wxbase)
imagepath = os.path.join(wxbase, "images")
sys.path.append(imagepath)

from grass.script import core as grass

import gselect
import gcmd
import goutput
import utils
from preferences import globalSettings as UserSettings
try:
    import subprocess
except:
    from compat import subprocess

wxUpdateDialog, EVT_DIALOG_UPDATE = NewEvent()

# From lib/gis/col_str.c, except purple which is mentioned
# there but not given RGB values
str2rgb = {'aqua': (100, 128, 255),
           'black': (0, 0, 0),
           'blue': (0, 0, 255),
           'brown': (180, 77, 25),
           'cyan': (0, 255, 255),
           'gray': (128, 128, 128),
           'green': (0, 255, 0),
           'grey': (128, 128, 128),
           'indigo': (0, 128, 255),
           'magenta': (255, 0, 255),
           'orange': (255, 128, 0),
           'purple': (128, 0, 128),
           'red': (255, 0, 0),
           'violet': (128, 0, 255),
           'white': (255, 255, 255),
           'yellow': (255, 255, 0)}
rgb2str = {}
for (s,r) in str2rgb.items():
    rgb2str[ r ] = s

def color_resolve(color):
    if len(color)>0 and color[0] in "0123456789":
        rgb = tuple(map(int,color.split( ':' )))
        label = color
    else:
        # Convert color names to RGB
        try:
            rgb = str2rgb[ color ]
            label = color
        except KeyError:
            rgb = (200,200,200)
            label = _('Select Color')
    return (rgb, label)

def text_beautify( someString , width=70):
    """
    Make really long texts shorter, clean up whitespace and
    remove trailing punctuation.
    """
    if width > 0:
        return escape_ampersand( string.strip(
                os.linesep.join( textwrap.wrap( utils.normalize_whitespace(someString), width ) ),
                ".,;:" ) )
    else:
        return escape_ampersand( string.strip(utils.normalize_whitespace(someString ), ".,;:" ))
    
def escape_ampersand(text):
    """!Escapes ampersands with additional ampersand for GUI"""
    return string.replace(text, "&", "&&")

class UpdateThread(Thread):
    """!Update dialog widgets in the thread"""
    def __init__(self, parent, event, eventId, task):
        Thread.__init__(self)
        
        self.parent = parent
        self.event = event
        self.eventId = eventId
        self.task = task
        self.setDaemon(True)
        
        # list of functions which updates the dialog
        self.data = {}
        
    def run(self):
        # get widget id
        if not self.eventId:
            for p in self.task.params:
                if p.get('gisprompt', False) == False:
                    continue
                prompt = p.get('element', '')
                if prompt == 'vector':
                    name = p.get('name', '')
                    if name in ('map', 'input'):
                        self.eventId = p['wxId'][0]
            if self.eventId is None:
                return
        
        p = self.task.get_param(self.eventId, element='wxId', raiseError=False)
        if not p or \
                not p.has_key('wxId-bind'):
            return

        # get widget prompt
        pType = p.get('prompt', '')
        if not pType:
            return

        # check for map/input parameter
        pMap = self.task.get_param('map', raiseError=False)
        if not pMap:
            pMap = self.task.get_param('input', raiseError=False)

        if pMap:
            map = pMap.get('value', '')
        else:
            map = None
        
        # update reference widgets
        for uid in p['wxId-bind']:
            win = self.parent.FindWindowById(uid)
            name = win.GetName()
            
            map = layer = None
            driver = db = table = None
            if name in ('LayerSelect', 'LayerNameSelect',
                        'ColumnSelect'):
                if p.get('element', '') == 'vector': # -> vector
                    # get map name
                    map = p.get('value', '')
                    
                    # get layer
                    for bid in p['wxId-bind']:
                        p = self.task.get_param(bid, element = 'wxId', raiseError = False)
                        if not p:
                            continue
                        
                        if p.get('element', '') == 'layer':
                            layer = p.get('value', '')
                            if layer != '':
                                layer = int(p.get('value', 1))
                            else:
                                layer = int(p.get('default', 1))
                            break
                        
                elif p.get('element', '') == 'layer': # -> layer
                    # get layer
                    layer = p.get('value', '')
                    if layer != '':
                        layer = int(p.get('value', 1))
                    else:
                        layer = int(p.get('default', 1))
                    
                    # get map name
                    pMap = self.task.get_param(p['wxId'][0], element = 'wxId-bind', raiseError = False)
                    if pMap:
                        map = pMap.get('value', '')
            
            if name == 'TableSelect' or \
                    (name == 'ColumnSelect' and not map):
                pDriver = self.task.get_param('dbdriver', element='prompt', raiseError=False)
                if pDriver:
                    driver = pDriver.get('value', '')
                pDb = self.task.get_param('dbname', element='prompt', raiseError=False)
                if pDb:
                    db = pDb.get('value', '')
                if name == 'ColumnSelect':
                    pTable = self.task.get_param('dbtable', element='element', raiseError=False)
                    if pTable:
                        table = pTable.get('value', '')
                
            if name == 'LayerSelect':
                self.data[win.InsertLayers] = { 'vector' : map }
            
            elif name == 'LayerNameSelect':
                # determine format
                native = True
                for id in pMap['wxId']:
                    winVec  = self.parent.FindWindowById(id)
                    if winVec.GetName() == 'VectorFormat' and \
                            winVec.GetSelection() != 0:
                        native = False
                        break
                if not native:
                    if map:
                        self.data[win.InsertLayers] = { 'dsn' : map.rstrip('@OGR') }
                    else:
                        self.data[win.InsertLayers] = { }
            
            elif name == 'TableSelect':
                self.data[win.InsertTables] = { 'driver' : driver,
                                                'database' : db }
                
            elif name == 'ColumnSelect':
                if map:
                    self.data[win.InsertColumns] = { 'vector' : map, 'layer' : layer }
                else: # table
                    if driver and db:
                        self.data[win.InsertTableColumns] = { 'table' : pTable.get('value'),
                                                              'driver' : driver,
                                                              'database' : db }
                    elif pTable:
                        self.data[win.InsertTableColumns] = { 'table'  : pTable.get('value') }
        
def UpdateDialog(parent, event, eventId, task):
    return UpdateThread(parent, event, eventId, task)

class UpdateQThread(Thread):
    """!Update dialog widgets in the thread"""
    requestId = 0
    def __init__(self, parent, requestQ, resultQ, **kwds):
        Thread.__init__(self, **kwds)
        
        self.parent = parent # cmdPanel
        self.setDaemon(True)
        
        self.requestQ = requestQ
        self.resultQ = resultQ
        
        self.start()
        
    def Update(self, callable, *args, **kwds):
        UpdateQThread.requestId += 1
        
        self.request = None
        self.requestQ.put((UpdateQThread.requestId, callable, args, kwds))
        
        return UpdateQThread.requestId
    
    def run(self):
        while True:
            requestId, callable, args, kwds = self.requestQ.get()
            
            requestTime = time.time()
            
            self.request = callable(*args, **kwds)

            self.resultQ.put((requestId, self.request.run()))
                        
            event = wxUpdateDialog(data = self.request.data)
            wx.PostEvent(self.parent, event)

class grassTask:
    """
    This class holds the structures needed for both filling by the parser and
    use by the interface constructor.

    Use as either grassTask() for empty definition or grassTask( 'grass.command' )
    for parsed filling.
    """
    def __init__(self, grassModule = None):
        self.path = grassModule
        self.name = _('unknown')
        self.params = []
        self.description = ''
        self.label = ''
        self.flags = []
        self.keywords = []
        if grassModule is not None:
            processTask(tree = etree.fromstring(getInterfaceDescription(grassModule)),
                        task = self)

    def get_name(self):
        """!Get task name"""
        return self.name
    
    def get_list_params(self, element = 'name'):
        """!Get list of parameters"""
        params = []
        for p in self.params:
            params.append(p['name'])
        
        return params

    def get_list_flags(self, element = 'name'):
        """!Get list of parameters"""
        flags = []
        for p in self.flags:
            flags.append(p['name'])
        
        return flags
    
    def get_param(self, value, element='name', raiseError=True):
        """!Find and return a param by name."""
        try:
            for p in self.params:
                val = p[element]
                if val is None:
                    continue
                if type(val) in (types.ListType, types.TupleType):
                    if value in val:
                        return p
                elif type(val) == types.StringType:
                    if p[element][:len(value)] == value:
                        return p
                else:
                    if p[element] == value:
                        return p
        except KeyError:
            pass
        
        if raiseError:
            raise ValueError, _("Parameter element '%(element)s' not found: '%(value)s'") % \
                { 'element' : element, 'value' : value }
        else:
            return None

    def set_param(self, aParam, aValue):
        """
        Set param value/values.
        """
        param = self.get_param(aParam)
        param['value'] = aValue
            
    def get_flag(self, aFlag):
        """
        Find and return a flag by name.
        """
        for f in self.flags:
            if f['name'] == aFlag:
                return f
        raise ValueError, _("Flag not found: %s") % aFlag

    def set_flag(self, aFlag, aValue):
        """
        Enable / disable flag.
        """
        param = self.get_flag(aFlag)
        param['value'] = aValue
                
    def getCmd(self, ignoreErrors = False):
        """
        Produce an array of command name and arguments for feeding
        into some execve-like command processor.

        If ignoreErrors==True then it will return whatever has been
        built so far, even though it would not be a correct command
        for GRASS.
        """
        cmd = [self.name]
        errors = 0
        errStr = ""

        for flag in self.flags:
            if 'value' in flag and flag['value']:
                if len(flag['name']) > 1: # e.g. overwrite
                    cmd += [ '--' + flag['name'] ]
                else:
                    cmd += [ '-' + flag['name'] ]
        for p in self.params:
            if p.get('value','') == '' and p.get('required','no') != 'no':
                if p.get('default', '') != '':
                    cmd += [ '%s=%s' % ( p['name'], p['default'] ) ]
                else:
                    cmd += [ '%s=%s' % ( p['name'], _('<required>') ) ]
                    errStr += _("Parameter %(name)s (%(desc)s) is missing.\n") % \
                        {'name' : p['name'], 'desc' : p['description']}
                    errors += 1
            elif p.get('value','') != '' and p['value'] != p.get('default','') :
                # Output only values that have been set, and different from defaults
                cmd += [ '%s=%s' % ( p['name'], p['value'] ) ]
        if errors and not ignoreErrors:
            raise ValueError, errStr

        return cmd

class processTask:
    """!A ElementTree handler for the --interface-description output,
    as defined in grass-interface.dtd. Extend or modify this and the
    DTD if the XML output of GRASS' parser is extended or modified.

    @param tree root tree node
    @param task grassTask instance or None
    @return grassTask instance
    """
    def __init__(self, tree, task = None):
        if task:
            self.task = task
        else:
            self.task = grassTask()
        
        self.root = tree
        
        self.__processModule()
        self.__processParams()
        self.__processFlags()

    def __processModule(self):
        """!Process module description"""
        self.task.name = self.root.get('name', default = 'unknown')
        
        # keywords
        for keyword in self.__getNodeText(self.root, 'keywords').split(','):
            self.task.keywords.append(keyword.strip())
        
        self.task.label       = self.__getNodeText(self.root, 'label')
        self.task.description = self.__getNodeText(self.root, 'description')
        
    def __processParams(self):
        """!Process parameters description"""
        for p in self.root.findall('parameter'):
            # gisprompt
            node_gisprompt = p.find('gisprompt')
            gisprompt = False
            age = element = prompt = None
            if node_gisprompt is not None:
                gisprompt = True
                age     = node_gisprompt.get('age', '')
                element = node_gisprompt.get('element', '')
                prompt  = node_gisprompt.get('prompt', '')
            
            # value(s)
            values = []
            values_desc = []
            node_values = p.find('values')
            if node_values is not None:
                for pv in node_values.findall('value'):
                    values.append(self.__getNodeText(pv, 'name'))
                    desc = self.__getNodeText(pv, 'description')
                    if desc:
                        values_desc.append(desc)
            
            # keydesc
            key_desc = []
            node_key_desc = p.find('keydesc')
            if node_key_desc is not None:
                for ki in node_key_desc.findall('item'):
                    key_desc.append(ki.text)
            
            self.task.params.append( {
                "name"           : p.get('name'),
                "type"           : p.get('type'),
                "required"       : p.get('required'),
                "multiple"       : p.get('multiple'),
                "label"          : self.__getNodeText(p, 'label'),
                "description"    : self.__getNodeText(p, 'description'),
                'gisprompt'      : gisprompt,
                'age'            : age,
                'element'        : element,
                'prompt'         : prompt,
                "guisection"     : self.__getNodeText(p, 'guisection'),
                "guidependency"  : self.__getNodeText(p, 'guidependency'),
                "default"        : self.__getNodeText(p, 'default'),
                "values"         : values,
                "values_desc"    : values_desc,
                "value"          : '',
                "key_desc"       : key_desc } )
            
    def __processFlags(self):
        """!Process flags description"""
        for p in self.root.findall('flag'):
            self.task.flags.append( {
                    "name"        : p.get('name'),
                    "label"       : self.__getNodeText(p, 'label'),
                    "description" : self.__getNodeText(p, 'description'),
                    "guisection"  : self.__getNodeText(p, 'guisection') } )
        
    def __getNodeText(self, node, tag, default = ''):
        """!Get node text"""
        p = node.find(tag)
        if p is not None:
            return utils.normalize_whitespace(p.text)
        
        return default
    
    def GetTask(self):
        """!Get grassTask intance"""
        return self.task
    
class helpPanel(wx.html.HtmlWindow):
    """
    This panel holds the text from GRASS docs.

    GISBASE must be set in the environment to find the html docs dir.
    The SYNOPSIS section is skipped, since this Panel is supposed to
    be integrated into the cmdPanel and options are obvious there.
    """
    def __init__(self, grass_command = "index", text = None,
                 skip_description=False, *args, **kwargs):
        """ If grass_command is given, the corresponding HTML help file will
        be presented, with all links pointing to absolute paths of
        local files.

        If 'skip_description' is True, the HTML corresponding to
        SYNOPSIS will be skipped, thus only presenting the help file
        from the DESCRIPTION section onwards.

        If 'text' is given, it must be the HTML text to be presented in the Panel.
        """

        wx.html.HtmlWindow.__init__(self, *args, **kwargs)
        self.fspath = gisbase + "/docs/html/"

        self.SetStandardFonts ( size = 10 )
        self.SetBorders(10)
        wx.InitAllImageHandlers()

        if text is None:
            if skip_description:
                self.fillContentsFromFile ( self.fspath + grass_command + ".html",
                                            skip_description=skip_description )
                self.Ok = True
            else:
                ### FIXME: calling LoadPage() is strangely time-consuming (only first call)
                # self.LoadPage(self.fspath + grass_command + ".html")
                self.Ok = False
        else:
            self.SetPage( text )
            self.Ok = True

    def fillContentsFromFile( self, htmlFile, skip_description=True ):
        aLink = re.compile( r'(<a href="?)(.+\.html?["\s]*>)', re.IGNORECASE )
        imgLink = re.compile( r'(<img src="?)(.+\.[png|gif])', re.IGNORECASE )
        try:
            # contents = [ '<head><base href="%s"></head>' % self.fspath ]
            contents = []
            skip = False
            for l in file( htmlFile, "rb" ).readlines():
                if "DESCRIPTION" in l:
                    skip = False
                if not skip:
                    # do skip the options description if requested
                    if "SYNOPSIS" in l:
                        skip = skip_description
                    else:
                        # FIXME: find only first item
                        findALink = aLink.search( l )
                        if findALink is not None: 
                            contents.append( aLink.sub(findALink.group(1)+
                                                           self.fspath+findALink.group(2),l) )
                        findImgLink = imgLink.search( l )
                        if findImgLink is not None: 
                            contents.append( imgLink.sub(findImgLink.group(1)+
                                                         self.fspath+findImgLink.group(2),l) )
        
                        if findALink is None and findImgLink is None:
                            contents.append( l )
            self.SetPage( "".join( contents ) )
            self.Ok = True
        except: # The Manual file was not found
            self.Ok = False

class mainFrame(wx.Frame):
    """
    This is the Frame containing the dialog for options input.

    The dialog is organized in a notebook according to the guisections
    defined by each GRASS command.

    If run with a parent, it may Apply, Ok or Cancel; the latter two close the dialog.
    The former two trigger a callback.

    If run standalone, it will allow execution of the command.

    The command is checked and sent to the clipboard when clicking 'Copy'.
    """
    def __init__(self, parent, ID, task_description, get_dcmd=None, layer=None):

        self.get_dcmd = get_dcmd
        self.layer = layer
        self.task = task_description
        self.parent = parent # LayerTree | None

        # module name + keywords
        if self.task.name.split('.')[-1] in ('py', 'sh'):
            title = str(self.task.name.rsplit('.',1)[0])
        else:
            title = self.task.name
        try:
            if self.task.keywords != ['']:
                title +=  " [" + ', '.join( self.task.keywords ) + "]"
        except ValueError:
            pass
        
        wx.Frame.__init__(self, parent=parent, id=ID, title=title,
                          pos=wx.DefaultPosition, style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.panel = wx.Panel(parent=self, id=wx.ID_ANY)

        # statusbar
        self.CreateStatusBar()

        # icon
        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass_dialog.ico'), wx.BITMAP_TYPE_ICO))
        
        guisizer = wx.BoxSizer(wx.VERTICAL)

        # set apropriate output window
        if self.parent:
            self.standalone   = False
        else:
            self.standalone = True
            #             try:
            #                 self.goutput  = self.parent.GetLogWindow()
            #             except:
            #                 self.goutput  = None

        # logo+description
        topsizer = wx.BoxSizer(wx.HORIZONTAL)

        # GRASS logo
        self.logo = wx.StaticBitmap(parent=self.panel,
                                    bitmap=wx.Bitmap(name=os.path.join(imagepath,
                                                                       'grass_form.png'),
                                                     type=wx.BITMAP_TYPE_PNG))
        topsizer.Add (item=self.logo, proportion=0, border=3,
                      flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        #
        # put module description
        #
        if self.task.label != '':
            module_desc = self.task.label + ' ' + self.task.description
        else:
            module_desc = self.task.description
        self.description = StaticWrapText (parent=self.panel,
                                           label=module_desc)
        topsizer.Add (item=self.description, proportion=1, border=5,
                      flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
                      
        guisizer.Add (item=topsizer, proportion=0, flag=wx.EXPAND)
        
        self.panel.SetSizerAndFit(guisizer)
        self.Layout()

        # notebooks
        self.notebookpanel = cmdPanel (parent=self.panel, task=self.task, standalone=self.standalone,
                                       mainFrame=self)
        ### add 'command output' tab also for dialog open from menu
        #         if self.standalone:
        self.goutput = self.notebookpanel.goutput
        self.notebookpanel.OnUpdateValues = self.updateValuesHook
        guisizer.Add (item=self.notebookpanel, proportion=1, flag=wx.EXPAND)

        # status bar
        status_text = _("Enter parameters for ") + self.task.name
        if self.notebookpanel.hasMain:
            # We have to wait for the notebookpanel to be filled in order
            # to know if there actually is a Main tab
            status_text += _(" (those in bold typeface are required)")
        try:
            self.task.getCmd()
            self.updateValuesHook()
        except ValueError:
            self.SetStatusText( status_text )

        # buttons
        btnsizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        # cancel
        self.btn_cancel = wx.Button(parent=self.panel, id=wx.ID_CLOSE)
        self.btn_cancel.SetToolTipString(_("Close this window without executing the command (Ctrl+Q)"))
        btnsizer.Add(item=self.btn_cancel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER, border=10)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        # help
        self.btn_help = wx.Button(parent=self.panel, id=wx.ID_HELP)
        self.btn_help.SetToolTipString(_("Show manual page of the command (Ctrl+H)"))
        self.btn_help.Bind(wx.EVT_BUTTON, self.OnHelp)
        if not hasattr(self.notebookpanel, "manual_tab_id"):
            self.btn_help.Hide()
        if self.get_dcmd is not None: # A callback has been set up
            btn_apply = wx.Button(parent=self.panel, id=wx.ID_APPLY)
            btn_ok = wx.Button(parent=self.panel, id=wx.ID_OK)
            btn_ok.SetDefault()

            btnsizer.Add(item=btn_apply, proportion=0,
                         flag=wx.ALL | wx.ALIGN_CENTER,
                         border=10)
            btnsizer.Add(item=btn_ok, proportion=0,
                         flag=wx.ALL | wx.ALIGN_CENTER,
                         border=10)

            btn_apply.Bind(wx.EVT_BUTTON, self.OnApply)
            btn_ok.Bind(wx.EVT_BUTTON, self.OnOK)
        else: # We're standalone
            # run
            self.btn_run = wx.Button(parent=self.panel, id=wx.ID_OK, label= _("&Run"))
            self.btn_run.SetToolTipString(_("Run the command (Ctrl+R)"))
            self.btn_run.SetDefault()
            # abort
            ### self.btn_abort = wx.Button(parent=self.panel, id=wx.ID_STOP)
            ### self.btn_abort.SetToolTipString(_("Abort the running command"))
            ### self.btn_abort.Enable(False)
            # copy
            self.btn_clipboard = wx.Button(parent=self.panel, id=wx.ID_COPY, label = _("C&opy"))
            self.btn_clipboard.SetToolTipString(_("Copy the current command string to the clipboard (Ctrl+C)"))

            ### btnsizer.Add(item=self.btn_abort, proportion=0,
            ### flag=wx.ALL | wx.ALIGN_CENTER,
            ### border=10)

            btnsizer.Add(item=self.btn_run, proportion=0,
                         flag=wx.ALL | wx.ALIGN_CENTER,
                         border=10)

            btnsizer.Add(item=self.btn_clipboard, proportion=0,
                         flag=wx.ALL | wx.ALIGN_CENTER,
                         border=10)

            self.btn_run.Bind(wx.EVT_BUTTON, self.OnRun)
            ### self.btn_abort.Bind(wx.EVT_BUTTON, self.OnAbort)
            self.btn_clipboard.Bind(wx.EVT_BUTTON, self.OnCopy)

        # add help button
        btnsizer.Add(item=self.btn_help, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

        guisizer.Add(item=btnsizer, proportion=0, flag=wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT,
                     border = 30)

        if self.parent is not None:
            self.outputType = None
            for p in self.task.params:
                if p.get('name', '') == 'output':
                    self.outputType = p.get('prompt', None)
                    break
            if self.outputType in ('raster', 'vector', '3d-raster'):
                # add newly created map into layer tree
                self.addbox = wx.CheckBox(parent=self.panel,
                                          label=_('Add created map into layer tree'), style = wx.NO_BORDER)
                self.addbox.SetValue(UserSettings.Get(group='cmd', key='addNewLayer', subkey='enabled'))
                guisizer.Add(item=self.addbox, proportion=0,
                             flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                             border=5)
        
        if self.get_dcmd is None:
            # close dialog when command is terminated
            self.closebox = wx.CheckBox(parent=self.panel,
                                        label=_('Close dialog on finish'), style = wx.NO_BORDER)
            self.closebox.SetValue(UserSettings.Get(group='cmd', key='closeDlg', subkey='enabled'))
            guisizer.Add(item=self.closebox, proportion=0,
                         flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                         border=5)

        self.Bind(wx.EVT_CLOSE,  self.OnCancel)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        
        #constrained_size = self.notebookpanel.GetSize()
        # 80 takes the tabbar into account
        #self.notebookpanel.SetSize( (constrained_size[0] + 25, constrained_size[1]) ) 
        #self.notebookpanel.Layout()

        #
        # do layout
        #
        guisizer.SetSizeHints(self.panel)
        # called automatically by SetSizer()
        self.panel.SetAutoLayout(True) 
        self.panel.SetSizerAndFit(guisizer)
        
        sizeFrame = self.GetBestSize()
        self.SetMinSize(sizeFrame)
        self.SetSize((sizeFrame[0], sizeFrame[1] +
                      self.notebookpanel.constrained_size[1] -
                      self.notebookpanel.panelMinHeight))

        # thread to update dialog
        # create queues
        self.requestQ = Queue.Queue()
        self.resultQ = Queue.Queue()
        self.updateThread = UpdateQThread(self.notebookpanel, self.requestQ, self.resultQ)

        self.Layout()

        #keep initial window size limited for small screens
        width,height = self.GetSizeTuple()
        if width > 640: width = 640
        if height > 480: height = 480
        self.SetSize((width,height))

    def updateValuesHook(self):
        """!Update status bar data"""
        self.SetStatusText(' '.join(self.notebookpanel.createCmd(ignoreErrors = True)) )

    def OnKeyUp(self, event):
        """!Key released (check hot-keys)"""
        try:
            kc = chr(event.GetKeyCode())
        except ValueError:
            event.Skip()
            return
        
        if not event.ControlDown():
            event.Skip()
            return
        
        if kc == 'Q':
            self.OnCancel(None)
        elif kc == 'S':
            self.OnAbort(None)
        elif kc == 'H':
            self.OnHelp(None)
        elif kc == 'R':
            self.OnRun(None)
        elif kc == 'C':
            self.OnCopy(None)
        
        event.Skip()

    def OnOK(self, event):
        """!OK button pressed"""
        cmd = self.OnApply(event)
        if cmd is not None and self.get_dcmd is not None:
            self.OnCancel(event)

    def OnApply(self, event):
        """!Apply the command"""
        cmd = self.createCmd()

        if cmd is not None and self.get_dcmd is not None:
            # return d.* command to layer tree for rendering
            self.get_dcmd(cmd, self.layer, {"params": self.task.params, 
                                            "flags" :self.task.flags},
                          self)
            # echo d.* command to output console
            # self.parent.writeDCommand(cmd)

        return cmd

    def OnRun(self, event):
        """!Run the command"""
        cmd = self.createCmd()
        
        if cmd == None or len(cmd) < 2:
            return

        if cmd[0][0:2] != "d.":
            # Send any non-display command to parent window (probably wxgui.py)
            # put to parents
            # switch to 'Command output'
            if self.notebookpanel.notebook.GetSelection() != self.notebookpanel.goutputId:
                self.notebookpanel.notebook.SetSelection(self.notebookpanel.goutputId)
            
            try:
                if self.task.path:
                    cmd[0] = self.task.path # full path
                self.goutput.RunCmd(cmd)
            except AttributeError, e:
                print >> sys.stderr, "%s: Propably not running in wxgui.py session?" % (e)
                print >> sys.stderr, "parent window is: %s" % (str(self.parent))
            # Send any other command to the shell.
        else:
            gcmd.Command(cmd)

        # update buttons status
        for btn in (self.btn_run,
                    self.btn_cancel,
                    self.btn_clipboard,
                    self.btn_help):
            btn.Enable(False)
        ### self.btn_abort.Enable(True)

    def OnAbort(self, event):
        """!Abort running command"""
        event = goutput.wxCmdAbort(aborted=True)
        wx.PostEvent(self.goutput, event)

    def OnCopy(self, event):
        """!Copy the command"""
        cmddata = wx.TextDataObject()
        # list -> string
        cmdstring = ' '.join(self.createCmd(ignoreErrors=True))
        cmddata.SetText(cmdstring)
        if wx.TheClipboard.Open():
#            wx.TheClipboard.UsePrimarySelection(True)
            wx.TheClipboard.SetData(cmddata)
            wx.TheClipboard.Close()
            self.SetStatusText( _("'%s' copied to clipboard") % \
                                    (cmdstring))

    def OnCancel(self, event):
        """!Cancel button pressed"""
        self.MakeModal(False)
        
        if self.get_dcmd and \
                self.parent and \
                self.parent.GetName() in ('LayerTree',
                                          'MapWindow'):
            # display decorations and 
            # pressing OK or cancel after setting layer properties
            if self.task.name in ['d.barscale','d.legend','d.histogram'] \
                or len(self.parent.GetPyData(self.layer)[0]['cmd']) >= 1:
                self.Hide()
            # canceled layer with nothing set
            elif len(self.parent.GetPyData(self.layer)[0]['cmd']) < 1:
                self.parent.Delete(self.layer)
                self.Destroy()
        else:
            # cancel for non-display commands
            self.Destroy()

    def OnHelp(self, event):
        """!Show manual page (switch to the 'Manual' notebook page)"""
        if hasattr(self.notebookpanel, "manual_tab_id"):
            self.notebookpanel.notebook.SetSelection(self.notebookpanel.manual_tab_id)
            self.notebookpanel.OnPageChange(None)
        
        if event:    
            event.Skip()
        
    def createCmd(self, ignoreErrors = False):
        """!Create command string (python list)"""
        return self.notebookpanel.createCmd(ignoreErrors=ignoreErrors)

class cmdPanel(wx.Panel):
    """
    A panel containing a notebook dividing in tabs the different guisections of the GRASS cmd.
    """
    def __init__( self, parent, task, standalone, mainFrame, *args, **kwargs ):
        wx.Panel.__init__( self, parent, *args, **kwargs )

        self.parent = mainFrame
        self.task = task
        fontsize = 10
        
        # Determine tab layout
        sections = []
        is_section = {}
        not_hidden = [ p for p in self.task.params + self.task.flags if not p.get( 'hidden','no' ) == 'yes' ]

        self.label_id = [] # wrap titles on resize

        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        for task in not_hidden:
            if task.get( 'required','no' ) == 'yes':
                # All required go into Main, even if they had defined another guisection
                task['guisection'] = _( 'Required' )
            if task.get( 'guisection','' ) == '':
                # Undefined guisections end up into Options
                task['guisection'] = _( 'Optional' )
            if not is_section.has_key(task['guisection']):
                # We do it like this to keep the original order, except for Main which goes first
                is_section[task['guisection']] = 1
                sections.append( task['guisection'] )
            else:
                is_section[ task['guisection'] ] += 1
        del is_section

        # 'Required' tab goes first, 'Optional' as the last one
        for (newidx,content) in [ (0,_( 'Required' )), (len(sections)-1,_('Optional')) ]:
            if content in sections:
                idx = sections.index( content )
                sections[idx:idx+1] = []
                sections[newidx:newidx] =  [content]

        panelsizer = wx.BoxSizer(orient=wx.VERTICAL)

        # Build notebook
        nbStyle = globalvar.FNPageStyle
        self.notebook = FN.FlatNotebook( self, id=wx.ID_ANY, style=nbStyle)
        self.notebook.SetTabAreaColour(globalvar.FNPageColor)
        self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChange)

        tab = {}
        tabsizer = {}
        for section in sections:
            tab[section] = wx.ScrolledWindow( parent=self.notebook )
            tab[section].SetScrollRate(10,10)
            tabsizer[section] = wx.BoxSizer(orient=wx.VERTICAL)
            self.notebook.AddPage( tab[section], text=section )

        # are we running from command line?
        ### add 'command output' tab regardless standalone dialog
        if self.parent.get_dcmd is None:
            self.goutput = goutput.GMConsole(parent=self, margin=False,
                                             pageid=self.notebook.GetPageCount())
            self.goutputId = self.notebook.GetPageCount()
            self.outpage = self.notebook.AddPage(self.goutput, text=_("Command output") )
        else:
            self.goutput = None
            self.goutputId = -1
        
        self.manual_tab = helpPanel(parent = self.notebook, grass_command = self.task.name)
        self.manual_tabsizer = wx.BoxSizer(wx.VERTICAL)
        if not os.path.isfile(self.manual_tab.fspath + self.task.name + ".html"):
            self.manual_tab.Hide()
        else:
            self.notebook.AddPage(self.manual_tab, text=_("Manual"))
            self.manual_tab_id = self.notebook.GetPageCount() - 1
        
        self.notebook.SetSelection(0)

        panelsizer.Add(item=self.notebook, proportion=1, flag=wx.EXPAND )

        #
        # flags
        #
        text_style = wx.FONTWEIGHT_NORMAL
        visible_flags = [ f for f in self.task.flags if not f.get( 'hidden', 'no' ) == 'yes' ]
        for f in visible_flags:
            which_sizer = tabsizer[ f['guisection'] ]
            which_panel = tab[ f['guisection'] ]
            # if label is given: description -> tooltip
            if f.get('label','') != '':
                title = text_beautify( f['label'])
                tooltip = text_beautify ( f['description'], width=-1)
            else:
                title = text_beautify( f['description'] )
                tooltip = None
            title_sizer = wx.BoxSizer(wx.HORIZONTAL)
            rtitle_txt = wx.StaticText(parent=which_panel,
                                       label = '(' + f['name'] + ')')
            chk = wx.CheckBox(parent=which_panel, label = title, style = wx.NO_BORDER)
            self.label_id.append(chk.GetId())
            if tooltip:
                chk.SetToolTipString(tooltip)
            if 'value' in f:
                chk.SetValue( f['value'] )
            title_sizer.Add(item=chk, proportion=1,
                            flag=wx.EXPAND)
            title_sizer.Add(item=rtitle_txt, proportion=0,
                            flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            which_sizer.Add(item=title_sizer, proportion=0,
                            flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=5)
            f['wxId'] = [ chk.GetId(), ]
            chk.Bind(wx.EVT_CHECKBOX, self.OnSetValue)
            if f['name'] in ('verbose', 'quiet'):
                chk.Bind(wx.EVT_CHECKBOX, self.OnVerbosity)
                vq = UserSettings.Get(group='cmd', key='verbosity', subkey='selection')
                if f['name'] == vq:
                    chk.SetValue(True)
                    f['value'] = True
            elif f['name'] == 'overwrite':
                chk.SetValue(UserSettings.Get(group='cmd', key='overwrite', subkey='enabled'))
                f['value'] = UserSettings.Get(group='cmd', key='overwrite', subkey='enabled')
                
        #
        # parameters
        #
        visible_params = [ p for p in self.task.params if not p.get( 'hidden', 'no' ) == 'yes' ]
        
        try:
            first_param = visible_params[0]
        except IndexError:
            first_param = None
        
        for p in visible_params:
            which_sizer = tabsizer[ p['guisection'] ]
            which_panel = tab[ p['guisection'] ]
            # if label is given -> label and description -> tooltip
            # otherwise description -> lavel
            if p.get('label','') != '':
                title = text_beautify( p['label'] )
                tooltip = text_beautify ( p['description'], width = -1)
            else:
                title = text_beautify( p['description'] )
                tooltip = None
            txt = None

            # text style (required -> bold)
            if p.get('required','no') == 'no':
                text_style = wx.FONTWEIGHT_NORMAL
            else:
                text_style = wx.FONTWEIGHT_BOLD

            # title sizer (description, name, type)
            if (len(p.get('values', []) ) > 0) and \
                    p.get('multiple', 'no') == 'yes' and \
                    p.get('gisprompt',False) == False and \
                    p.get('type', '') == 'string':
                title_txt = wx.StaticBox (parent=which_panel, id=wx.ID_ANY)
            else:
                title_sizer = wx.BoxSizer(wx.HORIZONTAL)
                title_txt = wx.StaticText(parent=which_panel)
                rtitle_txt = wx.StaticText(parent=which_panel,
                                           label = '(' + p['name'] + ', ' + p['type'] + ')')
                title_sizer.Add(item=title_txt, proportion=1,
                                flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)
                title_sizer.Add(item=rtitle_txt, proportion=0,
                                flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.TOP, border=5)
                which_sizer.Add(item=title_sizer, proportion=0,
                                flag=wx.EXPAND)
            self.label_id.append(title_txt.GetId())

            # title expansion
            if p.get('multiple','no') == 'yes' and len( p.get('values','') ) == 0:
                title = _("[multiple]") + " " + title
                if p.get('value','') ==  '' :
                    p['value'] = p.get('default','')

            if ( len(p.get('values', []) ) > 0):
                valuelist      = map(str, p.get('values',[]))
                valuelist_desc = map(unicode, p.get('values_desc',[]))

                if p.get('multiple', 'no') == 'yes' and \
                        p.get('gisprompt',False) == False and \
                        p.get('type', '') == 'string':
                    title_txt.SetLabel(" %s: (%s, %s) " % (title, p['name'], p['type']))
                    if len(valuelist) > 6:
                        hSizer=wx.StaticBoxSizer ( box=title_txt, orient=wx.VERTICAL )
                    else:
                        hSizer=wx.StaticBoxSizer ( box=title_txt, orient=wx.HORIZONTAL )
                    isEnabled = {}
                    # copy default values
                    if p['value'] == '':
                        p['value'] = p.get('default', '')
                        
                    for defval in p.get('value', '').split(','):
                        isEnabled[ defval ] = 'yes'
                        # for multi checkboxes, this is an array of all wx IDs
                        # for each individual checkbox
                        p[ 'wxId' ] = list()
                    idx = 0
                    for val in valuelist:
                        try:
                            label = valuelist_desc[idx]
                        except IndexError:
                            label = val
                        
                        chkbox = wx.CheckBox( parent=which_panel,
                                              label = text_beautify(label))
                        p[ 'wxId' ].append( chkbox.GetId() )
                        if isEnabled.has_key(val):
                            chkbox.SetValue( True )
                        hSizer.Add( item=chkbox, proportion=0,
                                    flag=wx.ADJUST_MINSIZE | wx.ALL, border=1 )
                        chkbox.Bind(wx.EVT_CHECKBOX, self.OnCheckBoxMulti)

                        idx += 1
                        
                    which_sizer.Add( item=hSizer, proportion=0,
                                     flag=wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5 )
                elif p.get('gisprompt', False) == False:
                    if len(valuelist) == 1: # -> textctrl
                        title_txt.SetLabel("%s. %s %s" % (title, _('Valid range'),
                                                          str(valuelist[0]) + ':'))
                        
                        if p.get('type','') == 'integer' and \
                                p.get('multiple','no') == 'no':

                            # for multiple integers use textctrl instead of spinsctrl
                            try:
                                minValue, maxValue = map(int, valuelist[0].split('-'))
                            except ValueError:
                                minValue = -1e6
                                maxValue = 1e6
                            txt2 = wx.SpinCtrl(parent=which_panel, id=wx.ID_ANY, size=globalvar.DIALOG_SPIN_SIZE,
                                               min=minValue, max=maxValue)
                            txt2.SetName("SpinCtrl")
                            style = wx.BOTTOM | wx.LEFT
                        else:
                            txt2 = wx.TextCtrl(parent=which_panel, value = p.get('default',''))
                            txt2.SetName("TextCtrl")
                            style = wx.EXPAND | wx.BOTTOM | wx.LEFT
                        
                        if p.get('value', '') != '':
                            # parameter previously set
                            if txt2.GetName() == "SpinCtrl":
                                txt2.SetValue(int(p['value']))
                            else:
                                txt2.SetValue(p['value'])
                        
                        which_sizer.Add(item=txt2, proportion=0,
                                        flag=style, border=5)

                        p['wxId'] = [ txt2.GetId(), ]
                        txt2.Bind(wx.EVT_TEXT, self.OnSetValue)
                    else:
                        # list of values (combo)
                        title_txt.SetLabel(title + ':')
                        cb = wx.ComboBox(parent=which_panel, id=wx.ID_ANY, value=p.get('default',''),
                                         size=globalvar.DIALOG_COMBOBOX_SIZE,
                                         choices=valuelist, style=wx.CB_DROPDOWN | wx.CB_READONLY)
                        if p.get('value','') != '':
                            cb.SetValue(p['value']) # parameter previously set
                        which_sizer.Add( item=cb, proportion=0,
                                         flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT, border=5)
                        p['wxId'] = [ cb.GetId(), ]
                        cb.Bind( wx.EVT_COMBOBOX, self.OnSetValue)

            # text entry
            if (p.get('type','string') in ('string','integer','float')
                and len(p.get('values',[])) == 0
                and p.get('gisprompt',False) == False
                and p.get('prompt','') != 'color'):

                title_txt.SetLabel(title + ':' )
                if p.get('multiple','yes') == 'yes' or \
                        p.get('type', 'string') in ('string', 'float') or \
                        len(p.get('key_desc', [])) > 1:
                    txt3 = wx.TextCtrl(parent=which_panel, value = p.get('default',''))
                    
                    if p.get('value','') != '':
                        txt3.SetValue(str(p['value'])) # parameter previously set

                    txt3.Bind(wx.EVT_TEXT, self.OnSetValue)
                    style = wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT
                else:
                    minValue = -1e9
                    maxValue = 1e9
                    txt3 = wx.SpinCtrl(parent=which_panel, value=p.get('default',''),
                                       size=globalvar.DIALOG_SPIN_SIZE,
                                       min=minValue, max=maxValue)
                    if p.get('value','') != '':
                        txt3.SetValue(int(p['value'])) # parameter previously set

                    txt3.Bind(wx.EVT_SPINCTRL, self.OnSetValue)
                    txt3.Bind(wx.EVT_TEXT, self.OnSetValue)
                    style = wx.BOTTOM | wx.LEFT | wx.RIGHT
                
                which_sizer.Add(item=txt3, proportion=0,
                                flag=style, border=5)
                p['wxId'] = [ txt3.GetId(), ]

            #
            # element selection tree combobox (maps, icons, regions, etc.)
            #
            if p.get('gisprompt', False) == True:
                title_txt.SetLabel(title + ':')
                # GIS element entry
                if p.get('prompt','') not in ('color',
                                              'color_none',
                                              'dbdriver',
                                              'dbname',
                                              'dbtable',
                                              'dbcolumn',
                                              'layer',
                                              'layer_all') and \
                       p.get('element', '') != 'file':
                    if p.get('multiple', 'no') == 'yes':
                        multiple = True
                    else:
                        multiple = False
                    if p.get('age', '') == 'new':
                        mapsets = [grass.gisenv()['MAPSET'],]
                    else:
                        mapsets = None
                        
                    selection = gselect.Select(parent=which_panel, id=wx.ID_ANY,
                                               size=globalvar.DIALOG_GSELECT_SIZE,
                                               type=p.get('element', ''),
                                               multiple=multiple, mapsets=mapsets)
                    if p.get('value','') != '':
                        selection.SetValue(p['value']) # parameter previously set
                    
                    # A select.Select is a combobox with two children: a textctl and a popupwindow;
                    # we target the textctl here
                    p['wxId'] = [selection.GetChildren()[0].GetId(), ]
                    selection.GetChildren()[0].Bind(wx.EVT_TEXT, self.OnSetValue)
                    if p.get('prompt', '') == 'vector':
                        selection.Bind(wx.EVT_TEXT, self.OnUpdateSelection)
                        
                        if p.get('age', '') == 'old':
                            # OGR supported (read-only)
                            hsizer = wx.GridBagSizer(vgap=5, hgap=5)
                            
                            hsizer.Add(item=selection,
                                       flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_TOP,
                                       border=5,
                                       pos = (0, 0))
                            
                            # format (native / ogr)
                            rbox = wx.RadioBox(parent = which_panel, id = wx.ID_ANY,
                                               label = " %s " % _("Format"),
                                               style = wx.RA_SPECIFY_ROWS,
                                               size = (100, -1),
                                               choices = [_("Native"), _("OGR")])
                            rbox.SetName('VectorFormat')
                            rbox.Bind(wx.EVT_RADIOBOX, self.OnVectorFormat)
                            
                            hsizer.Add(item=rbox,
                                       flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.ALIGN_TOP,
                                       pos = (0, 1),
                                       span = (3, 1),
                                       border=5)
                            
                            ogrSelection = filebrowse.DirBrowseButton(parent = which_panel, id = wx.ID_ANY, 
                                                                      size = globalvar.DIALOG_GSELECT_SIZE,
                                                                      labelText = '',
                                                                      dialogTitle = _('Choose OGR data source'),
                                                                      buttonText = _('Browse'),
                                                                      startDirectory = os.getcwd())
                            for win in ogrSelection.GetChildren():
                                win.SetName('OgrSelect')
                            ogrSelection.Enable(False)
                            ogrSelection.Bind(wx.EVT_TEXT, self.OnUpdateSelection)
                            ogrSelection.Bind(wx.EVT_TEXT, self.OnSetValue)
                                                        
                            hsizer.Add(item=wx.StaticText(parent = which_panel, id = wx.ID_ANY,
                                                          label = _("Name of OGR data source:")),
                                       flag=wx.ALIGN_BOTTOM | wx.LEFT,
                                       pos = (1, 0),
                                       border=5)
                            
                            hsizer.Add(item=ogrSelection,
                                       flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.ALIGN_TOP,
                                       pos = (2, 0),
                                       border=5)
                            
                            which_sizer.Add(item = hsizer, proportion = 0)
                            
                            p['wxId'].append(rbox.GetId())
                            p['wxId'].append(ogrSelection.GetChildren()[1].GetId())
                        else:
                            which_sizer.Add(item=selection, proportion=0,
                                            flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL,
                                            border=5)
                    else:
                        which_sizer.Add(item=selection, proportion=0,
                                        flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL,
                                        border=5)
                        
                # layer, dbdriver, dbname, dbcolumn, dbtable entry
                elif p.get('prompt', '') in ('dbdriver',
                                             'dbname',
                                             'dbtable',
                                             'dbcolumn',
                                             'layer',
                                             'layer_all'):
                    if p.get('multiple', 'no') == 'yes':
                        win = wx.TextCtrl(parent=which_panel, value = p.get('default',''),
                                          size=globalvar.DIALOG_TEXTCTRL_SIZE)
                        win.Bind(wx.EVT_TEXT, self.OnSetValue)
                    else:
                        if p.get('prompt', '') in ('layer',
                                                   'layer_all'):
                            if p.get('prompt', '') == 'layer_all':
                                all = True
                            else:
                                all = False
                            win = wx.BoxSizer(wx.HORIZONTAL)
                            if p.get('age', 'old_layer') == 'old_layer':
                                win1 = gselect.LayerSelect(parent=which_panel,
                                                          all=all,
                                                          default=p['default'])
                                win1.Bind(wx.EVT_CHOICE, self.OnUpdateSelection)
                                win1.Bind(wx.EVT_CHOICE, self.OnSetValue)
                            else:
                                win1 = wx.SpinCtrl(parent=which_panel, id=wx.ID_ANY,
                                                  min=1, max=100, initial=int(p['default']))
                                win1.Bind(wx.EVT_SPINCTRL, self.OnSetValue)
                            win2 = gselect.LayerNameSelect(parent = which_panel)
                            win2.Bind(wx.EVT_TEXT, self.OnSetValue)
                            p['wxId'] = [ win1.GetId(), win2.GetId() ]
                            win.Add(item = win1, proportion = 0)
                            win.Add(item = win2, proportion = 0,
                                    flag = wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
                                    border = 5)

                        elif p.get('prompt', '') == 'dbdriver':
                            win = gselect.DriverSelect(parent=which_panel,
                                                       choices=p['values'],
                                                       value=p['default'])
                            win.Bind(wx.EVT_COMBOBOX, self.OnUpdateSelection)
                            win.Bind(wx.EVT_COMBOBOX, self.OnSetValue)
                        elif p.get('prompt', '') == 'dbname':
                            win = gselect.DatabaseSelect(parent=which_panel,
                                                         value=p['default'])
                            win.Bind(wx.EVT_TEXT, self.OnUpdateSelection)
                            win.Bind(wx.EVT_TEXT, self.OnSetValue)
                        elif p.get('prompt', '') == 'dbtable':
                            if p.get('age', 'old_dbtable') == 'old_dbtable':
                                win = gselect.TableSelect(parent=which_panel)
                                win.Bind(wx.EVT_COMBOBOX, self.OnUpdateSelection)
                                win.Bind(wx.EVT_COMBOBOX, self.OnSetValue)
                            else:
                                win = wx.TextCtrl(parent=which_panel, value = p.get('default',''),
                                                  size=globalvar.DIALOG_TEXTCTRL_SIZE)
                                win.Bind(wx.EVT_TEXT, self.OnSetValue)
                        elif p.get('prompt', '') == 'dbcolumn':
                            win = gselect.ColumnSelect(parent=which_panel)
                            win.Bind(wx.EVT_COMBOBOX, self.OnSetValue)

                    try:
                        p['wxId'] = [ win.GetId(), ]
                    except AttributeError:
                        pass
                    
                    which_sizer.Add(item=win, proportion=0,
                                    flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT, border=5)
                # color entry
                elif p.get('prompt', '') in ('color',
                                             'color_none'):
                    default_color = (200,200,200)
                    label_color = _("Select Color")
                    if p.get('default','') != '':
                        default_color, label_color = color_resolve( p['default'] )
                    if p.get('value','') != '': # parameter previously set
                        default_color, label_color = color_resolve( p['value'] )
                    if p.get('prompt', '') == 'color_none':
                        this_sizer = wx.BoxSizer(orient=wx.HORIZONTAL )
                    else:
                        this_sizer = which_sizer
                    btn_colour = csel.ColourSelect(parent=which_panel, id=wx.ID_ANY,
                                                   label=label_color, colour=default_color,
                                                   pos=wx.DefaultPosition, size=(150,-1) )
                    this_sizer.Add(item=btn_colour, proportion=0,
                                   flag=wx.ADJUST_MINSIZE | wx.BOTTOM | wx.LEFT, border=5)
                    # For color selectors, this is a two-member array, holding the IDs of
                    # the selector proper and either a "transparent" button or None
                    p['wxId'] = [btn_colour.GetId(),]
                    btn_colour.Bind(csel.EVT_COLOURSELECT,  self.OnColorChange )
                    if p.get('prompt', '') == 'color_none':
                        none_check = wx.CheckBox(which_panel, wx.ID_ANY, _("Transparent") )
                        if p.get('value','') != '' and p.get('value',[''])[0] == "none":
                            none_check.SetValue(True)
                        else:
                            none_check.SetValue(False)
                        # none_check.SetFont( wx.Font( fontsize, wx.FONTFAMILY_DEFAULT, wx.NORMAL, text_style, 0, ''))
                        this_sizer.Add(item=none_check, proportion=0,
                                       flag=wx.ADJUST_MINSIZE | wx.LEFT | wx.RIGHT | wx.TOP, border=5)
                        which_sizer.Add( this_sizer )
                        none_check.Bind(wx.EVT_CHECKBOX, self.OnColorChange)
                        p['wxId'].append( none_check.GetId() )
                    else:
                        p['wxId'].append(None)
                # file selector
                elif p.get('prompt','') != 'color' and p.get('element', '') == 'file':
                    fbb = filebrowse.FileBrowseButton(parent=which_panel, id=wx.ID_ANY, 
                                                      size=globalvar.DIALOG_GSELECT_SIZE, labelText='',
                                                      dialogTitle=_('Choose %s') % \
                                                          p.get('description',_('File')),
                                                      buttonText=_('Browse'),
                                                      startDirectory=os.getcwd(), fileMode=0,
                                                      changeCallback=self.OnSetValue)
                    if p.get('value','') != '':
                        fbb.SetValue(p['value']) # parameter previously set
                    which_sizer.Add(item=fbb, proportion=0,
                                    flag=wx.EXPAND | wx.RIGHT, border=5)
                    # A file browse button is a combobox with two children:
                    # a textctl and a button;
                    # we have to target the button here
                    p['wxId'] = [ fbb.GetChildren()[1].GetId(), ]

            if title_txt is not None:
                # create tooltip if given
                if len(p['values_desc']) > 0:
                    if tooltip:
                        tooltip += 2 * os.linesep
                    else:
                        tooltip = ''
                    if len(p['values']) == len(p['values_desc']):
                        for i in range(len(p['values'])):
                            tooltip += p['values'][i] + ': ' + p['values_desc'][i] + os.linesep
                    tooltip.strip(os.linesep)
                if tooltip:
                    title_txt.SetToolTipString(tooltip)

            if p == first_param:
                if len(p['wxId']) > 0:
                    self.FindWindowById(p['wxId'][0]).SetFocus()
        
        #
        # set widget relations for OnUpdateSelection
        #
        pMap = None
        pLayer = []
        pDriver = None
        pDatabase = None
        pTable = None
        pColumn = []
        for p in self.task.params:
            if p.get('gisprompt', False) == False:
                continue
            
            guidep = p.get('guidependency', '')
            
            if guidep:
                # fixed options dependency defined
                options = guidep.split(',')
                for opt in options:
                    pOpt = self.task.get_param(opt, element = 'name', raiseError = False)
                    if id:
                        if not p.has_key('wxId-bind'):
                            p['wxId-bind'] = list()
                        p['wxId-bind'] += pOpt['wxId']
                continue
            
            prompt = p.get('element', '')
            if prompt == 'vector':
                name = p.get('name', '')
                if name in ('map', 'input'):
                    pMap = p
            elif prompt == 'layer':
                pLayer.append(p)
            elif prompt == 'dbcolumn':
                pColumn.append(p)
            elif prompt == 'dbdriver':
                pDriver = p
            elif prompt == 'dbname':
                pDatabase = p
            elif prompt == 'dbtable':
                pTable = p
        
        # collect ids
        pColumnIds = []
        for p in pColumn:
            pColumnIds += p['wxId']
        pLayerIds = []
        for p in pLayer:
            pLayerIds += p['wxId']
        
        # set wxId-bindings
        if pMap:
            pMap['wxId-bind'] = copy.copy(pColumnIds)
            if pLayer:
                pMap['wxId-bind'] += pLayerIds
        if len(pLayer) == 1:
            # TODO: fix modules with more 'layer' options
            pLayer[0]['wxId-bind'] = copy.copy(pColumnIds)

        if pDriver and pTable:
            pDriver['wxId-bind'] = pTable['wxId']

        if pDatabase and pTable:
            pDatabase['wxId-bind'] = pTable['wxId']

        if pTable and pColumnIds:
            pTable['wxId-bind'] = pColumnIds
        
	#
	# determine panel size
	#
        maxsizes = (0,0)
        for section in sections:
            # tabsizer[section].SetSizeHints( tab[section] )
            #tab[section].SetAutoLayout(True)
            tab[section].SetSizer( tabsizer[section] )
            tabsizer[section].Fit( tab[section] )
            tab[section].Layout()
            minsecsizes = tabsizer[section].GetSize()
            maxsizes = map( lambda x: max( maxsizes[x], minsecsizes[x] ), (0,1) )

        # TODO: be less arbitrary with these 600
        self.panelMinHeight = 100
        self.constrained_size = (min(600, maxsizes[0]) + 25, min(400, maxsizes[1]) + 25)
        for section in sections:
            tab[section].SetMinSize( (self.constrained_size[0], self.panelMinHeight) )
            # tab[section].SetMinSize( constrained_size )

        if self.manual_tab.Ok:
            self.manual_tab.SetMinSize( (self.constrained_size[0], self.panelMinHeight) )
            # manual_tab.SetMinSize( constrained_size )

        self.SetSizer( panelsizer )
        panelsizer.Fit(self.notebook)

        self.hasMain = tab.has_key( _('Required') ) # publish, to enclosing Frame for instance

        self.Bind(EVT_DIALOG_UPDATE, self.OnUpdateDialog)

    def OnVectorFormat(self, event):
        """!Change vector format (native / ogr)"""
        sel = event.GetSelection()
        idEvent = event.GetId()
        p = self.task.get_param(value = idEvent, element = 'wxId', raiseError = False)
        if not p:
            return # should not happen
        
        winNative = None
        winOGR    = None
        for id in p['wxId']:
            if id == idEvent:
                continue
            name = self.FindWindowById(id).GetName()
            if name == 'Select':
                winNative = self.FindWindowById(id + 1)  # fix the mystery (also in nviz_tools.py)
            elif name == 'OgrSelect':
                winOgr = self.FindWindowById(id + 2)
        
        # enable / disable widgets & update values
        if sel == 0:   # -> native
            winOgr.Enable(False)
            winNative.Enable(True)
            p['value'] = winNative.GetValue()
        elif sel == 1: # -> OGR
            winNative.Enable(False)
            winOgr.Enable(True)
            p['value'] = winOgr.GetValue()
        
        self.OnUpdateValues()
        self.OnUpdateSelection(event)
        
    def OnUpdateDialog(self, event):
        for fn, kwargs in event.data.iteritems():
            fn(**kwargs)
        
    def OnVerbosity(self, event):
        """!Verbosity level changed"""
        verbose = self.FindWindowById(self.task.get_flag('verbose')['wxId'][0])
        quiet = self.FindWindowById(self.task.get_flag('quiet')['wxId'][0])
        if event.IsChecked():
            if event.GetId() == verbose.GetId():
                if quiet.IsChecked():
                    quiet.SetValue(False)
                    self.task.get_flag('quiet')['value'] = False
            else:
                if verbose.IsChecked():
                    verbose.SetValue(False)
                    self.task.get_flag('verbose')['value'] = False

        event.Skip()

    def OnPageChange(self, event):
        if not event:
            sel = self.notebook.GetSelection()
        else:
            sel = event.GetSelection()

        if hasattr(self, "manual_tab_id") and \
                sel == self.manual_tab_id:
            # calling LoadPage() is strangely time-consuming (only first call)
            # FIXME: move to helpPage.__init__()
            if not self.manual_tab.Ok:
                wx.Yield()
                self.manual_tab.LoadPage(self.manual_tab.fspath + self.task.name + ".html")
                self.manual_tab.Ok = True

        self.Layout()

    def OnColorChange( self, event ):
        myId = event.GetId()
        for p in self.task.params:
            if 'wxId' in p and myId in p['wxId']:
                has_button = p['wxId'][1] is not None
                if has_button and wx.FindWindowById( p['wxId'][1] ).GetValue() == True:
                    p[ 'value' ] = 'none'
                else:
                    colorchooser = wx.FindWindowById( p['wxId'][0] )
                    new_color = colorchooser.GetValue()[:]
                    # This is weird: new_color is a 4-tuple and new_color[:] is a 3-tuple
                    # under wx2.8.1
                    new_label = rgb2str.get( new_color, ':'.join(map(str,new_color)) )
                    colorchooser.SetLabel( new_label )
                    colorchooser.SetColour( new_color )
                    colorchooser.Refresh()
                    p[ 'value' ] = colorchooser.GetLabel()
        self.OnUpdateValues()

    def OnUpdateValues(self):
        """
        If we were part of a richer interface, report back the current command being built.

        This method should be set by the parent of this panel if needed. It's a hook, actually.
        Beware of what is 'self' in the method def, though. It will be called with no arguments.
        """
        pass

    def OnCheckBoxMulti(self, event):
        """
        Fill the values as a ','-separated string according to current status of the checkboxes.
        """
        me = event.GetId()
        theParam = None
        for p in self.task.params:
            if 'wxId' in p and me in p['wxId']:
                theParam = p
                myIndex = p['wxId'].index( me )

        # Unpack current value list
        currentValues = {}
        for isThere in theParam.get('value', '').split(','):
            currentValues[isThere] = 1
        theValue = theParam['values'][myIndex]

        if event.Checked():
            currentValues[ theValue ] = 1
        else:
            del currentValues[ theValue ]

        # Keep the original order, so that some defaults may be recovered
        currentValueList = [] 
        for v in theParam['values']:
            if currentValues.has_key(v):
                currentValueList.append( v )

        # Pack it back
        theParam['value'] = ','.join( currentValueList )

        self.OnUpdateValues()

    def OnSetValue(self, event):
        """!
        Retrieve the widget value and set the task value field
        accordingly.

        Use for widgets that have a proper GetValue() method, i.e. not
        for selectors.
        """
        myId = event.GetId()
        me  = wx.FindWindowById(myId)
        name = me.GetName()
        
        for porf in self.task.params + self.task.flags:
            if 'wxId' in porf:
                found = False
                porf['wxId']
                for id in porf['wxId']:
                    if id == myId:
                        found = True
                        break
                
                if found:
                    if name in ('LayerSelect', 'DriverSelect', 'TableSelect',
                                'ColumnSelect'):
                        porf['value'] = me.GetStringSelection()
                    else:
                        porf['value'] = me.GetValue()
                    
                    if name == 'OgrSelect':
                        porf['value'] += '@OGR'
                    
        self.OnUpdateValues()
        
        event.Skip()
        
    def OnUpdateSelection(self, event):
        """
        Update dialog (layers, tables, columns, etc.)
        """
        if event:
            self.parent.updateThread.Update(UpdateDialog,
                                            self,
                                            event,
                                            event.GetId(),
                                            self.task)
        else:
            self.parent.updateThread.Update(UpdateDialog,
                                            self,
                                            None,
                                            None,
                                            self.task)
            
    def createCmd( self, ignoreErrors = False ):
        """
        Produce a command line string (list) or feeding into GRASS.

        If ignoreErrors==True then it will return whatever has been
        built so far, even though it would not be a correct command
        for GRASS.
        """
        try:
            cmd = self.task.getCmd( ignoreErrors=ignoreErrors )
        except ValueError, err:
            dlg = wx.MessageDialog(parent=self,
                                   message=unicode(err),
                                   caption=_("Error in %s") % self.task.name,
                                   style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
            dlg.ShowModal()
            dlg.Destroy()
            cmd = None

        return cmd
    
    def OnSize(self, event):
        width = event.GetSize()[0]
        fontsize = self.GetFont().GetPointSize()
        text_width = width / (fontsize - 3)
        if text_width < 70:
            text_width = 70
        
        for id in self.label_id:
            win = self.FindWindowById(id)
            label = win.GetLabel()
            label_new = '\n'.join(textwrap.wrap(label, text_width ))
            win.SetLabel(label_new)
            
        event.Skip()
        
def getInterfaceDescription( cmd ):
    """
    Returns the XML description for the GRASS cmd.

    The DTD must be located in $GISBASE/etc/grass-interface.dtd,
    otherwise the parser will not succeed.

    Note: 'cmd' is given as string
    """
    cmdout = os.popen(cmd + r' --interface-description', "r").read()
    if not len(cmdout) > 0 :
        raise IOError, _("Unable to fetch interface description for command '%s'.") % cmd
    p = re.compile( '(grass-interface.dtd)')
    p.search( cmdout )
    cmdout = p.sub(globalvar.ETCDIR + r'/grass-interface.dtd', cmdout)
    return cmdout

class GrassGUIApp(wx.App):
    """
    Stand-alone GRASS command GUI
    """
    def __init__(self, grass_task):
        self.grass_task = grass_task
        wx.App.__init__(self, False)

    def OnInit(self):
        self.mf = mainFrame(parent=None, ID=wx.ID_ANY, task_description=self.grass_task)
        self.mf.CentreOnScreen()
        self.mf.Show(True)
        self.SetTopWindow(self.mf)
        
        return True

class GUI:
    """
    Parses GRASS commands when module is imported and used
    from Layer Manager.
    """
    def __init__(self, parent=-1):
        self.parent = parent
        self.grass_task = None
        self.cmd = list()

    def GetCmd(self):
        """Get validated command"""
        return self.cmd
    
    def ParseInterface(self, cmd, parser = processTask):
        """!Parse interface

        @param cmd command to be parsed (given as list)
        """
        enc = locale.getdefaultlocale()[1]
        if enc and enc.lower() not in ("utf8", "utf-8"):
            tree = etree.fromstring(getInterfaceDescription(cmd[0]).decode(enc).encode("utf-8"))
        else:
            tree = etree.fromstring(getInterfaceDescription(cmd[0]))
            
        return processTask(tree).GetTask()
    
    def ParseCommand(self, cmd, gmpath=None, completed=None, parentframe=None,
                     show=True, modal=False):
        """
        Parse command

        Note: cmd is given as list

        If command is given with options, return validated cmd list:
        * add key name for first parameter if not given
        * change mapname to mapname@mapset
        """
        start = time.time()
        dcmd_params = {}
        if completed == None:
            get_dcmd = None
            layer = None
            dcmd_params = None
        else:
            get_dcmd = completed[0]
            layer = completed[1]
            if completed[2]:
                dcmd_params.update(completed[2])

        self.parent = parentframe

        # parse the interface decription
        self.grass_task = self.ParseInterface(cmd)

        # if layer parameters previously set, re-insert them into dialog
        if completed is not None:
            if 'params' in dcmd_params:
                self.grass_task.params = dcmd_params['params']
            if 'flags' in dcmd_params:
                self.grass_task.flags = dcmd_params['flags']

        # update parameters if needed && validate command
        if len(cmd) > 1:
            i = 0
            cmd_validated = [cmd[0]]
            for option in cmd[1:]:
                if option[0] == '-': # flag
                    if option[1] == '-':
                        self.grass_task.set_flag(option[2:], True)
                    else:
                        self.grass_task.set_flag(option[1], True)
                    cmd_validated.append(option)
                else: # parameter
                    try:
                        key, value = option.split('=', 1)
                    except:
                        if i == 0: # add key name of first parameter if not given
                            key = self.grass_task.firstParam
                            value = option
                        else:
                            raise ValueError, _("Unable to parse command %s") % ' '.join(cmd)

                    if self.grass_task.get_param(key)['element'] in ['cell', 'vector']:
                        # mapname -> mapname@mapset
                        if '@' not in value:
                            value = value + '@' + grass.gisenv()['MAPSET']
                    self.grass_task.set_param(key, value)
                    cmd_validated.append(key + '=' + value)
                    i = i + 1

            # update original command list
            cmd = cmd_validated
        
        if show is not None:
            self.mf = mainFrame(parent=self.parent, ID=wx.ID_ANY,
                                task_description=self.grass_task,
                                get_dcmd=get_dcmd, layer=layer)
        else:
            self.mf = None
        
        if get_dcmd is not None:
            # update only propwin reference
            get_dcmd(dcmd=None, layer=layer, params=None,
                     propwin=self.mf)

        if show is not None:
            self.mf.notebookpanel.OnUpdateSelection(None)
            if show is True:
                if self.parent:
                    self.mf.CentreOnParent()
                self.mf.Show(show)
                self.mf.MakeModal(modal)
            else:
                self.mf.OnApply(None)
        
        self.cmd = cmd
        
        return self.grass_task

    def GetCommandInputMapParamKey(self, cmd):
        """!Get parameter key for input raster/vector map
        
        @param cmd module name
        
        @return parameter key
        @return None on failure
        """
        # parse the interface decription
        if not self.grass_task:
            tree = etree.fromstring(getInterfaceDescription(cmd))
            self.grass_task = processTask(tree).GetTask()
            
            for p in self.grass_task.params:
                if p.get('name', '') in ('input', 'map'):
                    age = p.get('age', '')
                    prompt = p.get('prompt', '')
                    element = p.get('element', '') 
                    if age == 'old' and \
                            element in ('cell', 'grid3', 'vector') and \
                            prompt in ('raster', '3d-raster', 'vector'):
                        return p.get('name', None)
        return None

class StaticWrapText(wx.StaticText):
    """
    A Static Text field that wraps its text to fit its width, enlarging its height if necessary.
    """
    def __init__(self, parent, id=wx.ID_ANY, label=u'', *args, **kwds):
        self.originalLabel = label
        wx.StaticText.__init__(self, parent, id, u'', *args, **kwds)
        self.SetLabel(label)
        self.Bind(wx.EVT_SIZE, self.onResize)
    
    def SetLabel(self, label):
        self.originalLabel = label
        self.wrappedSize = None
        #self.onResize(None)
        
    def onResize(self, event):
        if not getattr(self, "resizing", False):
            self.resizing = True
            newSize = self.GetSize()
            if self.wrappedSize != newSize:
                wx.StaticText.SetLabel(self, self.originalLabel)
                self.Wrap(newSize.width)
                self.wrappedSize = self.GetMinSize()

                self.SetSize(self.wrappedSize)
            del self.resizing

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print _("usage: %s <grass command>") % sys.argv[0]
        sys.exit()
    if sys.argv[1] != 'test':
        q=wx.LogNull()
        GrassGUIApp(grassTask(sys.argv[1])).MainLoop()
    else: #Test
        # Test grassTask from within a GRASS session
        if os.getenv("GISBASE") is not None:
            task = grassTask( "d.vect" )
            task.get_param('map')['value'] = "map_name"
            task.get_flag('v')['value'] = True
            task.get_param('layer')['value'] = 1
            task.get_param('bcolor')['value'] = "red"
            assert ' '.join( task.getCmd() ) == "d.vect -v map=map_name layer=1 bcolor=red"
        # Test interface building with handmade grassTask,
        # possibly outside of a GRASS session.
        task = grassTask()
        task.name = "TestTask"
        task.description = "This is an artificial grassTask() object intended for testing purposes."
        task.keywords = ["grass","test","task"]
        task.params = [
            {
            "name" : "text",
            "description" : "Descriptions go into tooltips if labels are present, like this one",
            "label" : "Enter some text",
            },{
            "name" : "hidden_text",
            "description" : "This text should not appear in the form",
            "hidden" : "yes"
            },{
            "name" : "text_default",
            "description" : "Enter text to override the default",
            "default" : "default text"
            },{
            "name" : "text_prefilled",
            "description" : "You should see a friendly welcome message here",
            "value" : "hello, world"
            },{
            "name" : "plain_color",
            "description" : "This is a plain color, and it is a compulsory parameter",
            "required" : "yes",
            "gisprompt" : True,
            "prompt" : "color"
            },{
            "name" : "transparent_color",
            "description" : "This color becomes transparent when set to none",
            "guisection" : "tab",
            "gisprompt" : True,
            "prompt" : "color"
            },{
            "name" : "multi",
            "description" : "A multiple selection",
            'default': u'red,green,blue',
            'gisprompt': False,
            'guisection': 'tab',
            'multiple': u'yes',
            'type': u'string',
            'value': '',
            'values': ['red', 'green', u'yellow', u'blue', u'purple', u'other']
            },{
            "name" : "single",
            "description" : "A single multiple-choice selection",
            'values': ['red', 'green', u'yellow', u'blue', u'purple', u'other'],
            "guisection" : "tab"
            },{
            "name" : "large_multi",
            "description" : "A large multiple selection",
            "gisprompt" : False,
            "multiple" : "yes",
            # values must be an array of strings
            "values" : str2rgb.keys() + map( str, str2rgb.values() )
            },{
            "name" : "a_file",
            "description" : "A file selector",
            "gisprompt" : True,
            "element" : "file"
            }
            ]
        task.flags = [
            {
            "name" : "a",
            "description" : "Some flag, will appear in Main since it is required",
            "required" : "yes"
            },{
            "name" : "b",
            "description" : "pre-filled flag, will appear in options since it is not required",
            "value" : True
            },{
            "name" : "hidden_flag",
            "description" : "hidden flag, should not be changeable",
            "hidden" : "yes",
            "value" : True
            }
            ]
        q=wx.LogNull()
        GrassGUIApp( task ).MainLoop()

