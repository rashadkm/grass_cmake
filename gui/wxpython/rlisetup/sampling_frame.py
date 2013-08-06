# -*- coding: utf-8 -*-
"""!
@package rlisetup.sampling_frame

@brief r.li.setup - draw sample frame

Classes:
 - sampling_frame::RLiSetupMapPanel
 - sampling_frame::RLiSetupToolbar
 - sampling_frame::GraphicsSetItem

(C) 2013 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Anna Petrasova <kratochanna gmail.com>
"""

import os
import sys
import wx
import wx.aui

# adding a path to wxGUI modules
if __name__ == '__main__':
    WXGUIBASE = os.path.join(os.getenv('GISBASE'), 'etc', 'gui', 'wxpython')
    if WXGUIBASE not in sys.path:
        sys.path.append(WXGUIBASE)

from core.utils import _
from core.giface import StandaloneGrassInterface
from mapwin.base import MapWindowProperties
from mapwin.buffered import BufferedMapWindow
from core.render import Map
from gui_core.toolbars import BaseToolbar, BaseIcons
from icons.icon import MetaIcon

from grass.pydispatch.signal import Signal
from grass.pydispatch.errors import DispatcherKeyError


class RLiSetupMapPanel(wx.Panel):
    """!Panel with mapwindow used in r.li.setup"""
    def __init__(self, parent, map_=None):
        wx.Panel.__init__(self, parent=parent)
        self.mapWindowProperties = MapWindowProperties()
        self.mapWindowProperties.setValuesFromUserSettings()
        giface = StandaloneGrassInterface()

        self._region = {}
        self.sampleFrameChanged = Signal('RLiSetupMapPanel.sampleFrameChanged')

        if map_:
            self.map_ = map_
        else:
            self.map_ = Map()
        self.map_.region = self.map_.GetRegion()

        self._mgr = wx.aui.AuiManager(self)
        self.mapWindow = BufferedMapWindow(parent=self, giface=giface,
                                           Map=self.map_,
                                           properties=self.mapWindowProperties)
        self._mgr.AddPane(self.mapWindow, wx.aui.AuiPaneInfo().CentrePane().
                          Dockable(True).BestSize((-1, -1)).Name('mapwindow').
                          CloseButton(False).DestroyOnClose(True).
                          Layer(0))
        self.toolbar = RLiSetupToolbar(self)

        self._mgr.AddPane(self.toolbar,
                          wx.aui.AuiPaneInfo().
                          Name("maptoolbar").Caption(_("Map Toolbar")).
                          ToolbarPane().Left().Name('mapToolbar').
                          CloseButton(False).Layer(1).Gripper(False).
                          BestSize((self.toolbar.GetBestSize())))
        self._mgr.Update()

        self._initTool()

        self._registeredGraphics = self.mapWindow.RegisterGraphicsToDraw(graphicsType='rectangle')
        self._registeredGraphics.AddPen('rlisetup', wx.Pen(wx.GREEN, width=3, style=wx.SOLID))
        self._registeredGraphics.AddItem(coords=[[0, 0], [0, 0]], penName='rlisetup', hide=True)

    def _initTool(self):
        """!Initialize draw mode"""
        self.toolbar.ToggleTool(self.toolbar.draw, True)
        self.toolbar.action['id'] = self.toolbar.draw
        self.OnDraw(None)

    def GetMap(self):
        return self.map_

    def GetRegion(self):
        """!Returns currently drawn region in a dict"""
        return self._region

    def OnZoomIn(self, event):
        """!Zoom in the map.
        """
        self.SwitchTool(event)
        self._prepareZoom(mapWindow=self.mapWindow, zoomType=1)

    def OnZoomOut(self, event):
        """!Zoom out the map.
        """
        self.SwitchTool(event)
        self._prepareZoom(mapWindow=self.mapWindow, zoomType=-1)

    def _prepareZoom(self, mapWindow, zoomType):
        """!Prepares MapWindow for zoom

        @param mapWindow MapWindow to prepare
        @param zoomType 1 for zoom in, -1 for zoom out
        """
        mapWindow.mouse['use'] = "zoom"
        mapWindow.mouse['box'] = "box"
        mapWindow.zoomtype = zoomType
        mapWindow.pen = wx.Pen(colour='Red', width=2, style=wx.SHORT_DASH)

        # change the cursor
        mapWindow.SetNamedCursor('cross')

    def SwitchTool(self, event):
        """!Helper function to switch tools"""
        self.toolbar.OnTool(event)
        self.toolbar.action['desc'] = ''
        try:
            self.mapWindow.mouseLeftUp.disconnect(self._rectangleDrawn)
        except DispatcherKeyError:
            pass

    def OnPan(self, event):
        """!Panning, set mouse to drag
        """
        self.SwitchTool(event)

        self.mapWindow.mouse['use'] = "pan"
        self.mapWindow.mouse['box'] = "pan"
        self.mapWindow.zoomtype = 0

        # change the cursor
        self.mapWindow.SetNamedCursor('hand')

    def OnZoomToMap(self, event):
        layers = self.map_.GetListOfLayers()
        self.mapWindow.ZoomToMap(layers=layers, ignoreNulls=False, render=True)

    def OnDraw(self, event):
        """!Start draw mode"""
        self.SwitchTool(event)

        self.mapWindow.mouse['use'] = None
        self.mapWindow.mouse['box'] = "box"
        self.mapWindow.pen = wx.Pen(colour=wx.RED, width=2, style=wx.SHORT_DASH)
        self.mapWindow.SetNamedCursor('cross')

        self.mapWindow.mouseLeftUp.connect(self._rectangleDrawn)

    def _rectangleDrawn(self):
        """!When drawing finished, get region values"""
        mouse = self.mapWindow.mouse
        item = self._registeredGraphics.GetItem(0)
        p1 = self.mapWindow.Pixel2Cell(mouse['begin'])
        p2 = self.mapWindow.Pixel2Cell(mouse['end'])
        item.SetCoords([p1, p2])
        self._region = {'n': max(p1[1], p2[1]),
                        's': min(p1[1], p2[1]),
                        'w': min(p1[0], p2[0]),
                        'e': max(p1[0], p2[0])}
        item.SetPropertyVal('hide', False)
        self.mapWindow.ClearLines()
        self._registeredGraphics.Draw(self.mapWindow.pdcTmp)

        self.sampleFrameChanged.emit()


icons = {'draw': MetaIcon(img='edit',
                          label=_('Draw sampling frame'),
                          desc=_('Draw sampling frame by clicking and dragging'))}


class RLiSetupToolbar(BaseToolbar):
    """!IClass toolbar
    """
    def __init__(self, parent):
        """!RLiSetup toolbar constructor
        """
        BaseToolbar.__init__(self, parent, style=wx.NO_BORDER | wx.TB_VERTICAL)

        self.InitToolbar(self._toolbarData())
        # realize the toolbar
        self.Realize()

    def _toolbarData(self):
        """!Toolbar data"""
        return self._getToolbarData((('draw', icons['draw'],
                                     self.parent.OnDraw,
                                     wx.ITEM_CHECK),
                                     (None, ),
                                     ('pan', BaseIcons['pan'],
                                      self.parent.OnPan,
                                      wx.ITEM_CHECK),
                                     ('zoomIn', BaseIcons['zoomIn'],
                                      self.parent.OnZoomIn,
                                      wx.ITEM_CHECK),
                                     ('zoomOut', BaseIcons['zoomOut'],
                                      self.parent.OnZoomOut,
                                      wx.ITEM_CHECK),
                                     ('zoomExtent', BaseIcons['zoomExtent'],
                                      self.parent.OnZoomToMap),
                                     ))
