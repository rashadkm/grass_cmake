"""!
@package animation.dialogs

@brief Dialogs for animation management, changing speed of animation

Classes:
 - dialogs::SpeedDialog
 - dialogs::InputDialog
 - dialogs::EditDialog
 - dialogs::AnimationData


(C) 2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Anna Kratochvilova <kratochanna gmail.com>
"""
import os
import sys
import wx
import copy
import datetime
from wx.lib.newevent import NewEvent
import wx.lib.filebrowsebutton as filebrowse

if __name__ == '__main__':
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "gui", "wxpython"))

import grass.temporal as tgis

from core.gcmd import GMessage, GError, GException
from core import globalvar
from gui_core import gselect
from gui_core.dialogs import MapLayersDialog, EVT_APPLY_MAP_LAYERS, GetImageHandlers
from core.settings import UserSettings

from utils import TemporalMode, validateTimeseriesName, validateMapNames
from nviztask import NvizTask

SpeedChangedEvent, EVT_SPEED_CHANGED = NewEvent()

class SpeedDialog(wx.Dialog):
    def __init__(self, parent, title = _("Adjust speed of animation"),
                 temporalMode = None, minimumDuration = 20, timeGranularity = None,
                 initialSpeed = 200):#, framesCount = None
        wx.Dialog.__init__(self, parent = parent, id = wx.ID_ANY, title = title,
                           style = wx.DEFAULT_DIALOG_STYLE)

        self.minimumDuration = minimumDuration
        # self.framesCount = framesCount
        self.defaultSpeed = initialSpeed
        self.lastAppliedValue = self.defaultSpeed
        self.lastAppliedValueTemp = self.defaultSpeed

        self._layout()

        self.temporalMode = temporalMode
        self.timeGranularity = timeGranularity

        self._fillUnitChoice(self.choiceUnits)
        self.InitTimeSpin(self.defaultSpeed)

    def SetTimeGranularity(self, gran):
        self._timeGranularity = gran

    def GetTimeGranularity(self):
        return self._timeGranularity

    timeGranularity = property(fset = SetTimeGranularity, fget = GetTimeGranularity)

    def SetTemporalMode(self, mode):
        self._temporalMode = mode
        self._setTemporalMode()

    def GetTemporalMode(self):
        return self._temporalMode

    temporalMode = property(fset = SetTemporalMode, fget = GetTemporalMode)

    def _layout(self):
        """!Layout window"""
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        #
        # simple mode
        #
        self.nontemporalBox = wx.StaticBox(parent = self, id = wx.ID_ANY,
                                           label = ' %s ' % _("Simple mode"))
        box = wx.StaticBoxSizer(self.nontemporalBox, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(hgap = 5, vgap = 5)

        labelDuration = wx.StaticText(self, id = wx.ID_ANY, label = _("Frame duration:"))
        labelUnits = wx.StaticText(self, id = wx.ID_ANY, label = _("ms"))
        self.spinDuration = wx.SpinCtrl(self, id = wx.ID_ANY, min = self.minimumDuration, 
                                        max = 10000, initial = self.defaultSpeed)
        # TODO total time

        gridSizer.Add(item = labelDuration, pos = (0, 0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridSizer.Add(item = self.spinDuration, pos = (0, 1), flag = wx.ALIGN_CENTER)
        gridSizer.Add(item = labelUnits, pos = (0, 2), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridSizer.AddGrowableCol(0)

        box.Add(item = gridSizer, proportion = 1, border = 5, flag = wx.ALL | wx.EXPAND)
        self.nontemporalSizer = gridSizer
        mainSizer.Add(item = box, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 5)
        #
        # temporal mode
        #
        self.temporalBox = wx.StaticBox(parent = self, id = wx.ID_ANY,
                                        label = ' %s ' % _("Temporal mode"))
        box = wx.StaticBoxSizer(self.temporalBox, wx.VERTICAL)
        gridSizer = wx.GridBagSizer(hgap = 5, vgap = 5)

        labelTimeUnit = wx.StaticText(self, id = wx.ID_ANY, label = _("Time unit:"))
        labelDuration = wx.StaticText(self, id = wx.ID_ANY, label = _("Duration of time unit:"))
        labelUnits = wx.StaticText(self, id = wx.ID_ANY, label = _("ms"))
        self.spinDurationTemp = wx.SpinCtrl(self, id = wx.ID_ANY, min = self.minimumDuration,
                                            max = 10000, initial = self.defaultSpeed)
        self.choiceUnits = wx.Choice(self, id = wx.ID_ANY)

        # TODO total time

        gridSizer.Add(item = labelTimeUnit, pos = (0, 0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridSizer.Add(item = self.choiceUnits, pos = (0, 1), flag = wx.ALIGN_CENTER | wx.EXPAND)
        gridSizer.Add(item = labelDuration, pos = (1, 0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridSizer.Add(item = self.spinDurationTemp, pos = (1, 1), flag = wx.ALIGN_CENTER | wx.EXPAND)
        gridSizer.Add(item = labelUnits, pos = (1, 2), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridSizer.AddGrowableCol(1)

        self.temporalSizer = gridSizer
        box.Add(item = gridSizer, proportion = 1, border = 5, flag = wx.ALL | wx.EXPAND)
        mainSizer.Add(item = box, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 5)
        
        self.btnOk = wx.Button(self, wx.ID_OK)
        self.btnApply = wx.Button(self, wx.ID_APPLY)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)
        self.btnOk.SetDefault()

        self.btnOk.Bind(wx.EVT_BUTTON, self.OnOk)
        self.btnApply.Bind(wx.EVT_BUTTON, self.OnApply)
        self.btnCancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        self.Bind(wx.EVT_CLOSE,  self.OnCancel)
        # button sizer
        btnStdSizer = wx.StdDialogButtonSizer()
        btnStdSizer.AddButton(self.btnOk)
        btnStdSizer.AddButton(self.btnApply)
        btnStdSizer.AddButton(self.btnCancel)
        btnStdSizer.Realize()
        
        mainSizer.Add(item = btnStdSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border = 5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def _setTemporalMode(self):
        self.nontemporalBox.Enable(self.temporalMode == TemporalMode.NONTEMPORAL)
        self.temporalBox.Enable(self.temporalMode == TemporalMode.TEMPORAL)
        for child in self.temporalSizer.GetChildren():
            child.GetWindow().Enable(self.temporalMode == TemporalMode.TEMPORAL)
        for child in self.nontemporalSizer.GetChildren():
            child.GetWindow().Enable(self.temporalMode == TemporalMode.NONTEMPORAL)

        self.Layout()

    def _fillUnitChoice(self, choiceWidget):
        timeUnitsChoice = [_("year"), _("month"), _("day"), _("hour"), _("minute"), _("second")]
        timeUnits = ["years", "months", "days", "hours", "minutes", "seconds"]
        for item, cdata in zip(timeUnitsChoice, timeUnits):
            choiceWidget.Append(item, cdata)

        if self.temporalMode == TemporalMode.TEMPORAL:
            unit = self.timeGranularity.split()[1]
            try:
                index = timeUnits.index(unit)
            except ValueError:
                index = 0
            choiceWidget.SetSelection(index)
        else:
            choiceWidget.SetSelection(0)

    def OnOk(self, event):
        self._apply()
        self.OnCancel(None)

    def OnApply(self, event):
        self._apply()

    def OnCancel(self, event):
        self.spinDuration.SetValue(self.lastAppliedValue)
        self.spinDurationTemp.SetValue(self.lastAppliedValueTemp)
        self.Hide()

    def InitTimeSpin(self, timeTick):
        if self.temporalMode == TemporalMode.TEMPORAL:
            index = self.choiceUnits.GetSelection()
            unit = self.choiceUnits.GetClientData(index)
            delta = self._timedelta(unit = unit, number = 1)
            seconds1 = self._total_seconds(delta)

            number, unit = self.timeGranularity.split()
            number = float(number)
            delta = self._timedelta(unit = unit, number = number)
            seconds2 = self._total_seconds(delta)
            value = timeTick
            ms = value * seconds1 / float(seconds2)
            self.spinDurationTemp.SetValue(ms)
        else:
            self.spinDuration.SetValue(timeTick)

    def _apply(self):
        if self.temporalMode == TemporalMode.NONTEMPORAL:
            ms = self.spinDuration.GetValue()
            self.lastAppliedValue = self.spinDuration.GetValue()
        elif self.temporalMode == TemporalMode.TEMPORAL:
            index = self.choiceUnits.GetSelection()
            unit = self.choiceUnits.GetClientData(index)
            delta = self._timedelta(unit = unit, number = 1)
            seconds1 = self._total_seconds(delta)


            number, unit = self.timeGranularity.split()
            number = float(number)
            delta = self._timedelta(unit = unit, number = number)
            seconds2 = self._total_seconds(delta)

            value = self.spinDurationTemp.GetValue()
            ms = value * seconds2 / float(seconds1)
            if ms < self.minimumDuration:
                GMessage(parent = self, message = _("Animation speed is too high."))
                return
            self.lastAppliedValueTemp = self.spinDurationTemp.GetValue()
        else:
            return

        event = SpeedChangedEvent(ms = ms)
        wx.PostEvent(self, event)

    def _timedelta(self, unit, number):
        if unit == "years":
            delta = datetime.timedelta(days = 365.25 * number)
        elif unit == "months":
            delta = datetime.timedelta(days = 30.4375 * number) # 365.25/12
        elif unit == "days":
            delta = datetime.timedelta(days = 1 * number)
        elif unit == "hours":
            delta = datetime.timedelta(hours = 1 * number)
        elif unit == "minutes":
            delta = datetime.timedelta(minutes = 1 * number)
        elif unit == "seconds":
            delta = datetime.timedelta(seconds = 1 * number)

        return delta

    def _total_seconds(self, delta):
        """!timedelta.total_seconds is new in version 2.7.
        """
        return delta.seconds + delta.days * 24 * 3600


class InputDialog(wx.Dialog):
    def __init__(self, parent, mode, animationData):
        wx.Dialog.__init__(self, parent = parent, id = wx.ID_ANY,
                           style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        if mode == 'add':
            self.SetTitle(_("Add new animation"))
        elif mode == 'edit':
            self.SetTitle(_("Edit animation"))

        self.animationData = animationData

        self._layout()
        self.OnViewMode(event = None)

    def _layout(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.windowChoice = wx.Choice(self, id = wx.ID_ANY,
                                      choices = [_("top left"), _("top right"),
                                                 _("bottom left"), _("bottom right")])
        self.windowChoice.SetSelection(self.animationData.windowIndex)

        self.nameCtrl = wx.TextCtrl(self, id = wx.ID_ANY, value = self.animationData.name)

        self.nDChoice = wx.Choice(self, id = wx.ID_ANY)
        mode = self.animationData.viewMode
        index = 0
        for i, (viewMode, viewModeName) in enumerate(self.animationData.viewModes):
            self.nDChoice.Append(viewModeName, clientData = viewMode)
            if mode == viewMode:
                index = i

        self.nDChoice.SetSelection(index)
        # TODO
        self.nDChoice.SetToolTipString(_(""))
        self.nDChoice.Bind(wx.EVT_CHOICE, self.OnViewMode)

        gridSizer = wx.FlexGridSizer(cols = 2, hgap = 5, vgap = 5)
        gridSizer.Add(item = wx.StaticText(self, id = wx.ID_ANY, label = _("Name:")),
                      flag = wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(item = self.nameCtrl, proportion = 1, flag = wx.EXPAND)
        gridSizer.Add(item = wx.StaticText(self, id = wx.ID_ANY, label = _("Window position:")),
                      flag = wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(item = self.windowChoice, proportion = 1, flag = wx.ALIGN_RIGHT)
        gridSizer.Add(item = wx.StaticText(self, id = wx.ID_ANY, label = _("View mode:")),
                      flag = wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(item = self.nDChoice, proportion = 1, flag = wx.ALIGN_RIGHT)
        gridSizer.AddGrowableCol(0, 1)
        gridSizer.AddGrowableCol(1, 1)
        mainSizer.Add(item = gridSizer, proportion = 1, flag = wx.ALL | wx.EXPAND, border = 5)

        self.dataPanel = self._createDataPanel()
        self.threeDPanel = self._create3DPanel()
        mainSizer.Add(item = self.dataPanel, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 3)
        mainSizer.Add(item = self.threeDPanel, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 3)

        # buttons
        self.btnOk = wx.Button(self, wx.ID_OK)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)
        self.btnOk.SetDefault()
        self.btnOk.Bind(wx.EVT_BUTTON, self.OnOk)
        # button sizer
        btnStdSizer = wx.StdDialogButtonSizer()
        btnStdSizer.AddButton(self.btnOk)
        btnStdSizer.AddButton(self.btnCancel)
        btnStdSizer.Realize()
        
        mainSizer.Add(item = btnStdSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border = 5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def _createDataPanel(self):
        panel = wx.Panel(self, id = wx.ID_ANY)
        dataStBox = wx.StaticBox(parent = panel, id = wx.ID_ANY,
                               label = ' %s ' % _("Data"))
        dataBoxSizer = wx.StaticBoxSizer(dataStBox, wx.VERTICAL)

        self.dataChoice = wx.Choice(panel, id = wx.ID_ANY)
        self._setMapTypes()
        self.dataChoice.Bind(wx.EVT_CHOICE, self.OnDataType)

        self.dataSelect = gselect.Select(parent = panel, id = wx.ID_ANY,
                                           size = globalvar.DIALOG_GSELECT_SIZE)


        iconTheme = UserSettings.Get(group = 'appearance', key = 'iconTheme', subkey = 'type')
        bitmapPath = os.path.join(globalvar.ETCICONDIR, iconTheme, 'layer-open.png')
        if os.path.isfile(bitmapPath) and os.path.getsize(bitmapPath):
            bitmap = wx.Bitmap(name = bitmapPath)
        else:
            bitmap = wx.ArtProvider.GetBitmap(id = wx.ART_MISSING_IMAGE, client = wx.ART_TOOLBAR)
        self.addManyMapsButton = wx.BitmapButton(panel, id = wx.ID_ANY, bitmap = bitmap)
        self.addManyMapsButton.Bind(wx.EVT_BUTTON, self.OnAddMaps)

        self.OnDataType(None)
        if self.animationData.inputData is None:
            self.dataSelect.SetValue('')
        else:
            self.dataSelect.SetValue(self.animationData.inputData)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(item = wx.StaticText(panel, wx.ID_ANY, label = _("Input data type:")),
                proportion = 1, flag = wx.ALIGN_CENTER_VERTICAL)
        hbox.Add(item = self.dataChoice, proportion = 1, flag = wx.EXPAND)
        dataBoxSizer.Add(item = hbox, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 3)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        # hbox.Add(item = wx.StaticText(panel, wx.ID_ANY, label = _("Input data:")),
        #         proportion = 0, flag = wx.ALIGN_CENTER_VERTICAL)
        hbox.Add(item = self.dataSelect, proportion = 1, flag = wx.ALIGN_CENTER)
        hbox.Add(item = self.addManyMapsButton, proportion = 0, flag = wx.LEFT, border = 5)
        dataBoxSizer.Add(item = hbox, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 3)
        
        panel.SetSizerAndFit(dataBoxSizer)
        panel.SetAutoLayout(True)

        return panel

    def _create3DPanel(self):
        panel = wx.Panel(self, id = wx.ID_ANY)
        dataStBox = wx.StaticBox(parent = panel, id = wx.ID_ANY,
                                 label = ' %s ' % _("3D view parameters"))
        dataBoxSizer = wx.StaticBoxSizer(dataStBox, wx.VERTICAL)

        # workspace file
        self.fileSelector = filebrowse.FileBrowseButton(parent = panel, id = wx.ID_ANY, 
                                                    size = globalvar.DIALOG_GSELECT_SIZE,
                                                    labelText = _("Workspace file:"),
                                                    dialogTitle = _("Choose workspace file to import 3D view parameters"),
                                                    buttonText = _('Browse'),
                                                    startDirectory = os.getcwd(), fileMode = 0,
                                                    fileMask = "GRASS Workspace File (*.gxw)|*.gxw")
        if self.animationData.workspaceFile:
            self.fileSelector.SetValue(self.animationData.workspaceFile)
        self.paramLabel = wx.StaticText(panel, wx.ID_ANY, label = _("Parameter for animation:"))
        self.paramChoice = wx.Choice(panel, id = wx.ID_ANY, choices = self.animationData.nvizParameters)
        self.paramChoice.SetStringSelection(self.animationData.nvizParameter)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(item = self.fileSelector, proportion = 1, flag = wx.EXPAND | wx.ALIGN_CENTER)
        dataBoxSizer.Add(item = hbox, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 3)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(item = self.paramLabel, proportion = 1, flag = wx.ALIGN_CENTER_VERTICAL)
        hbox.Add(item = self.paramChoice, proportion = 1, flag = wx.EXPAND)
        dataBoxSizer.Add(item = hbox, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 3)
        
        panel.SetSizerAndFit(dataBoxSizer)
        panel.SetAutoLayout(True)

        return panel

    def _setMapTypes(self, view2d = True):
        index = 0
        if view2d:
            inputTypes = self.animationData.inputMapTypes[::2]
        else:
            inputTypes = self.animationData.inputMapTypes
        self.dataChoice.Clear()
        for i, (itype, itypeName) in enumerate(inputTypes):
            self.dataChoice.Append(itypeName, clientData = itype)
            if itype == self.animationData.inputMapType:
                index = i
        self.dataChoice.SetSelection(index)

    def OnViewMode(self, event):
        mode = self.nDChoice.GetSelection()
        self.Freeze()
        sizer = self.threeDPanel.GetContainingSizer()
        sizer.Show(self.threeDPanel, mode != 0, True)
        sizer.Layout()
        self._setMapTypes(mode == 0)
        self.Layout()
        self.Fit()
        self.Thaw()

    def OnDataType(self, event):
        etype = self.dataChoice.GetClientData(self.dataChoice.GetSelection())
        if etype in ('rast', 'vect'):
            self.dataSelect.SetType(etype = etype, multiple = True)
            self.addManyMapsButton.Enable(True)
        else:
            self.dataSelect.SetType(etype = etype, multiple = False)
            self.addManyMapsButton.Enable(False)

        self.dataSelect.SetValue('')

    def OnAddMaps(self, event):
        # TODO: fix dialog
        etype = self.dataChoice.GetClientData(self.dataChoice.GetSelection())
        index = 0
        if etype == 'vect':
            index = 2
            
        dlg = MapLayersDialog(self, title = _("Select raster maps for animation"))
        dlg.Bind(EVT_APPLY_MAP_LAYERS, self.OnApplyMapLayers)
        dlg.layerType.SetSelection(index)
        dlg.LoadMapLayers(dlg.GetLayerType(cmd = True),
                           dlg.mapset.GetStringSelection())
        if dlg.ShowModal() == wx.ID_OK:
            self.dataSelect.SetValue(','.join(dlg.GetMapLayers()))

        dlg.Destroy()

    def OnApplyMapLayers(self, event):
        self.dataSelect.SetValue(','.join(event.mapLayers))

    def _update(self):
        self.animationData.name = self.nameCtrl.GetValue()
        self.animationData.windowIndex = self.windowChoice.GetSelection()

        sel = self.dataChoice.GetSelection()
        self.animationData.inputMapType = self.dataChoice.GetClientData(sel)
        self.animationData.inputData = self.dataSelect.GetValue()
        sel = self.nDChoice.GetSelection()
        self.animationData.viewMode = self.nDChoice.GetClientData(sel)

        if self.threeDPanel.IsShown():
            self.animationData.workspaceFile = self.fileSelector.GetValue()
        if self.threeDPanel.IsShown():
            self.animationData.nvizParameter = self.paramChoice.GetStringSelection()

    def OnOk(self, event):
        try:
            self._update()
            self.EndModal(wx.ID_OK)
        except (GException, ValueError, IOError) as e:
            GError(message = str(e), showTraceback = False, caption = _("Invalid input"))


class EditDialog(wx.Dialog):
    def __init__(self, parent, evalFunction, animationData, maxAnimations):
        wx.Dialog.__init__(self, parent = parent, id = wx.ID_ANY,
                           style = wx.DEFAULT_DIALOG_STYLE)
        self.animationData = copy.deepcopy(animationData)
        self.eval = evalFunction
        self.SetTitle(_("Add, edit or remove animations"))
        self._layout()
        self.SetSize((300, -1))
        self.maxAnimations = maxAnimations
        self.result = None

    def _layout(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.StaticBox (parent = self, id = wx.ID_ANY, label = " %s " % _("List of animations"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        gridBagSizer = wx.GridBagSizer (hgap = 5, vgap = 5)
        gridBagSizer.AddGrowableCol(0)
        # gridBagSizer.AddGrowableCol(1,1)
        
        self.listbox = wx.ListBox(self, id = wx.ID_ANY, choices = [], style = wx.LB_SINGLE|wx.LB_NEEDED_SB)
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEdit)

        self.addButton = wx.Button(self, id = wx.ID_ANY, label = _("Add"))
        self.addButton.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.editButton = wx.Button(self, id = wx.ID_ANY, label = _("Edit"))
        self.editButton.Bind(wx.EVT_BUTTON, self.OnEdit)
        self.removeButton = wx.Button(self, id = wx.ID_ANY, label = _("Remove"))
        self.removeButton.Bind(wx.EVT_BUTTON, self.OnRemove)
        
        self._updateListBox()
        
        gridBagSizer.Add(self.listbox, pos = (0,0), span = (3, 1), flag = wx.ALIGN_CENTER_VERTICAL| wx.EXPAND, border = 0)
        gridBagSizer.Add(self.addButton, pos = (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border = 0)
        gridBagSizer.Add(self.editButton, pos = (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border = 0)
        gridBagSizer.Add(self.removeButton, pos = (2,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border = 0)
        sizer.Add(gridBagSizer, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 5)
        mainSizer.Add(item = sizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL, border = 5)

        # buttons
        self.btnOk = wx.Button(self, wx.ID_OK)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)
        self.btnOk.SetDefault()
        self.btnOk.Bind(wx.EVT_BUTTON, self.OnOk)
        # button sizer
        btnStdSizer = wx.StdDialogButtonSizer()
        btnStdSizer.AddButton(self.btnOk)
        btnStdSizer.AddButton(self.btnCancel)
        btnStdSizer.Realize()
        
        mainSizer.Add(item = btnStdSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border = 5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def _updateListBox(self):
        self.listbox.Clear()
        for anim in self.animationData:
            self.listbox.Append(anim.name, clientData = anim)
        self.listbox.SetSelection(0)

    def _getNextIndex(self):
        indices = [anim.windowIndex for anim in self.animationData]
        for i in range(self.maxAnimations):
            if i not in indices:
                return i
        return None

    def OnAdd(self, event):
        windowIndex = self._getNextIndex()
        if windowIndex is None:
            GMessage(self, message = _("Maximum number of animations is %d.") % self.maxAnimations)
            return
        animData = AnimationData()
        # number of active animations
        animationIndex = len(self.animationData)
        animData.SetDefaultValues(windowIndex, animationIndex)
        dlg = InputDialog(parent = self, mode = 'add', animationData = animData)
        if dlg.ShowModal() == wx.ID_CANCEL:
            dlg.Destroy()
            return
        dlg.Destroy()
        self.animationData.append(animData)
        
        self._updateListBox()


    def OnEdit(self, event):
        index = self.listbox.GetSelection()
        if index == wx.NOT_FOUND:
            return

        animData = self.listbox.GetClientData(index)
        dlg = InputDialog(parent = self, mode = 'edit', animationData = animData)
        if dlg.ShowModal() == wx.ID_CANCEL:
            dlg.Destroy()
            return
        dlg.Destroy()

        self._updateListBox()

    def OnRemove(self, event):
        index = self.listbox.GetSelection()
        if index == wx.NOT_FOUND:
            return

        animData = self.listbox.GetClientData(index)
        self.animationData.remove(animData)
        
        self._updateListBox()

    def GetResult(self):
        return self.result

    def OnOk(self, event):
        indices = set([anim.windowIndex for anim in self.animationData])
        if len(indices) != len(self.animationData):
            GError(parent = self, message = _("More animations are using one window."
                                                " Please select different window for each animation."))
            return
        try:
            temporalMode, tempManager = self.eval(self.animationData)
        except GException, e:
            GError(parent = self, message = e.value, showTraceback = False)
            return
        self.result = (self.animationData, temporalMode, tempManager)

        self.EndModal(wx.ID_OK)


class AnimationData(object):
    def __init__(self):
        self._inputMapTypes = [('rast', _("Multiple raster maps")),
                               ('vect', _("Multiple vector maps")),
                               ('strds', _("Space time raster dataset")),
                               ('stvds', _("Space time vector dataset"))]
        self._inputMapType = 'rast'
        self.inputData = None
        self.mapData = None
        self._viewModes = [('2d', _("2D view")),
                           ('3d', _("3D view"))]
        self.viewMode = '2d'

        self.nvizTask = NvizTask()
        self._nvizParameters = self.nvizTask.ListMapParameters()
        self.nvizParameter = self._nvizParameters[0]

        self.workspaceFile = None

    def GetName(self):
        return self._name

    def SetName(self, name):
        if name == '':
            raise ValueError(_("No animation name selected."))
        self._name = name

    name = property(fget = GetName, fset = SetName)

    def GetWindowIndex(self):
        return self._windowIndex

    def SetWindowIndex(self, windowIndex):
        self._windowIndex = windowIndex

    windowIndex = property(fget = GetWindowIndex, fset = SetWindowIndex)

    def GetInputMapTypes(self):
        return self._inputMapTypes

    inputMapTypes = property(fget = GetInputMapTypes)

    def GetInputMapType(self):
        return self._inputMapType
        
    def SetInputMapType(self, itype):
        if itype in [each[0] for each in self.inputMapTypes]:
            self._inputMapType = itype
        else:
            raise ValueError("Bad input type.")

    inputMapType = property(fget = GetInputMapType, fset = SetInputMapType)

    def GetInputData(self):
        return self._inputData

    def SetInputData(self, data):
        if data == '':
            raise ValueError(_("No data selected."))
        if data is None:
            self._inputData = data
            return

        if self.inputMapType in ('rast', 'vect'):
            maps = data.split(',')
            newNames = validateMapNames(maps, self.inputMapType)
            self._inputData = ','.join(newNames)
            self.mapData = newNames

        elif self.inputMapType in ('strds', 'stvds'):
            timeseries = validateTimeseriesName(data, etype = self.inputMapType)
            if self.inputMapType == 'strds':
                sp = tgis.SpaceTimeRasterDataset(ident = timeseries)
            elif self.inputMapType == 'stvds':
                sp = tgis.SpaceTimeRasterDataset(ident = timeseries)
            # else ?
            sp.select()
            rows = sp.get_registered_maps(columns = "id", where = None, order = "start_time", dbif = None)
            timeseriesMaps = []
            if rows:
                for row in rows:
                    timeseriesMaps.append(row["id"])
            self._inputData = timeseries
            self.mapData = timeseriesMaps
        else:
            self._inputData = data

    inputData = property(fget = GetInputData, fset = SetInputData)

    def SetMapData(self, data):
        self._mapData = data

    def GetMapData(self):
        return self._mapData

    mapData = property(fget = GetMapData, fset = SetMapData)

    def GetWorkspaceFile(self):
        return self._workspaceFile

    def SetWorkspaceFile(self, fileName):
        if fileName is None:
            self._workspaceFile = None
            return

        if fileName == '':
            raise ValueError(_("No workspace file selected."))

        if not os.path.exists(fileName):
            raise IOError(_("File %s not found") % fileName)
        self._workspaceFile = fileName

        self.nvizTask.Load(self.workspaceFile)

    workspaceFile = property(fget = GetWorkspaceFile, fset = SetWorkspaceFile)

    def SetDefaultValues(self, windowIndex, animationIndex):
        self.windowIndex = windowIndex
        self.name = _("Animation %d") % (animationIndex + 1)

    def GetNvizParameters(self):
        return self._nvizParameters

    nvizParameters = property(fget = GetNvizParameters)

    def GetNvizParameter(self):
        return self._nvizParameter

    def SetNvizParameter(self, param):
        self._nvizParameter = param

    nvizParameter = property(fget = GetNvizParameter, fset = SetNvizParameter)

    def GetViewMode(self):
        return self._viewMode

    def SetViewMode(self, mode):
        self._viewMode = mode

    viewMode = property(fget = GetViewMode, fset = SetViewMode)

    def GetViewModes(self):
        return self._viewModes

    viewModes = property(fget = GetViewModes)

    def GetNvizCommands(self):
        if not self.workspaceFile or not self.mapData:
            return []

        cmds = self.nvizTask.GetCommandSeries(series = self.mapData, paramName = self.nvizParameter)
        region = self.nvizTask.GetRegion()

        return {'commands': cmds, 'region': region}

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)



class ExportDialog(wx.Dialog):
    def __init__(self, parent, temporal):
        wx.Dialog.__init__(self, parent = parent, id = wx.ID_ANY, title = _("Export animation"),
                           style = wx.DEFAULT_DIALOG_STYLE)
        self.decorations = []

        self.temporal = temporal
        self._layout()

        self.OnFormatRadio(event = None)
        wx.CallAfter(self._hideAll)

    def _layout(self):
        notebook = wx.Notebook(self, id = wx.ID_ANY)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        notebook.AddPage(page = self._createExportFormatPanel(notebook), text = _("Format"))
        notebook.AddPage(page = self._createDecorationsPanel(notebook), text = _("Decorations"))
        mainSizer.Add(item = notebook, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border = 5)


        self.btnExport = wx.Button(self, wx.ID_OK)
        self.btnExport.SetLabel(_("Export"))
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)
        self.btnExport.SetDefault()

        self.btnExport.Bind(wx.EVT_BUTTON, self.OnExport)

        # button sizer
        btnStdSizer = wx.StdDialogButtonSizer()
        btnStdSizer.AddButton(self.btnExport)
        btnStdSizer.AddButton(self.btnCancel)
        btnStdSizer.Realize()
        
        mainSizer.Add(item = btnStdSizer, proportion = 0,
                      flag = wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border = 5)
        self.SetSizer(mainSizer)

        # set the longest option to fit
        self.hidevbox.Show(self.fontBox, True)
        self.hidevbox.Show(self.imageBox, False)
        self.hidevbox.Show(self.textBox, True)
        self.hidevbox.Show(self.posBox, True)
        self.hidevbox.Show(self.informBox, False)
        mainSizer.Fit(self)

    def _createDecorationsPanel(self, notebook):
        panel = wx.Panel(notebook, id = wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._createDecorationsList(panel), proportion = 0, flag = wx.ALL | wx.EXPAND, border = 10)
        sizer.Add(self._createDecorationsProperties(panel), proportion = 0, flag = wx.ALL | wx.EXPAND, border = 10)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        return panel

    def _createDecorationsList(self, panel):
        gridBagSizer = wx.GridBagSizer(hgap = 5, vgap = 5)

        gridBagSizer.AddGrowableCol(0)
        
        self.listbox = wx.ListBox(panel, id = wx.ID_ANY, choices = [], style = wx.LB_SINGLE|wx.LB_NEEDED_SB)
        self.listbox.Bind(wx.EVT_LISTBOX, self.OnSelectionChanged)

        gridBagSizer.Add(self.listbox, pos = (0, 0), span = (4, 1),
                         flag = wx.ALIGN_CENTER_VERTICAL| wx.EXPAND, border = 0)

        buttonNames = ['time', 'image', 'text']
        buttonLabels = [_("Add time stamp"), _("Add image"), _("Add text")]
        i = 0
        for buttonName, buttonLabel in zip(buttonNames, buttonLabels):
            if buttonName == 'time' and self.temporal == TemporalMode.NONTEMPORAL:
                continue
            btn = wx.Button(panel, id = wx.ID_ANY, name = buttonName, label = buttonLabel)
            btn.Bind(wx.EVT_BUTTON, lambda evt, temp = buttonName: self.OnAddDecoration(evt, temp))
            gridBagSizer.Add(btn, pos = (i ,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border = 0)
            i += 1
        removeButton = wx.Button(panel, id = wx.ID_ANY, label = _("Remove"))
        removeButton.Bind(wx.EVT_BUTTON, self.OnRemove)
        gridBagSizer.Add(removeButton, pos = (i, 1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border = 0)
        
        return gridBagSizer

    def _createDecorationsProperties(self, panel):
        self.hidevbox = wx.BoxSizer(wx.VERTICAL)
        # inform label
        self.informBox = wx.BoxSizer(wx.HORIZONTAL)
        if self.temporal == TemporalMode.TEMPORAL:
            label = _("Add time stamp, image or text decoration by one of the buttons above.")
        else:
            label = _("Add image or text decoration by one of the buttons above.")

        label = wx.StaticText(panel, id = wx.ID_ANY, label = label)
        label.Wrap(400)
        self.informBox.Add(label, proportion = 1, flag = wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border = 5)
        self.hidevbox.Add(self.informBox, proportion = 0, flag = wx.EXPAND | wx.BOTTOM, border = 5)
        
        # font
        self.fontBox = wx.BoxSizer(wx.HORIZONTAL)
        self.fontBox.Add(wx.StaticText(panel, id = wx.ID_ANY, label = _("Font settings:")),
                         proportion = 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border = 5)
        self.sampleLabel = wx.StaticText(panel, id = wx.ID_ANY, label = _("Sample text"))
        self.fontBox.Add(self.sampleLabel, proportion = 1,
                         flag = wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, border = 5)
        fontButton = wx.Button(panel, id = wx.ID_ANY, label = _("Set font"))
        fontButton.Bind(wx.EVT_BUTTON, self.OnFont)
        self.fontBox.Add(fontButton, proportion = 0, flag = wx.ALIGN_CENTER_VERTICAL)
        self.hidevbox.Add(self.fontBox, proportion = 0, flag = wx.EXPAND | wx.BOTTOM, border = 5)

        # image
        self.imageBox = wx.BoxSizer(wx.HORIZONTAL)
        filetype, ltype = GetImageHandlers(wx.EmptyImage(10, 10))
        self.browse = filebrowse.FileBrowseButton(parent = panel, id = wx.ID_ANY, fileMask = filetype,
                                                  labelText = _("Image file:"),
                                                  dialogTitle = _('Choose image file'),
                                                  buttonText = _('Browse'),
                                                  startDirectory = os.getcwd(), fileMode = wx.OPEN,
                                                  changeCallback = self.OnSetImage)
        self.imageBox.Add(self.browse, proportion = 1, flag = wx.EXPAND)
        self.hidevbox.Add(self.imageBox, proportion = 0, flag = wx.EXPAND | wx.BOTTOM, border = 5)
        # text
        self.textBox = wx.BoxSizer(wx.HORIZONTAL)
        self.textBox.Add(wx.StaticText(panel, id = wx.ID_ANY, label = _("Text:")),
                         proportion = 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border = 5)
        self.textCtrl = wx.TextCtrl(panel, id = wx.ID_ANY)
        self.textCtrl.Bind(wx.EVT_TEXT, self.OnText)
        self.textBox.Add(self.textCtrl, proportion = 1, flag = wx.EXPAND)
        self.hidevbox.Add(self.textBox, proportion = 0, flag = wx.EXPAND)

        self.posBox = self._positionWidget(panel)
        self.hidevbox.Add(self.posBox, proportion = 0, flag = wx.EXPAND | wx.TOP, border = 5)
        return self.hidevbox

    def _positionWidget(self, panel):
        grid = wx.GridBagSizer(vgap = 5, hgap = 5)
        label = wx.StaticText(panel, id = wx.ID_ANY, label = _("Placement as percentage of"
                              " screen coordinates (X: 0, Y: 0 is top left):"))
        label.Wrap(400)
        self.spinX = wx.SpinCtrl(panel, id = wx.ID_ANY, min = 0, max = 100, initial = 10)
        self.spinY = wx.SpinCtrl(panel, id = wx.ID_ANY, min = 0, max = 100, initial = 10)
        self.spinX.Bind(wx.EVT_SPINCTRL,  lambda evt, temp = 'X': self.OnPosition(evt, temp))
        self.spinY.Bind(wx.EVT_SPINCTRL,  lambda evt, temp = 'Y': self.OnPosition(evt, temp))
        
        grid.Add(label, pos = (0, 0), span = (1, 4), flag = wx.EXPAND)
        grid.Add(wx.StaticText(panel, id = wx.ID_ANY, label = _("X:")), pos = (1, 0),
                 flag = wx.ALIGN_CENTER_VERTICAL)
        grid.Add(wx.StaticText(panel, id = wx.ID_ANY, label = _("Y:")), pos = (1, 2),
                 flag = wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.spinX, pos = (1, 1))
        grid.Add(self.spinY, pos = (1, 3))

        return grid

    def _createExportFormatPanel(self, notebook):
        panel = wx.Panel(notebook, id = wx.ID_ANY)
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.gifRadio = wx.RadioButton(panel, id = wx.ID_ANY, 
                                       label = _("Export to animated GIF (not supported yet):"),
                                       style = wx.RB_GROUP)

        self.dirRadio = wx.RadioButton(panel, id = wx.ID_ANY, label = _("Export as image sequence:"))
        self.dirRadio.SetValue(True)
        self.gifRadio.Bind(wx.EVT_RADIOBUTTON, self.OnFormatRadio)
        self.dirRadio.Bind(wx.EVT_RADIOBUTTON, self.OnFormatRadio)

        prefixLabel = wx.StaticText(panel, id = wx.ID_ANY, label = _("File prefix:"))
        self.prefixCtrl = wx.TextCtrl(panel, id = wx.ID_ANY, value = _("animation"))
        
        formatLabel = wx.StaticText(panel, id = wx.ID_ANY, label = _("File format:"))
        self.formatChoice = wx.Choice(panel, id = wx.ID_ANY)
        wildcard, ltype = GetImageHandlers(wx.EmptyImage(10, 10))
        formats = [format for format in wildcard.split('|') if 'file' in format]
        for format, cdata in zip(formats, ltype):
            self.formatChoice.Append(format, cdata)

        self.formatChoice.SetSelection(0)
        
        self.dirBrowse = filebrowse.DirBrowseButton(parent = panel, id = wx.ID_ANY,
                                                    labelText = _("Export directory:"),
                                                     dialogTitle = _("Choose directory for export"),
                                                     buttonText = _("Browse"),
                                                     startDirectory = os.getcwd())
        self.gifBrowse = filebrowse.FileBrowseButton(parent = panel, id = wx.ID_ANY,
                                                     fileMask = "GIF file (*.gif)|*.gif",
                                                     labelText = _("GIF file:"),
                                                     dialogTitle = _("Choose image file"),
                                                     buttonText = _("Browse"),
                                                     startDirectory = os.getcwd(), fileMode = wx.SAVE)

        sizer.Add(self.gifRadio, proportion = 0, flag = wx.EXPAND)
        gifSizer = wx.BoxSizer(wx.HORIZONTAL)
        gifSizer.AddStretchSpacer(prop = 1)
        gifSizer.Add(self.gifBrowse, proportion = 6, flag = wx.EXPAND)
        sizer.Add(gifSizer, proportion = 0, flag = wx.EXPAND)

        sizer.Add(self.dirRadio, proportion = 0, flag = wx.EXPAND)

        dirSizer = wx.BoxSizer(wx.HORIZONTAL)
        dirSizer.AddStretchSpacer(prop = 1)
        self.dirGridSizer = wx.GridBagSizer(hgap = 5, vgap = 5)
        self.dirGridSizer.AddGrowableCol(1)
        self.dirGridSizer.Add(prefixLabel, pos = (0, 0), flag = wx.ALIGN_CENTER_VERTICAL)
        self.dirGridSizer.Add(self.prefixCtrl, pos = (0, 1), flag = wx.EXPAND)
        self.dirGridSizer.Add(formatLabel, pos = (1, 0), flag = wx.ALIGN_CENTER_VERTICAL)
        self.dirGridSizer.Add(self.formatChoice, pos = (1, 1), flag = wx.EXPAND)
        self.dirGridSizer.Add(self.dirBrowse, pos = (2, 0), flag = wx.EXPAND, span = (1, 2))
        dirSizer.Add(self.dirGridSizer, proportion = 6, flag = wx.EXPAND)

        sizer.Add(dirSizer, proportion = 0, flag = wx.EXPAND)
        borderSizer.Add(sizer, proportion = 0, flag = wx.EXPAND | wx.ALL, border = 10)
        panel.SetSizer(borderSizer)
        borderSizer.Fit(panel)

        return panel

    def OnFormatRadio(self, event):
        self.gifBrowse.Enable(self.gifRadio.GetValue())
        for child in self.dirGridSizer.GetChildren():
            child.GetWindow().Enable(self.dirRadio.GetValue())

    def OnFont(self, event):
        index = self.listbox.GetSelection()
        # should not happen
        if index == wx.NOT_FOUND:
            return
        cdata = self.listbox.GetClientData(index)
        font = cdata['font']
        
        fontdata = wx.FontData()
        fontdata.EnableEffects(True)
        fontdata.SetColour('black')
        fontdata.SetInitialFont(font)
        
        dlg = wx.FontDialog(self, fontdata)
        
        if dlg.ShowModal() == wx.ID_OK:
            newfontdata = dlg.GetFontData()
            font = newfontdata.GetChosenFont()
            self.sampleLabel.SetFont(font)
            cdata['font'] = font
            self.Layout()


    def OnPosition(self, event, coord):
        index = self.listbox.GetSelection()
        # should not happen
        if index == wx.NOT_FOUND:
            return
        cdata = self.listbox.GetClientData(index)
        cdata['pos'][coord == 'Y'] = event.GetInt()

    def OnSetImage(self, event):
        index = self.listbox.GetSelection()
        # should not happen
        if index == wx.NOT_FOUND:
            return
        cdata = self.listbox.GetClientData(index)
        cdata['file'] = event.GetString()

    def OnAddDecoration(self, event, name):
        if name == 'time':
            timeInfo = {'name': name, 'font': self.GetFont(), 'pos': [10, 10]}
            self.decorations.append(timeInfo)
        elif name == 'image':
            imageInfo = {'name': name, 'file': '', 'pos': [10, 10]}
            self.decorations.append(imageInfo)
        elif name == 'text':
            textInfo = {'name': name, 'font': self.GetFont(), 'text': '', 'pos': [10, 10]}
            self.decorations.append(textInfo)

        self._updateListBox()
        self.listbox.SetSelection(self.listbox.GetCount() - 1)
        self.OnSelectionChanged(event = None)

    def OnSelectionChanged(self, event):
        index = self.listbox.GetSelection()
        if index == wx.NOT_FOUND:
            self._hideAll()
            return
        cdata = self.listbox.GetClientData(index)
        self.hidevbox.Show(self.fontBox, (cdata['name'] in ('time', 'text')))
        self.hidevbox.Show(self.imageBox, (cdata['name'] == 'image'))
        self.hidevbox.Show(self.textBox, (cdata['name'] == 'text'))
        self.hidevbox.Show(self.posBox, True)
        self.hidevbox.Show(self.informBox, False)

        self.spinX.SetValue(cdata['pos'][0])
        self.spinY.SetValue(cdata['pos'][1])
        if cdata['name'] == 'image':
            self.browse.SetValue(cdata['file'])
        elif cdata['name'] in ('time', 'text'):
            self.sampleLabel.SetFont(cdata['font'])
            if cdata['name'] == 'text':
                self.textCtrl.SetValue(cdata['text'])

        self.hidevbox.Layout()
        # self.Layout()

    def OnText(self, event):
        index = self.listbox.GetSelection()
        # should not happen
        if index == wx.NOT_FOUND:
            return
        cdata = self.listbox.GetClientData(index)
        cdata['text'] = event.GetString()

    def OnRemove(self, event):
        index = self.listbox.GetSelection()
        if index == wx.NOT_FOUND:
            return

        decData = self.listbox.GetClientData(index)
        self.decorations.remove(decData)
        
        self._updateListBox()
        if self.listbox.GetCount():
            self.listbox.SetSelection(0)
            self.OnSelectionChanged(event = None)

    def OnExport(self, event):
        for decor in self.decorations:
            if decor['name'] == 'image':
                if not os.path.exists(decor['file']):
                    if decor['file']:
                        GError(parent = self, message = _("File %s not found.") % decor['file'])
                    else:
                        GError(parent = self, message = _("Decoration image file is missing."))
                    return

        if self.dirRadio.GetValue():
            name = self.dirBrowse.GetValue()
            if not os.path.exists(name):
                if name:
                    GError(parent = self, message = _("Directory %s not found.") % name)
                else:
                    GError(parent = self, message = _("Export directory is missing."))
                return
        elif self.gifRadio.GetValue():
            if not self.gifBrowse.GetValue():
                GError(parent = self, message = _("Export file is missing."))
                return

        self.EndModal(wx.ID_OK)
           
    def GetDecorations(self):
        return self.decorations

    def GetExportInformation(self):
        info = {}
        if self.gifRadio.GetValue():
            info['method'] = 'gif'
            info['file'] = self.gifBrowse.GetValue()
        else:
            info['method'] = 'sequence'
            info['directory'] = self.dirBrowse.GetValue()
            info['prefix'] = self.prefixCtrl.GetValue()
            info['format'] = self.formatChoice.GetClientData(self.formatChoice.GetSelection())
        return info

    def _updateListBox(self):
        self.listbox.Clear()
        names = {'time': _("Time stamp"), 'image': _("Image"), 'text': _("Text")}
        for decor in self.decorations:
            self.listbox.Append(names[decor['name']], clientData = decor)

    def _hideAll(self):
        self.hidevbox.Show(self.fontBox, False)
        self.hidevbox.Show(self.imageBox, False)
        self.hidevbox.Show(self.textBox, False)
        self.hidevbox.Show(self.posBox, False)
        self.hidevbox.Show(self.informBox, True)
        self.hidevbox.Layout()

def test():
    import wx.lib.inspection
    import gettext
    gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode = True)

    import grass.script as grass

    app = wx.PySimpleApp()

    testExport()
    # wx.lib.inspection.InspectionTool().Show()

    

    app.MainLoop()

def testAnimInput():
    anim = AnimationData()
    anim.SetDefaultValues(animationIndex = 0, windowIndex = 0)

    dlg = InputDialog(parent = None, mode = 'add', animationData = anim)
    dlg.Show()

def testAnimEdit():
    anim = AnimationData()
    anim.SetDefaultValues(animationIndex = 0, windowIndex = 0)

    dlg = EditDialog(parent = None, animationData = [anim])
    dlg.Show()

def testExport():
    dlg = ExportDialog(parent = None, temporal = TemporalMode.TEMPORAL)
    if dlg.ShowModal() == wx.ID_OK:
        print dlg.GetDecorations()
        print dlg.GetExportInformation()
        dlg.Destroy()
    else:
        dlg.Destroy()


if __name__ == '__main__':

    test()