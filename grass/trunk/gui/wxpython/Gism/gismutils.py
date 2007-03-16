import os,sys
import wx
import wx.lib.customtreectrl as CT
import wx.combo

import render
import grassenv
import track
import menuform
import optpanels.rastopt as rastopt
import optpanels.vectopt as vectopt
import optpanels.cmdopt as cmdopt

#FIXME??
try:
   import subprocess
except:
   from compat import subprocess


gmpath = os.getenv("GISBASE") + "/etc/wx/gism/"
sys.path.append(gmpath)

icons = ""

if not os.getenv("GRASS_ICONPATH"):
    icons = os.getenv("GISBASE") + "/etc/gui/icons/"
else:
    icons = os.environ["GRASS_ICONPATH"]

class LayerTree(CT.CustomTreeCtrl):
    """
    Creates layer tree structure
    """
    #	def __init__(self, parent, id, pos, size, style):
    def __init__(self, parent,
                 id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.SUNKEN_BORDER,
                 ctstyle=CT.TR_HAS_BUTTONS | CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                 CT.TR_HIDE_ROOT | CT.TR_ROW_LINES | CT.TR_FULL_ROW_HIGHLIGHT,
                 log=None):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style,ctstyle)

        self.SetAutoLayout(True)
        self.SetGradientStyle(1)
        self.EnableSelectionGradient(True)
        self.SetFirstGradientColour(wx.Colour(150, 150, 150))


        self.root = ""      # ID of layer tree root node
        self.layer = {}     # dictionary to index layers in layer tree
        self.node = 0       # index value for layers
        self.optpage = {}   # dictionary of notebook option pages for each map layer
        self.map = {}       # dictionary of map layers, indexed by tree node.
        self.layer_selected = ""   # ID of currently selected layer
        self.layername = "" # name off currently selected layer
        self.layertype = {} # dictionary of layer types for each layer

        self.root = self.AddRoot("Map Layers")
        self.SetPyData(self.root, None)

        #create image list to use with layer tree
        il = wx.ImageList(16, 16, False)

        trgif = wx.Image(icons + r'/element-cell.gif', wx.BITMAP_TYPE_GIF)
        trgif.Rescale(16, 16)
        trgif = trgif.ConvertToBitmap()
        self.rast_icon = il.Add(trgif)
        # print "width=",trgif.GetWidth()
        # print "height=",trgif.GetHeight()
        trgif = wx.Image(icons + r'/element-vector.gif', wx.BITMAP_TYPE_GIF)
        trgif.Rescale(16, 16)
        trgif = trgif.ConvertToBitmap()
        self.vect_icon = il.Add(trgif)

        trgif = wx.Image(icons + r'/gui-cmd.gif', wx.BITMAP_TYPE_GIF)
        trgif.Rescale(16, 16)
        trgif = trgif.ConvertToBitmap()
        self.cmd_icon = il.Add(trgif)

        checksize = il.GetSize(0)
        checkbmp = il.GetBitmap(0)
        # print "checksize=",checksize
        self.AssignImageList(il)

        # self.tree.SetItemImage(self.root, fldridx, wx.TreeItemIcon_Normal)
        # self.tree.SetItemImage(self.root, fldropenidx, wx.TreeItemIcon_Expanded)


        #        for x in range(15):
        #            child = self.AppendItem(self.root, "Item %d" % x)
        #            self.SetPyData(child, None)
        #            self.tree.SetItemImage(child, fldridx, wx.TreeItemIcon_Normal)
        #            self.tree.SetItemImage(child, fldropenidx, wx.TreeItemIcon_Expanded)

        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.onExpandNode)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onCollapseNode)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onActivateLayer)
        self.Bind(wx.EVT_TREE_SEL_CHANGED,    self.onChangeSel)
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.onLayerChecked)

    def AddLayer(self, idx, type):
#        layername = type + ':' + str(self.node)

        if type == 'rast':
            self.map = wx.combo.ComboCtrl(self, size=(250,-1),style=wx.CB_READONLY)
            tcp = TreeCtrlComboPopup()
            self.map.SetPopupControl(tcp)
            tcp.getElementList('cell')

        elif type == 'vect':
            self.map = wx.combo.ComboCtrl(self, size=(250,-1))
            tcp = TreeCtrlComboPopup()
            self.map.SetPopupControl(tcp)
            tcp.getElementList('vector')

        elif type == 'cmd':
            self.map = wx.TextCtrl(self, -1,
                                               "Enter a GRASS command here",
                                               wx.DefaultPosition, (250,40),
                                               style=wx.TE_MULTILINE|wx.TE_WORDWRAP)

        self.map.Bind(wx.EVT_TEXT, self.onMapChanged)

        if self.node >0 and self.layer_selected:
            self.layer = self.InsertItem(self.root, self.layer_selected,
                                                    '', ct_type=1,
                                                    wnd=self.map )
        else:
            self.layer = self.PrependItem(self.root, '',
                                                    ct_type=1, wnd=self.map)

        #add to layertype dictionary
        self.layertype[self.layer] = type

        self.SetPyData(self.layer, None)

#        #add icons for each layer
        if type == 'rast':
            self.SetItemImage(self.layer, self.rast_icon)
        elif type == 'vect':
            self.SetItemImage(self.layer, self.vect_icon)
        elif type == 'cmd':
            self.SetItemImage(self.layer, self.cmd_icon)

        #layer is initially checked as active
        self.CheckItem(self.layer)
        self.node += 1
        self.createLayerList()

    def onCollapseNode(self, event):
        print 'group collapsed'
        event.Skip()

    def onExpandNode(self, event):
        self.layer_selected = event.GetItem()
        print 'group expanded'
        event.Skip()

    def onActivateLayer(self, event):
        layer = event.GetItem()
        self.layer_selected = layer
       # When double clicked, open options dialog
        if self.layertype[layer] == 'rast':
            rastopt.MyFrame(self)
        elif self.layertype[layer] == 'vect':
            print 'its a vector'
            vectopt.MyPanel(self)
        self.createLayerList()

#        event.Skip()

    def onLayerChecked(self, event):
        Layer = event.GetItem()
        self.createLayerList()

    def onChangeSel(self, event):
        layer = event.GetItem()
        self.layer_selected = layer

#        event.Skip()

    def onMapChanged(self, event):
        map = event.GetString()

    def createLayerList(self):
        for layer in self.layertype.keys():
            if self.IsItemChecked(layer) == True and \
                self.GetItemWindow(layer).GetValue() != '' and \
                self.GetItemWindow(layer).GetValue()[0:7] != 'Mapset:':
                if self.layertype[layer] == 'rast':
                    render.Map().AddRasterLayer(name = self.GetItemWindow(layer).GetValue())
                    #TODO: need to add options for layer
                elif self.layertype[layer] == 'vect':
                    render.Map().AddVectorLayer(name = self.GetItemWindow(layer).GetValue())

class TreeCtrlComboPopup(wx.combo.ComboPopup):
    """
    Create a tree ComboBox for selecting maps and other GIS elements
    in accessible mapsets within the current location
    """

    # overridden ComboPopup methods

    def Init(self):
        self.value = None
        self.curitem = None


    def Create(self, parent):
        self.tree = wx.TreeCtrl(parent, style=wx.TR_HIDE_ROOT
                                |wx.TR_HAS_BUTTONS
                                |wx.TR_SINGLE
                                |wx.TR_LINES_AT_ROOT
                                |wx.SIMPLE_BORDER)
        self.tree.Bind(wx.EVT_MOTION, self.OnMotion)
        self.tree.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)


    def GetControl(self):
        return self.tree


    def GetStringValue(self):
        if self.value:
            return self.tree.GetItemText(self.value)
        return ""


    def OnPopup(self):
        if self.value:
            self.tree.EnsureVisible(self.value)
            self.tree.SelectItem(self.value)


    def SetStringValue(self, value):
        # this assumes that item strings are unique...
        root = self.tree.GetRootItem()
        if not root:
            return
        found = self.FindItem(root, value)
        if found:
            self.value = found
            self.tree.SelectItem(found)


    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        return wx.Size(minWidth, min(200, maxHeight))


    def getElementList(self, element):
        """
        Get list of GIS elements in accessible mapsets and display as tree
        with all relevant elements displayed beneath each mapset branch
        """
        #set environmental variables
        gisdbase = os.popen('g.gisenv get=GISDBASE', "r").read().strip()
        location = os.popen('g.gisenv get=LOCATION_NAME', "r").read().strip()
        curr_mapset = os.popen('g.gisenv get=MAPSET', "r").read().strip()
        location_path = os.path.join (gisdbase,location)
        windfile = os.path.join (location_path,'PERMANENT','WIND')
        symbol_path = os.path.join (os.environ['GISBASE'],'etc','symbol')

        #valid location test if needed
        if windfile != None:
            pass

        #mapsets in current location
        mapsets = os.popen('g.mapsets -p', "r").read().lstrip().rstrip().split(' ')

        #Get directory tree nodes
        for dir in mapsets:
            if dir == curr_mapset:
                #TODO: make current mapset node expanded
                dir_node = self.AddItem('Mapset: '+dir)
                self.tree.SetItemTextColour(dir_node,wx.Colour(50,50,200))
                elem_list = os.listdir(os.path.join (location_path, dir, element))
                #TODO: sort list items?
                for elem in elem_list:
                    self.AddItem(elem, parent=dir_node)
            else:
                dir_node = self.AddItem('Mapset: '+dir)
                self.tree.SetItemTextColour(dir_node,wx.Colour(50,50,200))
                elem_list = os.listdir(os.path.join (location_path, dir, element))
                #TODO: sort list items?
                for elem in elem_list:
                    self.AddItem(elem+'@'+dir, parent=dir_node)

    # helpers

    def FindItem(self, parentItem, text):
        item, cookie = self.tree.GetFirstChild(parentItem)
        while item:
            if self.tree.GetItemText(item) == text:
                return item
            if self.tree.ItemHasChildren(item):
                item = self.FindItem(item, text)
            item, cookie = self.tree.GetNextChild(parentItem, cookie)
        return wx.TreeItemId();


    def AddItem(self, value, parent=None):
        if not parent:
            root = self.tree.GetRootItem()
            if not root:
                root = self.tree.AddRoot("<hidden root>")
            parent = root

        item = self.tree.AppendItem(parent, value)
        return item


    def OnMotion(self, evt):
        # have the selection follow the mouse, like in a real combobox
        item, flags = self.tree.HitTest(evt.GetPosition())
        if item and flags & wx.TREE_HITTEST_ONITEMLABEL:
            self.tree.SelectItem(item)
            self.curitem = item
        evt.Skip()


    def OnLeftDown(self, evt):
        # do the combobox selection
        item, flags = self.tree.HitTest(evt.GetPosition())
        if item and flags & wx.TREE_HITTEST_ONITEMLABEL:
            self.curitem = item
            self.value = item
            self.Dismiss()
        evt.Skip()


class GMConsole(wx.Panel):
    """
    Create and manage output console for commands entered on the
    GIS Manager command line.
    """
    def __init__(self, parent, id=-1,
                     pos=wx.DefaultPosition, size=wx.DefaultSize,
                     style=wx.TAB_TRAVERSAL|wx.FULL_REPAINT_ON_RESIZE):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        #initialize variables

        self.cmd_output = ""
        self.console_command = ""
#        self.console_run = ""
        self.console_clear = ""
        self.console_save = ""
        self.gcmdlst = [] #list of commands in bin and scripts

        #text control for command output
        self.cmd_output = wx.TextCtrl(self, -1, "",
                                                  style=wx.TE_MULTILINE|
                                                  wx.TE_READONLY|wx.HSCROLL)

    	self.console_clear = wx.Button(self, -1, _("Clear"))
    	self.console_save = wx.Button(self, -1, _("Save"))

    	self.Bind(wx.EVT_BUTTON, self.clearHistory, self.console_clear)
    	self.Bind(wx.EVT_BUTTON, self.saveHistory, self.console_save)

		# output control layout
    	boxsizer1 = wx.BoxSizer(wx.VERTICAL)
    	gridsizer1 = wx.GridSizer(1, 2, 0, 0)
    	boxsizer1.Add(self.cmd_output, 1,
                              wx.EXPAND|wx.ADJUST_MINSIZE, 0)
    	gridsizer1.Add(self.console_clear, 0,
                               wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)
    	gridsizer1.Add(self.console_save, 0,
                               wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)

        boxsizer1.Add((0,5))
    	boxsizer1.Add(gridsizer1, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL)
        boxsizer1.Add((0,5))
        boxsizer1.Fit(self)
    	boxsizer1.SetSizeHints(self)
    	self.SetAutoLayout(True)
    	self.SetSizer(boxsizer1)

    def getGRASSCmds(self):
		'''
        Create list of all available GRASS commands to use when
        parsing string from the command line
        '''
		gisbase = os.environ['GISBASE']
		self.gcmdlst = os.listdir(gisbase+r'/bin')
		self.gcmdlst.append(os.listdir(gisbase+r'/scripts'))
		return self.gcmdlst

    def runCmd(self, cmd):
    	"""
        Run in GUI or shell GRASS (or other) commands typed into
    	console command text widget, echo command to
    	output text widget, and send stdout output to output
    	text widget.

        TODO: Display commands (*.d) are captured and
    	processed separately by mapdisp.py. Display commands are
    	rendered in map display widget that currently has
    	the focus (as indicted by mdidx).
        """

    	gcmdlst = self.getGRASSCmds()
    	cmdlst = []
#    	cmd = self.console_command.GetLineText(0)
    	cmdlst = cmd.split(' ')
        print 'command = ', cmd
    	disp_idx = int(track.Track().GetDisp()[0])
        print 'display = ', disp_idx
    	curr_disp = track.Track().GetDisp()[1]
        print 'Im here'

    	if len(cmdlst) == 1 and cmd in gcmdlst:
    		# Send GRASS command without arguments to GUI command interface
    		# except display commands (they are handled differently)
    		global gmpath
    		if cmd[0:2] == "d.":
    			print "Add map layer to GIS Manager to see " \
                                    "GUI for display command"
    			return
    		else:
    			menuform.GUI().parseCommand(cmd, gmpath)
    			self.cmd_output.write(cmdlst[0] +
                                                          "\n----------\n")

    	elif cmd[0:2] == "d." and len(cmdlst) > 1 and cmdlst[0] in gcmdlst:
    		# Send GRASS display command(s)with arguments
    		# to the display processor and echo to command output console.
    		# Accepts a list of d.* commands separated by commas.
    		# Display with focus receives display command(s).
    		self.cmd_output.write(cmd +
                                                  "\n----------\n")
    		dcmds = cmd.split(',')
    		curr_disp.setDcommandList(dcmds)

    	else:
    		# Send any other command to the shell. Send output to
    		# console output window.
            try:
                retcode = subprocess.call(cmd, shell=True)

                if retcode < 0:
    				print >> sys.stderr, "Child was terminated by signal", retcode
                elif retcode > 0:
    				print >> sys.stderr, "Child returned", retcode
            except OSError, e:
    			print >> sys.stderr, "Execution failed:", e

            self.cmd_output.write(cmd+"\n----------\n")
            #FIXME - why is PIPE not recognized?
#            self.out = subprocess.Popen(cmd, shell=True, stdout=PIPE).stdout
            self.out = os.popen(cmd, "r").read()
            self.cmd_output.write(self.out+"\n")

    def clearHistory(self, event):
		self.cmd_output.Clear()

    def saveHistory(self, event):
        self.history = self.cmd_output.GetStringSelection()
        if self.history == "":
            self.cmd_output.SetSelection(-1,-1)
            self.history = self.cmd_output.GetStringSelection()

        #Use a standard dialog for this
        wildcard = "Text file (*.txt)|*.txt"
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=os.getcwd(),
            defaultFile="grass_cmd_history.txt", wildcard=wildcard, style=wx.SAVE|wx.FD_OVERWRITE_PROMPT
            )

        # Show the dialog and retrieve the user response. If it is the OK response,
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

        output = open(path,"w")
        output.write(self.history)
        output.close()
        dlg.Destroy()


def GetTempfile( pref=None):
    """
    Creates GRASS temporary file using defined prefix.

    Returns:
        Path to file name (string) or None
    """

    tempfile = os.popen("g.tempfile pid=%d" %
                        os.getpid()).readlines()[0].strip()

    if not tempfile:
        return None
    else:
        path,file = os.path.split(tempfile)
        if pref:
            file = "%s%s" % (pref,file)
        return os.path.join(path,file)
