"""!
@package wxplot.scatter

@brief Scatter plotting using PyPlot

Classes:
 - scatter::ScatterFrame
 - scatter::ScatterToolbar

(C) 2011 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Michael Barton, Arizona State University
"""

import sys

import wx
import wx.lib.plot as plot

import grass.script as grass

from wxplot.base       import BasePlotFrame
from gui_core.toolbars import BaseToolbar
from icons.icon        import Icons
from wxplot.dialogs    import ScatterRasterDialog, PlotStatsFrame
from core.gcmd         import RunCommand, GException, GError

class ScatterFrame(BasePlotFrame):
    """!Mainframe for displaying bivariate scatter plot of two raster maps. Uses wx.lib.plot.
    """
    def __init__(self, parent, id, pos, style, size, rasterList = []):

        BasePlotFrame.__init__(self, parent)
        
        self.toolbar = ScatterToolbar(parent = self)
        self.SetToolBar(self.toolbar)
        self.SetLabel(_("GRASS Bivariate Scatterplot Tool"))

        #
        # Init variables
        #
        self.rasterList = rasterList
        self.plottype = 'scatter'
        self.ptitle = _('Bivariate Scatterplot')     # title of window
        self.xlabel = _("Raster cell values")           # default X-axis label
        self.ylabel = _("Raster cell values")           # default Y-axis label
        self.maptype = 'raster'                         # default type of scatterplot
        self.scattertype = 'normal' 
        self.bins = 255
        self.colorList = ["blue", "red", "black", "green", "yellow", "magenta", "cyan", \
                    "aqua", "grey", "orange", "brown", "purple", "violet", \
                    "indigo"]
        
        if len(self.rasterList) > 1: # set raster name(s) from layer manager if a map is selected
            self.InitRasterOpts(self.rasterList, 'scatter')

        self._initOpts()

    def _initOpts(self):
        """!Initialize plot options
        """
        self.InitPlotOpts('scatter')            

    def OnCreateScatter(self, event):
        """!Main routine for creating a scatterplot. Uses r.stats to
        create a list of cell value pairs. This is passed to
        plot to create a scatterplot.
        """
        self.SetCursor(self.parent.cursors["default"])
        self.SetGraphStyle()
        self.SetupScatterplot()
        p = self.CreatePlotList()
        self.DrawPlot(p)

    def OnSelectRaster(self, event):
        """!Select raster map(s) to profile
        """
        dlg = ScatterRasterDialog(parent = self)

        if dlg.ShowModal() == wx.ID_OK:
            rlist = dlg.rasterList
            if rlist < 2: 
                dlg.Destroy()
                return                        # need at least 2 rasters for scatterplot

            self.bins = dlg.bins                        # bins for r.stats with float and dcell maps
            self.scattertype = dlg.scattertype          # scatterplot or bubbleplot
            self.rasterList = self.CreatePairs(rlist)   # list of raster pairs (tuples)
            self.raster = self.InitRasterPairs(self.rasterList, 'scatter') # dictionary of raster pairs

            # plot histogram
            if len(self.rasterList) > 0:
                self.OnCreateScatter(event = None)

        dlg.Destroy()
        
    def CreatePairs(self, rlist):
        """!Transforms list of rasters into tuples of raster pairs
        """
        rasterList = []
        next = 'first'
        for r in rlist:
            if next == 'first':
                first = r
                next = 'second'
            else:
                second = r
                t = (first, second)
                rasterList.append(t)
                next = 'first'
                first = second = ''
                
        return rasterList

    def SetupScatterplot(self):
        """!Build data list for ploting each raster
        """

        #
        # initialize title string
        #
        self.ptitle = _('Bivariate Scatterplot of ')        

        #
        # create a datalist for plotting for each raster pair
        #
        if len(self.rasterList) == 0: return  # at least 1 pair of maps needed to plot        
        
        for rpair in self.rasterList:
            self.raster[rpair]['datalist'] = self.CreateDatalist(rpair)
            
            # update title
            self.ptitle += '%s vs %s, ' % (rpair[0].split('@')[0], rpair[1].split('@')[0])

        self.ptitle = self.ptitle.strip(', ')
        
        #
        # set xlabel & ylabel based on raster maps of first pair to be plotted
        #
        self.xlabel = _('Raster cell values')
        self.ylabel = _('Raster cell values') 
        
        units = self.raster[self.rasterList[0]][0]['units']
        if units != '':
            self.xlabel += _(': %s') % units

        units = self.raster[self.rasterList[0]][1]['units']
        if units != '':
            self.ylabel += _(': %s') % units
            
        print 'axis labels = ' + ' x:' + self.xlabel + ' y:' + self.ylabel

    def CreateDatalist(self, rpair):
        """!Build a list of cell value, frequency pairs for histogram
            frequency can be in cell counts, percents, or area
        """
        datalist = []
        
        if self.scattertype == 'bubble': 
            freqflag = 'cn'
        else:
            freqflag = 'n'
                
        try:
            ret = RunCommand("r.stats",
                             parent = self,
                             input = '%s,%s' % rpair,
                             flags = freqflag,
                             nsteps = self.bins,
                             fs = ',',
                             quiet = True,
                             read = True)
            
            if not ret:
                return datalist
            
            for line in ret.splitlines():
                rast1, rast2 = line.strip().split(',')
                rast1 = rast1.strip()
                if '-' in rast1:
                    if rast1[0] == '-':
                        rast1 = '-' + rast1.split('-')[1]
                    else:
                        rast1 = rast1.split('-')[0]

                rast2 = rast2.strip()
                if '-' in rast2:
                    if rast2[0] == '-':
                        rast2 = '-' + rast2.split('-')[1]
                    else:
                        rast2 = rast2.split('-')[0]
                
                rast1 = rast1.encode('ascii', 'ignore')
                rast2 = rast2.encode('ascii', 'ignore')
                    
                datalist.append((rast1,rast2))

            return datalist
        except GException, e:
            GError(parent = self,
                   message = e.value)
            return None
        
    def CreatePlotList(self):
        """!Make list of elements to plot
        """
        # graph the cell value, frequency pairs for the histogram
        self.plotlist = []

        for rpair in self.rasterList:
            if 'datalist' not in self.raster[rpair] or \
                self.raster[rpair]['datalist'] == None: return
            
            if len(self.raster[rpair]['datalist']) > 0:
                col = wx.Color(self.raster[rpair]['pcolor'][0],
                               self.raster[rpair]['pcolor'][1],
                               self.raster[rpair]['pcolor'][2],
                               255)
                scatterpoints = plot.PolyMarker(self.raster[rpair]['datalist'],
                                                legend = ' ' + self.raster[rpair]['plegend'],
                                                colour = col,size = self.raster[rpair]['psize'],
                                                fillstyle = self.ptfilldict[self.raster[rpair]['pfill']],
                                                marker = self.raster[rpair]['ptype'])

                self.plotlist.append(scatterpoints)
          
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
    
    def OnRegression(self, event):
        """!Displays regression information in messagebox
        """
        message = []
        title = _('Regression Statistics for Scatterplot(s)')

        for rpair in self.rasterList:
            if isinstance(rpair, tuple) == False: continue
            rast1, rast2 = rpair
            rast1 = rast1.split('@')[0] 
            rast2 = rast2.split('@')[0] 
            ret = grass.parse_command('r.regression.line', 
                                      map1 = rast1, 
                                      map2 = rast2, 
                                      flags = 'g', quiet = True,
                                      parse = (grass.parse_key_val, { 'sep' : '=' }))
            eqtitle = _('Regression equation for %s vs. %s:\n\n')  % (rast1, rast2)
            eq = _('   %s = %s + %s(%s)\n\n') % (rast2, ret['a'], ret['b'], rast1)
            num = _('N = %s\n') % ret['N']
            rval = _('R = %s\n') % ret['R']
            rsq = _('R-squared = %f\n') % pow(float(ret['R']), 2)
            ftest = _('F = %s\n') % ret['F']
            str = eqtitle + eq + num + rval + rsq + ftest
            message.append(str)
            
        stats = PlotStatsFrame(self, id = wx.ID_ANY, message = message, 
                                      title = title)

        if stats.Show() == wx.ID_CLOSE:
            stats.Destroy()       

class ScatterToolbar(BaseToolbar):
    """!Toolbar for bivariate scatterplots of raster map pairs
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
                                      self.parent.OnCreateScatter),
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
                                      self.parent.OnRegression),
                                     ('image', Icons['displayWindow']["saveFile"],
                                      self.parent.SaveToFile),
                                     ('print', Icons['displayWindow']["print"],
                                      self.parent.PrintMenu),
                                     (None, ),
                                     ('settings', icons["options"],
                                      self.parent.PlotOptionsMenu),
                                     ('quit', icons["quit"],
                                      self.parent.OnQuit),
                                     ))
