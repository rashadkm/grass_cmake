"""!
@package toolbar

@brief wxGUI toolbar widgets

Classes:
 - AbstractToolbar
 - MapToolbar
 - GRToolbar
 - GCPToolbar
 - VDigitToolbar
 - ProfileToolbar
 - NvizToolbar

(C) 2007-2010 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Michael Barton
@author Jachym Cepicky
@author Martin Landa <landa.martin gmail.com>
"""

import os
import sys
import platform

from grass.script import core as grass

import wx

import globalvar
import gcmd
import gdialogs
import vdigit
from vdigit import VDigitSettingsDialog as VDigitSettingsDialog
from debug import Debug as Debug
from icon import Icons as Icons
from preferences import globalSettings as UserSettings

gmpath = os.path.join(globalvar.ETCWXDIR, "icons")
sys.path.append(gmpath)

class AbstractToolbar(wx.ToolBar):
    """!Abstract toolbar class"""
    def __init__(self, parent):
        self.parent = parent
        wx.ToolBar.__init__(self, parent = self.parent, id = wx.ID_ANY)
    
        self.action = dict()
        
        self.Bind(wx.EVT_TOOL, self.OnTool)
        
        self.SetToolBitmapSize(globalvar.toolbarSize)
        
    def InitToolbar(self, toolData):
        """!Initialize toolbar, add tools to the toolbar
        """
        for tool in toolData:
            self.CreateTool(*tool)
        
        self._data = toolData
        
    def ToolbarData(self):
        """!Toolbar data (virtual)"""
        return None
    
    def CreateTool(self, tool, label, bitmap, kind,
                   shortHelp, longHelp, handler):
        """!Add tool to the toolbar
        
        @return id of tool
        """
        bmpDisabled=wx.NullBitmap
        
        if label:
            Debug.msg(3, "CreateTool(): tool=%d, label=%s bitmap=%s" % \
                  (tool, label, bitmap))
            toolWin = self.AddLabelTool(tool, label, bitmap,
                                           bmpDisabled, kind,
                                           shortHelp, longHelp)
            self.Bind(wx.EVT_TOOL, handler, toolWin)
        else: # separator
            self.AddSeparator()
        
        return tool
    
    def EnableLongHelp(self, enable=True):
        """!Enable/disable long help
        
        @param enable True for enable otherwise disable
        """
        for tool in self._data:
            if tool[0] == '': # separator
                continue
            
            if enable:
                self.SetToolLongHelp(tool[0], tool[5])
            else:
                self.SetToolLongHelp(tool[0], "")
        
    def OnTool(self, event):
        """!Tool selected"""
        if self.parent.toolbars['vdigit']:
            # update vdigit toolbar (unselect currently selected tool)
            id = self.parent.toolbars['vdigit'].GetAction(type='id')
            self.parent.toolbars['vdigit'].ToggleTool(id, False)
        
        if event:
            # deselect previously selected tool
            id = self.action.get('id', -1)
            if id != event.GetId():
                self.ToggleTool(self.action['id'], False)
            else:
                self.ToggleTool(self.action['id'], True)
            
            self.action['id'] = event.GetId()
            
            event.Skip()
        else:
            # initialize toolbar
            self.ToggleTool(self.action['id'], True)
        
    def GetAction(self, type='desc'):
        """!Get current action info"""
        return self.action.get(type, '')
    
    def SelectDefault(self, event):
        """!Select default tool"""
        self.ToggleTool(self.defaultAction['id'], True)
        self.defaultAction['bind'](event)
        self.action = { 'id' : self.defaultAction['id'],
                        'desc' : self.defaultAction.get('desc', '') }
        
    def FixSize(self, width):
	"""!Fix toolbar width on Windows
        
	@todo Determine why combobox causes problems here
	"""
        if platform.system() == 'Windows':
            size = self.GetBestSize()
            self.SetSize((size[0] + width, size[1]))

    def Enable(self, tool, enable = True):
        """!Enable defined tool
        
        @param tool name
        @param enable True to enable otherwise disable tool
        """
        try:
            id = getattr(self, tool)
        except AttributeError:
            return
        
        self.EnableTool(id, enable)
        
class MapToolbar(AbstractToolbar):
    """!Map Display toolbar
    """
    def __init__(self, parent, mapcontent):
        """!Map Display constructor

        @param parent reference to MapFrame
        @param mapcontent reference to render.Map (registred by MapFrame)
        """
        self.mapcontent = mapcontent # render.Map
        AbstractToolbar.__init__(self, parent = parent) # MapFrame
        
        self.InitToolbar(self.ToolbarData())
        
        # optional tools
        self.combo = wx.ComboBox(parent=self, id=wx.ID_ANY, value=_('2D view'),
                                 choices=[_('2D view'), _('3D view'), _('Digitize')],
                                 style=wx.CB_READONLY, size=(90, -1))
        
        self.comboid = self.AddControl(self.combo)
        self.parent.Bind(wx.EVT_COMBOBOX, self.OnSelectTool, self.comboid)
        
        # realize the toolbar
        self.Realize()
        
        # workaround for Mac bug. May be fixed by 2.8.8, but not before then.
        self.combo.Hide()
        self.combo.Show()
        
        self.action = { 'id' : self.pointer }
        self.defaultAction = { 'id' : self.pointer,
                               'bind' : self.parent.OnPointer }
        
        self.OnTool(None)
        
        self.EnableTool(self.zoomback, False)
        
        self.FixSize(width = 90)
        
    def ToolbarData(self):
        """!Toolbar data"""
        self.displaymap = wx.NewId()
        self.rendermap = wx.NewId()
        self.erase = wx.NewId()
        self.pointer = wx.NewId()
        self.query = wx.NewId()
        self.pan = wx.NewId()
        self.zoomin = wx.NewId()
        self.zoomout = wx.NewId()
        self.zoomback = wx.NewId()
        self.zoommenu = wx.NewId()
        self.analyze = wx.NewId()
        self.dec = wx.NewId()
        self.savefile = wx.NewId()
        self.printmap = wx.NewId()
        
        # tool, label, bitmap, kind, shortHelp, longHelp, handler
        return (
            (self.displaymap, "displaymap", Icons["displaymap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["displaymap"].GetLabel(), Icons["displaymap"].GetDesc(),
             self.parent.OnDraw),
            (self.rendermap, "rendermap", Icons["rendermap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["rendermap"].GetLabel(), Icons["rendermap"].GetDesc(),
             self.parent.OnRender),
            (self.erase, "erase", Icons["erase"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["erase"].GetLabel(), Icons["erase"].GetDesc(),
             self.parent.OnErase),
            ("", "", "", "", "", "", ""),
            (self.pointer, "pointer", Icons["pointer"].GetBitmap(),
             wx.ITEM_CHECK, Icons["pointer"].GetLabel(), Icons["pointer"].GetDesc(),
             self.parent.OnPointer),
            (self.query, "query", Icons["query"].GetBitmap(),
             wx.ITEM_CHECK, Icons["query"].GetLabel(), Icons["query"].GetDesc(),
             self.parent.OnQuery),
            (self.pan, "pan", Icons["pan"].GetBitmap(),
             wx.ITEM_CHECK, Icons["pan"].GetLabel(), Icons["pan"].GetDesc(),
             self.parent.OnPan),
            (self.zoomin, "zoom_in", Icons["zoom_in"].GetBitmap(),
             wx.ITEM_CHECK, Icons["zoom_in"].GetLabel(), Icons["zoom_in"].GetDesc(),
             self.parent.OnZoomIn),
            (self.zoomout, "zoom_out", Icons["zoom_out"].GetBitmap(),
             wx.ITEM_CHECK, Icons["zoom_out"].GetLabel(), Icons["zoom_out"].GetDesc(),
             self.parent.OnZoomOut),
            (self.zoomback, "zoom_back", Icons["zoom_back"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_back"].GetLabel(), Icons["zoom_back"].GetDesc(),
             self.parent.OnZoomBack),
            (self.zoommenu, "zoommenu", Icons["zoommenu"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoommenu"].GetLabel(), Icons["zoommenu"].GetDesc(),
             self.parent.OnZoomMenu),
            ("", "", "", "", "", "", ""),
            (self.analyze, "analyze", Icons["analyze"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["analyze"].GetLabel(), Icons["analyze"].GetDesc(),
             self.parent.OnAnalyze),
            ("", "", "", "", "", "", ""),
            (self.dec, "overlay", Icons["overlay"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["overlay"].GetLabel(), Icons["overlay"].GetDesc(),
             self.parent.OnDecoration),
            ("", "", "", "", "", "", ""),
            (self.savefile, "savefile", Icons["savefile"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["savefile"].GetLabel(), Icons["savefile"].GetDesc(),
             self.parent.SaveToFile),
            (self.printmap, "printmap", Icons["printmap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["printmap"].GetLabel(), Icons["printmap"].GetDesc(),
             self.parent.PrintMenu),
            ("", "", "", "", "", "", "")
            )
    
    def OnSelectTool(self, event):
        """!
        Select / enable tool available in tools list
        """
        tool =  event.GetSelection()
        
        if tool == 0:
            self.ExitToolbars()
            self.Enable2D(True)
        
        elif tool == 1 and not self.parent.toolbars['nviz']:
            self.ExitToolbars()
            self.parent.AddToolbar("nviz")
            
        elif tool == 2 and not self.parent.toolbars['vdigit']:
            self.ExitToolbars()
            self.parent.AddToolbar("vdigit")
            self.parent.MapWindow.SetFocus()
        
    def ExitToolbars(self):
        if self.parent.toolbars['vdigit']:
            self.parent.toolbars['vdigit'].OnExit()
        if self.parent.toolbars['nviz']:       
            self.parent.toolbars['nviz'].OnExit()
    
    def Enable2D(self, enabled):
        """!Enable/Disable 2D display mode specific tools"""
        for tool in (self.pointer,
                     self.query,
                     self.pan,
                     self.zoomin,
                     self.zoomout,
                     self.zoomback,
                     self.zoommenu,
                     self.analyze,
                     self.dec,
                     self.savefile,
                     self.printmap):
            self.EnableTool(tool, enabled)
        
class GRToolbar(AbstractToolbar):
    """
    Georectification toolbar
    """
    def __init__(self, parent, mapcontent):
        """!
        Georectification toolbar constructor

        @param parent reference to MapFrame
        @param mapcontent reference to render.Map (registred by MapFrame)
        """
        self.mapcontent = mapcontent
        AbstractToolbar.__init__(self, parent)
        
        self.InitToolbar(self.ToolbarData())
        
        # realize the toolbar
        self.Realize()
        
        self.action = { 'id' : self.gcpset }
        self.defaultAction = { 'id' : self.gcpset,
                               'bind' : self.parent.OnPointer }
        
        self.OnTool(None)
        
        self.EnableTool(self.zoomback, False)
        
    def ToolbarData(self):
        """!Toolbar data"""
        self.displaymap = wx.NewId()
        self.rendermap = wx.NewId()
        self.erase = wx.NewId()
        self.gcpset = wx.NewId()
        self.pan = wx.NewId()
        self.zoomin = wx.NewId()
        self.zoomout = wx.NewId()
        self.zoomback = wx.NewId()
        self.zoomtomap = wx.NewId()
        
        # tool, label, bitmap, kind, shortHelp, longHelp, handler
        return (
            (self.displaymap, "displaymap", Icons["displaymap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["displaymap"].GetLabel(), Icons["displaymap"].GetDesc(),
             self.parent.OnDraw),
            (self.rendermap, "rendermap", Icons["rendermap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["rendermap"].GetLabel(), Icons["rendermap"].GetDesc(),
             self.parent.OnRender),
            (self.erase, "erase", Icons["erase"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["erase"].GetLabel(), Icons["erase"].GetDesc(),
             self.parent.OnErase),
            ("", "", "", "", "", "", ""),
            (self.gcpset, "grGcpSet", Icons["grGcpSet"].GetBitmap(),
             wx.ITEM_RADIO, Icons["grGcpSet"].GetLabel(), Icons["grGcpSet"].GetDesc(),
             self.parent.OnPointer),
            (self.pan, "pan", Icons["pan"].GetBitmap(),
             wx.ITEM_RADIO, Icons["pan"].GetLabel(), Icons["pan"].GetDesc(),
             self.parent.OnPan),
            (self.zoomin, "zoom_in", Icons["zoom_in"].GetBitmap(),
             wx.ITEM_RADIO, Icons["zoom_in"].GetLabel(), Icons["zoom_in"].GetDesc(),
             self.parent.OnZoomIn),
            (self.zoomout, "zoom_out", Icons["zoom_out"].GetBitmap(),
             wx.ITEM_RADIO, Icons["zoom_out"].GetLabel(), Icons["zoom_out"].GetDesc(),
             self.parent.OnZoomOut),
            (self.zoomback, "zoom_back", Icons["zoom_back"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_back"].GetLabel(), Icons["zoom_back"].GetDesc(),
             self.parent.OnZoomBack),
            (self.zoomtomap, "zoomtomap", Icons["zoommenu"].GetBitmap(),
             wx.ITEM_NORMAL, _("Zoom to map"), _("Zoom to displayed map"),
             self.OnZoomMap),
            )
    
    def OnZoomMap(self, event):
        """!Zoom to selected map"""
        self.parent.MapWindow.ZoomToMap(layers = self.mapcontent.GetListOfLayers())
        if event:
            event.Skip()
        
class GCPToolbar(AbstractToolbar):
    """!
    Toolbar for managing ground control points during georectification

    @param parent reference to GCP widget
    """
    def __init__(self, parent):
        AbstractToolbar.__init__(self, parent)
        
        self.InitToolbar(self.ToolbarData())
        
        # realize the toolbar
        self.Realize()

    def ToolbarData(self):
        self.gcpSave = wx.NewId()
        self.gcpAdd = wx.NewId()
        self.gcpDelete = wx.NewId()
        self.gcpClear = wx.NewId()
        self.gcpReload = wx.NewId()
        self.rms = wx.NewId()
        self.georect = wx.NewId()
        self.settings = wx.NewId()
        self.quit = wx.NewId()

        return (
            (self.gcpSave, 'grGcpSave', Icons["grGcpSave"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["grGcpSave"].GetLabel(), Icons["grGcpSave"].GetDesc(),
             self.parent.SaveGCPs),
            (self.gcpAdd, 'grGrGcpAdd', Icons["grGcpAdd"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["grGcpAdd"].GetLabel(), Icons["grGcpAdd"].GetDesc(),
             self.parent.AddGCP),
            (self.gcpDelete, 'grGrGcpDelete', Icons["grGcpDelete"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["grGcpDelete"].GetLabel(), Icons["grGcpDelete"].GetDesc(), 
             self.parent.DeleteGCP),
            (self.gcpClear, 'grGcpClear', Icons["grGcpClear"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["grGcpClear"].GetLabel(), Icons["grGcpClear"].GetDesc(), 
             self.parent.ClearGCP),
            (self.gcpReload, 'grGcpReload', Icons["grGcpReload"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["grGcpReload"].GetLabel(), Icons["grGcpReload"].GetDesc(), 
             self.parent.ReloadGCPs),

            ("", "", "", "", "", "", ""),
            (self.rms, 'grGcpRms', Icons["grGcpRms"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["grGcpRms"].GetLabel(), Icons["grGcpRms"].GetDesc(),
             self.parent.OnRMS),
            (self.georect, 'grGeorect', Icons["grGeorect"].GetBitmap(), 
             wx.ITEM_NORMAL, Icons["grGeorect"].GetLabel(), Icons["grGeorect"].GetDesc(),
             self.parent.OnGeorect),
            ("", "", "", "", "", "", ""),
            (self.settings, 'grSettings', Icons["grSettings"].GetBitmap(), 
             wx.ITEM_NORMAL, Icons["grSettings"].GetLabel(), Icons["grSettings"].GetDesc(),
             self.parent.OnSettings),
            (self.quit, 'grGcpQuit', Icons["grGcpQuit"].GetBitmap(), 
             wx.ITEM_NORMAL, Icons["grGcpQuit"].GetLabel(), Icons["grGcpQuit"].GetDesc(),
             self.parent.OnQuit)
            )
    
class VDigitToolbar(AbstractToolbar):
    """
    Toolbar for digitization
    """
    def __init__(self, parent, mapcontent, layerTree=None, log=None):
        self.mapcontent    = mapcontent # Map class instance
        self.layerTree     = layerTree  # reference to layer tree associated to map display
        self.log           = log        # log area
        AbstractToolbar.__init__(self, parent)
        
        # currently selected map layer for editing (reference to MapLayer instance)
        self.mapLayer = None
        # list of vector layers from Layer Manager (only in the current mapset)
        self.layers   = [] 
        
        self.comboid    = None
        
        # only one dialog can be open
        self.settingsDialog   = None
        
        # create toolbars (two rows optionally)
        self.InitToolbar(self.ToolbarData())
        self.Bind(wx.EVT_TOOL, self.OnTool)
        
        # default action (digitize new point, line, etc.)
        self.action = { 'desc' : 'addLine',
                        'type' : 'point',
                        'id'   : self.addPoint }
        
        # list of available vector maps
        self.UpdateListOfLayers(updateTool=True)
        
        # realize toolbar
        self.Realize()
        # workaround for Mac bug. May be fixed by 2.8.8, but not before then.
        self.combo.Hide()
        self.combo.Show()
        
        # disable undo/redo
        self.EnableTool(self.undo, False)
        
        # toogle to pointer by default
        self.OnTool(None)
        
        self.FixSize(width = 105)
        
    def ToolbarData(self):
        """!
        Toolbar data
        """
        data = []
        
        self.addPoint = wx.NewId()
        self.addLine = wx.NewId()
        self.addBoundary = wx.NewId()
        self.addCentroid = wx.NewId()
        self.moveVertex = wx.NewId()
        self.addVertex = wx.NewId()
        self.removeVertex = wx.NewId()
        self.splitLine = wx.NewId()
        self.editLine = wx.NewId()
        self.moveLine = wx.NewId()
        self.deleteLine = wx.NewId()
        self.additionalTools = wx.NewId()
        self.displayCats = wx.NewId()
        self.displayAttr = wx.NewId()
        self.copyCats = wx.NewId()
        self.undo = wx.NewId()
        self.settings = wx.NewId()
        self.exit = wx.NewId()
        
        data = [("", "", "", "", "", "", ""),
                (self.addPoint, "digAddPoint", Icons["digAddPoint"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digAddPoint"].GetLabel(), Icons["digAddPoint"].GetDesc(),
                 self.OnAddPoint),
                (self.addLine, "digAddLine", Icons["digAddLine"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digAddLine"].GetLabel(), Icons["digAddLine"].GetDesc(),
                 self.OnAddLine),
                (self.addBoundary, "digAddBoundary", Icons["digAddBoundary"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digAddBoundary"].GetLabel(), Icons["digAddBoundary"].GetDesc(),
                 self.OnAddBoundary),
                (self.addCentroid, "digAddCentroid", Icons["digAddCentroid"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digAddCentroid"].GetLabel(), Icons["digAddCentroid"].GetDesc(),
                 self.OnAddCentroid),
                (self.moveVertex, "digMoveVertex", Icons["digMoveVertex"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digMoveVertex"].GetLabel(), Icons["digMoveVertex"].GetDesc(),
                 self.OnMoveVertex),
                (self.addVertex, "digAddVertex", Icons["digAddVertex"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digAddVertex"].GetLabel(), Icons["digAddVertex"].GetDesc(),
                 self.OnAddVertex),
                (self.removeVertex, "digRemoveVertex", Icons["digRemoveVertex"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digRemoveVertex"].GetLabel(), Icons["digRemoveVertex"].GetDesc(),
                 self.OnRemoveVertex),
                (self.splitLine, "digSplitLine", Icons["digSplitLine"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digSplitLine"].GetLabel(), Icons["digSplitLine"].GetDesc(),
                 self.OnSplitLine),
                (self.editLine, "digEditLine", Icons["digEditLine"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digEditLine"].GetLabel(), Icons["digEditLine"].GetDesc(),
                 self.OnEditLine),
                (self.moveLine, "digMoveLine", Icons["digMoveLine"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digMoveLine"].GetLabel(), Icons["digMoveLine"].GetDesc(),
                 self.OnMoveLine),
                (self.deleteLine, "digDeleteLine", Icons["digDeleteLine"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digDeleteLine"].GetLabel(), Icons["digDeleteLine"].GetDesc(),
                 self.OnDeleteLine),
                (self.displayCats, "digDispCats", Icons["digDispCats"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digDispCats"].GetLabel(), Icons["digDispCats"].GetDesc(),
                 self.OnDisplayCats),
                (self.copyCats, "digCopyCats", Icons["digCopyCats"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digCopyCats"].GetLabel(), Icons["digCopyCats"].GetDesc(),
                 self.OnCopyCA),
                (self.displayAttr, "digDispAttr", Icons["digDispAttr"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digDispAttr"].GetLabel(), Icons["digDispAttr"].GetDesc(),
                 self.OnDisplayAttr),
                (self.additionalTools, "digAdditionalTools", Icons["digAdditionalTools"].GetBitmap(),
                 wx.ITEM_CHECK, Icons["digAdditionalTools"].GetLabel(),
                 Icons["digAdditionalTools"].GetDesc(),
                 self.OnAdditionalToolMenu),
                ("", "", "", "", "", "", ""),
                (self.undo, "digUndo", Icons["digUndo"].GetBitmap(),
                 wx.ITEM_NORMAL, Icons["digUndo"].GetLabel(), Icons["digUndo"].GetDesc(),
                 self.OnUndo),
                # data.append((self.undo, "digRedo", Icons["digRedo"].GetBitmap(),
                #             wx.ITEM_NORMAL, Icons["digRedo"].GetLabel(), Icons["digRedo"].GetDesc(),
                #             self.OnRedo))
                (self.settings, "digSettings", Icons["digSettings"].GetBitmap(),
                 wx.ITEM_NORMAL, Icons["digSettings"].GetLabel(), Icons["digSettings"].GetDesc(),
                 self.OnSettings),
                (self.exit, "digExit", Icons["quit"].GetBitmap(),
                 wx.ITEM_NORMAL, Icons["digExit"].GetLabel(), Icons["digExit"].GetDesc(),
                 self.OnExit)]
        
        return data
    
    def OnTool(self, event):
        """!Tool selected -> disable selected tool in map toolbar"""
        id = self.parent.toolbars['map'].GetAction(type='id')
        self.parent.toolbars['map'].ToggleTool(id, False)
        
        # set cursor
        cursor = self.parent.cursors["cross"]
        self.parent.MapWindow.SetCursor(cursor)
        
        # pointer
        self.parent.OnPointer(None)
        
        if event:
            # deselect previously selected tool
            id = self.action.get('id', -1)
            if id != event.GetId():
                self.ToggleTool(self.action['id'], False)
            else:
                self.ToggleTool(self.action['id'], True)
            
            self.action['id'] = event.GetId()
            
            event.Skip()
        
        self.ToggleTool(self.action['id'], True)
        
        # clear tmp canvas
        if self.action['id'] != id:
            self.parent.MapWindow.ClearLines(pdc=self.parent.MapWindow.pdcTmp)
            if self.parent.digit and \
                    len(self.parent.digit.driver.GetSelected()) > 0:
                # cancel action
                self.parent.MapWindow.OnMiddleDown(None)
        
        # set focus
        self.parent.MapWindow.SetFocus()
        
    def OnAddPoint(self, event):
        """!Add point to the vector map Laier"""
        Debug.msg (2, "VDigitToolbar.OnAddPoint()")
        self.action = { 'desc' : "addLine",
                        'type' : "point",
                        'id'   : self.addPoint }
        self.parent.MapWindow.mouse['box'] = 'point'
        
    def OnAddLine(self, event):
        """!Add line to the vector map layer"""
        Debug.msg (2, "VDigitToolbar.OnAddLine()")
        self.action = { 'desc' : "addLine",
                        'type' : "line",
                        'id'   : self.addLine }
        self.parent.MapWindow.mouse['box'] = 'line'
        ### self.parent.MapWindow.polycoords = [] # reset temp line
                
    def OnAddBoundary(self, event):
        """!Add boundary to the vector map layer"""
        Debug.msg (2, "VDigitToolbar.OnAddBoundary()")
        if self.action['desc'] != 'addLine' or \
                self.action['type'] != 'boundary':
            self.parent.MapWindow.polycoords = [] # reset temp line
        self.action = { 'desc' : "addLine",
                        'type' : "boundary",
                        'id'   : self.addBoundary }
        self.parent.MapWindow.mouse['box'] = 'line'
        
    def OnAddCentroid(self, event):
        """!Add centroid to the vector map layer"""
        Debug.msg (2, "VDigitToolbar.OnAddCentroid()")
        self.action = { 'desc' : "addLine",
                        'type' : "centroid",
                        'id'   : self.addCentroid }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnExit (self, event=None):
        """!Quit digitization tool"""
        # stop editing of the currently selected map layer
        if self.mapLayer:
            self.StopEditing()
        
        # close dialogs if still open
        if self.settingsDialog:
            self.settingsDialog.OnCancel(None)
            
        # set default mouse settings
        self.parent.MapWindow.mouse['use'] = "pointer"
        self.parent.MapWindow.mouse['box'] = "point"
        self.parent.MapWindow.polycoords = []
        
        # disable the toolbar
        self.parent.RemoveToolbar("vdigit")
                
    def OnMoveVertex(self, event):
        """!Move line vertex"""
        Debug.msg(2, "Digittoolbar.OnMoveVertex():")
        self.action = { 'desc' : "moveVertex",
                        'id'   : self.moveVertex }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnAddVertex(self, event):
        """!Add line vertex"""
        Debug.msg(2, "Digittoolbar.OnAddVertex():")
        self.action = { 'desc' : "addVertex",
                        'id'   : self.addVertex }
        self.parent.MapWindow.mouse['box'] = 'point'
        
    def OnRemoveVertex(self, event):
        """!Remove line vertex"""
        Debug.msg(2, "Digittoolbar.OnRemoveVertex():")
        self.action = { 'desc' : "removeVertex",
                        'id'   : self.removeVertex }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnSplitLine(self, event):
        """!Split line"""
        Debug.msg(2, "Digittoolbar.OnSplitLine():")
        self.action = { 'desc' : "splitLine",
                        'id'   : self.splitLine }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnEditLine(self, event):
        """!Edit line"""
        Debug.msg(2, "Digittoolbar.OnEditLine():")
        self.action = { 'desc' : "editLine",
                        'id'   : self.editLine }
        self.parent.MapWindow.mouse['box'] = 'line'

    def OnMoveLine(self, event):
        """!Move line"""
        Debug.msg(2, "Digittoolbar.OnMoveLine():")
        self.action = { 'desc' : "moveLine",
                        'id'   : self.moveLine }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnDeleteLine(self, event):
        """!Delete line"""
        Debug.msg(2, "Digittoolbar.OnDeleteLine():")
        self.action = { 'desc' : "deleteLine",
                        'id'   : self.deleteLine }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnDisplayCats(self, event):
        """!Display/update categories"""
        Debug.msg(2, "Digittoolbar.OnDisplayCats():")
        self.action = { 'desc' : "displayCats",
                        'id'   : self.displayCats }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnDisplayAttr(self, event):
        """!Display/update attributes"""
        Debug.msg(2, "Digittoolbar.OnDisplayAttr():")
        self.action = { 'desc' : "displayAttrs",
                        'id'   : self.displayAttr }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnCopyCA(self, event):
        """!Copy categories/attributes menu"""
        point = wx.GetMousePosition()
        toolMenu = wx.Menu()
        # Add items to the menu
        cats = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                           text=_('Copy categories'),
                           kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(cats)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnCopyCats, cats)
        if self.action['desc'] == "copyCats":
            cats.Check(True)
        
        attrb = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                            text=_('Duplicate attributes'),
                            kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(attrb)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnCopyAttrb, attrb)
        if self.action['desc'] == "copyAttrs":
            attrb.Check(True)
        
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.parent.MapWindow.PopupMenu(toolMenu)
        toolMenu.Destroy()
        
        if self.action['desc'] == "addPoint":
            self.ToggleTool(self.copyCats, False)
        
    def OnCopyCats(self, event):
        """!Copy categories"""
        if self.action['desc'] == 'copyCats': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.copyCats, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnCopyCats():")
        self.action = { 'desc' : "copyCats",
                        'id'   : self.copyCats }
        self.parent.MapWindow.mouse['box'] = 'point'

    def OnCopyAttrb(self, event):
        if self.action['desc'] == 'copyAttrs': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.copyCats, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnCopyAttrb():")
        self.action = { 'desc' : "copyAttrs",
                        'id'   : self.copyCats }
        self.parent.MapWindow.mouse['box'] = 'point'
        
    def OnUndo(self, event):
        """!Undo previous changes"""
        self.parent.digit.Undo()
        
        event.Skip()

    def EnableUndo(self, enable=True):
        """!Enable 'Undo' in toolbar
        
        @param enable False for disable
        """
        if enable:
            if self.GetToolEnabled(self.undo) is False:
                self.EnableTool(self.undo, True)
        else:
            if self.GetToolEnabled(self.undo) is True:
                self.EnableTool(self.undo, False)
        
    def OnSettings(self, event):
        """!Show settings dialog"""
        if self.parent.digit is None:
            reload(vdigit)
            from vdigit import VDigit as VDigit
            try:
                self.parent.digit = VDigit(mapwindow=self.parent.MapWindow)
            except SystemExit:
                self.parent.digit = None
        
        if not self.settingsDialog:
            self.settingsDialog = VDigitSettingsDialog(parent=self.parent, title=_("Digitization settings"),
                                                       style=wx.DEFAULT_DIALOG_STYLE)
            self.settingsDialog.Show()

    def OnAdditionalToolMenu(self, event):
        """!Menu for additional tools"""
        point = wx.GetMousePosition()
        toolMenu = wx.Menu()
        # Add items to the menu
        copy = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                           text=_('Copy features from (background) vector map'),
                           kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(copy)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnCopy, copy)
        if self.action['desc'] == "copyLine":
            copy.Check(True)
        
        flip = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                           text=_('Flip selected lines/boundaries'),
                           kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(flip)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnFlip, flip)
        if self.action['desc'] == "flipLine":
            flip.Check(True)
        
        merge = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                            text=_('Merge selected lines/boundaries'),
                            kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(merge)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnMerge, merge)
        if self.action['desc'] == "mergeLine":
            merge.Check(True)
        
        breakL = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                             text=_('Break selected lines/boundaries at intersection'),
                             kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(breakL)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnBreak, breakL)
        if self.action['desc'] == "breakLine":
            breakL.Check(True)
        
        snap = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                           text=_('Snap selected lines/boundaries (only to nodes)'),
                           kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(snap)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnSnap, snap)
        if self.action['desc'] == "snapLine":
            snap.Check(True)
        
        connect = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                              text=_('Connect selected lines/boundaries'),
                              kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(connect)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnConnect, connect)
        if self.action['desc'] == "connectLine":
            connect.Check(True)
        
        query = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                            text=_('Query features'),
                            kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(query)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnQuery, query)
        if self.action['desc'] == "queryLine":
            query.Check(True)
        
        zbulk = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                            text=_('Z bulk-labeling of 3D lines'),
                            kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(zbulk)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnZBulk, zbulk)
        if self.action['desc'] == "zbulkLine":
            zbulk.Check(True)
        
        typeconv = wx.MenuItem(parentMenu=toolMenu, id=wx.ID_ANY,
                               text=_('Feature type conversion'),
                               kind=wx.ITEM_CHECK)
        toolMenu.AppendItem(typeconv)
        self.parent.MapWindow.Bind(wx.EVT_MENU, self.OnTypeConversion, typeconv)
        if self.action['desc'] == "typeConv":
            typeconv.Check(True)
        
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.parent.MapWindow.PopupMenu(toolMenu)
        toolMenu.Destroy()
        
        if self.action['desc'] == 'addPoint':
            self.ToggleTool(self.additionalTools, False)
        
    def OnCopy(self, event):
        """!Copy selected features from (background) vector map"""
        if self.action['desc'] == 'copyLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnCopy():")
        self.action = { 'desc' : "copyLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnFlip(self, event):
        """!Flip selected lines/boundaries"""
        if self.action['desc'] == 'flipLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnFlip():")
        self.action = { 'desc' : "flipLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnMerge(self, event):
        """!Merge selected lines/boundaries"""
        if self.action['desc'] == 'mergeLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnMerge():")
        self.action = { 'desc' : "mergeLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnBreak(self, event):
        """!Break selected lines/boundaries"""
        if self.action['desc'] == 'breakLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnBreak():")
        self.action = { 'desc' : "breakLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnSnap(self, event):
        """!Snap selected features"""
        if self.action['desc'] == 'snapLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnSnap():")
        self.action = { 'desc' : "snapLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnConnect(self, event):
        """!Connect selected lines/boundaries"""
        if self.action['desc'] == 'connectLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnConnect():")
        self.action = { 'desc' : "connectLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnQuery(self, event):
        """!Query selected lines/boundaries"""
        if self.action['desc'] == 'queryLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnQuery(): %s" % \
                      UserSettings.Get(group='vdigit', key='query', subkey='selection'))
        self.action = { 'desc' : "queryLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnZBulk(self, event):
        """!Z bulk-labeling selected lines/boundaries"""
        if not self.parent.digit.driver.Is3D():
            wx.MessageBox(parent=self.parent,
                          message=_("Vector map is not 3D. Operation canceled."),
                          caption=_("Error"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
            return
        
        if self.action['desc'] == 'zbulkLine': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnZBulk():")
        self.action = { 'desc' : "zbulkLine",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'line'

    def OnTypeConversion(self, event):
        """!Feature type conversion

        Supported conversions:
         - point <-> centroid
         - line <-> boundary
        """
        if self.action['desc'] == 'typeConv': # select previous action
            self.ToggleTool(self.addPoint, True)
            self.ToggleTool(self.additionalTools, False)
            self.OnAddPoint(event)
            return
        
        Debug.msg(2, "Digittoolbar.OnTypeConversion():")
        self.action = { 'desc' : "typeConv",
                        'id'   : self.additionalTools }
        self.parent.MapWindow.mouse['box'] = 'box'

    def OnSelectMap (self, event):
        """
        Select vector map layer for editing

        If there is a vector map layer already edited, this action is
        firstly terminated. The map layer is closed. After this the
        selected map layer activated for editing.
        """
        if event.GetSelection() == 0: # create new vector map layer
            if self.mapLayer:
                openVectorMap = self.mapLayer.GetName(fullyQualified=False)['name']
            else:
                openVectorMap = None
            mapName = gdialogs.CreateNewVector(self.parent,
                                               exceptMap = openVectorMap, log = self.log,
                                               cmd = (('v.edit',
                                                       { 'tool' : 'create' },
                                                       'map')),
                                               disableAdd=True)[0]
            if mapName:
                # add layer to map layer tree
                if self.layerTree:
                    self.layerTree.AddLayer(ltype='vector',
                                            lname=mapName,
                                            lchecked=True,
                                            lopacity=1.0,
                                            lcmd=['d.vect', 'map=%s' % mapName])
                    
                    vectLayers = self.UpdateListOfLayers(updateTool=True)
                    selection = vectLayers.index(mapName)
                else:
                    pass # TODO (no Layer Manager)
            else:
                self.combo.SetValue(_('Select vector map'))
                return 
        else:
            selection = event.GetSelection() - 1 # first option is 'New vector map'
        
        # skip currently selected map
        if self.layers[selection] == self.mapLayer:
            return False
        
        if self.mapLayer:
            # deactive map layer for editing
            self.StopEditing()
        
        # select the given map layer for editing
        self.StartEditing(self.layers[selection])
        
        event.Skip()

        return True
    
    def StartEditing (self, mapLayer):
        """
        Start editing selected vector map layer.

        @param mapLayer reference to MapLayer instance
        """
        # deactive layer
        self.mapcontent.ChangeLayerActive(mapLayer, False)
        
        # clean map canvas
        ### self.parent.MapWindow.EraseMap()
        
        # unset background map if needed
        if mapLayer:
            if UserSettings.Get(group='vdigit', key='bgmap',
                                subkey='value', internal=True) == mapLayer.GetName():
                UserSettings.Set(group='vdigit', key='bgmap',
                                 subkey='value', value='', internal=True)
            
            self.parent.statusbar.SetStatusText(_("Please wait, "
                                                  "opening vector map <%s> for editing...") % \
                                                    mapLayer.GetName(),
                                                0)
        
        # reload vdigit module
        reload(vdigit)
        from vdigit import VDigit as VDigit
        # use vdigit's PseudoDC
        self.parent.MapWindow.DefinePseudoDC(vdigit = True)
        self.parent.digit = VDigit(mapwindow=self.parent.MapWindow)
        
        self.mapLayer = mapLayer
        
        # open vector map
        try:
            if not self.parent.MapWindow.CheckPseudoDC():
                raise gcmd.DigitError(parent=self.parent,
                                      message=_("Unable to initialize display driver of vector "
                                                "digitizer. See 'Command output' for details."))
            self.parent.digit.SetMapName(mapLayer.GetName())
        except gcmd.DigitError, e:
            self.mapLayer = None
            self.StopEditing()
            print >> sys.stderr, e # wxMessageBox
            return False
        
        # update toolbar
        self.combo.SetValue(mapLayer.GetName())
        self.parent.toolbars['map'].combo.SetValue (_('Digitize'))
        
        Debug.msg (4, "VDigitToolbar.StartEditing(): layer=%s" % mapLayer.GetName())
        
        # change cursor
        if self.parent.MapWindow.mouse['use'] == 'pointer':
            self.parent.MapWindow.SetCursor(self.parent.cursors["cross"])
        
        # create pseudoDC for drawing the map
        self.parent.MapWindow.pdcVector = vdigit.PseudoDC()
        self.parent.digit.driver.SetDevice(self.parent.MapWindow.pdcVector)

        if not self.parent.MapWindow.resize:
            self.parent.MapWindow.UpdateMap(render=True)
        
        opacity = mapLayer.GetOpacity(float=True)
        if opacity < 1.0:
            alpha = int(opacity * 255)
            self.parent.digit.driver.UpdateSettings(alpha)
        
        return True

    def StopEditing(self):
        """!Stop editing of selected vector map layer.

        @return True on success
        @return False on failure
        """
        # use wx's PseudoDC
        self.parent.MapWindow.DefinePseudoDC(vdigit = False)
        
        self.combo.SetValue (_('Select vector map'))
        
        # save changes
        if self.mapLayer:
            Debug.msg (4, "VDigitToolbar.StopEditing(): layer=%s" % self.mapLayer.GetName())
            if UserSettings.Get(group='vdigit', key='saveOnExit', subkey='enabled') is False:
                if self.parent.digit.GetUndoLevel() > 0:
                    dlg = wx.MessageDialog(parent=self.parent,
                                           message=_("Do you want to save changes "
                                                     "in vector map <%s>?") % self.mapLayer.GetName(),
                                           caption=_("Save changes?"),
                                           style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
                    if dlg.ShowModal() == wx.ID_NO:
                        # revert changes
                        self.parent.digit.Undo(0)
                    dlg.Destroy()
        
            self.parent.statusbar.SetStatusText(_("Please wait, "
                                                  "closing and rebuilding topology of "
                                                  "vector map <%s>...") % self.mapLayer.GetName(),
                                                0)
        
            self.parent.digit.SetMapName(None) # -> close map
        
            # re-active layer 
            item = self.parent.tree.FindItemByData('maplayer', self.mapLayer)
            if item and self.parent.tree.IsItemChecked(item):
                self.mapcontent.ChangeLayerActive(self.mapLayer, True)
        
        # change cursor
        self.parent.MapWindow.SetCursor(self.parent.cursors["default"])
        
        # disable pseudodc for vector map layer
        self.parent.MapWindow.pdcVector = None
        self.parent.digit.driver.SetDevice(None)
        
        # close dialogs
        for dialog in ('attributes', 'category'):
            if self.parent.dialogs[dialog]:
                self.parent.dialogs[dialog].Close()
                self.parent.dialogs[dialog] = None
        
        self.parent.digit.__del__() # FIXME: destructor is not called here (del)
        self.parent.digit = None
        
        self.mapLayer = None
        
        self.parent.MapWindow.redrawAll = True
        
        return True
    
    def UpdateListOfLayers (self, updateTool=False):
        """!
        Update list of available vector map layers.
        This list consists only editable layers (in the current mapset)

        Optionally also update toolbar
        """
        Debug.msg (4, "VDigitToolbar.UpdateListOfLayers(): updateTool=%d" % \
                   updateTool)
        
        layerNameSelected = None
         # name of currently selected layer
        if self.mapLayer:
            layerNameSelected = self.mapLayer.GetName()
        
        # select vector map layer in the current mapset
        layerNameList = []
        self.layers = self.mapcontent.GetListOfLayers(l_type="vector",
                                                      l_mapset=grass.gisenv()['MAPSET'])
        for layer in self.layers:
            if not layer.name in layerNameList: # do not duplicate layer
                layerNameList.append (layer.GetName())
        
        if updateTool: # update toolbar
            if not self.mapLayer:
                value = _('Select vector map')
            else:
                value = layerNameSelected

            if not self.comboid:
                self.combo = wx.ComboBox(self, id=wx.ID_ANY, value=value,
                                         choices=[_('New vector map'), ] + layerNameList, size=(115, -1),
                                         style=wx.CB_READONLY)
                self.comboid = self.InsertControl(0, self.combo)
                self.parent.Bind(wx.EVT_COMBOBOX, self.OnSelectMap, self.comboid)
            else:
                self.combo.SetItems([_('New vector map'), ] + layerNameList)
            
            self.Realize()
        
        return layerNameList

    def GetLayer(self):
        """!Get selected layer for editing -- MapLayer instance"""
        return self.mapLayer
    
class ProfileToolbar(AbstractToolbar):
    """!
    Toolbar for profiling raster map
    """ 
    def __init__(self, parent):
        AbstractToolbar.__init__(self, parent)
        
        self.InitToolbar(self.ToolbarData())
        
        # realize the toolbar
        self.Realize()
        
    def ToolbarData(self):
        """!Toolbar data"""
        self.transect = wx.NewId()
        self.addraster = wx.NewId()
        self.draw = wx.NewId()
        self.options = wx.NewId()
        self.drag = wx.NewId()
        self.zoom = wx.NewId()
        self.unzoom = wx.NewId()
        self.erase = wx.NewId()
        self.save = wx.NewId()
        self.printer = wx.NewId()
        self.quit = wx.NewId()
                
        # tool, label, bitmap, kind, shortHelp, longHelp, handler
        return   (
            (self.addraster, 'raster', Icons["addrast"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["addrast"].GetLabel(), Icons["addrast"].GetDesc(),
             self.parent.OnSelectRaster),
            (self.transect, 'transect', Icons["transect"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["transect"].GetLabel(), Icons["transect"].GetDesc(),
             self.parent.OnDrawTransect),
            (self.draw, 'profiledraw', Icons["profiledraw"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["profiledraw"].GetLabel(), Icons["profiledraw"].GetDesc(),
             self.parent.OnCreateProfile),
            (self.options, 'options', Icons["profileopt"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["profileopt"].GetLabel(), Icons["profileopt"].GetDesc(),
             self.parent.ProfileOptionsMenu),
            (self.drag, 'drag', Icons['pan'].GetBitmap(),
             wx.ITEM_NORMAL, Icons["pan"].GetLabel(), Icons["pan"].GetDesc(),
             self.parent.OnDrag),
            (self.zoom, 'zoom', Icons['zoom_in'].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_in"].GetLabel(), Icons["zoom_in"].GetDesc(),
             self.parent.OnZoom),
            (self.unzoom, 'unzoom', Icons['zoom_back'].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_back"].GetLabel(), Icons["zoom_back"].GetDesc(),
             self.parent.OnRedraw),
            (self.erase, 'erase', Icons["erase"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["erase"].GetLabel(), Icons["erase"].GetDesc(),
             self.parent.OnErase),
            ("", "", "", "", "", "", ""),
            (self.save, 'save', Icons["savefile"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["savefile"].GetLabel(), Icons["savefile"].GetDesc(),
             self.parent.SaveToFile),
            (self.printer, 'print', Icons["printmap"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["printmap"].GetLabel(), Icons["printmap"].GetDesc(),
             self.parent.PrintMenu),
            (self.quit, 'quit', Icons["quit"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["quit"].GetLabel(), Icons["quit"].GetDesc(),
             self.parent.OnQuit),
            )
    
class NvizToolbar(AbstractToolbar):
    """!
    Nviz toolbar
    """
    def __init__(self, parent, mapcontent):
        self.mapcontent = mapcontent
        AbstractToolbar.__init__(self, parent)
        
        self.InitToolbar(self.ToolbarData())
        
        # realize the toolbar
        self.Realize()
        
    def ToolbarData(self):
        """!Toolbar data"""
        self.settings = wx.NewId()
        self.quit = wx.NewId()
        
        # tool, label, bitmap, kind, shortHelp, longHelp, handler
        return   (
            (self.settings, "settings", Icons["nvizSettings"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["nvizSettings"].GetLabel(), Icons["nvizSettings"].GetDesc(),
             self.OnSettings),
            (self.quit, 'quit', Icons["quit"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["quit"].GetLabel(), Icons["quit"].GetDesc(),
             self.OnExit),
            )
    
    def OnSettings(self, event):
        win = self.parent.nvizToolWin
        if not win.IsShown():
            self.parent.nvizToolWin.Show()
        else:
            self.parent.nvizToolWin.Hide()

    def OnExit (self, event=None):
        """!Quit nviz tool (swith to 2D mode)"""
        # hide dialogs if still open
        if self.parent.nvizToolWin:
            self.parent.nvizToolWin.Hide()
        
        # set default mouse settings
        self.parent.MapWindow.mouse['use'] = "pointer"
        self.parent.MapWindow.mouse['box'] = "point"
        self.parent.MapWindow.polycoords = []
        
        # disable the toolbar
        self.parent.RemoveToolbar("nviz")
        

