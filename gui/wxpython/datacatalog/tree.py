"""
@package datacatalog::tree

@brief Data catalog tree classes

Classes:
 - datacatalog::LocationMapTree
 - datacatalog::DataCatalogTree


(C) 2014-2015 by Tereza Fiedlerova, and the GRASS Development Team


This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Tereza Fiedlerova
@author Anna Petrasova (kratochanna gmail com)
"""
import os
from multiprocessing import Process, Queue, cpu_count

import wx

from core.gcmd import RunCommand, GError, GMessage, GWarning
from core.utils import GetListOfLocations
from core.debug import Debug
from gui_core.dialogs import TextEntryDialog
from core.giface import StandaloneGrassInterface
from core.treemodel import TreeModel, DictNode
from gui_core.treeview import TreeView

from grass.pydispatch.signal import Signal

import grass.script as gscript
from grass.exceptions import CalledModuleError


def getEnvironment(gisdbase, location, mapset):
    """Creates environment to be passed in run_command for example.
    Returns tuple with temporary file path and the environment. The user
    of this function is responsile for deleting the file."""
    tmp_gisrc_file = gscript.tempfile()
    with open(tmp_gisrc_file, 'w') as f:
        f.write('MAPSET: {mapset}\n'.format(mapset=mapset))
        f.write('GISDBASE: {g}\n'.format(g=gisdbase))
        f.write('LOCATION_NAME: {l}\n'.format(l=location))
        f.write('GUI: text\n')
    env = os.environ.copy()
    env['GISRC'] = tmp_gisrc_file
    return tmp_gisrc_file, env


def getLocationTree(gisdbase, location, queue):
    """Creates dictionary with mapsets, elements, layers for given location.
    Returns tuple with the dictionary and error (or None)"""
    tmp_gisrc_file, env = getEnvironment(gisdbase, location, 'PERMANENT')
    env['GRASS_SKIP_MAPSET_OWNER_CHECK'] = '1'

    maps_dict = {}
    elements = ['raster', 'raster_3d', 'vector']
    try:
        mapsets = gscript.read_command('g.mapsets', flags='l', quiet=True, env=env).strip()
    except CalledModuleError:
        queue.put((maps_dict, _("Failed to read mapsets from location {l}.").format(l=location)))
        gscript.try_remove(tmp_gisrc_file)
        return
    else:
        listOfMapsets = mapsets.split()
        for each in listOfMapsets:
            maps_dict[each] = {}
            for elem in elements:
                maps_dict[each][elem] = []
    try:
        maplist = gscript.read_command('g.list', flags='mt', type=elements,
                                       mapset=','.join(listOfMapsets), quiet=True, env=env).strip()
    except CalledModuleError:
        queue.put((maps_dict, _("Failed to read maps from location {l}.").format(l=location)))
        gscript.try_remove(tmp_gisrc_file)
        return
    else:
        # fill dictionary
        for each in maplist.splitlines():
            ltype, wholename = each.split('/')
            name, mapset = wholename.split('@')
            maps_dict[mapset][ltype].append(name)

    queue.put((maps_dict, None))
    gscript.try_remove(tmp_gisrc_file)


class DataCatalogNode(DictNode):
    """Node representing item in datacatalog."""
    def __init__(self, label, data=None):
        super(DataCatalogNode, self).__init__(label=label, data=data)

    def match(self, **kwargs):
        """Method used for searching according to given parameters.

        :param value: dictionary value to be matched
        :param key: data dictionary key
        """
        if not kwargs:
            return False

        for key in kwargs:
            if not (key in self.data and self.data[key] == kwargs[key]):
                return False
        return True


class LocationMapTree(TreeView):
    def __init__(self, parent, model=None, style=wx.TR_HIDE_ROOT | wx.TR_EDIT_LABELS | wx.TR_LINES_AT_ROOT |
                 wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_SINGLE):
        """Location Map Tree constructor."""
        self._model = TreeModel(DataCatalogNode)
        super(LocationMapTree, self).__init__(parent=parent, model=self._model, id=wx.ID_ANY, style=style)
        self.showNotification = Signal('Tree.showNotification')
        self.parent = parent
        self.contextMenu.connect(self.OnRightClick)

        self._initVariables()

    def _initTreeItems(self, locations=None, mapsets=None):
        """Add locations, mapsets and layers to the tree.
        Runs in multiple processes. Saves resulting data and error."""
        # mapsets param currently unused
        if not locations:
            locations = GetListOfLocations(self.gisdbase)

        loc_count = proc_count = 0
        queue_list = []
        proc_list = []
        loc_list = []
        nprocs = 4
        try:
            nprocs = cpu_count()
        except NotImplementedError:
                nprocs = 4
        results = dict()
        errors = []
        location_nodes = []
        for location in locations:
            results[location] = dict()
            varloc = self._model.AppendNode(parent=self._model.root, label=location,
                                            data=dict(type='location', name=location))
            location_nodes.append(varloc)
            loc_count += 1

            q = Queue()
            p = Process(target=getLocationTree,
                        args=(self.gisdbase, location, q))
            p.start()

            queue_list.append(q)
            proc_list.append(p)
            loc_list.append(location)

            proc_count += 1
            # Wait for all running processes
            if proc_count == nprocs or loc_count == len(locations):
                for i in range(len(loc_list)):
                    proc_list[i].join()
                    maps, error = queue_list[i].get()
                    if error:
                        errors.append(error)
                    for key in sorted(maps.keys()):
                        mapset_node = self._model.AppendNode(parent=location_nodes[i], label=key,
                                                             data=dict(type='mapset', name=key))
                        for elem in maps[key]:
                            if maps[key][elem]:
                                element_node = self._model.AppendNode(parent=mapset_node, label=elem,
                                                                      data=dict(type='element', name=elem))
                                for layer in maps[key][elem]:
                                    self._model.AppendNode(parent=element_node, label=layer,
                                                           data=dict(type=elem, name=layer))

                proc_count = 0
                proc_list = []
                queue_list = []
                loc_list = []
                location_nodes = []

        if errors:
            GWarning('\n'.join(errors))
        Debug.msg(1, "Tree filled")
        self.RefreshItems()

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

        gisenv = gscript.gisenv()
        self.gisdbase = gisenv['GISDBASE']
        self.glocation = gisenv['LOCATION_NAME']
        self.gmapset = gisenv['MAPSET']

    def GetControl(self):
        """Returns control itself."""
        return self

    def DefineItems(self, item):
        """Set selected items."""
        self.selected_layer = None
        self.selected_type = None
        self.selected_mapset = None
        self.selected_location = None

        type = item.data['type']
        if type in ('raster', 'raster_3d', 'vector'):
            self.selected_layer = item
            type = 'element'
            item = item.parent
        if type == 'element':
            self.selected_type = item
            type = 'mapset'
            item = item.parent
        if type == 'mapset':
            self.selected_mapset = item
            type = 'location'
            item = item.parent
        if type == 'location':
            self.selected_location = item

    def OnSelChanged(self, event):
        self.selected_layer = None

    def OnRightClick(self, node):
        """Display popup menu."""
        self.DefineItems(node)
        if self.selected_layer:
            self._popupMenuLayer()
        elif self.selected_mapset and not self.selected_type:
            self._popupMenuMapset()

    def ExpandCurrentLocation(self):
        """Expand current location"""
        location = gscript.gisenv()['LOCATION_NAME']
        item = self._model.SearchNodes(name=location, type='location')
        if item:
            self.Select(item[0], select=True)
            self.ExpandNode(item[0], recursive=True)
        else:
            Debug.msg(1, "Location <%s> not found" % location)


class DataCatalogTree(LocationMapTree):
    def __init__(self, parent, giface=None):
        """Data Catalog Tree constructor."""
        super(DataCatalogTree, self).__init__(parent)
        self._giface = giface

        self._initVariablesCatalog()
        self.beginDrag = Signal('DataCatalogTree.beginDrag')
        self.endDrag = Signal('DataCatalogTree.endDrag')
        self.startEdit = Signal('DataCatalogTree.startEdit')
        self.endEdit = Signal('DataCatalogTree.endEdit')

        self.Bind(wx.EVT_TREE_BEGIN_DRAG, lambda evt:
            self._emitSignal(evt.GetItem(), self.beginDrag, event=evt))
        self.Bind(wx.EVT_TREE_END_DRAG, lambda evt:
            self._emitSignal(evt.GetItem(), self.endDrag, event=evt))
        self.beginDrag.connect(self.OnBeginDrag)
        self.endDrag.connect(self.OnEndDrag)

        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, lambda evt:
            self._emitSignal(evt.GetItem(), self.startEdit, event=evt))
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, lambda evt:
            self._emitSignal(evt.GetItem(), self.endEdit, event=evt))
        self.startEdit.connect(self.OnStartEditLabel)
        self.endEdit.connect(self.OnEditLabel)

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
        label = _("Layer {layer} copied to clipboard."
                  "You can paste it to selected mapset.".format(layer=self.copy_layer.label))
        self.showNotification.emit(message=label)

    def OnRename(self, event):
        """Rename levent with dialog"""
        if self.selected_layer:
            self.old_name = self.selected_layer.label
            self.new_name = self._getUserEntry(_('New name'), _('Rename map'), self.old_name)
            self.Rename()

    def OnStartEditLabel(self, node, event):
        """Start label editing"""
        self.DefineItems(node)
        Debug.msg(1, "Start label edit {name}".format(name=node.label))
        label = _("Editing {name}").format(name=node.label)
        self.showNotification.emit(message=label)
        if not self.selected_layer:
            event.Veto()

    def OnEditLabel(self, node, event):
        """End label editing"""
        if self.selected_layer and not event.IsEditCancelled():
            self.old_name = node.label
            Debug.msg(1, "End label edit {name}".format(name=self.old_name))
            self.new_name = event.GetLabel()
            self.Rename()

    def Rename(self):
        """Rename layer"""
        if self.selected_layer and self.new_name:
            string = self.old_name + ',' + self.new_name
            gisrc, env = getEnvironment(self.gisdbase, self.selected_location.label, self.selected_mapset.label)
            renamed = 0
            label = _("Renaming {name}...").format(name=string)
            self.showNotification.emit(message=label)
            if self.selected_type.label == 'vector':
                renamed = RunCommand('g.rename', vector=string, env=env)
            elif self.selected_type.label == 'raster':
                renamed = RunCommand('g.rename', raster=string, env=env)
            else:
                renamed = RunCommand('g.rename', raster3d=string, env=env)
            if renamed == 0:
                self.selected_layer.label = self.new_name
                self.selected_layer.data['name'] = self.new_name
                self.RefreshNode(self.selected_layer)
                label = "g.rename " + self.selected_type.label + "=" + string + "   -- completed"
                self.showNotification.emit(message=label)
                Debug.msg(1, "LAYER RENAMED TO: " + self.new_name)
            gscript.try_remove(gisrc)

    def OnPaste(self, event):
        """Paste layer or mapset"""
        # copying between mapsets of one location
        if not self.copy_layer:
            return
        if self.selected_location == self.copy_location and self.selected_mapset:
            if self.selected_type:
                if self.copy_type.label != self.selected_type.label:  # copy raster to vector or vice versa
                    GError(_("Failed to copy layer: invalid type."), parent=self)
                    return
            self.new_name = self._getUserEntry(_('New name'), _('Copy map'),
                                               self.copy_layer.label + '_copy')
            if not self.new_name:
                return
            if self.copy_layer.label == self.new_name:
                GMessage(_("Layer was not copied: new layer has the same name"), parent=self)
                return
            string = self.copy_layer.label + '@' + self.copy_mapset.label + ',' + self.new_name
            gisrc, env = getEnvironment(self.gisdbase, self.selected_location.label, self.selected_mapset.label)
            pasted = 0
            label = _("Copying {name}...").format(name=string)
            self.showNotification.emit(message=label)
            if self.copy_type.label == 'vector':
                pasted = RunCommand('g.copy', vector=string, env=env)
                node = 'vector'
            elif self.copy_type.label == 'raster':
                pasted = RunCommand('g.copy', raster=string, env=env)
                node = 'raster'
            else:
                pasted = RunCommand('g.copy', raster_3d=string, env=env)
                node = 'raster_3d'
            if pasted == 0:
                if not self.selected_type:
                    found = self._model.SearchNodes(parent=self.selected_mapset, type=node)
                    self.selected_type = found[0] if found else None
                    if not self.selected_type:
                        # add type node if not exists
                        self.selected_type = self._model.AppendNode(parent=self.selected_mapset, label=node,
                                                                    data=dict(type='element', name=node))
                self._model.AppendNode(parent=self.selected_type, label=self.new_name,
                                       data=dict(type=node, name=self.new_name))
                self._model.SortChildren(self.selected_type)
                self.RefreshNode(self.selected_type, recursive=True)
                Debug.msg(1, "COPIED TO: " + self.new_name)
                label = "g.copy " + self.copy_type.label + "=" + string + "    -- completed"  # generate this message (command) automatically?
                self.showNotification.emit(message=label)
            gscript.try_remove(gisrc)
        else:
            GError(_("Failed to copy layer: action is allowed only within the same location."),
                   parent=self)

        # expand selected mapset
        self.ExpandNode(self.selected_mapset, recursive=True)

    def OnDelete(self, event):
        """Delete layer or mapset"""
        if self.selected_layer:
            string = self.selected_layer.label
            gisrc, env = getEnvironment(self.gisdbase, self.selected_location.label, self.selected_mapset.label)
            removed = 0
            # TODO: rewrite this that it will tell map type in the dialog
            if self._confirmDialog(question=_('Do you really want to delete map <{m}>?').format(m=string),
                                   title=_('Delete map')) == wx.ID_YES:
                label = _("Deleting {name}...").format(name=string)
                self.showNotification.emit(message=label)
                if self.selected_type.label == 'vector':
                    removed = RunCommand('g.remove', flags='f', type='vector',
                                         name=string, env=env)
                elif self.selected_type.label == 'raster':
                    removed = RunCommand('g.remove', flags='f', type='raster',
                                         name=string, env=env)
                else:
                    removed = RunCommand('g.remove', flags='f', type='raster_3d',
                                         name=string, env=env)
                if removed == 0:
                    self._model.RemoveNode(self.selected_layer)
                    self.RefreshNode(self.selected_type, recursive=True)
                    Debug.msg(1, "LAYER " + string + " DELETED")
                    label = "g.remove -f type=" + self.selected_type.label + " name=" + string + "    -- completed"  # generate this message (command) automatically?
                    self.showNotification.emit(message=label)
            gscript.try_remove(gisrc)

    def OnDisplayLayer(self, event):
        """Display layer in current graphics view"""
        layerName = []
        if self.selected_location.label == self.glocation and self.selected_mapset:
            string = self.selected_layer.label + '@' + self.selected_mapset.label
            layerName.append(string)
            label = _("Displaying {name}...").format(name=string)
            self.showNotification.emit(message=label)
            label = "d." + self.selected_type.label + " --q map=" + string + \
                    "    -- completed. Go to Map layers for further operations."
            if self.selected_type.label == 'vector':
                self._giface.lmgr.AddMaps(layerName, 'vector', True)
            elif self.selected_type.label == 'raster':
                self._giface.lmgr.AddMaps(layerName, 'raster', True)
            else:
                self._giface.lmgr.AddMaps(layerName, 'raster_3d', True)
                label = "d.rast --q map=" + string + "    -- completed. Go to 'Map layers' for further operations."  # generate this message (command) automatically?
            self.showNotification.emit(message=label)
            Debug.msg(1, "LAYER " + self.selected_layer.label + " DISPLAYED")
        else:
            GError(_("Failed to display layer: not in current mapset or invalid layer"),
                   parent=self)

    def OnBeginDrag(self, node, event):
        """Just copy necessary data"""
        if wx.GetMouseState().ControlDown():
            #cursor = wx.StockCursor(wx.CURSOR_HAND)
            #self.SetCursor(cursor)
            event.Allow()
            self.DefineItems(node)
            self.OnCopy(event)
            Debug.msg(1, "DRAG")
        else:
            event.Veto()
            Debug.msg(1, "DRAGGING without ctrl key does nothing")

    def OnEndDrag(self, node, event):
        """Copy layer into target"""
        #cursor = wx.StockCursor(wx.CURSOR_ARROW)
        #self.SetCursor(cursor)
        if node:
            self.DefineItems(node)
            if self.selected_location == self.copy_location and self.selected_mapset:
                event.Allow()
                self.OnPaste(event)
                #cursor = wx.StockCursor(wx.CURSOR_DEFAULT)
                #self.SetCursor(cursor) # TODO: change cursor while dragging and then back, this is not working
                Debug.msg(1, "DROP DONE")
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
