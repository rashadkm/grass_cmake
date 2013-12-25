"""!
@package gmodeler.dialogs

@brief wxGUI Graphical Modeler - dialogs

Classes:
 - dialogs::ModelDataDialog
 - dialogs::ModelSearchDialog
 - dialogs::ModelRelationDialog
 - dialogs::ModelItemDialog
 - dialogs::ModelLoopDialog
 - dialogs::ModelConditionDialog
 - dialogs::ModelListCtrl
 - dialogs::ValiableListCtrl
 - dialogs::ItemListCtrl
 - dialogs::ItemCheckListCtrl

(C) 2010-2011 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Martin Landa <landa.martin gmail.com>
"""

import os
import sys

import wx
import wx.lib.mixins.listctrl as listmix

from core                 import globalvar
from core                 import utils
from core.utils import _
from gui_core.widgets     import SearchModuleWidget, SimpleValidator
from core.gcmd            import GError, EncodeString
from gui_core.dialogs     import SimpleDialog, MapLayersDialogForModeler
from gui_core.prompt      import GPromptSTC
from gui_core.gselect     import Select, ElementSelect
from gmodeler.model       import *
from lmgr.menudata        import LayerManagerMenuData

from grass.script import task as gtask

class ModelDataDialog(SimpleDialog):
    """!Data item properties dialog"""
    def __init__(self, parent, shape, title = _("Data properties")):
        self.parent = parent
        self.shape = shape
        
        label, etype = self._getLabel()
        self.etype = etype
        SimpleDialog.__init__(self, parent, title)
                
        self.element = Select(parent = self.panel,
                              validator = SimpleValidator(callback = self.ValidatorCallback))
        self.element.SetValue(shape.GetValue())
        
        self.Bind(wx.EVT_BUTTON, self.OnOK,     self.btnOK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.btnCancel)
        if self.etype:
            self.typeSelect = ElementSelect(parent = self.panel,
                                            size = globalvar.DIALOG_GSELECT_SIZE)
            self.typeSelect.Bind(wx.EVT_CHOICE, self.OnType)
        
        if shape.GetValue():
            self.btnOK.Enable()
        
        self._layout()
        self.SetMinSize(self.GetSize())
        
    def _getLabel(self):
        etype = False
        prompt = self.shape.GetPrompt()
        if prompt == 'raster':
            label = _('Name of raster map:')
        elif prompt == 'vector':
            label = _('Name of vector map:')
        else:
            etype = True
            label = _('Name of element:')

        return label, etype
    
    def _layout(self):
        """!Do layout"""
        if self.etype:
            self.dataSizer.Add(item = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                                    label = _("Type of element:")),
                               proportion = 0, flag = wx.ALL, border = 1)
            self.dataSizer.Add(item = self.typeSelect,
                               proportion = 0, flag = wx.ALL, border = 1)
        self.dataSizer.Add(item = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                                label = _("Name of element:")),
                           proportion = 0, flag = wx.ALL, border = 1)
        self.dataSizer.Add(self.element, proportion=0,
                      flag=wx.EXPAND | wx.ALL, border=1)
        
        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def GetType(self):
        """!Get element type"""
        if not self.etype:
            return
        return self.element.tcp.GetType()

    def OnType(self, event):
        """!Select element type"""
        evalue = self.typeSelect.GetValue(event.GetString())
        self.element.SetType(evalue)

    def OnOK(self, event):
        """!Ok pressed"""
        self.shape.SetValue(self.element.GetValue())
        if self.etype:
            elem = self.GetType()
            if elem == 'rast':
                self.shape.SetPrompt('raster')
            elif elem == 'vect':
                self.shape.SetPrompt('raster')
        
        self.parent.canvas.Refresh()
        self.parent.SetStatusText('', 0)
        self.shape.SetPropDialog(None)
        
        if self.IsModal():
            event.Skip() 
        else:
            self.Destroy()
    
    def OnCancel(self, event):
        """!Cancel pressed"""
        self.shape.SetPropDialog(None)
        if self.IsModal():
            event.Skip()
        else:
            self.Destroy()

class ModelSearchDialog(wx.Dialog):
    def __init__(self, parent, title = _("Add new GRASS module to the model"),
                 style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, **kwargs):
        """!Graphical modeler module search window
        
        @param parent parent window
        @param id window id
        @param title window title
        @param kwargs wx.Dialogs' arguments
        """
        self.parent = parent
        
        wx.Dialog.__init__(self, parent = parent, id = wx.ID_ANY, title = title, **kwargs)
        self.SetName("ModelerDialog")
        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass.ico'), wx.BITMAP_TYPE_ICO))
        
        self._command = None
        self.panel = wx.Panel(parent = self, id = wx.ID_ANY)
        
        self.cmdBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                   label=" %s " % _("Command"))
        
        # menu data for search widget and prompt
        menuModel = LayerManagerMenuData()
        
        self.cmd_prompt = GPromptSTC(parent = self, menuModel = menuModel.GetModel(), updateCmdHistory = False)
        self.cmd_prompt.promptRunCmd.connect(self.OnCommand)
        self.search = SearchModuleWidget(parent = self.panel,
                                         model = menuModel.GetModel(),
                                         showTip = True)
        self.search.moduleSelected.connect(lambda name:
                                           self.cmd_prompt.SetTextAndFocus(name + ' '))
        wx.CallAfter(self.cmd_prompt.SetFocus)
        
        self.btnCancel = wx.Button(self.panel, wx.ID_CANCEL)
        self.btnOk     = wx.Button(self.panel, wx.ID_OK)
        self.btnOk.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.OnOk, self.btnOk)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.btnCancel)
        
        self._layout()
        
        self.SetSize((500, 275))

    def _layout(self):
        cmdSizer = wx.StaticBoxSizer(self.cmdBox, wx.VERTICAL)
        cmdSizer.Add(item = self.cmd_prompt, proportion = 1,
                     flag = wx.EXPAND)
        
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.btnCancel)
        btnSizer.AddButton(self.btnOk)
        btnSizer.Realize()
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(item = self.search, proportion = 0,
                      flag = wx.EXPAND | wx.ALL, border = 3)
        mainSizer.Add(item = cmdSizer, proportion = 1,
                      flag = wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border = 3)
        mainSizer.Add(item = btnSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, border = 5)
        
        self.panel.SetSizer(mainSizer)
        mainSizer.Fit(self.panel)
        
        self.Layout()

    def GetPanel(self):
        """!Get dialog panel"""
        return self.panel

    def _getCmd(self):
        line = self.cmd_prompt.GetCurLine()[0].strip()
        if len(line) == 0:
            cmd = list()
        else:
            try:
                cmd = utils.split(str(line))
            except UnicodeError:
                cmd = utils.split(EncodeString((line)))
        return cmd

    def GetCmd(self):
        """!Get command"""
        return self._command

    def ValidateCmd(self, cmd):
        if len(cmd) < 1:
            GError(parent = self,
                   message = _("Command not defined.\n\n"
                               "Unable to add new action to the model."))
            return False
        
        if cmd[0] not in globalvar.grassCmd:
            GError(parent = self,
                   message = _("'%s' is not a GRASS module.\n\n"
                               "Unable to add new action to the model.") % cmd[0])
            return False
        return True

    def OnCommand(self, cmd):
        """!Command in prompt confirmed"""
        if self.ValidateCmd(cmd):
            self._command = cmd
            self.EndModal(wx.ID_OK)

    def OnOk(self, event):
        """!Button 'OK' pressed"""
        cmd = self._getCmd()
        if self.ValidateCmd(cmd):
            self._command = cmd
            self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        """Cancel pressed, close window"""
        self.Hide()
        
    def Reset(self):
        """!Reset dialog"""
        self.search.Reset()
        self.cmd_prompt.OnCmdErase(None)
        self.cmd_prompt.SetFocus()

class ModelRelationDialog(wx.Dialog):
    """!Relation properties dialog"""
    def __init__(self, parent, shape, id = wx.ID_ANY, title = _("Relation properties"),
                 style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, **kwargs):
        self.parent = parent
        self.shape = shape
        
        options = self._getOptions()
        if not options:
            self.valid = False
            return
        
        self.valid = True
        wx.Dialog.__init__(self, parent, id, title, style = style, **kwargs)
        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass.ico'), wx.BITMAP_TYPE_ICO))
        
        self.panel = wx.Panel(parent = self, id = wx.ID_ANY)
        
        self.fromBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                    label = " %s " % _("From"))
        self.toBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                  label = " %s " % _("To"))
        
        self.option = wx.ComboBox(parent = self.panel, id = wx.ID_ANY,
                                  style = wx.CB_READONLY,
                                  choices = options)
        self.option.Bind(wx.EVT_COMBOBOX, self.OnOption)
        
        self.btnCancel = wx.Button(self.panel, wx.ID_CANCEL)
        self.btnOk     = wx.Button(self.panel, wx.ID_OK)
        self.btnOk.Enable(False)
        
        self._layout()

    def _layout(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        fromSizer = wx.StaticBoxSizer(self.fromBox, wx.VERTICAL)
        self._layoutShape(shape = self.shape.GetFrom(), sizer = fromSizer)
        toSizer = wx.StaticBoxSizer(self.toBox, wx.VERTICAL)
        self._layoutShape(shape = self.shape.GetTo(), sizer = toSizer)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.btnCancel)
        btnSizer.AddButton(self.btnOk)
        btnSizer.Realize()
        
        mainSizer.Add(item = fromSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL, border = 5)
        mainSizer.Add(item = toSizer, proportion = 0,
                      flag = wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border = 5)
        mainSizer.Add(item = btnSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, border = 5)
        
        self.panel.SetSizer(mainSizer)
        mainSizer.Fit(self.panel)
        
        self.Layout()
        self.SetSize(self.GetBestSize())
        
    def _layoutShape(self, shape, sizer):
        if isinstance(shape, ModelData):
            sizer.Add(item = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                           label = _("Data: %s") % shape.GetLog()),
                      proportion = 1, flag = wx.EXPAND | wx.ALL,
                      border = 5)
        elif isinstance(shape, ModelAction):
            gridSizer = wx.GridBagSizer (hgap = 5, vgap = 5)
            gridSizer.Add(item = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                               label = _("Command:")),
                          pos = (0, 0))
            gridSizer.Add(item = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                               label = shape.GetLabel()),
                          pos = (0, 1))
            gridSizer.Add(item = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                               label = _("Option:")),
                          flag = wx.ALIGN_CENTER_VERTICAL,
                          pos = (1, 0))
            gridSizer.Add(item = self.option,
                          pos = (1, 1))
            sizer.Add(item = gridSizer,
                      proportion = 1, flag = wx.EXPAND | wx.ALL,
                      border = 5)
            
    def _getOptions(self):
        """!Get relevant options"""
        items = []
        fromShape = self.shape.GetFrom()
        if not isinstance(fromShape, ModelData):
            GError(parent = self.parent,
                   message = _("Relation doesn't start with data item.\n"
                               "Unable to add relation."))
            return items
        
        toShape = self.shape.GetTo()
        if not isinstance(toShape, ModelAction):
            GError(parent = self.parent,
                   message = _("Relation doesn't point to GRASS command.\n"
                               "Unable to add relation."))
            return items
        
        prompt = fromShape.GetPrompt()
        task = toShape.GetTask()
        for p in task.get_options()['params']:
            if p.get('prompt', '') == prompt and \
                    'name' in p:
                items.append(p['name'])
        
        if not items:
            GError(parent = self.parent,
                   message = _("No relevant option found.\n"
                               "Unable to add relation."))
        return items
    
    def GetOption(self):
        """!Get selected option"""
        return self.option.GetStringSelection()
    
    def IsValid(self):
        """!Check if relation is valid"""
        return self.valid
    
    def OnOption(self, event):
        """!Set option"""
        if event.GetString():
            self.btnOk.Enable()
        else:
            self.btnOk.Enable(False)

class ModelItemDialog(wx.Dialog):
    """!Abstract item properties dialog"""
    def __init__(self, parent, shape, title, id = wx.ID_ANY,
                 style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, **kwargs):
        self.parent = parent
        self.shape = shape
        
        wx.Dialog.__init__(self, parent, id, title = title, style = style, **kwargs)
        
        self.panel = wx.Panel(parent = self, id = wx.ID_ANY)
        
        self.condBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                    label=" %s " % _("Condition"))
        self.condText = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY,
                                    value = shape.GetText())
        
        self.itemList = ItemCheckListCtrl(parent = self.panel,
                                          columns = [_("Name"),
                                                     _("Command")],
                                          shape = shape,
                                          frame = parent)
        
        self.itemList.Populate(self.parent.GetModel().GetItems())
        
        self.btnCancel = wx.Button(parent = self.panel, id = wx.ID_CANCEL)
        self.btnOk     = wx.Button(parent = self.panel, id = wx.ID_OK)
        self.btnOk.SetDefault()
        
    def _layout(self):
        """!Do layout (virtual method)"""
        pass
    
    def GetCondition(self):
        """!Get loop condition"""
        return self.condText.GetValue()

class ModelLoopDialog(ModelItemDialog):
    """!Loop properties dialog"""
    def __init__(self, parent, shape, id = wx.ID_ANY, title = _("Loop properties"),
                 style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, **kwargs):
        ModelItemDialog.__init__(self, parent, shape, title,
                                 style = style, **kwargs)
        
        self.listBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                    label=" %s " % _("List of items in loop"))
        
        self.btnSeries = wx.Button(parent = self.panel, id = wx.ID_ANY,
                                   label = _("Series"))
        self.btnSeries.SetToolTipString(_("Define map series as condition for the loop"))
        self.btnSeries.Bind(wx.EVT_BUTTON, self.OnSeries)
        
        self._layout()
        self.SetMinSize(self.GetSize())
        self.SetSize((500, 400))
        
    def _layout(self):
        """!Do layout"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        condSizer = wx.StaticBoxSizer(self.condBox, wx.HORIZONTAL)
        condSizer.Add(item = self.condText, proportion = 1,
                      flag = wx.ALL, border = 3)
        condSizer.Add(item = self.btnSeries, proportion = 0,
                      flag = wx.EXPAND)

        listSizer = wx.StaticBoxSizer(self.listBox, wx.VERTICAL)
        listSizer.Add(item = self.itemList, proportion = 1,
                      flag = wx.EXPAND | wx.ALL, border = 3)
        
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.btnCancel)
        btnSizer.AddButton(self.btnOk)
        btnSizer.Realize()

        sizer.Add(item = condSizer, proportion = 0,
                  flag = wx.EXPAND | wx.ALL, border = 3)
        sizer.Add(item = listSizer, proportion = 1,
                  flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 3)
        sizer.Add(item = btnSizer, proportion=0,
                  flag = wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, border=5)
        
        self.panel.SetSizer(sizer)
        sizer.Fit(self.panel)
        
        self.Layout()
        
    def GetItems(self):
        """!Get list of selected actions"""
        return self.itemList.GetItems()

    def OnSeries(self, event):
        """!Define map series as condition"""
        dialog = MapLayersDialogForModeler(parent = self, title = _("Define series of maps"))
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        
        cond = dialog.GetDSeries()
        if not cond:
            cond = 'map in %s' % map(lambda x: str(x), dialog.GetMapLayers())
        
        self.condText.SetValue(cond)
                               
        dialog.Destroy()

class ModelConditionDialog(ModelItemDialog):
    """!Condition properties dialog"""
    def __init__(self, parent, shape, id = wx.ID_ANY, title = _("If-else properties"),
                 style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, **kwargs):
        ModelItemDialog.__init__(self, parent, shape, title,
                                 style = style, **kwargs)
        
        self.listBoxIf = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                      label=" %s " % _("List of items in 'if' block"))
        self.itemListIf = self.itemList
        self.itemListIf.SetName('IfBlockList')
        
        self.listBoxElse = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                        label=" %s " % _("List of items in 'else' block"))
        self.itemListElse = ItemCheckListCtrl(parent = self.panel,
                                              window = self,
                                              columns = [_("Name"),
                                                         _("Command")],
                                              shape = shape)
        self.itemListElse.SetName('ElseBlockList')
        self.itemListElse.Populate(self.parent.GetModel().GetItems())
        
        self._layout()
        self.SetMinSize(self.GetSize())
        self.SetSize((500, 400))
        
    def _layout(self):
        """!Do layout"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        condSizer = wx.StaticBoxSizer(self.condBox, wx.VERTICAL)
        condSizer.Add(item = self.condText, proportion = 1,
                      flag = wx.EXPAND)
        
        listIfSizer = wx.StaticBoxSizer(self.listBoxIf, wx.VERTICAL)
        listIfSizer.Add(item = self.itemListIf, proportion = 1,
                        flag = wx.EXPAND)
        listElseSizer = wx.StaticBoxSizer(self.listBoxElse, wx.VERTICAL)
        listElseSizer.Add(item = self.itemListElse, proportion = 1,
                          flag = wx.EXPAND)
        
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.btnCancel)
        btnSizer.AddButton(self.btnOk)
        btnSizer.Realize()

        sizer.Add(item = condSizer, proportion = 0,
                  flag = wx.EXPAND | wx.ALL, border = 3)
        sizer.Add(item = listIfSizer, proportion = 1,
                  flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 3)
        sizer.Add(item = listElseSizer, proportion = 1,
                  flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 3)
        sizer.Add(item = btnSizer, proportion=0,
                  flag = wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, border=5)
        
        self.panel.SetSizer(sizer)
        sizer.Fit(self.panel)
        
        self.Layout()

    def OnCheckItemIf(self, index, flag):
        """!Item in if-block checked/unchecked"""
        if flag is False:
            return
        
        aId = int(self.itemListIf.GetItem(index, 0).GetText())
        if aId in self.itemListElse.GetItems()['checked']:
            self.itemListElse.CheckItemById(aId, False)
            
    def OnCheckItemElse(self, index, flag):
        """!Item in else-block checked/unchecked"""
        if flag is False:
            return
        
        aId = int(self.itemListElse.GetItem(index, 0).GetText())
        if aId in self.itemListIf.GetItems()['checked']:
            self.itemListIf.CheckItemById(aId, False)
        
    def GetItems(self):
        """!Get items"""
        return { 'if'   : self.itemListIf.GetItems(),
                 'else' : self.itemListElse.GetItems() }

class ModelListCtrl(wx.ListCtrl,
                    listmix.ListCtrlAutoWidthMixin,
                    listmix.TextEditMixin,
                    listmix.ColumnSorterMixin):
    def __init__(self, parent, columns, frame, id = wx.ID_ANY, columnsNotEditable = [],
                 style = wx.LC_REPORT | wx.BORDER_NONE |
                 wx.LC_SORT_ASCENDING |wx.LC_HRULES |
                 wx.LC_VRULES, **kwargs):
        """!List of model variables"""
        self.parent = parent
        self.columns = columns
        self.shape = None
        self.frame  = frame
        self.columnNotEditable = columnsNotEditable

        wx.ListCtrl.__init__(self, parent, id = id, style = style, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 4)
        
        i = 0
        for col in columns:
            self.InsertColumn(i, col)
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE_USEHEADER)
            i += 1
        
        self.itemDataMap = {} # requested by sorter
        self.itemCount   = 0
        
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndEdit)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightUp) #wxMSW
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)            #wxGTK
                
    def OnBeginEdit(self, event):
        """!Editing of item started"""
        if self.columnNotEditable and event.m_col in self.columnNotEditable:
            event.Veto()
            self.SetItemState(event.m_itemIndex,
                              wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
        else:
            event.Allow()

    def OnEndEdit(self, event):
        """!Finish editing of item"""
        pass
    
    def OnColClick(self, event):
        """!Click on column header (order by)"""
        event.Skip()

class VariableListCtrl(ModelListCtrl):
    def __init__(self, parent, columns, **kwargs):
        """!List of model variables"""
        ModelListCtrl.__init__(self, parent, columns, **kwargs)

        self.SetColumnWidth(2, 200) # default value

    def GetListCtrl(self):
        """!Used by ColumnSorterMixin"""
        return self
    
    def GetData(self):
        """!Get list data"""
        return self.itemDataMap
    
    def Populate(self, data):
        """!Populate the list"""
        self.itemDataMap = dict()
        i = 0
        for name, values in data.iteritems():
            self.itemDataMap[i] = [name, values['type'],
                                   values.get('value', ''),
                                   values.get('description', '')]
            i += 1
        
        self.itemCount = len(self.itemDataMap.keys())
        self.DeleteAllItems()
        i = 0
        for name, vtype, value, desc in self.itemDataMap.itervalues():
            index = self.InsertStringItem(sys.maxint, name)
            self.SetStringItem(index, 0, name)
            self.SetStringItem(index, 1, vtype)
            self.SetStringItem(index, 2, value)
            self.SetStringItem(index, 3, desc)
            self.SetItemData(index, i)
            i += 1
        
    def Append(self, name, vtype, value, desc):
        """!Append new item to the list

        @return None on success
        @return error string
        """
        for iname, ivtype, ivalue, idesc in self.itemDataMap.itervalues():
            if iname == name:
                return _("Variable <%s> already exists in the model. "
                         "Adding variable failed.") % name
        
        index = self.InsertStringItem(sys.maxint, name)
        self.SetStringItem(index, 0, name)
        self.SetStringItem(index, 1, vtype)
        self.SetStringItem(index, 2, value)
        self.SetStringItem(index, 3, desc)
        self.SetItemData(index, self.itemCount)
        
        self.itemDataMap[self.itemCount] = [name, vtype, value, desc]
        self.itemCount += 1
        
        return None

    def OnRemove(self, event):
        """!Remove selected variable(s) from the model"""
        item = self.GetFirstSelected()
        while item != -1:
            self.DeleteItem(item)
            del self.itemDataMap[item]
            item = self.GetFirstSelected()
        self.parent.UpdateModelVariables()
        
        event.Skip()
        
    def OnRemoveAll(self, event):
        """!Remove all variable(s) from the model"""
        dlg = wx.MessageBox(parent=self,
                            message=_("Do you want to delete all variables from "
                                      "the model?"),
                            caption=_("Delete variables"),
                            style=wx.YES_NO | wx.CENTRE)
        if dlg != wx.YES:
            return
        
        self.DeleteAllItems()
        self.itemDataMap = dict()
        
        self.parent.UpdateModelVariables()
        
    def OnEndEdit(self, event):
        """!Finish editing of item"""
        itemIndex = event.GetIndex()
        columnIndex = event.GetColumn()
        nameOld = self.GetItem(itemIndex, 0).GetText()

        if columnIndex == 0: # TODO
            event.Veto()
        
        self.itemDataMap[itemIndex][columnIndex] = event.GetText()
        
        self.parent.UpdateModelVariables()

    def OnReload(self, event):
        """!Reload list of variables"""
        self.Populate(self.parent.parent.GetModel().GetVariables())

    def OnRightUp(self, event):
        """!Mouse right button up"""
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnRemove,    id = self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnRemoveAll, id = self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnReload,    id = self.popupID3)
        
        # generate popup-menu
        menu = wx.Menu()
        menu.Append(self.popupID1, _("Delete selected"))
        menu.Append(self.popupID2, _("Delete all"))
        if self.GetFirstSelected() == -1:
            menu.Enable(self.popupID1, False)
            menu.Enable(self.popupID2, False)
        
        menu.AppendSeparator()
        menu.Append(self.popupID3, _("Reload"))
        
        self.PopupMenu(menu)
        menu.Destroy()

class ItemListCtrl(ModelListCtrl):
    def __init__(self, parent, columns, frame, disablePopup = False, **kwargs):
        """!List of model actions"""
        self.disablePopup = disablePopup

        ModelListCtrl.__init__(self, parent, columns, frame, **kwargs)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 65)
        
    def GetListCtrl(self):
        """!Used by ColumnSorterMixin"""
        return self
    
    def GetData(self):
        """!Get list data"""
        return self.itemDataMap
    
    def Populate(self, data):
        """!Populate the list"""
        self.itemDataMap = dict()
        
        if self.shape:
            if isinstance(self.shape, ModelCondition):
                if self.GetLabel() == 'ElseBlockList':
                    shapeItems = map(lambda x: x.GetId(), self.shape.GetItems()['else'])
                else:
                    shapeItems = map(lambda x: x.GetId(), self.shape.GetItems()['if'])
            else:
                shapeItems = map(lambda x: x.GetId(),
                                 self.shape.GetItems(self.frame.GetModel().GetItems(objType=ModelAction)))
        else:
            shapeItems = list()
        
        i = 0
        if len(self.columns) == 2: # ItemCheckList
            checked = list()
        for action in data:
            if isinstance(action, ModelData) or \
                    action == self.shape:
                continue
            
            if len(self.columns) == 2:
                self.itemDataMap[i] = [action.GetLabel(),
                                       action.GetLog()]
                aId = action.GetBlockId()
                if action.GetId() in shapeItems:
                    checked.append(aId)
                else:
                    checked.append(None)
            else:
                bId = action.GetBlockId()
                if not bId:
                    bId = _('No')
                else:
                    bId = _("Yes")
                self.itemDataMap[i] = [action.GetLabel(),
                                       bId,
                                       action.GetLog()]
            
            i += 1
        
        self.itemCount = len(self.itemDataMap.keys())
        self.DeleteAllItems()
        i = 0
        if len(self.columns) == 2:
            for name, desc in self.itemDataMap.itervalues():
                index = self.InsertStringItem(sys.maxint, str(i))
                self.SetStringItem(index, 0, name)
                self.SetStringItem(index, 1, desc)
                self.SetItemData(index, i)
                if checked[i]:
                    self.CheckItem(index, True)
                i += 1
        else:
            for name, inloop, desc in self.itemDataMap.itervalues():
                index = self.InsertStringItem(sys.maxint, str(i))
                self.SetStringItem(index, 0, name)
                self.SetStringItem(index, 1, inloop)
                self.SetStringItem(index, 2, desc)
                self.SetItemData(index, i)
                i += 1
                
    def OnRemove(self, event):
        """!Remove selected action(s) from the model"""
        model = self.frame.GetModel()
        canvas = self.frame.GetCanvas()
        
        item = self.GetFirstSelected()
        while item != -1:
            self.DeleteItem(item)
            del self.itemDataMap[item]
            
            action = model.GetItem(item+1) # action indeces starts at 1
            if not action:
                item = self.GetFirstSelected()
                continue
            
            canvas.RemoveShapes([action])
            self.frame.ModelChanged()
            
            item = self.GetFirstSelected()
        
        canvas.Refresh()
        
        event.Skip()
    
    def OnEndEdit(self, event):
        """!Finish editing of item"""
        itemIndex = event.GetIndex()
        columnIndex = event.GetColumn()
        self.itemDataMap[itemIndex][columnIndex] = event.GetText()
        action = self.frame.GetModel().GetItem(itemIndex + 1)
        if not action:
            event.Veto()
            return

        action.SetLabel(label = event.GetText())
        self.frame.ModelChanged()

    def OnReload(self, event = None):
        """!Reload list of actions"""
        self.Populate(self.frame.GetModel().GetItems(objType=ModelAction))

    def OnRightUp(self, event):
        """!Mouse right button up"""
        if self.disablePopup:
            return
        
        if not hasattr(self, "popupId"):
            self.popupID = dict()
            self.popupID['remove'] = wx.NewId()
            self.popupID['reload'] = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnRemove,    id = self.popupID['remove'])
            self.Bind(wx.EVT_MENU, self.OnReload,    id = self.popupID['reload'])

        # generate popup-menu
        menu = wx.Menu()
        menu.Append(self.popupID['remove'], _("Delete selected"))
        if self.GetFirstSelected() == -1:
            menu.Enable(self.popupID['remove'], False)
        menu.AppendSeparator()
        menu.Append(self.popupID['reload'], _("Reload"))
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def MoveItems(self, items, up):
        """!Move items in the list

        @param items list of items to move
        @param up True to move up otherwise down
        """
        if len(items) < 1:
            return
        
        if items[0] == 0 and up:
            del items[0]
        if len(items) < 1:
            return
        
        if items[-1] == len(self.itemDataMap.keys())-1 and not up:
            del items[-1]
        if len(items) < 1:
            return

        model = self.frame.GetModel()        
        modelActions = model.GetItems(objType=ModelAction)
        idxList = dict()
        for i in items:
            if up:
                idx = i-1
            else:
                idx = i+1
            idxList[model.GetItemIndex(modelActions[i])] = model.GetItemIndex(modelActions[idx])
        
        # reorganize model items
        model.ReorderItems(idxList)
        model.Normalize()
        self.Populate(model.GetItems(objType=ModelAction))
        
        # re-selected originaly selected item
        for item in idxList.itervalues():
            self.SetItemState(item,  wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)

class ItemCheckListCtrl(ItemListCtrl, listmix.CheckListCtrlMixin):
    def __init__(self, parent, shape, columns, frame, **kwargs):
        self.parent = parent
        self.frame  = frame
        
        ItemListCtrl.__init__(self, parent, columns, frame,
                              disablePopup = True, **kwargs)
        listmix.CheckListCtrlMixin.__init__(self)
        self.SetColumnWidth(0, 100)
        
        self.shape  = shape
        
    def OnBeginEdit(self, event):
        """!Disable editing"""
        event.Veto()
        
    def OnCheckItem(self, index, flag):
        """!Item checked/unchecked"""
        name = self.GetLabel()
        if name == 'IfBlockList' and self.window:
            self.window.OnCheckItemIf(index, flag)
        elif name == 'ElseBlockList' and self.window:
            self.window.OnCheckItemElse(index, flag)
        
    def GetItems(self):
        """!Get list of selected actions"""
        ids = { 'checked'   : list(),
                'unchecked' : list() }
        # action ids start at 1
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                ids['checked'].append(i+1)
            else:
                ids['unchecked'].append(i+1)
            
        return ids

    def CheckItemById(self, aId, flag):
        """!Check/uncheck given item by id"""
        for i in range(self.GetItemCount()):
            iId = int(self.GetItem(i, 0).GetText())
            if iId == aId:
                self.CheckItem(i, flag)
                break
