"""
@package nviz.py

@brief 2.5/3D visialization mode for Map Display Window

List of classes:
 - GLWindow
 - NvizToolWindow
 - ViewPositionWindow

(C) 2008 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Martin Landa <landa.martin gmail.com> (Google SoC 2008)
"""

import os
import sys
import time

from threading import Thread

import wx
import wx.lib.colourselect as csel
import wx.lib.scrolledpanel as scrolled
errorMsg = ''
try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError, e:
    haveGLCanvas = False
    errorMsg = e
try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    haveOpenGL = True
except ImportError, e:
    haveOpenGL = False
    errorMsg = e

import globalvar
import gcmd
import gselect
from debug import Debug as Debug
from mapdisp import MapWindow as MapWindow
from preferences import globalSettings as UserSettings
try:
    nvizPath = os.path.join(globalvar.ETCWXDIR, "nviz")
    sys.path.append(nvizPath)
    import grass7_wxnviz as wxnviz
    haveNviz = True
except ImportError, e:
    haveNviz = False
    errorMsg = e

class GLWindow(MapWindow, glcanvas.GLCanvas):
    """OpenGL canvas for Map Display Window"""
    def __init__(self, parent, id,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE,
                 Map=None, tree=None, gismgr=None):

        self.parent = parent # MapFrame
        self.Map = Map
        self.tree = tree
        self.gismgr = gismgr
        
        glcanvas.GLCanvas.__init__(self, parent, id)
        MapWindow.__init__(self, parent, id, pos, size, style,
                           Map, tree, gismgr)


        self.parent = parent # MapFrame

        # attribList=[wx.WX_GL_RGBA, wx.GLX_RED_SIZE, 1,
        #             wx.GLX_GREEN_SIZE, 1,
        #             wx.GLX_BLUE_SIZE, 1,
        #             wx.GLX_DEPTH_SIZE, 1,
        #             None])

        self.init = False
        self.render = True # render in full resolution

        #
        # create nviz instance
        #
        self.nvizClass = wxnviz.Nviz()

        #
        # set current display
        #
        self.nvizClass.SetDisplay(self)

        #
        # set default lighting model
        #
        self.nvizClass.SetLightsDefault()

        #
        # initialize mouse position
        #
        self.lastX = self.x = 30
        self.lastY = self.y = 30

        #
        # default values
        #
        self.view = UserSettings.Get(group='nviz', key='view') # reference
        self.update = {} # update view/controls
        self.object = {} # loaded data objects (layer index / gsurf id)

        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseAction)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseAction)

    def OnEraseBackground(self, event):
        pass # do nothing, to avoid flashing on MSW

    def OnSize(self, event):
        self.size = self.parent.GetClientSize()
        if self.GetContext():
            Debug.msg(3, "GLCanvas.OnPaint(): w=%d, h=%d" % \
                      (self.size.width, self.size.height))
            self.SetCurrent()
            self.nvizClass.ResizeWindow(self.size.width,
                                        self.size.height)
        
        event.Skip()

    def OnPaint(self, event):
        Debug.msg(3, "GLCanvas.OnPaint()")

        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.init:
            self.nvizClass.InitView()
            self.LoadDataLayers()
            self.view['z-exag']['value'], \
                self.view['height']['value'] = self.nvizClass.SetViewDefault()
            
            if hasattr(self.parent, "nvizToolWin"):
                self.parent.nvizToolWin.UpdatePage('view')
                self.parent.nvizToolWin.UpdateSettings()
            self.init = True
        self.UpdateMap()

    def OnMouseAction(self, event):
        # change position
        if event.Dragging() and event.LeftIsDown():
            self.lastX = self.lastY = self.x = self.y
            self.x, self.y = event.GetPosition()
            self.Refresh(False)

        # change perspective with mouse wheel
        wheel = event.GetWheelRotation()

        if wheel != 0:
            current  = event.GetPositionTuple()[:]
            Debug.msg (5, "GLWindow.OnMouseMotion(): wheel=%d" % wheel)
            if wheel > 0:
                value = -1 * self.view['persp']['step']
            else:
                value = self.view['persp']['step']
            self.view['persp']['value'] += value
            if self.view['persp']['value'] < 1:
                self.view['persp']['value'] = 1
            elif self.view['persp']['value'] > 100:
                self.view['persp']['value'] = 100

            if hasattr(self.parent, "nvizToolWin"):
                self.parent.nvizToolWin.UpdateSettings()

            self.nvizClass.SetView(self.view['pos']['x'], self.view['pos']['y'],
                                   self.view['height']['value'],
                                   self.view['persp']['value'],
                                   self.view['twist']['value'])

            # redraw map
            self.OnPaint(None)

            # update statusbar
            ### self.parent.StatusbarUpdate()

    def OnLeftDown(self, event):
        self.CaptureMouse()
        self.x, self.y = self.lastX, self.lastY = event.GetPosition()
        
    def OnLeftUp(self, event):
        self.ReleaseMouse()

    def UpdateMap(self, render=True):
        """
        Updates the canvas anytime there is a change to the
        underlaying images or to the geometry of the canvas.

        @param render re-render map composition
        """
        start = time.clock()

        self.resize = False

        # if self.size is None:
        #    self.size = self.GetClientSize()
        
        #         w, h = self.size
        #         w = float(max(w, 1.0))
        #         h = float(max(h, 1.0))
        #         d = float(min(w, h))
        #         xScale = d / w
        #         yScale = d / h
        # print w, h, d, xScale, yScale
        # print self.y, self.lastY, self.x, self.lastX
        # print (self.y - self.lastY) * yScale, (self.x - self.lastX) * xScale 
        # print self.x * xScale
        
        #glRotatef((self.y - self.lastY) * yScale, 1.0, 0.0, 0.0);
        #glRotatef((self.x - self.lastX) * xScale, 0.0, 1.0, 0.0);

        if self.render:
            self.parent.onRenderGauge.Show()
            self.parent.onRenderGauge.SetRange(2)
            self.parent.onRenderGauge.SetValue(0)

        if 'view' in self.update.keys():
            self.nvizClass.SetView(self.view['pos']['x'], self.view['pos']['y'],
                                   self.view['height']['value'],
                                   self.view['persp']['value'],
                                   self.view['twist']['value'])
            del self.update['view']

        if 'z-exag' in self.update.keys():
            self.nvizClass.SetZExag(self.view['z-exag']['value'])
            del self.update['z-exag']

        if self.render is True:
            self.parent.onRenderGauge.SetValue(1)
            wx.Yield()
            self.nvizClass.Draw(False)
        else:
            self.nvizClass.Draw(True) # quick

        self.SwapBuffers()

        stop = time.clock()

        if self.render:
            self.parent.onRenderGauge.SetValue(2)
            # hide process bar
            self.parent.onRenderGauge.Hide()

        #
        # update statusbar
        #
        # self.parent.StatusbarUpdate()

        Debug.msg(3, "GLWindow.UpdateMap(): render=%s, -> time=%g" % \
                      (self.render, (stop-start)))

    def EraseMap(self):
        """
        Erase the canvas
        """
        self.nvizClass.EraseMap()
        self.SwapBuffers()

    def LoadDataLayers(self):
        """Load raster/vector from current layer tree

        @todo volumes
        """
        # load raster maps
        for layer in self.Map.GetListOfLayers(l_type='raster', l_active=True):
            self.LoadRaster(layer)

        # load vector maps
        for layer in self.Map.GetListOfLayers(l_type='vector', l_active=True):
            self.LoadVector(layer)

    def LoadRaster(self, layer):
        """Load raster map -> surface"""
        if layer.type != 'raster':
            return

        id = self.nvizClass.LoadSurface(str(layer.name), None, None)
        if id < 0:
            raise gcmd.NvizError(parent=self.parent,
                                 message=_("Unable to load raster map <%s>" % layer.name))

        # set resolution
        res = UserSettings.Get(group='nviz', key='surface',
                               subkey=['draw', 'res-fine'])
        wire = UserSettings.Get(group='nviz', key='surface',
                                subkey=['draw', 'res-coarse'])

        self.nvizClass.SetSurfaceRes(id, res, wire)
        self.object[self.Map.GetLayerIndex(layer)] = id ### FIXME layer index is not fixed id!

    def UnloadRaster(self, layer):
        """Unload raster map"""
        if layer.type != 'raster':
            return

        idx = self.Map.GetLayerIndex(layer) ### FIXME layer index is not fixed id!
        if not self.object.has_key(idx):
            return

        if layer.type == 'raster':
            if self.nvizClass.UnloadSurface(self.object[idx]) == 0:
                raise gcmd.NvizError(parent=self.parent,
                                     message=_("Unable to unload raster map <%s>" % layer.name))
    def LoadVector(self, layer):
        """Load vector map overlay"""
        if layer.type != 'vector':
            return

        id = self.nvizClass.LoadVector(str(layer.name))
        if id < 0:
            raise gcmd.NvizError(parent=self.parent,
                                 message=_("Unable to load vector map <%s>" % layer.name))

        self.object[self.Map.GetLayerIndex(layer)] = id ### FIXME layer index is not fixed id!

    def UnloadVector(self, layer):
        """Unload vector map overlay"""
        if layer.type != 'vector':
            return

        idx = self.Map.GetLayerIndex(layer) ### FIXME layer index is not fixed id!
        if not self.object.has_key(idx):
            return

        if layer.type == 'vector':
            if self.nvizClass.UnloadVector(self.object[idx]) == 0:
                raise gcmd.NvizError(parent=self.parent,
                                     message=_("Unable to unload vector map <%s>" % layer.name))

    def Reset(self):
        """Reset (unload data)"""
        self.nvizClass.Reset()
        self.init = False

    def OnZoomToMap(self, event):
        """
        Set display extents to match selected raster
        or vector map or volume.

        @todo vector, volume
        """
        layer = self.GetSelectedLayer()

        if layer is None:
            return

        Debug.msg (3, "GLWindow.OnZoomToMap(): layer=%s, type=%s" % \
                       (layer.name, layer.type))

        self.nvizClass.SetViewportDefault()

    def ResetView(self):
        """Reset to default view"""
        self.view['pos']['x'] = wxnviz.VIEW_DEFAULT_POS_X
        self.view['pos']['y'] = wxnviz.VIEW_DEFAULT_POS_Y
        self.view['z-exag']['value'], \
            self.view['height']['value'] = self.nvizClass.SetViewDefault()
        self.view['persp']['value'] = wxnviz.VIEW_DEFAULT_PERSP
        self.view['twist']['value'] = wxnviz.VIEW_DEFAULT_TWIST

        self.update['view'] = None
        self.update['z-exag'] = None

    def GetMapObjId(self, layer):
        """Get map object id of given map layer (2D)

        @param layer MapLayer instance
        """
        index = self.Map.GetLayerIndex(layer)

        try:
            return self.object[index]
        except:
            return -1

    def SetLayerSettings(self, data):
        """Set settings for selected layer

        @param data settings

        @return 1 on success
        @return 0 on failure
        """
        # get currently selected map layer
        if not self.tree or not self.tree.GetSelection():
            return 0
        
        item = self.tree.GetSelection()
        try:
            self.tree.SetPyData(item)[0]['nviz'] = data
        except:
            return 0
            
        return 1

class NvizToolWindow(wx.Frame):
    """Experimental window for Nviz tools

    @todo integrate with Map display
    """
    def __init__(self, parent=None, id=wx.ID_ANY, title=_("Nviz tools"),
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, mapWindow=None):
        
        self.parent = parent # MapFrame
        self.mapWindow = mapWindow
        self.settings = mapWindow.view # GLWindow.view

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # dialog body
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.win = {} # window ids

        #
        # notebook
        #
        self.notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)

        self.page = {}
        # view page
        self.__createViewPage()
        self.page['view'] = 0
        # surface page
        self.__createSurfacePage()
        self.page['surface'] = 1
        # vector page
        self.__createVectorPage()
        self.page['vector'] = 2
        # settings page
        self.__createSettingsPage()
        self.page['settings'] = 3
        self.pageUpdated = True
        self.UpdatePage('surface')
        self.UpdatePage('vector')
        self.UpdatePage('settings')

        mainSizer.Add(item=self.notebook, proportion=1,
                      flag=wx.EXPAND | wx.ALL, border=5)

        #
        # update dialog (selected layer)
        #
        mapLayer = self.mapWindow.GetSelectedLayer()
        if mapLayer:
            type = mapLayer.type
            if type == 'raster':
                self.UpdatePage('surface')
            elif type == 'vector':
                self.UpdatePage('vector')

        #
        # bindings
        #
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        #
        # layout
        #
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        
    def __createViewPage(self):
        """Create view settings page"""
        panel = wx.Panel(parent=self.notebook, id=wx.ID_ANY)
        self.notebook.AddPage(page=panel,
                              text=" %s " % _("View"))
        
        pageSizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=3, hgap=3)

        self.win['view'] = {}

        # position
        posSizer = wx.GridBagSizer(vgap=3, hgap=3)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("W")),
                     pos=(1, 0), flag=wx.ALIGN_CENTER)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("N")),
                     pos=(0, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_BOTTOM)
        viewPos = ViewPositionWindow(panel, id=wx.ID_ANY, size=(175, 175),
                                     settings=self.settings, mapwindow=self.mapWindow)
        self.win['view']['pos'] = viewPos.GetId()
        posSizer.Add(item=viewPos,
                     pos=(1, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("S")),
                     pos=(2, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_TOP)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("E")),
                     pos=(1, 2), flag=wx.ALIGN_CENTER)
        gridSizer.Add(item=posSizer, pos=(0, 0))
                  
        # perspective
        self.CreateControl(panel, dict=self.win['view'], name='persp',
                           range=(self.settings['persp']['min'], self.settings['persp']['max']),
                           bind=(self.OnViewChange, self.OnViewChanged, self.OnViewChangedSpin))
        gridSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Perspective:")),
                      pos=(1, 0), flag=wx.ALIGN_CENTER)
        gridSizer.Add(item=self.FindWindowById(self.win['view']['persp']['slider']), pos=(2, 0))
        gridSizer.Add(item=self.FindWindowById(self.win['view']['persp']['spin']), pos=(3, 0),
                      flag=wx.ALIGN_CENTER)        

        # twist
        self.CreateControl(panel, dict=self.win['view'], name='twist',
                           range=(self.settings['twist']['min'], self.settings['twist']['max']),
                           bind=(self.OnViewChange, self.OnViewChanged, self.OnViewChangedSpin))
        gridSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Twist:")),
                      pos=(1, 1), flag=wx.ALIGN_CENTER)
        gridSizer.Add(item=self.FindWindowById(self.win['view']['twist']['slider']), pos=(2, 1))
        gridSizer.Add(item=self.FindWindowById(self.win['view']['twist']['spin']), pos=(3, 1),
                      flag=wx.ALIGN_CENTER)        

        # height + z-exag
        self.CreateControl(panel, dict=self.win['view'], name='height', sliderHor=False,
                           range=(self.settings['height']['min'], self.settings['height']['max']),
                           bind=(self.OnViewChange, self.OnViewChanged, self.OnViewChangedSpin))
        self.CreateControl(panel, dict=self.win['view'], name='z-exag', sliderHor=False,
                           range=(self.settings['z-exag']['min'], self.settings['z-exag']['max']),
                           bind=(self.OnViewChange, self.OnViewChanged, self.OnViewChangedSpin))
        heightSizer = wx.GridBagSizer(vgap=3, hgap=3)
        heightSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Height:")),
                      pos=(0, 0), flag=wx.ALIGN_LEFT, span=(1, 2))
        heightSizer.Add(item=self.FindWindowById(self.win['view']['height']['slider']),
                        flag=wx.ALIGN_RIGHT, pos=(1, 0))
        heightSizer.Add(item=self.FindWindowById(self.win['view']['height']['spin']),
                        flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.TOP |
                        wx.BOTTOM | wx.RIGHT, pos=(1, 1))
        heightSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Z-exag:")),
                      pos=(0, 2), flag=wx.ALIGN_LEFT, span=(1, 2))
        heightSizer.Add(item=self.FindWindowById(self.win['view']['z-exag']['slider']),
                        flag=wx.ALIGN_RIGHT, pos=(1, 2))
        heightSizer.Add(item=self.FindWindowById(self.win['view']['z-exag']['spin']),
                        flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.TOP |
                        wx.BOTTOM | wx.RIGHT, pos=(1, 3))

        gridSizer.Add(item=heightSizer, pos=(0, 1), flag=wx.ALIGN_RIGHT)

        # view setup + reset
        viewSizer = wx.BoxSizer(wx.HORIZONTAL)

        viewSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY,
                                         label=_("Look at:")),
                      flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        
        viewType = wx.Choice (parent=panel, id=wx.ID_ANY, size=(125, -1),
                              choices = [_("top"),
                                         _("north"),
                                         _("south"),
                                         _("east"),
                                         _("west"),
                                         _("north-west"),
                                         _("north-east"),
                                         _("south-east"),
                                         _("south-west")])
        viewType.SetSelection(0)
        viewType.Bind(wx.EVT_CHOICE, self.OnLookAt)
        # self.win['lookAt'] = viewType.GetId()
        viewSizer.Add(item=viewType, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                      border=5)

        reset = wx.Button(panel, id=wx.ID_ANY, label=_("Reset"))
        reset.SetToolTipString(_("Reset to default view"))
        # self.win['reset'] = reset.GetId()
        reset.Bind(wx.EVT_BUTTON, self.OnResetView)

        viewSizer.Add(item=reset, proportion=1,
                      flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                      border=5)

        gridSizer.AddGrowableCol(3)
        gridSizer.Add(item=viewSizer, pos=(4, 0), span=(1, 2),
                      flag=wx.EXPAND)

        # body
        pageSizer.Add(item=gridSizer, proportion=1,
                      flag=wx.EXPAND | wx.ALL,
                      border=5)

        panel.SetSizer(pageSizer)

    def __createSurfacePage(self):
        """Create view settings page"""
        panel = wx.Panel(parent=self.notebook, id=wx.ID_ANY)
        # panel = scrolled.ScrolledPanel(parent=self.notebook, id=wx.ID_ANY)
        # panel.SetupScrolling(scroll_x=True, scroll_y=True)

        self.notebook.AddPage(page=panel,
                              text=" %s " % _("Surface"))
        
        pageSizer = wx.BoxSizer(wx.VERTICAL)

        self.win['surface'] = {}
        #
        # surface attributes
        #
        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s " % (_("Surface attributes")))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=3, hgap=3)

        # labels
        # col = 0
        #         for type in (_("Attribute"),
        #                      _("Use"),
        #                      _("Map"),
        #                      _("Constant")):
        #             gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
        #                                              label=type),
        #                           pos=(0, col))
        #             col += 1

        # type 
        self.win['surface']['attr'] = {}
        row = 0
        for code, attrb in (('topo', _("Topography")),
                           ('color', _("Color")),
                           ('mask', _("Mask")),
                           ('transp', _("Transparency")),
                           ('shine', _("Shininess")),
                           ('emit', _("Emission"))):
            self.win['surface'][code] = {} 
            gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                             label=attrb + ':'),
                          pos=(row, 0), flag=wx.ALIGN_CENTER_VERTICAL)
            use = wx.Choice (parent=panel, id=wx.ID_ANY, size=(100, -1),
                             choices = [_("map")])
            if code not in ('topo', 'color', 'shine'):
                use.Insert(item=_("unset"), pos=0)
                self.win['surface'][code]['required'] = False
            else:
                self.win['surface'][code]['required'] = True
            if code != 'mask':
                use.Append(item=_('constant'))
            self.win['surface'][code]['use'] = use.GetId()
            use.Bind(wx.EVT_CHOICE, self.OnSurfaceUse)
            gridSizer.Add(item=use, flag=wx.ALIGN_CENTER_VERTICAL,
                          pos=(row, 1))

            map = gselect.Select(parent=panel, id=wx.ID_ANY,
                                 # size=globalvar.DIALOG_GSELECT_SIZE,
                                 size=(200, -1),
                                 type="raster")
            self.win['surface'][code]['map'] = map.GetId() - 1 # FIXME
            map.Bind(wx.EVT_TEXT, self.OnSurfaceMap)
            # changing map topography not allowed
            if code == 'topo':
                map.Enable(False)
            gridSizer.Add(item=map, flag=wx.ALIGN_CENTER_VERTICAL,
                          pos=(row, 2))

            if code == 'color':
                value = csel.ColourSelect(panel, id=wx.ID_ANY,
                                          colour=UserSettings.Get(group='nviz', key='surface',
                                                                  subkey=['color', 'value']))
                value.Bind(csel.EVT_COLOURSELECT, self.OnSurfaceMap)
            elif code == 'mask':
                value = None
            else:
                value = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(65, -1),
                                    initial=0)
                if code == 'topo':
                    value.SetRange(minVal=-1e9, maxVal=1e9)
                elif code in ('shine', 'transp', 'emit'):
                    value.SetRange(minVal=0, maxVal=255)
                else:
                    value.SetRange(minVal=0, maxVal=100)
                value.Bind(wx.EVT_TEXT, self.OnSurfaceMap)
            
            if value:
                self.win['surface'][code]['const'] = value.GetId()
                value.Enable(False)
                gridSizer.Add(item=value, flag=wx.ALIGN_CENTER_VERTICAL,
                              pos=(row, 3))
            else:
                self.win['surface'][code]['const'] = None

            self.SetSurfaceUseMap(code) # -> enable map / disable constant
                
            row += 1

        boxSizer.Add(item=gridSizer, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=3)
        pageSizer.Add(item=boxSizer, proportion=0,
                      flag=wx.EXPAND | wx.ALL,
                      border=5)

        #
        # draw
        #
        self.win['surface']['draw'] = {}
        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s " % (_("Draw")))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=5, hgap=5)
        gridSizer.AddGrowableCol(4)

        # mode
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Mode:")),
                      pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        mode = wx.Choice (parent=panel, id=wx.ID_ANY, size=(100, -1),
                          choices = [_("coarse"),
                                     _("fine"),
                                     _("both")])
        mode.SetName("selection")
        mode.Bind(wx.EVT_CHOICE, self.OnSurfaceMode)
        self.win['surface']['draw']['mode'] = mode.GetId()
        gridSizer.Add(item=mode, flag=wx.ALIGN_CENTER_VERTICAL,
                      pos=(0, 1))

        # resolution (mode)
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Resolution:")),
                      pos=(0, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        resSizer = wx.BoxSizer(wx.HORIZONTAL)
        resSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                        label=_("coarse:")),
                     flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=3)
        resC = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(65, -1),
                           initial=1,
                           min=1,
                           max=100)
        resC.SetName("value")
        self.win['surface']['draw']['res-coarse'] = resC.GetId()
        resC.Bind(wx.EVT_SPINCTRL, self.OnSurfaceResolution)
        resSizer.Add(item=resC, flag=wx.ALL, border=3)
        
        resSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                        label=_("fine:")),
                     flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=3)
        resF = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(65, -1),
                           initial=1,
                           min=1,
                           max=100)
        resF.SetName("value")
        self.win['surface']['draw']['res-fine'] = resF.GetId()
        resF.Bind(wx.EVT_SPINCTRL, self.OnSurfaceResolution)
        resSizer.Add(item=resF, flag=wx.ALL, border=3)

        gridSizer.Add(item=resSizer, pos=(0, 3), span=(1, 2))

        # style
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Coarse style:")),
                      pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        style = wx.Choice (parent=panel, id=wx.ID_ANY, size=(100, -1),
                          choices = [_("wire"),
                                     _("surface")])
        style.SetName("selection")
        self.win['surface']['draw']['style'] = style.GetId()
        style.Bind(wx.EVT_CHOICE, self.OnSurfaceMode)
        gridSizer.Add(item=style, flag=wx.ALIGN_CENTER_VERTICAL,
                      pos=(1, 1))

        # shading
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Shading:")),
                      pos=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        shade = wx.Choice (parent=panel, id=wx.ID_ANY, size=(100, -1),
                           choices = [_("flat"),
                                      _("gouraud")])
        shade.SetName("selection")
        self.win['surface']['draw']['shading'] = shade.GetId()
        shade.Bind(wx.EVT_CHOICE, self.OnSurfaceMode)
        gridSizer.Add(item=shade, flag=wx.ALIGN_CENTER_VERTICAL,
                      pos=(1, 3))

        # color
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Wire color:")),
                      pos=(2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        color = csel.ColourSelect(panel, id=wx.ID_ANY)
        color.SetName("colour")
        color.Bind(csel.EVT_COLOURSELECT, self.OnSurfaceWireColor)
        self.win['surface']['draw']['color'] = color.GetId()
        gridSizer.Add(item=color, flag=wx.ALIGN_CENTER_VERTICAL,
                      pos=(2, 1))

        boxSizer.Add(item=gridSizer, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=3)
        pageSizer.Add(item=boxSizer, proportion=0,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=5)

        all = wx.Button(panel, id=wx.ID_ANY, label=_("All"))
        all.SetToolTipString(_("Use for all loaded surfaces"))
        # self.win['reset'] = reset.GetId()
        all.Bind(wx.EVT_BUTTON, self.OnSurfaceModeAll)
        gridSizer.Add(item=all, flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
                      pos=(2, 4))

        #
        # mask
        #
        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s " % (_("Mask")))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=5, hgap=5)

        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Mask zeros:")),
                      pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)

        elev = wx.CheckBox(parent=panel, id=wx.ID_ANY,
                           label=_("by elevation"))
        elev.Enable(False) # TODO: not implemented yet
        gridSizer.Add(item=elev, pos=(0, 1))

        color = wx.CheckBox(parent=panel, id=wx.ID_ANY,
                           label=_("by color"))
        color.Enable(False) # TODO: not implemented yet
        gridSizer.Add(item=color, pos=(0, 2))

        boxSizer.Add(item=gridSizer, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=3)
        pageSizer.Add(item=boxSizer, proportion=0,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=5)

        #
        # position
        #
        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s " % (_("Position")))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=5, hgap=5)

        # position
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label="X:"),
                      pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        x = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(100, -1),
                        initial=0,
                        min=0,
                        max=100)
        x.Enable(False) # TODO: not implemented yet
        gridSizer.Add(item=x, pos=(0, 1))

        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label="X:"),
                      pos=(0, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(100, -1),
                        initial=0,
                        min=0,
                        max=100)
        y.Enable(False) # TODO: not implemented yet
        gridSizer.Add(item=y, pos=(0, 3))

        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label="X:"),
                      pos=(0, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        z = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(100, -1),
                        initial=0,
                        min=0,
                        max=100)
        z.Enable(False) # TODO: not implemented yet
        gridSizer.Add(item=z, pos=(0, 5))

        boxSizer.Add(item=gridSizer, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=3)
        pageSizer.Add(item=boxSizer, proportion=0,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=5)
        
        panel.SetSizer(pageSizer)

    def __createVectorPage(self):
        """Create view settings page"""
        panel = wx.Panel(parent=self.notebook, id=wx.ID_ANY)
        self.notebook.AddPage(page=panel,
                              text=" %s " % _("Vector"))
        
        pageSizer = wx.BoxSizer(wx.VERTICAL)

        self.win['vector'] = {}
        #
        # vector lines
        #
        self.win['vector']['lines'] = {}
        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s " % (_("Vector lines")))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=5, hgap=5)

        # width
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Width:")),
                      pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)

        width = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(65, -1),
                            initial=1,
                            min=1,
                            max=100)
        self.win['vector']['lines']['width'] = width.GetId()
        width.Bind(wx.EVT_SPINCTRL, self.OnVectorLines)
        gridSizer.Add(item=width, pos=(0, 1),
                      flag=wx.ALIGN_CENTER_VERTICAL)

        gridSizer.AddGrowableCol(2)

        # color
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Color:")),
                      pos=(0, 3), flag=wx.ALIGN_CENTER_VERTICAL)

        color = csel.ColourSelect(panel, id=wx.ID_ANY,
                                  colour=UserSettings.Get(group='nviz', key='vector',
                                                          subkey=['lines', 'color']))
        self.win['vector']['lines']['color'] = color.GetId()
        color.Bind(csel.EVT_COLOURSELECT, self.OnVectorLines)

        gridSizer.Add(item=color, pos=(0, 4))

        gridSizer.AddGrowableCol(5)

        # display
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Display:")),
                      pos=(0, 6), flag=wx.ALIGN_CENTER_VERTICAL)

        display = wx.Choice (parent=panel, id=wx.ID_ANY, size=(100, -1),
                             choices = [_("on surface"),
                                        _("flat")])
        self.win['vector']['lines']['flat'] = display.GetId()
        display.Bind(wx.EVT_CHOICE, self.OnVectorDisplay)

        gridSizer.Add(item=display, flag=wx.ALIGN_CENTER_VERTICAL,
                      pos=(0, 7))

        surface = wx.ComboBox(parent=panel, id=wx.ID_ANY, size=(250, -1),
                              style=wx.CB_SIMPLE | wx.CB_READONLY,
                              choices=[])
        self.win['vector']['lines']['surface'] = surface.GetId()
        gridSizer.Add(item=surface, 
                      pos=(1, 0), span=(1, 8),
                      flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)

        # high
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Hight above surface:")),
                      pos=(2, 0), flag=wx.ALIGN_CENTER_VERTICAL,
                      span=(1, 2))
        
        self.CreateControl(panel, dict=self.win['vector']['lines'], name='height', size=300,
                           range=(0, 1000),
                           bind=(self.OnVectorHeight, self.OnVectorHeight, self.OnVectorHeight))
        gridSizer.Add(item=self.FindWindowById(self.win['vector']['lines']['height']['slider']),
                      pos=(2, 2), span=(1, 6))
        gridSizer.Add(item=self.FindWindowById(self.win['vector']['lines']['height']['spin']),
                      pos=(3, 4),
                      flag=wx.ALIGN_CENTER)

        boxSizer.Add(item=gridSizer, proportion=1,
                     flag=wx.ALL | wx.EXPAND, border=3)
        pageSizer.Add(item=boxSizer, proportion=0,
                      flag=wx.EXPAND | wx.ALL,
                      border=5)

        panel.SetSizer(pageSizer)

    def __createSettingsPage(self):
        """Create settings page"""
        panel = wx.Panel(parent=self.notebook, id=wx.ID_ANY)
        self.notebook.AddPage(page=panel,
                              text=" %s " % _("Settings"))
        
        pageSizer = wx.BoxSizer(wx.VERTICAL)

        self.win['settings'] = {}

        #
        # general
        #
        self.win['settings']['general'] = {}
        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s " % (_("General")))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=3, hgap=3)

        # background color
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Background color:")),
                      pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)

        color = csel.ColourSelect(panel, id=wx.ID_ANY,
                                  colour=UserSettings.Get(group='nviz', key='settings',
                                                          subkey=['general', 'bgcolor']))
        self.win['settings']['general']['bgcolor'] = color.GetId()
        color.Bind(csel.EVT_COLOURSELECT, self.OnSettings)
        gridSizer.Add(item=color, pos=(0, 1))


        boxSizer.Add(item=gridSizer, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=3)
        pageSizer.Add(item=boxSizer, proportion=0,
                      flag=wx.EXPAND | wx.ALL,
                      border=5)
        
        panel.SetSizer(pageSizer)


        panel.SetSizer(pageSizer)

    def CreateControl(self, parent, dict, name, range, bind, sliderHor=True, size=200):
        """Add control (Slider + SpinCtrl)"""
        dict[name] = {}
        if sliderHor:
            style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | \
                wx.SL_BOTTOM
            sizeW = (size, -1)
        else:
            style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | \
                wx.SL_BOTTOM | wx.SL_INVERSE
            sizeW = (-1, size)
        slider = wx.Slider(parent=parent, id=wx.ID_ANY,
                           value=self.settings[name]['value'],
                           minValue=range[0],
                           maxValue=range[1],
                           style=style,
                           size=sizeW)
        slider.SetName('slider')
        slider.Bind(wx.EVT_SCROLL, bind[0])
        slider.Bind(wx.EVT_SCROLL_CHANGED, bind[1])
        dict[name]['slider'] = slider.GetId()

        spin = wx.SpinCtrl(parent=parent, id=wx.ID_ANY, size=(65, -1),
                           initial=self.settings[name]['value'],
                           min=range[0],
                           max=range[1])
        #         spin = wx.SpinButton(parent=parent, id=wx.ID_ANY)
        #         spin.SetValue (self.settings[name]['value'])
        #         spin.SetRange(self.settings[name]['min'],
        #                      self.settings[name]['max'])

        # no 'changed' event ... (FIXME)
        spin.SetName('spin')
        spin.Bind(wx.EVT_SPINCTRL, bind[2])
        dict[name]['spin'] = spin.GetId()

    def UpdateSettings(self):
        """Update dialog settings"""
        for control in ('height',
                        'persp',
                        'twist',
                        'z-exag'):
            for win in self.win['view'][control].itervalues():
                self.FindWindowById(win).SetValue(int(self.settings[control]['value']))

        self.FindWindowById(self.win['view']['pos']).Draw()
        self.FindWindowById(self.win['view']['pos']).Refresh(False)
        
        self.Refresh(False)

    def __GetWindowName(self, dict, id):
        for name in dict.iterkeys():
            if type(dict[name]) is type({}):
                for win in dict[name].itervalues():
                    if win == id:
                        return name
            else:
                if dict[name] == id:
                    return name

        return None

    def OnViewChange(self, event):
        """Change view, render in quick mode"""
        # find control
        winName = self.__GetWindowName(self.win['view'], event.GetId())
        if not winName:
            return

        self.settings[winName]['value'] = event.GetInt()
        for win in self.win['view'][winName].itervalues():
            self.FindWindowById(win).SetValue(self.settings[winName]['value'])

        if winName in ('pos', 'height', 'twist', 'persp'):
            self.mapWindow.update['view'] = None
        else:
            self.mapWindow.update[winName] = None

        self.mapWindow.render = False
        self.mapWindow.Refresh(False)

    def OnViewChanged(self, event):
        """View changed, render in full resolution"""
        self.mapWindow.render = True
        self.mapWindow.Refresh(False)

    def OnViewChangedSpin(self, event):
        """View changed, render in full resolution"""
        self.OnViewChange(event)
        self.OnViewChanged(None)

    def OnResetView(self, event):
        """Reset to default view (view page)"""
        self.mapWindow.ResetView()
        self.UpdateSettings()
        self.mapWindow.Refresh(False)

    def OnLookAt(self, event):
        """Look at (view page)"""
        sel = event.GetSelection()
        if sel == 0: # top
            self.settings['pos']['x'] = 0.5
            self.settings['pos']['y'] = 0.5
        elif sel == 1: # north
            self.settings['pos']['x'] = 0.5
            self.settings['pos']['y'] = 0.0
        elif sel == 2: # south
            self.settings['pos']['x'] = 0.5
            self.settings['pos']['y'] = 1.0
        elif sel == 3: # east
            self.settings['pos']['x'] = 1.0
            self.settings['pos']['y'] = 0.5
        elif sel == 4: # west
            self.settings['pos']['x'] = 0.0
            self.settings['pos']['y'] = 0.5
        elif sel == 5: # north-west
            self.settings['pos']['x'] = 0.0
            self.settings['pos']['y'] = 0.0
        elif sel == 6: # north-east
            self.settings['pos']['x'] = 1.0
            self.settings['pos']['y'] = 0.0
        elif sel == 7: # south-east
            self.settings['pos']['x'] = 1.0
            self.settings['pos']['y'] = 1.0
        elif sel == 8: # south-west
            self.settings['pos']['x'] = 0.0
            self.settings['pos']['y'] = 1.0

        self.mapWindow.update['view'] = None
        self.UpdateSettings()
        self.mapWindow.Refresh(False)

    def OnSave(self, event):
        """OK button pressed
        
        Apply changes, update map and save settings of selected layer
        """
        #
        # apply changes
        #
        self.OnApply(None)

        #
        # save settings
        #
        type = self.mapWindow.GetSelectedLayer().type
        data = self.mapWindow.GetSelectedLayer(nviz=True)
        if data is None: # no settings
            data = {}
    
        if type == 'raster': # -> surface
            #
            # surface attributes
            #
            data['attribute'] = {}
            for attrb in ('topo', 'color', 'mask',
                         'transp', 'shine', 'emit'):
                use = self.FindWindowById(self.win['surface'][attrb]['use']).GetSelection()
                if self.win['surface'][attrb]['required']: # map, constant
                    if use == 0: # map
                        map = True
                    elif use == 1: # constant
                        map = False
                else: # unset, map, constant
                    if use == 0: # unset
                        map = None
                    elif use == 1: # map
                        map = True
                    elif use == 2: # constant
                        map = False

                if map is None:
                    continue

                if map:
                    value = self.FindWindowById(self.win['surface'][attrb]['map']).GetValue()
                else:
                    if attrb == 'color':
                        value = self.FindWindowById(self.win['surface'][attrb]['map']).GetColour()
                    else:
                        value = self.FindWindowById(self.win['surface'][attrb]['const']).GetValue()
                    
                data['attribute'][attrb] = {}
                data['attribute'][attrb]['map'] = map
                data['attribute'][attrb]['value'] = value

            #
            # draw
            #
            data['draw'] = {}
            for control in ('mode', 'shading', 'style'):
                data['draw'][control] = self.FindWindowById(self.win['surface']['draw'][control]).GetSelection()
            for control in ('res-coarse', 'res-fine'):
                data['draw'][control] = self.FindWindowById(self.win['surface']['draw'][control]).GetValue()
            
        self.mapWindow.SetLayerSettings(data)

    def UpdateLayerProperties(self):
        """Update data layer properties"""
        mapLayer = self.mapWindow.GetSelectedLayer()
        data = self.mapWindow.GetSelectedLayer(nviz=True)
        print '#1', data
        id = self.mapWindow.GetMapObjId(mapLayer)

        if mapLayer.type == 'raster':
            self.UpdateRasterProperties(id, data)
        elif mapLayer.type == 'vector':
            self.UpdateVectorProperies(id, data)

        print '#2', self.mapWindow.GetSelectedLayer(nviz=True)

    def UpdateRasterProperties(self, id, data):
        """Apply changes for surfaces"""
        # surface attributes
        for attrb in ('topo', 'color', 'mask',
                     'transp', 'shine', 'emit'):
            if self.mapWindow.update.has_key(attrb):
                map, value = self.mapWindow.update[attrb]
                if map is None: # unset
                    # only optional attributes
                    if attrb == 'mask':
                        # TODO: invert mask
                        # TODO: broken in NVIZ
                        self.mapWindow.nvizClass.UnsetSurfaceMask(id)
                    elif attrb == 'transp':
                        self.mapWindow.nvizClass.UnsetSurfaceTransp(id)
                    elif attrb == 'emit':
                        self.mapWindow.nvizClass.UnsetSurfaceEmit(id) 
                else:
                    if len(value) <= 0: # ignore empty values (TODO: warning)
                        continue
                    if attrb == 'topo':
                        self.mapWindow.nvizClass.SetSurfaceTopo(id, map, str(value)) 
                    elif attrb == 'color':
                        self.mapWindow.nvizClass.SetSurfaceColor(id, map, str(value))
                    elif attrb == 'mask':
                        # TODO: invert mask
                        # TODO: broken in NVIZ
                        self.mapWindow.nvizClass.SetSurfaceMask(id, False, str(value))
                    elif attrb == 'transp':
                        self.mapWindow.nvizClass.SetSurfaceTransp(id, map, str(value)) 
                    elif attrb == 'shine':
                        self.mapWindow.nvizClass.SetSurfaceShine(id, map, str(value)) 
                    elif attrb == 'emit':
                        self.mapWindow.nvizClass.SetSurfaceEmit(id, map, str(value)) 

                # update properties
                data[attrb] = self.mapWindow.update[attrb]
                del self.mapWindow.update[attrb]

        # draw res
        if self.mapWindow.update.has_key('draw-res'):
            coarse, fine, all = self.mapWindow.update['draw-res']
            if all:
                self.mapWindow.nvizClass.SetSurfaceRes(-1, fine, coarse)
            else:
                self.mapWindow.nvizClass.SetSurfaceRes(id, fine, coarse)

            # update properties
            data['draw-res'] = self.mapWindow.update['draw-res']

        # draw style
        if self.mapWindow.update.has_key('draw-style'):
            style, all = self.mapWindow.update['draw-style']
            if all:
                self.mapWindow.nvizClass.SetSurfaceStyle(-1, style)
            else:
                self.mapWindow.nvizClass.SetSurfaceStyle(id, style)

            # update properties
            data['draw-style'] = self.mapWindow.update['draw-style']

        # wire color
        if self.mapWindow.update.has_key('draw-color'):
            color, all = self.mapWindow.update['draw-color']
            if all:
                self.mapWindow.nvizClass.SetWireColor(id, str(color))
            else:
                self.mapWindow.nvizClass.SetWireColor(-1, str(color))

            # update properties
            data['draw-color'] = self.mapWindow.update['draw-color']

    def UpdateVectorProperties(self, id, data):
        """Apply changes for vector"""
        if self.mapWindow.update.has_key('vector-lines'):
            width, color, flat = self.mapWindow.update['vector-lines']
            self.mapWindow.nvizClass.SetVectorLineMode(id, color, width, flat)
            
        if self.mapWindow.update.has_key('vector-height'):
            height = self.mapWindow.update['vector-height']
            self.mapWindow.nvizClass.SetVectorHeight(id, height)
            
    def ApplySettings(self):
        """Apply changes in settings"""
        # bgcolor
        color = self.FindWindowById(self.win['settings']['general']['bgcolor']).GetColour()
        color = str(color[0]) + ':' + str(color[1]) + ':' + str(color[2])

        self.mapWindow.nvizClass.SetBgColor(str(color))

    def OnClose(self, event):
        """Close button pressed
        
        Close dialog
        """
        self.Hide()

    def OnSurfaceUse(self, event):
        """Surface attribute -- use -- map/constant"""
        if not self.mapWindow.init:
            return

        # find attribute row
        attrb = self.__GetWindowName(self.win['surface'], event.GetId())
        if not attrb:
            return

        selection = event.GetSelection()
        if self.win['surface'][attrb]['required']: # no 'unset'
            selection += 1
        if selection == 0: # unset
            useMap = None
            value = ''
        elif selection == 1: # map
            useMap = True
            value = self.FindWindowById(self.win['surface'][attrb]['map']).GetValue()
        elif selection == 2: # constant
            useMap = False
            if attrb == 'color':
                value = self.FindWindowById(self.win['surface'][attrb]['const']).GetColour()
                value = str(value[0]) + ':' + str(value[1]) + ':' + str(value[2])
            else:
                value = self.FindWindowById(self.win['surface'][attrb]['const']).GetValue()

        self.SetSurfaceUseMap(attrb, useMap)
        
        self.mapWindow.update[attrb] = (useMap, str(value))
        self.UpdateLayerProperties()

        if self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)

    def SetSurfaceUseMap(self, attrb, map=None):
        if attrb in ('topo', 'color', 'shine'):
            incSel = -1 # decrement selection (no 'unset')
        else:
            incSel = 0

        if map is True: # map
            if attrb != 'topo': # changing map topography not allowed
                self.FindWindowById(self.win['surface'][attrb]['map'] + 1).Enable(True) # FIXME
            if self.win['surface'][attrb]['const']:
                self.FindWindowById(self.win['surface'][attrb]['const']).Enable(False)
            self.FindWindowById(self.win['surface'][attrb]['use']).SetSelection(1 + incSel)
        elif map is False: # const
            self.FindWindowById(self.win['surface'][attrb]['map'] + 1).Enable(False)
            if self.win['surface'][attrb]['const']:
                self.FindWindowById(self.win['surface'][attrb]['const']).Enable(True)
            self.FindWindowById(self.win['surface'][attrb]['use']).SetSelection(2 + incSel)
        else: # unset
            self.FindWindowById(self.win['surface'][attrb]['map'] + 1).Enable(False)
            if self.win['surface'][attrb]['const']:
                self.FindWindowById(self.win['surface'][attrb]['const']).Enable(False)
            self.FindWindowById(self.win['surface'][attrb]['use']).SetSelection(0)

    def OnSurfaceMap(self, event):
        """Set surface attribute"""
        if not self.mapWindow.init:
            return

        attrb = self.__GetWindowName(self.win['surface'], event.GetId()) 
        if not attrb:
            return

        selection = self.FindWindowById(self.win['surface'][attrb]['use']).GetSelection()
        if self.win['surface'][attrb]['required']:
            selection += 1

        if selection == 0: # unset
            map = None
            value = ''
        elif selection == 1: # map
            value = self.FindWindowById(self.win['surface'][attrb]['map']).GetValue()
            map = True
        else: # constant
            if attrb == 'color':
                value = self.FindWindowById(self.win['surface'][attrb]['const']).GetColour()
                value = str(value[0]) + ':' + str(value[1]) + ':' + str(value[2])
            else:
                value = self.FindWindowById(self.win['surface'][attrb]['const']).GetValue()
            map = False

        if self.pageUpdated: # do not update when selection is changed
            self.mapWindow.update[attrb] = (map, str(value))
            self.UpdateLayerProperties()

            if self.parent.autoRender.IsChecked():
                self.mapWindow.Refresh(False)

    def OnSurfaceResolution(self, event):
        """Draw resolution changed"""
        self.SetSurfaceResolution()

        if apply and self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)

    def SetSurfaceResolution(self, all=False):
        """Set draw resolution"""
        coarse = self.FindWindowById(self.win['surface']['draw']['res-coarse']).GetValue()
        fine = self.FindWindowById(self.win['surface']['draw']['res-fine']).GetValue()
            
        self.mapWindow.update['draw-res'] = (coarse, fine, all) 
        self.UpdateLayerProperties()

    def SetSurfaceMode(self, all=False):
        """Set draw mode

        @param apply allow auto-rendering
        """
        value = 0

        mode = self.FindWindowById(self.win['surface']['draw']['mode']).GetSelection()
        if mode == 0: # coarse
            value |= wxnviz.DM_WIRE
            self.FindWindowById(self.win['surface']['draw']['res-coarse']).Enable(True)
            self.FindWindowById(self.win['surface']['draw']['res-fine']).Enable(False)
        elif mode == 1: # fine
            value |= wxnviz.DM_POLY
            self.FindWindowById(self.win['surface']['draw']['res-coarse']).Enable(False)
            self.FindWindowById(self.win['surface']['draw']['res-fine']).Enable(True)
        else: # both
            value |= wxnviz.DM_WIRE_POLY
            self.FindWindowById(self.win['surface']['draw']['res-coarse']).Enable(True)
            self.FindWindowById(self.win['surface']['draw']['res-fine']).Enable(True)

        style = self.FindWindowById(self.win['surface']['draw']['style']).GetSelection()
        if style == 0: # wire
            value |= wxnviz.DM_GRID_WIRE
        else: # surface
            value |= wxnviz.DM_GRID_SURF

        shade = self.FindWindowById(self.win['surface']['draw']['shading']).GetSelection()
        if shade == 0:
            value |= wxnviz.DM_FLAT
        else: # surface
            value |= wxnviz.DM_GOURAUD

        if self.pageUpdated:
            self.mapWindow.update['draw-style'] = (value, all)
            self.UpdateLayerProperties()

    def OnSurfaceMode(self, event):
        """Set draw mode"""
        self.SetSurfaceMode()

        if apply and self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)

    def OnSurfaceModeAll(self, event):
        """Set draw mode (including wire color) for all loaded surfaces"""
        self.SetSurfaceMode(all=True)
        self.SetSurfaceResolution(all=True)
        color = self.FindWindowById(self.win['surface']['draw']['color']).GetColour()
        self.SetSurfaceWireColor(color, all=True)

        if apply and self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)

    def SetSurfaceWireColor(self, color, all=False, apply=True):
        """Set wire color"""
        value = str(color[0]) + ':' + str(color[1]) + ':' + str(color[2])

        if self.pageUpdated:
            self.mapWindow.update['draw-color'] = (value, all)
            self.UpdateLayerProperties()

    def OnSurfaceWireColor(self, event):
        """Set wire color"""
        self.SetSurfaceWireColor(event.GetValue())

        if self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)

    def OnVectorDisplay(self, event):
        """Display vector lines on surface/flat"""
        if event.GetSelection() == 0: # surface
            self.FindWindowById(self.win['vector']['lines']['surface']).Enable(True)
            # set first found surface
            ### TODO
        else: # flat
            self.FindWindowById(self.win['vector']['lines']['surface']).Enable(False)

        self.OnVectorLines(event)

        event.Skip()

    def OnVectorLines(self, event):
        """Set vector lines mode, apply changes if auto-rendering is enabled"""
        width = self.FindWindowById(self.win['vector']['lines']['width']).GetValue()

        color = self.FindWindowById(self.win['vector']['lines']['color']).GetColour()
        color = str(color[0]) + ':' + str(color[1]) + ':' + str(color[2])

        if self.FindWindowById(self.win['vector']['lines']['flat']).GetSelection() == 0:
            flat = False
        else:
            flat = True

        self.mapWindow.update['vector-lines'] = (width, color, flat)
        self.UpdateLayerProperties()
                
        if self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)
        
    def OnVectorHeight(self, event):
        value = event.GetInt()
        if type(event) == type(wx.ScrollEvent()):
            # slider
            win = self.FindWindowById(self.win['vector']['lines']['height']['spin'])
        else:
            # spin
            win = self.FindWindowById(self.win['vector']['lines']['height']['slider'])
        win.SetValue(value)

        self.mapWindow.update['vector-height'] = value
        self.UpdateLayerProperties()

        if self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)
    
    def OnSettings(self, event):
        """Update settings, apply changes if auto-rendering is enabled""" 
        
        if self.parent.autoRender.IsChecked():
            self.mapWindow.Refresh(False)
            
    def UpdatePage(self, pageId):
        """Update dialog (selected page)"""
        self.pageUpdated = False
        layer = self.mapWindow.GetSelectedLayer()
        data = self.mapWindow.GetSelectedLayer(nviz=True)

        if pageId == 'view':
            max = self.settings['z-exag']['value'] * 10
            for control in ('spin', 'slider'):
                self.FindWindowById(self.win['view']['z-exag'][control]).SetRange(0,
                                                                                  max)
        elif pageId == 'surface':
            # disable vector and enable surface page
            self.notebook.GetPage(self.page['surface']).Enable(True)
            self.notebook.GetPage(self.page['vector']).Enable(False)

            # use default values
            if data == {}:
                # attributes
                for attr in ('topo', 'color'): # required
                    if layer and layer.type == 'raster':
                        self.FindWindowById(self.win['surface'][attr]['map']).SetValue(layer.name)
                    else:
                        self.FindWindowById(self.win['surface'][attr]['map']).SetValue('')
                    self.SetSurfaceUseMap(attr, True) # -> map
                if UserSettings.Get(group='nviz', key='surface', subkey=['shine', 'map']) is False:
                    self.SetSurfaceUseMap('shine', False)
                    value = UserSettings.Get(group='nviz', key='surface', subkey=['shine', 'value'])
                    self.FindWindowById(self.win['surface']['shine']['const']).SetValue(value)

                #
                # draw
                #
                for control, value in UserSettings.Get(group='nviz', key='surface', subkey='draw').iteritems():
                    win = self.FindWindowById(self.win['surface']['draw'][control])

                    name = win.GetName()

                    if name == "selection":
                        win.SetSelection(value)
                    elif name == "colour":
                        win.SetColour(value)
                    else:
                        win.SetValue(value)
                # enable/disable res widget + set draw mode
                self.SetSurfaceMode()
                color = self.FindWindowById(self.win['surface']['draw']['color'])
                self.SetSurfaceWireColor(color.GetColour())

            elif layer.type == 'raster':
                # surface attributes
                for attr in data['attr']:
                    if attr['map']:
                        win = self.FindWindowById(self.win['surface'][attr]['map'])
                    else:
                        win = self.FindWindowById(self.win['surface'][attr]['const'])
                        
                    win.SetValue(data['value'])
        elif pageId == 'vector':
            # disable surface and enable current
            self.notebook.GetPage(self.page['surface']).Enable(False)
            self.notebook.GetPage(self.page['vector']).Enable(True)

            if data is None: # defaut values
                # lines
                for name in ('width', 'color'):
                    win = self.FindWindowById(self.win['vector']['lines'][name])
                    win.SetValue(UserSettings.Get(group='nviz', key='vector',
                                                  subkey=['lines', name]))

                display = self.FindWindowById(self.win['vector']['lines']['flat'])
                if UserSettings.Get(group='nviz', key='vector',
                                    subkey=['lines', 'flat']):
                    display.SetSelection(1)
                else:
                    display.SetSelection(0)
            
                value = UserSettings.Get(group='nviz', key='vector',
                                         subkey=['lines', 'height'])
                for type in ('slider', 'spin'):
                    win = self.FindWindowById(self.win['vector']['lines']['height'][type])
                    win.SetValue(value)

        self.pageUpdated = True

    def SetPage(self, name):
        """Get named page"""
        self.notebook.SetSelection(self.page[name])

class ViewPositionWindow(wx.Window):
    """Position control window (for NvizToolWindow)"""
    def __init__(self, parent, id, mapwindow,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize, settings={}):
        self.settings = settings
        self.mapWindow = mapwindow

        wx.Window.__init__(self, parent, id, pos, size)

        self.SetBackgroundColour("WHITE")

        self.pdc = wx.PseudoDC()

        self.pdc.SetBrush(wx.Brush(colour='dark green', style=wx.SOLID))
        self.pdc.SetPen(wx.Pen(colour='dark green', width=2, style=wx.SOLID))

        self.Draw()

        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.Bind(wx.EVT_MOTION,       self.OnMouse)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)

    def Draw(self, pos=None):
        w, h = self.GetClientSize()

        if pos is None:
            x = self.settings['pos']['x']
            y = self.settings['pos']['y']
            x = x * w
            y = y * h
        else:
            x, y = pos

        self.pdc.Clear()
        self.pdc.BeginDrawing()
        self.pdc.DrawLine(w / 2, h / 2, x, y)
        self.pdc.DrawCircle(x, y, 5)
        self.pdc.EndDrawing()

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush("White"))
        dc.Clear()

        self.PrepareDC(dc)
        self.pdc.DrawToDC(dc)

    def OnMouse(self, event):
        if event.LeftIsDown():
            x, y = event.GetPosition()
            self.Draw(pos=(x, y))
            self.Refresh(False)
            w, h = self.GetClientSize()
            x = float(x) / w
            y = float(y) / h
            self.settings['pos']['x'] = x
            self.settings['pos']['y'] = y
            self.mapWindow.update['view'] = None

            self.mapWindow.render = False
        
        if event.LeftUp():
            self.mapWindow.render = True
        
        self.mapWindow.Refresh(eraseBackground=False)
        
