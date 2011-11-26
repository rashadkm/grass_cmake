"""!
@package wxplot.histogram

@brief Histogramming using PyPlot

Classes:
 - Histogram2Frame
 - Histogram2Toolbar

(C) 2011 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Michael Barton, Arizona State University
"""

import sys

import wx
import wx.lib.plot as plot

import grass.script as grass

from gui_core.toolbars import BaseToolbar
from wxplot.base       import BasePlotFrame
from icons.icon        import Icons
from wxplot.dialogs    import HistRasterDialog, PlotStatsFrame

class Histogram2Frame(BasePlotFrame):
    def __init__(self, parent, id, pos, style, size, rasterList = []):
        """!Mainframe for displaying histogram of raster map. Uses wx.lib.plot.
        """
        BasePlotFrame.__init__(self, parent)
        
        self.toolbar = Histogram2Toolbar(parent = self)
        self.SetToolBar(self.toolbar)
        self.SetLabel(_("GRASS Histogramming Tool"))

        #
        # Init variables
        #
        self.rasterList = rasterList
        self.plottype = 'histogram'
        self.group = '' 
        self.ptitle = _('Histogram of')         # title of window
        self.xlabel = _("Raster cell values")   # default X-axis label
        self.ylabel = _("Cell counts")          # default Y-axis label
        self.maptype = 'raster'                 # default type of histogram to plot
        self.histtype = 'count' 
        self.bins = 255
        self.colorList = ["blue", "green", "red", "yellow", "magenta", "cyan", \
                    "aqua", "black", "grey", "orange", "brown", "purple", "violet", \
                    "indigo"]
        
        if len(self.rasterList) > 0: # set raster name(s) from layer manager if a map is selected
            self.InitRasterOpts(self.rasterList, self.plottype)

        self._initOpts()

    def _initOpts(self):
        """!Initialize plot options
        """
        self.InitPlotOpts('histogram')            

    def OnCreateHist(self, event):
        """!Main routine for creating a histogram. Uses r.stats to
        create a list of cell value and count/percent/area pairs. This is passed to
        plot to create a line graph of the histogram.
        """
        self.SetCursor(self.parent.cursors["default"])
        self.SetGraphStyle()
        self.SetupHistogram()
        p = self.CreatePlotList()
        self.DrawPlot(p)

    def OnSelectRaster(self, event):
        """!Select raster map(s) to profile
        """
        dlg = HistRasterDialog(parent = self)

        if dlg.ShowModal() == wx.ID_OK:
            self.rasterList = dlg.rasterList
            self.group = dlg.group
            self.bins = dlg.bins
            self.histtype = dlg.histtype
            self.maptype = dlg.maptype
            self.raster = self.InitRasterOpts(self.rasterList, self.plottype)

            # plot histogram
            if len(self.rasterList) > 0:
                self.OnCreateHist(event = None)

        dlg.Destroy()

    def SetupHistogram(self):
        """!Build data list for ploting each raster
        """

        #
        # populate raster dictionary
        #
        if len(self.rasterList) == 0: return  # nothing selected
        
        for r in self.rasterList:
            self.raster[r]['datalist'] = self.CreateDatalist(r)
            
        #
        # update title
        #
        if self.maptype == 'group':
            self.ptitle = _('Histogram of %s') % self.group.split('@')[0] 
        else: 
            self.ptitle = _('Histogram of %s') % self.rasterList[0].split('@')[0] 

        
        #
        # set xlabel based on first raster map in list to be histogrammed
        #
        units = self.raster[self.rasterList[0]]['units']
        if units != '' and units != '(none)' and units != None:
            self.xlabel = _('Raster cell values %s') % units
        else:
            self.xlabel = _('Raster cell values') 

        #
        # set ylabel from self.histtype
        #
        if self.histtype == 'count': self.ylabel = _('Cell counts')
        if self.histtype == 'percent': self.ylabel = _('Percent of total cells')
        if self.histtype == 'area': self.ylabel = _('Area')

    def CreateDatalist(self, raster):
        """!Build a list of cell value, frequency pairs for histogram
            frequency can be in cell counts, percents, or area
        """
        datalist = []
        
        if self.histtype == 'count': freqflag = 'cn'
        if self.histtype == 'percent': freqflag = 'pn'
        if self.histtype == 'area': freqflag = 'an'
                
        try:
            ret = gcmd.RunCommand("r.stats",
                                  parent = self,
                                  input = raster,
                                  flags = freqflag,
                                  nsteps = self.bins,
                                  fs = ',',
                                  quiet = True,
                                  read = True)
            
            if not ret:
                return datalist
            
            for line in ret.splitlines():
                cellval, histval = line.strip().split(',')
                histval = histval.strip()
                if self.raster[raster]['datatype'] != 'CELL':
                    cellval = cellval.split('-')[0]
                if self.histtype == 'percent':
                    histval = histval.rstrip('%')
                    
                datalist.append((cellval,histval))

            return datalist
        except gcmd.GException, e:
            gcmd.GError(parent = self,
                        message = e.value)
            return None
        
    def CreatePlotList(self):
        """!Make list of elements to plot
        """
        
        # graph the cell value, frequency pairs for the histogram
        self.plotlist = []

        for r in self.rasterList:
            if len(self.raster[r]['datalist']) > 0:
                col = wx.Color(self.raster[r]['pcolor'][0],
                               self.raster[r]['pcolor'][1],
                               self.raster[r]['pcolor'][2],
                               255)
                self.raster[r]['pline'] = plot.PolyLine(self.raster[r]['datalist'],
                                                        colour = col,
                                                        width = self.raster[r]['pwidth'],
                                                        style = self.linestyledict[self.raster[r]['pstyle']],
                                                        legend = self.raster[r]['plegend'])

                self.plotlist.append(self.raster[r]['pline'])
          
        if len(self.plotlist) > 0:        
            return self.plotlist
        else:
            return None

    def Update(self):
        """!Update histogram after changing options
        """
        self.SetGraphStyle()
        p = self.CreatePlotList()
        self.DrawPlot(p)
 
    def OnStats(self, event):
        """!Displays regression information in messagebox
        """
        message = []
        title = _('Statistics for Map(s) Histogrammed')

        for r in self.rasterList:
            rast = r.split('@')[0] 
            ret = grass.read_command('r.univar', map = r, flags = 'e', quiet = True)
            stats = _('Statistics for %s\n\n%s\n') % (rast, ret)
            message.append(stats)
            
        stats = PlotStatsFrame(self, id = wx.ID_ANY, message = message, 
                               title = title)

        if stats.Show() == wx.ID_CLOSE:
            stats.Destroy()       

class Histogram2Toolbar(BaseToolbar):
    """!Toolbar for histogramming raster map
    """ 
    def __init__(self, parent):
        BaseToolbar.__init__(self, parent)
        
        self.InitToolbar(self._toolbarData())
        
        # realize the toolbar
        self.Realize()
        
    def _toolbarData(self):
        """!Toolbar data"""
        icons = Icons['plot']
        return self._getToolbarData((('addraster', Icons['layerManager']["addRast"],
                                      self.parent.OnSelectRaster),
                                     (None, ),
                                     ('draw', icons["draw"],
                                      self.parent.OnCreateHist),
                                     ('erase', Icons['displayWindow']["erase"],
                                      self.parent.OnErase),
                                     ('drag', Icons['displayWindow']['pan'],
                                      self.parent.OnDrag),
                                     ('zoom', Icons['displayWindow']['zoomIn'],
                                      self.parent.OnZoom),
                                     ('unzoom', Icons['displayWindow']['zoomBack'],
                                      self.parent.OnRedraw),
                                     (None, ),
                                     ('statistics', icons['statistics'],
                                      self.parent.OnStats),
                                     ('image', Icons['displayWindow']["saveFile"],
                                      self.parent.SaveToFile),
                                     ('print', Icons['displayWindow']["print"],
                                      self.parent.PrintMenu),
                                     (None, ),
                                     ('settings', icons["options"],
                                      self.parent.PlotOptionsMenu),
                                     ('quit', icons["quit"],
                                      self.parent.OnQuit),
                                     )
)
