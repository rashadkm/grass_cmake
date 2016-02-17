"""
@package datacatalog::catalog

@brief Data catalog

Classes:
 - datacatalog::DataCatalog

(C) 2014 by Tereza Fiedlerova, and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Tereza Fiedlerova
"""

import wx

from core.gthread import gThread
from core.debug import Debug
from datacatalog.tree import DataCatalogTree
from core.utils import _

from grass.pydispatch.signal import Signal

class DataCatalog(wx.Panel):
    """Data catalog panel"""
    def __init__(self, parent, giface=None, id = wx.ID_ANY, title=_("Data catalog"),
                 name='catalog', **kwargs):
        """Panel constructor  """
        self.showNotification = Signal('DataCatalog.showNotification')
        self.parent = parent
        self.baseTitle = title
        wx.Panel.__init__(self, parent = parent, id = id, **kwargs)
        self.SetName("DataCatalog")
        
        Debug.msg(1, "DataCatalog.__init__()")
        
        # tree with layers
        self.tree = DataCatalogTree(self, giface=giface)
        self.thread = gThread()
        self._loaded = False
        self.tree.showNotification.connect(self.showNotification)

        # some layout
        self._layout()

    def _layout(self):
        """Do layout"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(item = self.tree.GetControl(), proportion = 1,
                  flag = wx.EXPAND)          
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        
        self.Layout()

    def LoadItems(self):
        if self._loaded:
            return
        
        self.thread.Run(callable=self.tree.InitTreeItems,
                        ondone=lambda event: self.LoadItemsDone())

    def LoadItemsDone(self):
        self._loaded = True
        self.tree.ExpandCurrentMapset()
