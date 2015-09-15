"""
@package datacatalog::tree

@brief Data catalog tree classes

Classes:
 - datacatalog::LocationMapTree
 - datacatalog::DataCatalogTree

@todo:
 - use gui_core/treeview.py

(C) 2014-2015 by Tereza Fiedlerova, and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Tereza Fiedlerova
"""

import wx

from core.gcmd import RunCommand, GError, GMessage
from core.utils import GetListOfLocations, ListOfMapsets
from core.debug import Debug
from gui_core.dialogs import TextEntryDialog
from core.giface import StandaloneGrassInterface

from grass.pydispatch.signal import Signal

import grass.script as grass

class LocationMapTree(wx.TreeCtrl):
    def __init__(self, parent, style=wx.TR_HIDE_ROOT | wx.TR_EDIT_LABELS | wx.TR_LINES_AT_ROOT |
                 wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_SINGLE):
        """Location Map Tree constructor."""
        super(LocationMapTree, self).__init__(parent, id=wx.ID_ANY, style=style)
        self.showNotification = Signal('Tree.showNotification')
        self.parent = parent
        self.root = self.AddRoot('Catalog') # will not be displayed when we use TR_HIDE_ROOT flag
        
        self._initVariables()
        self.MakeBackup()

        wx.EVT_TREE_ITEM_RIGHT_CLICK(self, wx.ID_ANY, self.OnRightClick)
        
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

    def _initTreeItems(self, locations = [], mapsets = []):
        """Add locations, mapsets and layers to the tree."""
        if not locations:
            locations = GetListOfLocations(self.gisdbase)
        if not mapsets:
            mapsets = ['*']
        
        first = True
        for loc in locations:
            location = loc
            if first:
                self.ChangeEnvironment(location, 'PERMANENT')
                first = False
            else:
                self.ChangeEnvironment(location)
            
            varloc = self.AppendItem(self.root, loc)
            # add all mapsets
            mapsets = ListOfMapsets()
            if mapsets:
                for mapset in mapsets:
                    self.AppendItem(varloc, mapset)
            else:
                self.AppendItem(varloc, _("No mapsets readable"))
                continue

            # get list of all maps in location
            maplist = RunCommand('g.list', flags='mt', type='raster,raster_3d,vector', mapset=','.join(mapsets),
                                 quiet=True, read=True)
            maplist = maplist.splitlines()
            for ml in maplist:
                # parse
                parts1 = ml.split('/')
                parts2 = parts1[1].split('@')
                mapset = parts2[1]
                mlayer = parts2[0]
                ltype = parts1[0]

                # add mapset
                if self.itemExists(mapset, varloc) == False:
                    varmapset = self.AppendItem(varloc, mapset)
                else:
                    varmapset = self.getItemByName(mapset, varloc)

                # add type node if not exists
                if self.itemExists(ltype, varmapset) == False:
                    vartype = self.AppendItem(varmapset, ltype)
                
                self.AppendItem(vartype, mlayer)
            
        self.RestoreBackup()          
        Debug.msg(1, "Tree filled")    

    def InitTreeItems(self):
        """Create popup menu for layers"""
        raise NotImplementedError()

    def _popupMenuLayer(self):
        """Create popup menu for layers"""
        raise NotImplementedError()

    def _popupMenuMapset(self):
        """Create popup menu for mapsets"""
        raise NotImplementedError()

    def _initVariables(self):
        """Init variables."""
        self.selected_layer = None
        self.selected_type = None
        self.selected_mapset = None
        self.selected_location = None
        
        self.gisdbase =  grass.gisenv()['GISDBASE']
        self.ctrldown = False

    def GetControl(self):
        """Returns control itself."""
        return self
    
    def DefineItems(self, item0):
        """Set selected items."""
        self.selected_layer = None
        self.selected_type = None
        self.selected_mapset = None
        self.selected_location = None
        items = []
        item = item0
        while (self.GetItemParent(item)):
            items.insert(0,item)
            item = self.GetItemParent(item)
        
        self.selected_location = items[0]
        length = len(items)
        if (length > 1):
            self.selected_mapset = items[1]
            if (length > 2):
                self.selected_type = items[2]
                if (length > 3):
                    self.selected_layer = items[3]
        
    def getItemByName(self, match, root):
        """Return match item from the root."""
        item, cookie = self.GetFirstChild(root)
        while item.IsOk():
            if self.GetItemText(item) == match:
                return item
            item, cookie = self.GetNextChild(root, cookie)
        return None
    
    def itemExists(self, match, root):
        """Return true if match item exists in the root item."""
        item, cookie = self.GetFirstChild(root)
        while item.IsOk():
            if self.GetItemText(item) == match:
                return True
            item, cookie = self.GetNextChild(root, cookie)
        return False       
    
    def UpdateTree(self):
        """Update whole tree."""
        self.DeleteAllItems()
        self.root = self.AddRoot('Tree')
        self.AddTreeItems()
        label = "Tree updated."
        self.showNotification.emit(message=label)
        
    def OnSelChanged(self, event):
        self.selected_layer = None
        
    def OnRightClick(self, event):
        """Display popup menu."""
        self.DefineItems(event.GetItem())
        if(self.selected_layer):
            self._popupMenuLayer()
        elif(self.selected_mapset and self.selected_type==None):
            self._popupMenuMapset() 
    
    def OnDoubleClick(self, event):
        """Double click"""
        Debug.msg(1, "Double CLICK")
            
    def OnKeyDown(self, event):
        """Set key event and check if control key is down"""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self.ctrldown = True
            Debug.msg(1,"CONTROL ON")

    def OnKeyUp(self, event):
        """Check if control key is up"""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self.ctrldown = False
            Debug.msg(1,"CONTROL OFF")

    def MakeBackup(self):
        """Make backup for case of change"""
        gisenv = grass.gisenv()
        self.glocation = gisenv['LOCATION_NAME']
        self.gmapset = gisenv['MAPSET']

    def RestoreBackup(self):
        """Restore backup"""
        stringl = 'LOCATION_NAME='+self.glocation
        RunCommand('g.gisenv', set=stringl)
        stringm = 'MAPSET='+self.gmapset
        RunCommand('g.gisenv', set=stringm)
        
    def ChangeEnvironment(self, location, mapset=None):
        """Change gisenv variables -> location, mapset"""
        stringl = 'LOCATION_NAME='+location
        RunCommand('g.gisenv', set=stringl)
        if mapset:
            stringm = 'MAPSET='+mapset
            RunCommand('g.gisenv', set=stringm)

    def ExpandCurrentLocation(self):
        """Expand current location"""
        location = grass.gisenv()['LOCATION_NAME']
        item = self.getItemByName(location, self.root)
        if item is not None:
            self.SelectItem(item)
            self.ExpandAllChildren(item)
            self.EnsureVisible(item)
        else:
            Debug.msg(1, "Location <%s> not found" % location)

class DataCatalogTree(LocationMapTree):
    def __init__(self, parent, giface=None):
        """Data Catalog Tree constructor."""
        super(DataCatalogTree, self).__init__(parent)
        self._giface = giface
        
        self._initVariablesCatalog()

        wx.EVT_TREE_BEGIN_DRAG(self, wx.ID_ANY, self.OnBeginDrag)
        wx.EVT_TREE_END_DRAG(self, wx.ID_ANY, self.OnEndDrag)
        
        wx.EVT_TREE_END_LABEL_EDIT(self, wx.ID_ANY, self.OnEditLabel)
        wx.EVT_TREE_BEGIN_LABEL_EDIT(self, wx.ID_ANY, self.OnStartEditLabel)
    
    def _initVariablesCatalog(self):
        """Init variables."""
        self.copy_layer = None
        self.copy_type = None
        self.copy_mapset = None
        self.copy_location = None

    def InitTreeItems(self):
        """Add locations, mapsets and layers to the tree."""
        self._initTreeItems()
        
    def OnCopy(self, event): 
        """Copy layer or mapset (just save it temporarily, copying is done by paste)"""
        self.copy_layer = self.selected_layer
        self.copy_type = self.selected_type
        self.copy_mapset = self.selected_mapset
        self.copy_location = self.selected_location 
        label = "Layer "+self.GetItemText(self.copy_layer)+" copied to clipboard. You can paste it to selected mapset."
        self.showNotification.emit(message=label)
        
    def OnRename(self, event): 
        """Rename levent with dialog"""
        if (self.selected_layer):
            self.old_name = self.GetItemText(self.selected_layer)
            self.new_name = self._getUserEntry(_('New name'), _('Rename map'), self.old_name)
            self.rename() 
    
    def OnStartEditLabel(self, event):
        """Start label editing"""
        item = event.GetItem()
        self.DefineItems(item)
        Debug.msg(1, "Start label edit "+self.GetItemText(item))
        label = _("Editing") + " " + self.GetItemText(item)
        self.showNotification.emit(message=label)
        if (self.selected_layer == None):
            event.Veto()
    
    def OnEditLabel(self, event):
        """End label editing"""
        if (self.selected_layer):
            item = event.GetItem()
            self.old_name = self.GetItemText(item)
            Debug.msg(1, "End label edit "+self.old_name)
            wx.CallAfter(self.afterEdit, self, item)
            
    def afterEdit(pro, self, item):
        self.new_name = self.GetItemText(item)
        self.rename()
    
    def rename(self):
        """Rename layer"""
        if self.selected_layer and self.new_name:
            string = self.old_name+','+self.new_name
            self.ChangeEnvironment(self.GetItemText(self.selected_location), self.GetItemText(self.selected_mapset))
            renamed = 0
            label = _("Renaming") + " " + string + " ..."
            self.showNotification.emit(message=label)
            if (self.GetItemText(self.selected_type)=='vector'):
                renamed = RunCommand('g.rename', vector=string)
            elif (self.GetItemText(self.selected_type)=='raster'):
                renamed = RunCommand('g.rename', raster=string)
            else:
                renamed = RunCommand('g.rename', raster3d=string)
            if (renamed==0):
                self.SetItemText(self.selected_layer,self.new_name)
                label = "g.rename "+self.GetItemText(self.selected_type)+"="+string+"   -- completed"
                self.showNotification.emit(message=label)
                Debug.msg(1,"LAYER RENAMED TO: "+self.new_name)
            self.RestoreBackup()    
        
    def OnPaste(self, event):
        """Paste layer or mapset""" 
        # copying between mapsets of one location
        if (self.copy_layer == None):
                return
        if (self.selected_location == self.copy_location and self.selected_mapset):
            if (self.selected_type != None):
                if (self.GetItemText(self.copy_type) != self.GetItemText(self.selected_type)): # copy raster to vector or vice versa
                    GError(_("Failed to copy layer: invalid type."), parent = self)
                    return
            self.new_name = self._getUserEntry(_('New name'), _('Copy map'),
                                               self.GetItemText(self.copy_layer) + '_copy')
            if not self.new_name:
                return
            if (self.GetItemText(self.copy_layer) == self.new_name):
                GMessage(_("Layer was not copied: new layer has the same name"), parent=self) 
                return
            string = self.GetItemText(self.copy_layer)+'@'+self.GetItemText(self.copy_mapset)+','+self.new_name
            self.ChangeEnvironment(self.GetItemText(self.selected_location), self.GetItemText(self.selected_mapset))
            pasted = 0
            type = None
            label = _("Copying") + " " + string + " ..."
            self.showNotification.emit(message=label)
            if (self.GetItemText(self.copy_type)=='vector'):
                pasted = RunCommand('g.copy', vector=string)
                node = 'vector'     
            elif (self.GetItemText(self.copy_type)=='raster'):
                pasted = RunCommand('g.copy', raster=string)
                node = 'raster'
            else:
                pasted = RunCommand('g.copy', raster_3d=string)
                node = 'raster_3d'
            if pasted == 0:
                if self.selected_type == None:
                    self.selected_type = self.getItemByName(node, self.selected_mapset)
                    if self.selected_type == None:
                        # add type node if not exists
                        self.selected_type = self.AppendItem(self.selected_mapset, node)
                self.AppendItem(self.selected_type,self.new_name) 
                self.SortChildren(self.selected_type)
                Debug.msg(1,"COPIED TO: "+self.new_name)
                label = "g.copy "+self.GetItemText(self.copy_type)+"="+string+"    -- completed" # generate this message (command) automatically?
                self.showNotification.emit(message=label)
        else:
            GError(_("Failed to copy layer: action is allowed only within the same location."),
                   parent=self)
        
        # expand selected mapset
        self.ExpandAllChildren(self.selected_mapset)
        self.EnsureVisible(self.selected_mapset)
        
        self.RestoreBackup()
        
        
    def OnDelete(self, event):
        """Delete layer or mapset"""
        if (self.selected_layer):
            string = self.GetItemText(self.selected_layer)
            self.ChangeEnvironment(self.GetItemText(self.selected_location), self.GetItemText(self.selected_mapset))
            removed = 0
            # TODO: rewrite this that it will tell map type in the dialog
            if (self._confirmDialog(question=_('Do you really want to delete map <{m}>?').format(m=string),
                                    title=_('Delete map')) == wx.ID_YES):
                label = _("Deleting") + " " + string + " ..."
                self.showNotification.emit(message=label)
                if (self.GetItemText(self.selected_type)=='vector'):
                    removed = RunCommand('g.remove', flags='f', type='vector',
                                         name=string)
                elif (self.GetItemText(self.selected_type)=='raster'):
                    removed = RunCommand('g.remove', flags='f', type='raster',
                                         name=string)
                else:
                    removed = RunCommand('g.remove', flags='f', type='raster_3d',
                                         name=string)
                if (removed==0):
                    self.Delete(self.selected_layer)
                    Debug.msg(1,"LAYER "+string+" DELETED")
                    label = "g.remove -f type="+self.GetItemText(self.selected_type)+" name="+string+"    -- completed" # generate this message (command) automatically?
                    self.showNotification.emit(message=label)
            self.RestoreBackup()
            
    def OnDisplayLayer(self, event):
        """Display layer in current graphics view"""
        layerName = []
        if (self.GetItemText(self.selected_location) == self.glocation and self.selected_mapset):
            string = self.GetItemText(self.selected_layer)+'@'+self.GetItemText(self.selected_mapset)
            layerName.append(string)
            label = _("Displaying") + " " + string + " ..."
            self.showNotification.emit(message=label)
            label = "d."+self.GetItemText(self.selected_type)+" --q map="+string+"    -- completed. Go to Map layers for further operations."
            if (self.GetItemText(self.selected_type)=='vector'):
                self._giface.lmgr.AddMaps(layerName, 'vector', True)
            elif (self.GetItemText(self.selected_type)=='raster'):
                self._giface.lmgr.AddMaps(layerName, 'raster', True)     
            else:
                self._giface.lmgr.AddMaps(layerName, 'raster_3d', True)
                label = "d.rast --q map="+string+"    -- completed. Go to 'Map layers' for further operations." # generate this message (command) automatically?
            self.showNotification.emit(message=label)
            Debug.msg(1,"LAYER "+self.GetItemText(self.selected_layer)+" DISPLAYED")
        else:
            GError(_("Failed to display layer: not in current mapset or invalid layer"),
                   parent = self)

    def OnBeginDrag(self, event):
        """Just copy necessary data"""
        if (self.ctrldown):
            #cursor = wx.StockCursor(wx.CURSOR_HAND)
            #self.SetCursor(cursor)
            event.Allow()
            self.DefineItems(event.GetItem())
            self.OnCopy(event)
            Debug.msg(1,"DRAG")
        else:
            event.Veto()
            Debug.msg(1,"DRAGGING without ctrl key does nothing") 
        
    def OnEndDrag(self, event):
        """Copy layer into target"""
        #cursor = wx.StockCursor(wx.CURSOR_ARROW)
        #self.SetCursor(cursor)
        if (event.GetItem()): 
            self.DefineItems(event.GetItem())
            if (self.selected_location == self.copy_location and self.selected_mapset):
                event.Allow()
                self.OnPaste(event)
                self.ctrldown = False
                #cursor = wx.StockCursor(wx.CURSOR_DEFAULT)
                #self.SetCursor(cursor) # TODO: change cursor while dragging and then back, this is not working
                Debug.msg(1,"DROP DONE") 
            else:
                event.Veto()

    def _getUserEntry(self, message, title, value):
        """Dialog for simple text entry"""
        dlg = TextEntryDialog(self, message, title)
        dlg.SetValue(value)
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
        else:
            name = None
        dlg.Destroy()

        return name

    def _confirmDialog(self, question, title):
        """Confirm dialog"""
        dlg = wx.MessageDialog(self, question, title, wx.YES_NO)
        res = dlg.ShowModal()
        dlg.Destroy()
        return res

    def _popupMenuLayer(self):
        """Create popup menu for layers"""
        menu = wx.Menu()
        
        item = wx.MenuItem(menu, wx.NewId(), _("&Copy"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCopy, item)

        item = wx.MenuItem(menu, wx.NewId(), _("&Paste"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPaste, item)
 
        item = wx.MenuItem(menu, wx.NewId(), _("&Delete"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnDelete, item)
        
        item = wx.MenuItem(menu, wx.NewId(), _("&Rename"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnRename, item)

        if not isinstance(self._giface, StandaloneGrassInterface):
            item = wx.MenuItem(menu, wx.NewId(), _("&Display layer"))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnDisplayLayer, item)
        
        self.PopupMenu(menu)
        menu.Destroy()
        
    def _popupMenuMapset(self):
        """Create popup menu for mapsets"""
        menu = wx.Menu()

        item = wx.MenuItem(menu, wx.NewId(), _("&Paste"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPaste, item)
        
        self.PopupMenu(menu)
        menu.Destroy()
