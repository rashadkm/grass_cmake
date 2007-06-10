"""
MODULE: toolbar

PURPOSE: Toolbars for Map Display window

AUTHORS: The GRASS Development Team
         Michael Barton, Martin Landa, Jachym Cepicky

COPYRIGHT: (C) 2007 by the GRASS Development Team
           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

import wx
import os, sys

gmpath = os.path.join( os.getenv("GISBASE"),"etc","wx","icons")
sys.path.append(gmpath)

import cmd
import grassenv
from debug import Debug as Debug
from icon import Icons as Icons

class AbstractToolbar:
    """Abstract toolbar class"""
    def __init__():
        pass

    def InitToolbar(self, parent):
        """Initialize toolbar, i.e. add tools to the toolbar"""

        for tool in self.ToolbarData():
            self.CreateTool(parent, self.toolbar, *tool)

    def ToolbarData(self):
        """Toolbar data"""

        return None

    def CreateTool(self, parent, toolbar, tool, label, bitmap, kind,
                   shortHelp, longHelp, handler):
        """Add tool to the toolbar"""
        
        bmpDisabled=wx.NullBitmap

        if label:
            tool = toolbar.AddLabelTool(wx.ID_ANY, label, bitmap,
                                             bmpDisabled, kind,
                                             shortHelp, longHelp)
            parent.Bind(wx.EVT_TOOL, handler, tool)
        else: # add separator
            toolbar.AddSeparator()

class MapToolbar(AbstractToolbar):
    """
    Main Map Display toolbar
    """

    def __init__(self, mapdisplay, map):
        self.mapcontent = map
        self.mapdisplay = mapdisplay

        self.toolbar = wx.ToolBar(parent=self.mapdisplay, id=wx.ID_ANY)

        # self.SetToolBar(self.toolbar)
        tsize = (24, 24)
        self.toolbar.SetToolBitmapSize(tsize)

        self.InitToolbar(self.mapdisplay)

        # optional tools
        self.combo = wx.ComboBox(parent=self.toolbar, id=wx.ID_ANY, value='Tools',
                                 choices=['Digitize'], style=wx.CB_READONLY, size=(90, -1))

        self.comboid = self.toolbar.AddControl(self.combo)
        self.mapdisplay.Bind(wx.EVT_COMBOBOX, self.OnSelect, self.comboid)

        # realize the toolbar
        self.toolbar.Realize()

    def ToolbarData(self):
        """Toolbar data"""

        self.displaymap = self.rendermap = self.erase = \
        self.pointer = self.query = self.pan = self.zoomin = self.zoomout = \
        self.zoomback = self.zoommenu = self.analyze = self.dec = self.savefile = self.printmap =None

        # tool, label, bitmap, kind, shortHelp, longHelp, handler
        return (
            (self.displaymap, "displaymap", Icons["displaymap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["displaymap"].GetLabel(), Icons["displaymap"].GetDesc(),
             self.mapdisplay.ReDraw),
            (self.rendermap, "rendermap", Icons["rendermap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["rendermap"].GetLabel(), Icons["rendermap"].GetDesc(),
             self.mapdisplay.ReRender),
            (self.erase, "erase", Icons["erase"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["erase"].GetLabel(), Icons["erase"].GetDesc(),
             self.mapdisplay.OnErase),
            ("", "", "", "", "", "", ""), 
            (self.pointer, "pointer", Icons["pointer"].GetBitmap(),
             wx.ITEM_RADIO, Icons["pointer"].GetLabel(), Icons["pointer"].GetDesc(),
             self.mapdisplay.Pointer),
            (self.query, "query", Icons["query"].GetBitmap(),
             wx.ITEM_RADIO, Icons["query"].GetLabel(), Icons["query"].GetDesc(),
             self.mapdisplay.OnQuery),
            (self.pan, "pan", Icons["pan"].GetBitmap(),
             wx.ITEM_RADIO, Icons["pan"].GetLabel(), Icons["pan"].GetDesc(),
             self.mapdisplay.OnPan), 
            (self.zoomin, "zoom_in", Icons["zoom_in"].GetBitmap(),
             wx.ITEM_RADIO, Icons["zoom_in"].GetLabel(), Icons["zoom_in"].GetDesc(),
             self.mapdisplay.OnZoomIn),
            (self.zoomout, "zoom_out", Icons["zoom_out"].GetBitmap(),
             wx.ITEM_RADIO, Icons["zoom_out"].GetLabel(), Icons["zoom_out"].GetDesc(),
             self.mapdisplay.OnZoomOut),
            (self.zoomback, "zoom_back", Icons["zoom_back"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_back"].GetLabel(), Icons["zoom_back"].GetDesc(),
             self.mapdisplay.OnZoomBack),
            (self.zoommenu, "zoommenu", Icons["zoommenu"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoommenu"].GetLabel(), Icons["zoommenu"].GetDesc(),
             self.mapdisplay.OnZoomMenu),
            ("", "", "", "", "", "", ""),
            (self.analyze, "analyze", Icons["analyze"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["analyze"].GetLabel(), Icons["analyze"].GetDesc(),
             self.mapdisplay.OnAnalyze),
            ("", "", "", "", "", "", ""),
            (self.dec, "overlay", Icons["overlay"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["overlay"].GetLabel(), Icons["overlay"].GetDesc(),
             self.mapdisplay.OnDecoration),
            ("", "", "", "", "", "", ""),
            (self.savefile, "savefile", Icons["savefile"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["savefile"].GetLabel(), Icons["savefile"].GetDesc(),
             self.mapdisplay.SaveToFile),
            (self.printmap, "printmap", Icons["printmap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["printmap"].GetLabel(), Icons["printmap"].GetDesc(),
             self.mapdisplay.PrintMenu),
            ("", "", "", "", "", "", "")
            )

    def OnSelect(self, event):
        """
        Select / enable tool available in tools list
        """
        tool =  event.GetString()

        if tool == "Digitize" and not self.mapdisplay.digittoolbar:
            self.mapdisplay.AddToolbar("digit")

class DigitToolbar(AbstractToolbar):
    """
    Toolbar for digitization
    """

    def __init__(self, parent, map):
        self.mapcontent = map
        self.parent     = parent

        # selected map to digitize
        self.layerSelectedID    = None
        self.layers     = []
        # action (digitize new point, line, etc.
        self.action     = "add"
        self.type       = "point"
        self.addString  = ""

        self.comboid    = None

        # create toolbar
        self.toolbar = wx.ToolBar(parent=self.parent, id=wx.ID_ANY)
        self.toolbar.SetToolBitmapSize(wx.Size(24,24))

        # create toolbar
        self.InitToolbar(self.parent)

        # list of available vector maps
        self.UpdateListOfLayers(updateTool=True)

        # additional bindings
        self.parent.Bind(wx.EVT_COMBOBOX, self.OnSelectMap, self.comboid)

        # realize toolbar
        self.toolbar.Realize()

    def ToolbarData(self):
        """
        Toolbar data
        """

        self.addPoint = self.addLine = self.addBoundary = self.addCentroid = self.exit = None
        self.moveVertex = self.addVertex = self.removeVertex = None
        self.splitLine = self.editLine = self.moveLine = self.deleteLine = None
        self.displayCats = self.displayAttr = self.copyCats = self.settings = None

        return (("", "", "", "", "", "", ""),
                (self.addPoint, "digAddPoint", Icons["digAddPoint"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digAddPoint"].GetLabel(), Icons["digAddPoint"].GetDesc(),
                 self.OnAddPoint),
                (self.addLine, "digAddLine", Icons["digAddLine"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digAddLine"].GetLabel(), Icons["digAddLine"].GetDesc(),
                 self.OnAddLine),
                (self.addBoundary, "digAddBoundary", Icons["digAddBoundary"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digAddBoundary"].GetLabel(), Icons["digAddBoundary"].GetDesc(),
                 self.OnAddBoundary),
                (self.addCentroid, "digAddCentroid", Icons["digAddCentroid"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digAddCentroid"].GetLabel(), Icons["digAddCentroid"].GetDesc(),
                 self.OnAddCentroid),
                ("", "", "", "", "", "", ""),
                (self.moveVertex, "digMoveVertex", Icons["digMoveVertex"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digMoveVertex"].GetLabel(), Icons["digMoveVertex"].GetDesc(),
                 self.OnMoveVertex),
                (self.addVertex, "digAddVertex", Icons["digAddVertex"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digAddVertex"].GetLabel(), Icons["digAddVertex"].GetDesc(),
                 self.OnAddVertex),
                (self.removeVertex, "digRemoveVertex", Icons["digRemoveVertex"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digRemoveVertex"].GetLabel(), Icons["digRemoveVertex"].GetDesc(),
                 self.OnRemoveVertex),
                ("", "", "", "", "", "", ""),
                (self.splitLine, "digSplitLine", Icons["digSplitLine"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digSplitLine"].GetLabel(), Icons["digSplitLine"].GetDesc(),
                 self.OnSplitLine),
                (self.editLine, "digEditLine", Icons["digEditLine"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digEditLine"].GetLabel(), Icons["digEditLine"].GetDesc(),
                 self.OnEditLine),
                (self.moveLine, "digMoveLine", Icons["digMoveLine"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digMoveLine"].GetLabel(), Icons["digMoveLine"].GetDesc(),
                 self.OnMoveLine),
                (self.deleteLine, "digDeleteLine", Icons["digDeleteLine"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digDeleteLine"].GetLabel(), Icons["digDeleteLine"].GetDesc(),
                 self.OnDeleteLine),
                ("", "", "", "", "", "", ""),
                (self.displayCats, "digDispCats", Icons["digDispCats"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digDispCats"].GetLabel(), Icons["digDispCats"].GetDesc(),
                 self.OnDisplayCats),
                (self.copyCats, "digCopyCats", Icons["digCopyCats"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digCopyCats"].GetLabel(), Icons["digCopyCats"].GetDesc(),
                 self.OnCopyCats),
                (self.displayAttr, "digDispAttr", Icons["digDispAttr"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digDispAttr"].GetLabel(), Icons["digDispAttr"].GetDesc(),
                 self.OnDisplayAttr),
                (self.settings, "digSettings", Icons["digSettings"].GetBitmap(),
                 wx.ITEM_RADIO, Icons["digSettings"].GetLabel(), Icons["digSettings"].GetDesc(),
                 self.OnSettings),
                ("", "", "", "", "", "", ""),
                (self.exit, "digExit", Icons["digExit"].GetBitmap(),
                 wx.ITEM_NORMAL, Icons["digExit"].GetLabel(), Icons["digExit"].GetDesc(),
                 self.OnExit))

    def OnAddPoint(self, event):
        """Add point to the vector map layer"""
        Debug.msg (3, "DigitToolbar.OnAddPoint()")
        self.action = "add"
        self.type   = "point"
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnAddLine(self, event):
        """Add line to the vector map layer"""
        Debug.msg (3, "DigitToolbar.OnAddLine()")
        self.action = "add"
        self.type   = "line"
        self.parent.MapWindow.mouse['box'] = 'line'

    def OnAddBoundary(self, event):
        """Add boundary to the vector map layer"""
        Debug.msg (3, "DigitToolbar.OnAddBoundary()")
        self.action = "add"
        self.type   = "boundary"
        self.parent.MapWindow.mouse['box'] = 'line'

    def OnAddCentroid(self, event):
        """Add centroid to the vector map layer"""
        Debug.msg (3, "DigitToolbar.OnAddCentroid()")
        self.action = "add"
        self.type   = "centroid"
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnExit (self, event):
        """
        Quit digitization tool
        """
        # stop editing of the currently selected map layer
        self.StopEditing()
        
        # disable the toolbar
        self.parent.RemoveToolbar ("digit")

    def OnMoveVertex(self, event):
        pass

    def OnAddVertex(self, event):
        pass

    def OnRemoveVertex(self, event):
        pass

    def OnSplitLine(self, event):
        pass

    def OnEditLine(self, event):
        pass

    def OnMoveLine(self, event):
        pass

    def OnDeleteLine(self, event):
        pass

    def OnDisplayCats(self, event):
        pass
    
    def OnDisplayAttr(self, event):
        pass

    def OnCopyCats(self, event):
        pass

    def OnSettings(self, event):
        pass

    def OnSelectMap (self, event):
        """
        Select vector map layer for editing

        If there is a vector map layer already edited, this action is
        firstly terminated. The map layer is closed. After this the
        selected map layer activated for editing.
        """
        if self.layerSelectedID: # deactive map layer for editing
            # TODO
            pass

        # select the given map layer for editing
        layerSelectedID = self.combo.GetCurrentSelection()
        self.StartEditing(self.layers[layerSelectedID])

    def StartEditing (self, layerSelected):
        """
        Mark selected map layer as enabled for digitization

        Return True on success or False if layer cannot be edited
        """
        try:
            self.layerSelectedID = self.layers.index(layerSelected)
            self.combo.SetValue (layerSelected.name)
            self.parent.maptoolbar.combo.SetValue ('Digitize')
            Debug.msg (4, "DigitToolbar.StartEditing(): layerSelectedID=%d layer=%s" % \
                       (self.layerSelectedID, self.layers[self.layerSelectedID].name))
            return True
        except:
            return False

    def StopEditing (self):
        """
        Unmark currently enabled map layer.
        """
        if self.layerSelectedID:
            Debug.msg (4, "DigitToolbar.StopEditing(): layer=%s" % \
                       self.layers[self.layerSelectedID].name)
        else:
            Debug.msg (4, "DigitToolbar.StopEditing(): layer=None")
        
        self.layerSelectedID = None
        self.combo.SetValue ('Select vector map')
        # TODO
        
    def UpdateListOfLayers (self, updateTool=False):
        """
        Update list of available vector map layers.
        This list consists only editable layers (in the current mapset)

        Optionaly also update toolbar
        """

        layerNameSelected = None
        if self.layerSelectedID != None: # name of currently selected layer
            layerNameSelected = self.layers[self.layerSelectedID].name

        # select vector map layer in the current mapset
        layerNameList = []
        self.layers = self.mapcontent.GetListOfLayers(l_type="vector", l_mapset=grassenv.env["MAPSET"])
        for layer in self.layers:
            if not layer.name in layerNameList: # do not duplicate layer
                layerNameList.append (layer.name)

        if updateTool: # update toolbar
            if self.layerSelectedID == None:
                value = 'Select vector map'
            else:
                value = layerNameSelected

            # ugly ...
            if self.comboid:
                self.toolbar.DeleteToolByPos(0)
                #self.combo.Destroy()

            self.combo = wx.ComboBox(self.toolbar, id=wx.ID_ANY, value=value,
                                     choices=layerNameList, size=(150, -1))

            self.comboid = self.toolbar.InsertControl(0, self.combo)
            self.toolbar.Realize()

        return layerNameList
