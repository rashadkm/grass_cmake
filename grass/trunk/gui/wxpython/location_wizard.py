import wx
import wx.wizard as wiz
import wx.lib.rcsizer  as rcs
import wx.lib.mixins.listctrl  as  listmix

try:
    import subprocess
except:
    from compat import subprocess

import os
import sys
import string
import re

import gui_modules
gmpath = gui_modules.__path__[0]
sys.path.append(gmpath)

import gui_modules.cmd as cmd

global coordsys
global north
global south
global east
global west
global resolution
global wizerror
global proj4string

coordsys = ''
north = ''
south = ''
east = ''
west = ''
resolution = ''
proj4string = ''

class TitledPage(wiz.WizardPageSimple):
    def __init__(self, parent, title):
        wiz.WizardPageSimple.__init__(self, parent)

        self.title = wx.StaticText(self,-1,title)
        self.title.SetFont(wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.sizer = rcs.RowColSizer()
        tmpsizer = wx.BoxSizer(wx.VERTICAL)

        tmpsizer.Add(self.title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        tmpsizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 0)
        tmpsizer.Add(self.sizer, wx.EXPAND)

        self.SetSizer(tmpsizer)
        self.SetAutoLayout(True)

    def MakeRLabel(self, text=""):
        try:
            if text[-1] != " ":
                text += " "
        except:
            pass
        return wx.StaticText(self, -1, text, style=wx.ALIGN_RIGHT)

    def MakeLLabel(self, text=""):
        try:
            if text[-1] != " ":
                text += " "
        except:
            pass
        return wx.StaticText(self, -1, text, style=wx.ALIGN_LEFT)

    def MakeTextCtrl(self,text='', size=(100,-1)):
        return wx.TextCtrl(self,-1, text, size=size)

    def MakeButton(self,text, size=(75,25)):
        return wx.Button(self, -1, text,
                style=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
                size=size)


class DatabasePage(TitledPage):
    def __init__(self, wizard, parent, grassdatabase):
        TitledPage.__init__(self, wizard, "Define GRASS database and new Location Name")

        self.grassdatabase = grassdatabase
        self.location = ''

        # buttons
        self.bbrowse = self.MakeButton("Browse...")

        # text controls
        self.tgisdbase = self.MakeTextCtrl(grassdatabase, size=(300, -1))
        self.tlocation = self.MakeTextCtrl("newLocation", size=(300, -1))

        # layout
        self.sizer.Add(self.MakeRLabel("GIS Data Directory:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=1, col=2)
        self.sizer.Add(self.tgisdbase,0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=1, col=3)
        self.sizer.Add(self.bbrowse, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=1, col=4)
        #
        self.sizer.Add(self.MakeRLabel("Project Location"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=2, col=2)
        self.sizer.Add(self.tlocation,0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=2, col=3)
        self.sizer.Add(self.MakeRLabel("(projection/coordinate system)"), 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=2, col=4)

        # bindings
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, self.bbrowse)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.onPageChanging)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)

    def OnBrowse(self, event):
        dlg = wx.DirDialog(self, "Choose GRASS data directory:", os.getcwd(),wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
                    self.grassdatabase = dlg.GetPath()
                    self.tgisdbase.SetValue(self.grassdatabase)
        dlg.Destroy()

    def onPageChanging(self,event=None):
        if os.path.isdir(os.path.join(self.tgisdbase.GetValue(),self.tlocation.GetValue())):
            dlg = wx.MessageDialog(self, "Could not create new location: <%s> directory exists "\
                    % str(self.tlocation.GetValue()),"Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            event.Veto()
            return

        if not self.tlocation.GetValue():
            dlg = wx.MessageDialog(self, "Could not create new location: location not set "\
                    ,"Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            event.Veto()
            return

        self.location = self.tlocation.GetValue()
        self.grassdatabase = self.tgisdbase.GetValue()

    def OnPageChanged(self,event=None):
        self.grassdatabase = self.tgisdbase.GetValue()
        self.location = self.tlocation.GetValue()


class CoordinateSystemPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Choose coordinate system for location")

        self.parent = parent
        global coordsys

        # toggles
        self.radio1 = wx.RadioButton( self, -1, " Select coordinate system " , style = wx.RB_GROUP)
        self.radio2 = wx.RadioButton( self, -1, " Select EPSG code for coordinate system " )
        self.radio3 = wx.RadioButton( self, -1, " Use coordinate system of selected georeferenced file " )
        self.radio4 = wx.RadioButton( self, -1, " Create custom PROJ.4 parameters string for coordinate system " )
        self.radio5 = wx.RadioButton( self, -1, " Create arbitrary non-earth coordinate system (XY)" )

        # layout
        self.sizer.Add(self.radio1, 0, wx.ALIGN_LEFT, row=1, col=2)
        self.sizer.Add(self.radio2, 0, wx.ALIGN_LEFT, row=2, col=2)
        self.sizer.Add(self.radio3, 0, wx.ALIGN_LEFT, row=3, col=2)
        self.sizer.Add(self.radio4, 0, wx.ALIGN_LEFT, row=4, col=2)
        self.sizer.Add(self.radio5, 0, wx.ALIGN_LEFT, row=5, col=2)

        # bindings
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio1.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio2.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio3.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio4.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio5.GetId())
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)

    def OnPageChange(self,event=None):
        global coordsys
        if not coordsys:
            wx.MessageBox('You must select a coordinate system')
            event.Veto()

        if coordsys == "xy":
            self.parent.bboxpage.cstate.Enable(False)
        else:
            self.parent.bboxpage.cstate.Enable(True)

    def SetVal(self,event):
        global coordsys
        if event.GetId() == self.radio1.GetId():
            coordsys = "proj"
            self.SetNext(self.parent.projpage)
            self.parent.datumpage.SetPrev(self.parent.projpage)
            self.parent.bboxpage.SetPrev(self.parent.datumpage)
        elif event.GetId() == self.radio2.GetId():
            coordsys = "epsg"
            self.SetNext(self.parent.epsgpage)
            self.parent.sumpage.SetPrev(self.parent.epsgpage)
        elif event.GetId() == self.radio3.GetId():
            coordsys = "file"
            self.SetNext(self.parent.filepage)
            self.parent.sumpage.SetPrev(self.parent.filepage)
        elif event.GetId() == self.radio4.GetId():
            coordsys = "custom"
            self.SetNext(self.parent.custompage)
            self.parent.sumpage.SetPrev(self.parent.custompage)
        elif event.GetId() == self.radio5.GetId():
            coordsys = "xy"
            self.SetNext(self.parent.bboxpage)
            self.parent.bboxpage.cstate.Enable(False)


class ProjectionsPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Choose projection")

        self.parent = parent
        self.proj = ''
        self.projdesc = ''

        # text input
        self.tproj = self.MakeTextCtrl("", size=(200,-1))

        # search box
        self.searchb = wx.SearchCtrl(self, size=(200,-1),
                                     style=wx.TE_PROCESS_ENTER)

        self.projlist = wx.ListCtrl(self, id=wx.ID_ANY,
                                     size=(650,275),
                                     style=wx.LC_REPORT |
                                     wx.LC_HRULES |
                                     wx.EXPAND)
        self.projlist.InsertColumn(0, 'Code')
        self.projlist.InsertColumn(1, 'Description')
        self.projlist.SetColumnWidth(0, 100)
        self.projlist.SetColumnWidth(1, 500)

        # layout
        self.sizer.Add(self.MakeRLabel("Projection code:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=2)
        self.sizer.Add(self.tproj, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=3)

        self.sizer.Add(self.MakeRLabel("Search in projection description"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2, col=2)
        self.sizer.Add(self.searchb, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2, col=3)

        self.sizer.Add(self.projlist,
                       wx.EXPAND |
                       wx.ALIGN_LEFT |
                       wx.ALL, 5, row=3, col=1, colspan=4)

        # events
        self.Bind(wx.EVT_TEXT, self.OnText, self.tproj)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.projlist)
        self.searchb.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.searchb)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)

        self._onBrowseProj(None, None)

    def OnPageChange(self,event):
        if not self.proj:
            wx.MessageBox('You must select a projection')
            event.Veto()
        if self.proj == 'utm':
            self.parent.projtypepage.text_utm.SetEditable(True)
            self.parent.projtypepage.hemischoices = ['north','south']
        else:
            self.parent.projtypepage.text_utm.SetValue('')
            self.parent.projtypepage.text_utm.SetEditable(False)
            self.parent.projtypepage.hemischoices = []

    def OnText(self, event):
        self.proj = event.GetString()
        if self.proj in self.parent.projections:
            self.projdesc = self.parent.projections[self.proj]

    def OnDoSearch(self,event):
        str =  self.searchb.GetValue()
        listItem  = self.projlist.GetColumn(1)

        for i in range(self.projlist.GetItemCount()):
            listItem = self.projlist.GetItem(i,1)
            if listItem.GetText().find(str) > -1:
                self.proj = self.projlist.GetItem(i, 0).GetText()
                self.tproj.SetValue(self.proj)
                break

        self._onBrowseProj(None,str)

    def OnItemSelected(self,event):
        index = event.m_itemIndex
        item = event.GetItem()

        self.proj = item.GetText()
        self.projdesc = self.projlist.GetItem(index, 1).GetText()
        self.tproj.SetValue(self.proj)

    def _onBrowseProj(self,event,search=None):
        try:
            projlist = self.parent.projections.items()
            projlist.sort()
            self.projlist.DeleteAllItems()
            for proj,desc in projlist:
                entry = self.projlist.GetItemCount()
                if search and (proj.lower().find(search.lower()) > -1 or \
                               desc.lower().find(search.lower()) > -1) or \
                               not search:
                    index = self.projlist.InsertStringItem(entry,proj)
                    self.projlist.SetStringItem(index,1,desc)

            self.projlist.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.projlist.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.projlist.SendSizeEvent()

        except StandardError, e:
            dlg = wx.MessageDialog(self, "Could not read projections list: %s " % e,
                                   "Could not read projections",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

class ProjTypePage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Choose method of specifying georeferencing parameters")
        global coordsys

        self.utmzone = ''
        self.utmhemisphere = ''
        self.hemischoices = ["north","south"]
        self.parent = parent

        self.radio1 = wx.RadioButton( self, -1, " Select datum with associated ellipsoid", style = wx.RB_GROUP )
        self.radio2 = wx.RadioButton( self, -1, " Select ellipsoid" )

        # layout
        self.sizer.Add(self.radio1, 0, wx.ALIGN_LEFT, row=1, col=2)
        self.sizer.Add(self.radio2, 0, wx.ALIGN_LEFT, row=2, col=2)

        self.title_utm = self.MakeLLabel("Set zone for UTM projection")
        self.text_utm = self.MakeTextCtrl(size=(100,-1))
        self.label_utm = self.MakeRLabel("Zone: ")
        self.hemisphere = wx.Choice(self, -1, (100, 50), choices = self.hemischoices)
        self.label_hemisphere = self.MakeRLabel("Hemisphere for zone: ")

        self.sizer.Add(self.title_utm, 0, wx.ALIGN_LEFT|wx.ALL, 5, row=4,col=2)
        self.sizer.Add(self.label_utm, 0, wx.ALIGN_RIGHT|wx.ALL, 5, row=5,col=1)
        self.sizer.Add(self.text_utm, 0, wx.ALIGN_LEFT|wx.ALL, 5, row=5,col=2)
        self.sizer.Add(self.label_hemisphere, 0, wx.ALIGN_RIGHT|wx.ALL, 5, row=6,col=1)
        self.sizer.Add(self.hemisphere, 0, wx.ALIGN_LEFT|wx.ALL, 5, row=6,col=2)

        # bindings
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio1.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=self.radio2.GetId())
        self.Bind(wx.EVT_CHOICE, self.OnHemisphere, self.hemisphere)
        self.Bind(wx.EVT_TEXT, self.GetUTM, self.text_utm)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)

    def OnPageChange(self,event=None):
        if self.parent.projpage.proj == 'utm' and self.utmzone == '':
            wx.MessageBox('You must set a zone for a UTM projection')
            event.Veto()

    def SetVal(self, event):
        global coordsys
        if event.GetId() == self.radio1.GetId():
            self.SetNext(self.parent.datumpage)
        elif event.GetId() == self.radio2.GetId():
            self.SetNext(self.parent.ellipsepage)

    def GetUTM(self, event):
        self.utmzone = event.GetString()

    def OnHemisphere(self, event):
        self.utmhemisphere = event.GetString()


class DatumPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Specify geodetic datum")

        self.parent = parent
        self.datum = ''
        self.datumdesc = ''
        self.ellipsoid = ''
        self.datumparams = ''
        self.transform = ''
        self.transregion = ''
        self.transparams = ''
        self.hastransform = False
        self.proj4params = ''

        # text input
        self.tdatum = self.MakeTextCtrl("", size=(200,-1))
        self.ttrans = self.MakeTextCtrl("", size=(200,-1))

        # search box
        self.searchb = wx.SearchCtrl(self, size=(200,-1),
                                     style=wx.TE_PROCESS_ENTER)

        # button
#        self.bupdate = self.MakeButton("Update trans. parms.",
#                                       size=(-1,-1))

        # create list control for datum/elipsoid list
        self.datumlist = wx.ListCtrl(self, id=wx.ID_ANY,
                                     size=(650,150),
                                     style=wx.LC_REPORT|
                                     wx.LC_HRULES|
                                     wx.EXPAND)
        self.datumlist.InsertColumn(0, 'Code')
        self.datumlist.InsertColumn(1, 'Description')
        self.datumlist.InsertColumn(2, 'Ellipsoid')
        self.datumlist.SetColumnWidth(0, 100)
        self.datumlist.SetColumnWidth(1, 250)
        self.datumlist.SetColumnWidth(2, 100)

        # create list control for datum transformation parameters list
        self.transformlist = wx.ListCtrl(self, id=wx.ID_ANY,
                                     size=(650,125),
                                     style=wx.LC_REPORT |
                                     wx.LC_HRULES |
                                     wx.EXPAND)
        self.transformlist.InsertColumn(0, 'Code')
        self.transformlist.InsertColumn(1, 'Datum')
        self.transformlist.InsertColumn(2, 'Description')
        self.transformlist.SetColumnWidth(0, 50)
        self.transformlist.SetColumnWidth(1, 125)
        self.transformlist.SetColumnWidth(2, 250)

        # layout
        self.sizer.Add(self.MakeRLabel("Datum code:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, col=1, row=1)
        self.sizer.Add(self.tdatum, 0 ,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=2)
#        self.sizer.Add(self.bupdate, 0 ,
#                       wx.ALIGN_LEFT |
#                       wx.ALIGN_CENTER_VERTICAL |
#                       wx.ALL, 5, row=1, col=3)
        self.sizer.Add(self.MakeRLabel("Search in description:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, col=1, row=2)
        self.sizer.Add(self.searchb, 0 ,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2, col=2)

        self.sizer.Add(self.datumlist,
                       wx.EXPAND |
                       wx.ALIGN_LEFT |
                       wx.ALL, 5, row=3, col=1, colspan=4)

        self.sizer.Add(self.MakeRLabel("Transformation parameters:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, col=1, row=5)
        self.sizer.Add(self.ttrans, 0 ,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=5, col=2)

        self.sizer.Add(self.transformlist,
                       wx.EXPAND |
                       wx.ALIGN_LEFT |
                       wx.ALL, 5, row=6, col=1, colspan=4)

        # events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnDatumSelected, self.datumlist)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTransformSelected, self.transformlist)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)
#        self.bupdate.Bind(wx.EVT_BUTTON, self._onBrowseParams)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.searchb)
        self.Bind(wx.EVT_TEXT, self.OnDText, self.tdatum)

        self._onBrowseDatums(None,None)

    def OnPageChange(self,event):
        self.proj4params = ''
        if not self.datum:
            wx.MessageBox('You must select a datum')
            event.Veto()
#        if self.hastransform == True and self.transform == '':
#            wx.MessageBox('You must select a datum transform')
#            event.Veto()
        self.GetNext().SetPrev(self)
        self.parent.ellipsepage.ellipseparams = self.parent.ellipsoids[self.ellipsoid][1]

        global proj4string

    def OnDText(self, event):
        self.datum = event.GetString()
        self.datumdesc = self.parent.datums[self.datum][0]
        self.ellipsoid = self.parent.datums[self.datum][1]
        self.datumparams = self.parent.datums[self.datum][2]

        self._onBrowseParams(None,self.datum)

    def OnTText(self, event):
        self.transform = event.GetString()
        self.transdatum = self.parent.transforms[self.transform][0]
        self.transregion = self.parent.transforms[self.transform][1]
        self.transparams = self.parent.transforms[self.transform][2]

    def OnDoSearch(self,event):
        str =  self.searchb.GetValue()
        listItem  = self.datumlist.GetColumn(1)

        for i in range(self.datumlist.GetItemCount()):
            listItem = self.datumlist.GetItem(i,1)
            if listItem.GetText().find(str) > -1:
                datum = self.datumlist.GetItem(i, 0)
                self.tdatum.SetValue(datum.GetText())
                break

        self._onBrowseDatums(None,str)

    def OnTransformSelected(self,event):
        index = event.m_itemIndex
        item = event.GetItem()

        self.transform = item.GetText()
        self.transdatum = self.parent.transforms[self.transform][0]
        self.transregion = self.parent.transforms[self.transform][1]
        self.transparams = self.parent.transforms[self.transform][2]

        self.ttrans.SetValue(str(self.transform))

    def OnDatumSelected(self,event):
        index = event.m_itemIndex
        item = event.GetItem()

        self.datum = item.GetText()
        self.datumdesc = self.parent.datums[self.datum][0]
        self.ellipsoid = self.parent.datums[self.datum][1]
        self.datumparams = self.parent.datums[self.datum][2]

        self.tdatum.SetValue(self.datum)
        self._onBrowseParams(None, self.datum)
        event.Skip()

    def _onBrowseParams(self, event=None, search=None):
        search = self.datum.strip()
        try:
            self.transform = ''
            self.transformlist.DeleteAllItems()
            for item in self.parent.transforms:
                transdatum = self.parent.transforms[item][0]
                transregion = self.parent.transforms[item][1]
                entry = self.transformlist.GetItemCount()
                if (transdatum.lower() == search.lower()):
                    index = self.transformlist.InsertStringItem(entry,item)
                    self.transformlist.SetStringItem(index,1,transdatum)
                    self.transformlist.SetStringItem(index,2,transregion)
                    self.hastransform = True

            self.transformlist.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.transformlist.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.transformlist.SetColumnWidth(2, wx.LIST_AUTOSIZE)
            self.transformlist.SendSizeEvent()

        except IOError, e:
            self.transformlist.DeleteAllItems()
            dlg = wx.MessageDialog(self, "Could not read datum params: %s " % e,
                                   "Could not read file",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def _onBrowseDatums(self,event,search=None):
        try:
            self.datum = ''
            self.datumlist.DeleteAllItems()

            datumlist = self.parent.datums.items()
            datumlist.sort()
            for datum,info in datumlist:
                datumdesc = info[0]
                ellipse = info[1]
                entry = self.datumlist.GetItemCount()
                if search and (datum.lower().find(search.lower()) > -1 or\
                              datumdesc.lower().find(search.lower()) > -1 or\
                              ellipse.lower().find(search.lower()) > -1) or\
                        not search:
                    index = self.datumlist.InsertStringItem(entry,datum)
                    self.datumlist.SetStringItem(index,1,datumdesc)
                    self.datumlist.SetStringItem(index,2,ellipse)

            self.datumlist.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.datumlist.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.datumlist.SetColumnWidth(2, wx.LIST_AUTOSIZE)
            self.datumlist.SendSizeEvent()

        except IOError, e:
            dlg = wx.MessageDialog(self, "Could not read datums: %s " % e,
                                   "Could not read datums list",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()


class EllipsePage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Specify ellipsoid")

        self.parent = parent
        self.ellipse = ''
        self.ellipsedesc = ''
        self.ellipseparams = ''
        self.proj4params = ''

        # text input
        self.tellipse = self.MakeTextCtrl("", size=(200,-1))

        # search box
        self.searchb = wx.SearchCtrl(self, size=(200,-1),
                                     style=wx.TE_PROCESS_ENTER)

        # create list control for ellipse list
        self.ellipselist = wx.ListCtrl(self, id=wx.ID_ANY,
                                     size=(650,250),
                                     style=wx.LC_REPORT|
                                     wx.LC_HRULES|
                                     wx.EXPAND)
        self.ellipselist.InsertColumn(0, 'Code')
        self.ellipselist.InsertColumn(1, 'Description')
        self.ellipselist.SetColumnWidth(0, 100)
        self.ellipselist.SetColumnWidth(1, 250)

        # layout
        self.sizer.Add(self.MakeRLabel("Ellipse code:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=1)
        self.sizer.Add(self.tellipse, 0 ,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=2)
        self.sizer.Add(self.MakeRLabel("Search in description:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2, col=1)
        self.sizer.Add(self.searchb, 0 ,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2, col=2)

        self.sizer.Add(self.ellipselist, 0 ,
                       wx.EXPAND |
                       wx.ALIGN_LEFT |
                       wx.ALL, 5, row=3, col=1, colspan=3)

        # events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnEllipseSelected, self.ellipselist)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)
        self.searchb.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.searchb)
        self.Bind(wx.EVT_TEXT, self.OnText, self.tellipse)

        self._onBrowseEllipse(None,None)

    def OnPageChange(self,event):
        self.proj4params = ''
        if not self.ellipse:
            wx.MessageBox('You must select an ellipse')
            event.Veto()
        self.GetNext().SetPrev(self)
        self.parent.datumpage.datumparams = ''
        self.parent.datumpage.transparams = ''

    def OnText(self, event):
        self.ellipse = event.GetString()
        if self.ellipse in self.parent.ellipseoids:
            self.ellipsedesc = self.parent.ellipsoids[self.ellipse][0]
            self.ellipseparams = self.parent.ellipsoids[self.ellipse][1]

    def OnDoSearch(self,event):
        str =  self.searchb.GetValue()
        listItem  = self.ellipselist.GetColumn(1)

        for i in range(self.ellipselist.GetItemCount()):
            item = self.ellipselist.GetItem(i,0)
            itemdesc = self.ellipselist.GetItem(i,1)
            if itemdesc.GetText().find(str) > -1:
                self.ellipse = item.GetText()
                self.tellipse.SetValue(self.ellipse)
                self.ellipselist.EnsureVisible(long(self.ellipselist.GetItem(i)))
                break

        self._onBrowseEllipse(None,str)

    def OnEllipseSelected(self,event):
        index = event.m_itemIndex
        item = event.GetItem()

        self.ellipse = item.GetText()
        self.ellipsedesc = self.parent.ellipsoids[self.ellipse][0]
        self.ellipseparams = self.parent.ellipsoids[self.ellipse][1]

        self.tellipse.SetValue(self.ellipse)
        self._onBrowseEllipse(None)

    def _onBrowseEllipse(self,event,search=None):
        try:
            ellipselist = self.parent.ellipsoids.items()
            ellipselist.sort()
            self.ellipselist.DeleteAllItems()
            for ellipsoid,info in ellipselist:
                desc = info[0]
                entry = self.ellipselist.GetItemCount()
                if search and (ellipsoid.lower().find(search.lower()) > -1 or \
                               desc.lower().find(search.lower()) > -1) or \
                               not search:
                    index = self.ellipselist.InsertStringItem(entry,ellipsoid)
                    self.ellipselist.SetStringItem(index,1,desc)

            self.ellipselist.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.ellipselist.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.ellipselist.SendSizeEvent()
        except IOError, e:
            dlg = wx.MessageDialog(self, "Could not read ellipse information: %s " % e,
                                   "Problem parsing ellipse list",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()


class GeoreferencedFilePage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Select georeferenced file")

        self.georeffile = ''

        # create controls
        self.lfile= wx.StaticText(self, -1, "Georeferenced file: ",
                style=wx.ALIGN_RIGHT)
        self.tfile = wx.TextCtrl(self,-1, "", size=(300,-1))
        self.bbrowse = wx.Button(self, -1, "Browse...")

        # do layout
        self.sizer.Add(self.lfile, 0, wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTRE_VERTICAL |
                       wx.ALL, 5, row=1, col=2)
        self.sizer.Add(self.tfile, 0, wx.ALIGN_LEFT |
                       wx.ALIGN_CENTRE_VERTICAL |
                       wx.ALL, 5, row=1, col=3)
        self.sizer.Add(self.bbrowse, 0, wx.ALIGN_LEFT |
                       wx.ALL, 5, row=1, col=4)

        self.bbrowse.Bind(wx.EVT_BUTTON, self.OnBrowse)
        self.Bind(wx.EVT_TEXT, self.OnText, self.tfile)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)

    def OnPageChange(self, event):
        if self.georeffile == '':
            wx.MessageBox('You must select a file')
            event.Veto()
        self.GetNext().SetPrev(self)

    def OnText(self, event):
        self.georeffile = event.GetString()

    def OnBrowse(self, event):

        dlg = wx.FileDialog(self, "Choose a georeferenced file:", os.getcwd(), "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    self.tfile.SetValue(path)
        dlg.Destroy()

    def OnCreate(self, event):
        pass


class EPSGPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Choose EPSG Code")
        self.parent = parent
        self.epsgcode = ''
        self.epsgdesc = ''


        # labels
        self.lfile= wx.StaticText(self, -1, "Path to the EPSG-codes file: ",
                style=wx.ALIGN_RIGHT)
        self.lcode= wx.StaticText(self, -1, "EPSG code: ",
                style=wx.ALIGN_RIGHT)
        self.lsearch= wx.StaticText(self, -1, "Search in code description: ",
                style=wx.ALIGN_RIGHT)

        # text input
        epsgdir = os.path.join(os.environ["GRASS_PROJSHARE"], 'epsg')
        self.tfile = wx.TextCtrl(self,-1, epsgdir, size=(200,-1))
        self.tcode = wx.TextCtrl(self,-1, "", size=(200,-1))

        # buttons
        self.bbrowse = wx.Button(self, -1, "Browse...")
        self.bbcodes = wx.Button(self, -1, "Browse Codes...")

        # search box
        self.searchb = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)

        self.epsglist = wx.ListCtrl(self, id=wx.ID_ANY,
                     size=(650,275),
                     style=wx.LC_REPORT|
                     wx.LC_HRULES|
                     wx.EXPAND)
        self.epsglist.InsertColumn(0, 'Code', wx.LIST_FORMAT_CENTRE)
        self.epsglist.InsertColumn(1, 'Description', wx.LIST_FORMAT_LEFT)
        self.epsglist.InsertColumn(2, 'Parameters', wx.LIST_FORMAT_LEFT)
        self.epsglist.SetColumnWidth(0, 50)
        self.epsglist.SetColumnWidth(1, 300)
        self.epsglist.SetColumnWidth(2, 325)

        # layout
        self.sizer.Add(self.lfile, 0, wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, col=1, row=1)
        self.sizer.Add(self.tfile, 0, wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=2)
        self.sizer.Add(self.bbrowse, 0, wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=1, col=3)

        self.sizer.Add(self.lcode, 0, wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, col=1, row=2)
        self.sizer.Add(self.tcode, 0, wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2, col=2)

        self.sizer.Add(self.lsearch, 0, wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, col=1, row=3)
        self.sizer.Add(self.searchb, 0, wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=3, col=2)
        self.sizer.Add(self.bbcodes, 0 , wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=3, col=3)

        self.sizer.Add(self.epsglist, wx.ALIGN_LEFT|wx.EXPAND, 0, row=4, col=1, colspan=5)

        # events
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, self.bbrowse)
        self.Bind(wx.EVT_BUTTON, self.OnBrowseCodes, self.bbcodes)
        self.Bind(wx.EVT_TEXT, self.OnText, self.tcode)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.epsglist)
        self.searchb.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.searchb)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)

    def OnPageChange(self, event):
        if not self.epsgcode:
            wx.MessageBox('You must select an EPSG code')
            event.Veto()
        self.GetNext().SetPrev(self)

    def OnText(self, event):
        self.epsgcode = self.GetString()

    def OnDoSearch(self,event):
        str =  self.searchb.GetValue()
        listItem  = self.epsglist.GetColumn(1)

        for i in range(self.epsglist.GetItemCount()):
            listItem = self.epsglist.GetItem(i,1)
            if listItem.GetText().find(str) > -1:
                self.epsgcode = self.epsglist.GetItem(i, 0)
                self.tcode.SetValue(self.epsgcode.GetText())
                break

        self.OnBrowseCodes(None,str)


    def OnBrowse(self, event):

        dlg = wx.FileDialog(self, "Choose EPSG codes file:",
        "/", "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    self.tfile.SetValue(path)
        dlg.Destroy()

    def OnItemSelected(self,event):
        index = event.m_itemIndex
        item = event.GetItem()

        self.epsgcode = item.GetText()
        self.epsgdesc = self.epsglist.GetItem(index, 1).GetText()
        self.tcode.SetValue(str(self.epsgcode))

    def OnBrowseCodes(self,event,search=None):
        try:
            self.epsglist.DeleteAllItems()
            f = open(self.tfile.GetValue(),"r")
            i=1
            j = 0
            descr = None
            code = None
            params = ""
            #self.epsglist.ClearAll()
            for line in f.readlines():
                line = line.strip()
                if line.find("#") == 0:
                    descr = line[1:].strip()
                elif line.find("<") == 0:
                    code = line.split(" ")[0]
                    for par in line.split(" ")[1:]:
                        params += par + " "
                    code = code[1:-1]
                if code == None: code = 'no code'
                if descr == None: descr = 'no description'
                if params == None: params = 'no parameters'
                if i%2 == 0:
                    if search and descr.lower().find(search.lower()) > -1 or\
                        not search:
                        index = self.epsglist.InsertStringItem(j, code)
                        self.epsglist.SetStringItem(index, 1, descr)
                        self.epsglist.SetStringItem(index, 2, params)
                        j  += 1
                    # reset
                    descr = None; code = None; params = ""
#                if i%2 == 0:
#                    self.epsglist.SetItemBackgroundColour(i, "grey")
                i += 1
            f.close()
            self.epsglist.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            self.epsglist.SetColumnWidth(2, wx.LIST_AUTOSIZE)
            self.SendSizeEvent()
        except StandardError, e:
            dlg = wx.MessageDialog(self, "Could not read EPGS codes: %s " % e,
                                   "Could not read file",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()


class CustomPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Choose method of specifying georeferencing parameters")
        global coordsys
        self.proj4string = ''
        self.parent = parent

        self.text_proj4string = self.MakeTextCtrl(size=(400,100))
        self.label_proj4string = self.MakeRLabel("Enter PROJ.4 parameters string: ")
        if proj4string:
            self.text_proj4string.SetValue(proj4string)

        self.sizer.Add(self.label_proj4string, 0, wx.ALIGN_RIGHT|wx.ALL, 5, row=5,col=1)
        self.sizer.Add(self.text_proj4string, 0, wx.ALIGN_LEFT|wx.ALL, 5, row=5,col=2)

        self.Bind(wx.EVT_TEXT, self.GetProjstring, self.text_proj4string)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)

    def OnPageChange(self, event):
        if not self.proj4string:
            wx.MessageBox('You must enter a PROJ.4 string')
            event.Veto()
        self.GetNext().SetPrev(self)

    def GetProjstring(self, event):
        proj4string
        self.proj4string = event.GetString()


class SummaryPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Summary")

        self.parent = parent

        self.sizer.Add(self.MakeRLabel("GRASS database:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=1, col=0)
        self.sizer.Add(self.MakeRLabel("Location name:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=2, col=0)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL, 0, row=3, col=0, colspan=2)
        self.sizer.Add((10,10), 1, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, border=5, row=4, col=0)
        self.sizer.Add(self.MakeRLabel("Projection:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=5, col=0)
        self.sizer.Add(self.MakeRLabel("North:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=6, col=0)
        self.sizer.Add(self.MakeRLabel("South:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=7, col=0)
        self.sizer.Add(self.MakeRLabel("East:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=8, col=0)
        self.sizer.Add(self.MakeRLabel("West:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=9, col=0)
        self.sizer.Add(self.MakeRLabel("Resolution:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=10, col=0)
        self.sizer.Add(self.MakeRLabel("Rows:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=12, col=0)
        self.sizer.Add(self.MakeRLabel("Columns:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=13, col=0)
        self.sizer.Add(self.MakeRLabel("Cells:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=14, col=0)
        self.sizer.Add(self.MakeRLabel("PROJ.4 string:"), 1, flag=wx.ALIGN_RIGHT|wx.ALL, border=5, row=16, col=0)

        # labels
        self.ldatabase  =	self.MakeLLabel("")
        self.llocation  =	self.MakeLLabel("")
        self.lprojection =	self.MakeLLabel("")
        self.lnorth =	    self.MakeLLabel("")
        self.lsouth  =	    self.MakeLLabel("")
        self.least =	    self.MakeLLabel("")
        self.lwest =	    self.MakeLLabel("")
        self.lres =	        self.MakeLLabel("")
        self.lrows =	    self.MakeLLabel("")
        self.lcols =	    self.MakeLLabel("")
        self.lcells =	    self.MakeLLabel("")
        self.lproj4 =       self.MakeLLabel("")

        self.sizer.Add(self.ldatabase, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=1, col=1)
        self.sizer.Add(self.llocation, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=2, col=1)
        self.sizer.Add(self.lprojection, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=5, col=1)
        self.sizer.Add(self.lnorth, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=6, col=1)
        self.sizer.Add(self.lsouth, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=7, col=1)
        self.sizer.Add(self.least, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=8, col=1)
        self.sizer.Add(self.lwest, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=9, col=1)
        self.sizer.Add(self.lres, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=10, col=1)
        self.sizer.Add(self.lrows, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=12, col=1)
        self.sizer.Add(self.lcols, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=13, col=1)
        self.sizer.Add(self.lcells, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=14, col=1)
        self.sizer.Add(self.lproj4, 1, flag=wx.ALIGN_LEFT|wx.ALL, border=5, row=16, col=1)

    def FillVars(self,event=None):
        database = self.parent.startpage.grassdatabase
        location = self.parent.startpage.location
        global coordsys
        global north
        global south
        global east
        global west
        global resolution
        global proj4string

        if not coordsys:
            coordsys = 0
        if not north:
            north  = 0
        if not south:
            south = 0
        if not east:
            east = 0
        if not west:
            west = 0
        if not resolution:
            resolution = 1

        #if projection != "latlong":
        rows = int(round((float(north)-float(south))/float(resolution)))
        cols = int(round((float(east)-float(west))/float(resolution)))
        cells = int(rows*cols)

        projection = self.parent.projpage.proj
        projdesc = self.parent.projpage.projdesc
        utmzone = self.parent.projtypepage.utmzone
        utmhemisphere = self.parent.projtypepage.utmhemisphere
        ellipse = self.parent.ellipsepage.ellipse
        ellipsedesc = self.parent.ellipsepage.ellipsedesc
        datum = self.parent.datumpage.datum
        datumdesc = self.parent.datumpage.datumdesc
        ellipsoid = self.parent.datumpage.ellipsoid
        datumparams = self.parent.datumpage.datumparams
        transform = self.parent.datumpage.transform
        transregion = self.parent.datumpage.transregion
        transparams = self.parent.datumpage.transparams

        self.ldatabase.SetLabel(str(database))
        self.llocation.SetLabel(str(location))

        label = ''
        if coordsys == 'epsg':
            label = 'EPSG code %s: %s' % (self.parent.epsgpage.epsgcode,self.parent.epsgpage.epsgdesc)
            self.lprojection.SetLabel(label)
        elif coordsys == 'file':
            label = 'Matches file: %s' % self.parent.filepage.georeffile
            self.lprojection.SetLabel(label)
        elif coordsys == 'proj':
            label = ('Projection: %s, %s%s' % (projdesc, datumdesc, ellipsedesc))
            self.lprojection.SetLabel(label)
        elif coordsys == 'xy':
            label = ('XY coordinate system. Not projected')
            self.lprojection.SetLabel(label)
        elif coordsys == 'custom':
            label = ('Custom PROJ.4 string')
        self.lprojection.Wrap(500)

        self.lnorth.SetLabel(str(north))
        self.lsouth.SetLabel(str(south))
        self.least.SetLabel(str(east))
        self.lwest.SetLabel(str(west))
        self.lres.SetLabel(str(resolution))
        self.lrows.SetLabel(str(rows))
        self.lcols.SetLabel(str(cols))
        self.lcells.SetLabel(str(cells))
        self.lproj4.SetLabel(proj4string)


class BBoxPage(TitledPage):
    def __init__(self, wizard, parent):
        TitledPage.__init__(self, wizard, "Set default region extents and resolution")

        self.parent = parent
        # inputs
        self.ttop = self.MakeTextCtrl("1", size=(150, -1))
        self.tbottom = self.MakeTextCtrl("0", size=(150, -1))
        self.tleft = self.MakeTextCtrl("0", size=(150, -1))
        self.tright = self.MakeTextCtrl("1", size=(150, -1))
        self.tres = self.MakeTextCtrl("1", size=(150, -1))

        self.tgdal = self.MakeTextCtrl("", size=(250, -1))
        self.tdsn = self.MakeTextCtrl("", size=(250, -1))
        # list of layers
        self.layers = []
        self.llayers = wx.ComboBox(self, -1,
                       choices=self.layers,
                       size=(250,-1),
                       style=wx.CB_DROPDOWN)

        # labels
        self.lmessage = wx.StaticText(self,-1, "", size=(300,50))

        # buttons
        self.bbrowsegdal = self.MakeButton("Browse...", size=(150,-1))
        self.bbrowseogr = self.MakeButton("Browse...", size=(150,-1))
        self.bgetlayers = self.MakeButton("Get Layers", size=(150,-1))
        self.bset = self.MakeButton("Set coordinates", size=(150,-1))

        # list of states
        self.states = []
        self.coords = []
        try:
            f = open(os.path.join(os.getenv("GISBASE"),"etc","wx","states.txt"),"r")
            for line in f.readlines():
                if line[0] == "#":
                    continue
                state,coord = line.split(";")
                coord = coord.replace(","," ")
                self.states.append(state)
                self.coords.append(coord.split())
            f.close()
        except:
            pass
        # NOTE: ComboCtcl should come here, but nobody knows, how to
        # implement it
        # self.stateslist = wx.ListCtrl(self,
        #                    style=wx.LC_LIST|wx.LC_SINGLE_SEL|wx.SIMPLE_BORDER)
        # self.cstate = wx.combo.ComboCtrl(self, -1, pos=(50, 170), size=(150, -1),
        #          style=wx.CB_READONLY)

        self.cstate = wx.ComboBox(self, -1,
                       size=(250,-1),
                       choices=self.states,
                       style=wx.CB_DROPDOWN)

        # layout
        self.sizer.Add(self.MakeRLabel("North"), 0,
                       wx.ALIGN_CENTER_HORIZONTAL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 0, row=1,col=2)
        self.sizer.Add(self.ttop, 0,
                       wx.ALIGN_CENTER_HORIZONTAL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=2,col=2)

        self.sizer.Add(self.MakeRLabel("West"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 0, row=3,col=0)
        self.sizer.Add(self.tleft, 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,  row=3,col=1)

        self.sizer.Add(self.tright, 0,
                       wx.ALIGN_CENTER_HORIZONTAL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,  row=3,col=3)
        self.sizer.Add(self.MakeRLabel("East"), 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 0, row=3,col=4)

        self.sizer.Add(self.tbottom, 0,
                       wx.ALIGN_CENTER_HORIZONTAL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=4,col=2)
        self.sizer.Add(self.MakeRLabel("South"), 0,
                       wx.ALIGN_CENTER_HORIZONTAL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 0, row=5,col=2)

        self.sizer.Add(self.MakeRLabel("Initial resolution"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=6,col=1)
        self.sizer.Add(self.tres, 0,
                       wx.ALIGN_CENTER_HORIZONTAL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=6,col=2)
        self.sizer.Add(self.bset, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=6, col=3 )

        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 0, row=7, col=0, colspan=6)

        self.sizer.Add(self.MakeRLabel("Match extents of georeferenced raster map or image"), 3,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=8,col=0, colspan=3)

        self.sizer.Add(self.MakeRLabel("File:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=9,col=0, colspan=1)
        self.sizer.Add(self.tgdal, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=9,col=1, colspan=2)
        self.sizer.Add(self.bbrowsegdal, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=9,col=3)

        self.sizer.Add(wx.StaticLine(self, -1), 0,
                       wx.EXPAND|wx.ALL, 0,
                       row=10, col=0, colspan=6)

        self.sizer.Add(self.MakeRLabel("Match extents of georeferenced vector map"), 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=11,col=0, colspan=3 )

        self.sizer.Add(self.MakeRLabel("Data source/directory:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=12,col=0, colspan=1)
        self.sizer.Add(self.tdsn, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=12, col=1, colspan=2)
        self.sizer.Add(self.bbrowseogr, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=12, col=3)

        self.sizer.Add(self.MakeRLabel("Layer/file:"), 0,
                       wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=13,col=0, colspan=1)
        self.sizer.Add(self.llayers, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=13,col=1, colspan=2)
        self.sizer.Add(self.bgetlayers, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=13,col=3)

        self.sizer.Add(wx.StaticLine(self, -1), 0,
                       wx.EXPAND|wx.ALL |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=14, col=0, colspan=6)
        self.sizer.Add(self.MakeRLabel("Match extents of selected country"), 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=15,col=0, colspan=3)
        self.sizer.Add(self.cstate, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5, row=16,col=1, colspan=2)

        self.sizer.Add(self.lmessage, 0,
                       wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL |
                       wx.ALL, 5,
                       row=17,col=1, colspan=3)

        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChange)
        self.Bind(wx.EVT_COMBOBOX, self.OnItemSelected, self.cstate)
        self.Bind(wx.EVT_TEXT, self.OnStateText, self.cstate)
        self.Bind(wx.EVT_BUTTON, self.OnSetButton, self.bset)
        self.Bind(wx.EVT_BUTTON, self.OnBrowseGdal, self.bbrowsegdal)
        self.Bind(wx.EVT_BUTTON, self.OnBrowseOGR, self.bbrowseogr)
        self.Bind(wx.EVT_BUTTON, self.OnGetOGRLayers, self.bgetlayers)

    def OnBrowseGdal(self, event):
        dlg = wx.FileDialog(self, "Choose a raster file:", os.getcwd(), "", "*.*", wx.OPEN)
        path = ""
        if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    self.tgdal.SetValue(path)
        dlg.Destroy()

        self.OnSetButton()

    def OnBrowseOGR(self, event):
        dlg = wx.FileDialog(self, "Choose a data source name:", os.getcwd(), "", "*.*", wx.OPEN)
        path = ""
        if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    self.tdsn.SetValue(path)
        dlg.Destroy()
        self.OnGetOGRLayers(None)

    def OnSetButton(self,event=None):
        if self.tgdal.GetValue():
            self.__setGDAL()
        if self.tdsn.GetValue() and self.llayers.GetSelection()>-1:
            self.__setOGR()
        elif self.cstate.GetSelection() > -1:
            sys.stderr.write("##############"+str(self.cstate.GetSelection())+"\n")
            self.OnItemSelected(None)

    def OnGetOGRLayers(self, event):
        path = self.tdsn.GetValue()
        line = ""

        sys.stderr.write(path+"####\n")
        self.layers = []
        self.llayers.Clear()
        cmd = os.popen("ogrinfo -so %s\n" % (path))
        line = cmd.readline()
        # 1: cr (Polygon)
        rex = re.compile("^(\d+):\s+(.+)\s+\(.*\)")
        while 1:
            if not line or line == "":
                break
            try:
                sys.stderr.write("#####"+line+"####\n")
                number, name = rex.findall(line)[0]
                self.layers.append(name)
            except:
                pass
            line = cmd.readline()
        self.llayers.AppendItems(self.layers)
        #sys.stderr.write(str( self.layers)+"\n")
        #self.sizer.Remove(self.llayers)
        #self.llayers = wx.ComboBox(self, -1, choices=self.layers, size=(100,-1),
        #        style=wx.CB_DROPDOWN)
        #self.sizer.Add(self.llayers, 0, wx.ALIGN_CENTER_VERTICAL, row=12,col=3)
        #self.sizer.ShowItems(True)
        self.OnSetButton()
        pass

    def __setOGR(self):
        layer = self.layers[self.llayers.GetSelection()]
        path = self.tdsn.GetValue()
        number="-?\d+\.\d+"
        line = ""

        #test values
        self.ttop.SetValue(500)
        self.tleft.SetValue(500)

        #Extent: (-146.976217, -55.985484) - (72.774632, 80.594358)
        rex = re.compile("\((%s),\s*(%s)\)\s*-\s*\((%s),\s*(%s)\)" %(number, number, number, number))
        cmd = os.popen("ogrinfo -so %s %s" % (path ,layer))
        line = cmd.readline()
        while 1:
            if not line or line == "":
                    break
            sys.stderr.write(line+"\n")
            if line.find("Extent")>-1:
                sys.stderr.write(line[0]+"#####\n")
                x1,y1,x2,y2 = rex.findall(line)[0]
                self.tbottom.SetValue(y1)
                self.tleft.SetValue(x1)
                self.ttop.SetValue(y2)
                self.tright.SetValue(x2)
                break
            line = cmd.readline()
        return

    def __setGDAL(self):
        path = self.tgdal.GetValue()
        line = ""
        number="-?\d+\.\d+"

        #test values
        self.ttop.SetValue(500)
        self.tleft.SetValue(500)

        # Upper Left  (    0.0,    0.0)
        rex=re.compile("\(\s*(%s)\s*,\s*(%s)\)" % (number, number))
        obj = os.popen("gdalinfo %s | grep \"Upper\|Lower\"" % path)

        line = obj.readline()
        while 1:
            sys.stderr.write(line+"\n")
            if not line:
                    break
            if line.find("Upper Left")>-1:
                x,y = rex.findall(line)[0]
                self.ttop.SetValue(y)
                self.tleft.SetValue(x)
            if line.find("Lower Right")>-1:
                x,y = rex.findall(line)[0]
                self.tbottom.SetValue(y)
                self.tright.SetValue(x)
            line = obj.readline()
        return

    def OnStateText(self,event):
        item = self.llayers.FindString(event.GetString())
        self.llayers.SetSelection(item)
        self.llayers.SetValue(self.llayers.GetStringSelection())
        pass
        #.log.WriteText('EvtTextEnter: %s' % event.GetString())
        #sys.stderr.write(event.GetString()+"\n")
        #text=event.GetString().lower()
        #for idx in range(len(self.states)):
        #    if self.states[idx].lower() == text:
        #        self.cstate.Select(idx)
        #        break

    def OnPageChange(self, event):
        self.GetNext().FillVars()
        self.GetNext().SetPrev(self)

        global north
        north = self.ttop.GetValue()
        global south
        south = self.tbottom.GetValue()
        global east
        east = self.tright.GetValue()
        global west
        west = self.tleft.GetValue()
        global resolution
        resolution = self.tres.GetValue()

    def OnItemSelected(self, event):
        item = self.cstate.GetSelection()
        w,s,e,n = self.coords[item]
        #  4
        # 1 3
        #  2

        if self.parent.csystemspage.cs == "latlong":
            pass
        if self.parent.csystemspage.cs == "xy":
            pass
        else:
            if self.parent.csystemspage.cs == "epsg":
                to="+init=epsg:%d" % (int(self.parent.epsgpage.tcode.GetValue()))
            elif self.parent.csystemspage.cs == "proj":
                to="+proj=%s" % (self.parent.projpage.tproj.GetValue())
            elif self.parent.csystemspage.cs == "utm":
                to="+proj=utm"
            else:
                sys.stderr.write(self.parent.csystemspage.cs+"\n")

            try:
                sin, sout = os.popen2("cs2cs +proj=latlong +datum=WGS84 +to %s" %  (to))
                sin.write("%s %s\n" % (w,s))
                sin.write("%s %s\n" % (e,n))
                sin.close()
                w,s,t = sout.readline().split()
                e,n,t = sout.readline().split()
                self.lmessage.SetLabel("")
            except:
                n = s = w = e="NULL"
                self.lmessage.SetLabel("Unable to calculate country extends:\n cs2cs +proj=latlong +datum=WGS84 +to %s"% to)

        self.ttop.SetValue( str(n) )
        self.tbottom.SetValue( str(s) )
        self.tright.SetValue( str(e) )
        self.tleft.SetValue( str(w) )



class GWizard:
    def __init__(self, parent, grassdatabase):
        wizbmp = wx.Image(os.path.join(os.getenv("GISBASE"),"etc","wx","images","wizard.png"), wx.BITMAP_TYPE_PNG)
        wizbmp.Rescale(250,600)
        wizbmp = wizbmp.ConvertToBitmap()

        global coordsys

        # get georeferencing information from tables in $GISBASE/etc

        # make projections dictionary
        f = open(os.path.join(os.getenv("GISBASE"), "etc","projections"),"r")
        self.projections = {}
        for line in f.readlines():
            line = line.expandtabs(1)
            line = line.strip()
            if not line:
                continue
            if line == '' or line[0] == "#":
                continue
            proj,projdesc = line.split(":", 1)
            proj = proj.strip()
            projdesc = projdesc.strip()
            self.projections[proj] = projdesc
        f.close()

        f = open(os.path.join(os.getenv("GISBASE"), "etc","datum.table"),"r")
        self.datums = {}
        paramslist = []
        for line in f.readlines():
            line = line.expandtabs(1)
            line = line.strip()
            if not line:
                continue
            if line == '' or line[0] == "#":
                continue
            datum,info = line.split(" ", 1)
            info = info.strip()
            datumdesc,params = info.split(" ",1)
            datumdesc = datumdesc.strip('"')
            paramlist = params.split()
            ellipsoid = paramlist.pop(0)
            self.datums[datum] = (datumdesc,ellipsoid,paramlist)
        f.close()

        # make datum transforms dictionary
        f = open(os.path.join(os.getenv("GISBASE"), "etc","datumtransform.table"),"r")
        self.transforms = {}
        j = 1
        for line in f.readlines():
            transcode = 'T'+str(j)
            line = line.expandtabs(1)
            line = line.strip()
            if not line:
                continue
            if line == '' or line[0] == "#":
                continue
            datum,rest = line.split(" ", 1)
            rest = rest.strip('" ')
            params,rest = rest.split('"', 1)
            params = params.strip()
            rest = rest.strip('" ')
            try:
                region,info = rest.split('"', 1)
                info = info.strip('" ')
                info = region+': '+info
            except:
                info = rest
            self.transforms[transcode] = (datum,info,params)
            j+=1
        f.close()

        # make ellipsiods dictionary
        f = open(os.path.join(os.getenv("GISBASE"), "etc","ellipse.table"),"r")
        self.ellipsoids = {}
        for line in f.readlines():
            line = line.expandtabs(1)
            line = line.strip()
            if not line:
                continue
            if line == '' or line[0] == "#":
                continue
            ellipse,rest = line.split(" ", 1)
            rest = rest.strip('" ')
            desc,params = rest.split('"', 1)
            desc = desc.strip('" ')
            paramslist = params.split()
            self.ellipsoids[ellipse] = (desc,paramslist)
        f.close()

        # define wizard pages
        self.wizard = wiz.Wizard(parent, -1, "Define new Location",
                bitmap=wizbmp)
        self.startpage = DatabasePage(self.wizard, self, grassdatabase)
        self.csystemspage = CoordinateSystemPage(self.wizard, self)
        self.projpage = ProjectionsPage(self.wizard, self)
        self.projtypepage = ProjTypePage(self.wizard,self)
        self.epsgpage = EPSGPage(self.wizard, self)
        self.bboxpage = BBoxPage(self.wizard, self)
        self.filepage = GeoreferencedFilePage(self.wizard, self)
        self.datumpage = DatumPage(self.wizard, self)
        self.ellipsepage = EllipsePage(self.wizard, self)
        self.custompage = CustomPage(self.wizard, self)
        self.sumpage = SummaryPage(self.wizard, self)


        # Set the initial order of the pages
        # it should follow the epsg line
        self.startpage.SetNext(self.csystemspage)

        self.csystemspage.SetPrev(self.startpage)
        self.csystemspage.SetNext(self.bboxpage)

        self.projtypepage.SetPrev(self.projpage)
        self.projtypepage.SetNext(self.datumpage)

        self.datumpage.SetPrev(self.projtypepage)
        self.datumpage.SetNext(self.bboxpage)

        self.ellipsepage.SetPrev(self.projtypepage)
        self.ellipsepage.SetNext(self.bboxpage)

        self.projpage.SetPrev(self.csystemspage)
        self.projpage.SetNext(self.projtypepage)

        self.epsgpage.SetPrev(self.csystemspage)
        self.epsgpage.SetNext(self.bboxpage)

        self.filepage.SetPrev(self.csystemspage)
        self.filepage.SetNext(self.bboxpage)

        self.custompage.SetPrev(self.csystemspage)
        self.custompage.SetNext(self.bboxpage)

        self.bboxpage.SetPrev(self.csystemspage)
        self.bboxpage.SetNext(self.sumpage)

        self.sumpage.SetPrev(self.bboxpage)

        self.wizard.FitToPage(self.bboxpage)

        success = False

        if self.wizard.RunWizard(self.startpage):
            success = self.onWizFinished()
            if success == True:
                wx.MessageBox("New location created.")
            else:
                wx.MessageBox("Unable to create new location.")
        else:
            wx.MessageBox("Location wizard canceled. New location not created.")

        self.wizard.Destroy()

    def onWizFinished(self):
        database = self.startpage.grassdatabase
        location = self.startpage.location
        global coordsys
        success = ''

#        wx.MessageBox("finished database: %s, location: %s, coordsys: %s" % (database, location, coordsys))
        if os.path.isdir(os.path.join(database,location)):
            dlg = wx.MessageDialog(self, "Could not create new location: %s already exists"
                                   % os.path.join(database,location),"Could not create location",
                                   wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if coordsys == "xy":
            success = self.XYCreate()
        elif coordsys == "latlong":
            rows = int(round((float(north)-float(south))/float(resolution)))
            cols = int(round((float(east)-float(west))/float(resolution)))
            cells = int(rows*cols)
            success = self.LatlongCreate()
        elif coordsys == "proj":
            success = self.Proj4Create()
        elif coordsys == 'custom':
            success - self.CustomCreate
        elif coordsys == "epsg":
            success = self.EPSGCreate()
        elif coordsys == "file":
            success = self.FileCreate()

        return success

    def XYCreate(self):
        """
        Create an XY location
        """
        wx.MessageBox('Not implemented: Create xy location')


    def Proj4Create(self):
        """
        Create a new location for selected projection
        """

        location = self.startpage.location
        proj = self.projpage.proj
        projdesc = self.projpage.projdesc

        utmzone = self.projtypepage.utmzone
        utmhemisphere = self.projtypepage.utmhemisphere

        datum = self.datumpage.datum
        if self.datumpage.datumdesc:
            datumdesc = self.datumpage.datumdesc+' - '+self.datumpage.ellipsoid
        else: datumdesc = ''
        datumparams = self.datumpage.datumparams
        transparams = self.datumpage.transparams

        ellipse = self.ellipsepage.ellipse
        ellipsedesc = self.ellipsepage.ellipsedesc
        ellipseparams = self.ellipsepage.ellipseparams

        # Creating PROJ.4 string
        if proj == 'll':
            proj = 'longlat'

        if proj == 'utm' and utmhemisphere == 'south':
            proj4string = '+proj=%s +zone=%s +south' % (proj, utmzone)
        elif proj == 'utm':
            proj4string = '+proj=%s +zone=%s' % (proj, utmzone)
        else:
            proj4string = '+proj=%s ' % (proj)

        proj4params = ''
        # set ellipsoid parameters
        for item in ellipseparams:
            if item[:4] == 'f=1/':
                item = '+rf='+item[4:]
            else:
                item = '+'+item
            proj4params = '%s %s' % (proj4params, item)
        # set datum and transform parameters if relevant
        if datumparams:
            for item in datumparams:
                proj4params = '%s +%s' % (proj4params,item)
            if transparams:
                proj4params = '%s +no_defs +%s' % (proj4params,transparams)
            else:
                proj4params = '%s +no_defs' % proj4params
        else:
            proj4params = '%s +no_defs' % proj4params

        proj4string = '%s %s' % (proj4string, proj4params)

        dlg = wx.MessageDialog(self.wizard, "New location '%s' will be created georeferenced to \n\
                            %s: %s%s\n\
                            (PROJ.4 string: %s)" % (location,projdesc,datumdesc,ellipsedesc,proj4string),
                            "Create new location?",
                            wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_NO:
            dlg.Destroy()
            return False
        else:
            dlg.Destroy()

        # Creating location from PROJ.4 string passed to g.proj
        try:
            cmdlist = ['g.proj', '-c', 'proj4=%s' % proj4string, 'location=%s' % location]
            cmd.Command(cmdlist)
            return True

        except StandardError, e:
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: %s " % str(e),
                                   "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def CustomCreate(self):
        proj4string = self.custompage.proj4string

        dlg = wx.MessageDialog(self.wizard, "New location '%s' will be created using \
                            PROJ.4 string: %s" % (location,proj4string),
                               "Create new location?",
                               wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_NO:
            dlg.Destroy()
            return False
        else:
            dlg.Destroy()

        try:
            cmdlist = ['g.proj','-c','proj4="%s"' % proj4string,'location=%s' % location]
            wx.MessageBox('cmdlist: %s' % cmdlist)
            cmd.Command(cmdlist)
            return True

        except StandardError, e:
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: %s " % str(e),
                                   "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False


    def EPSGCreate(self):
        """
        Create a new location from an EPSG code.
        """
        epsgcode = self.epsgpage.epsgcode
        epsgdesc = self.epsgpage.epsgdesc
        location = self.startpage.location
        cmdlist = []

        if not epsgcode:
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: EPSG Code value missing",
                    "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        dlg = wx.MessageDialog(self.wizard, "New location '%s' will be created georeferenced to \
                               EPSG code %s: %s" % (location, epsgcode, epsgdesc),
                               "Create new location from EPSG code?",
                               wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_NO:
            dlg.Destroy()
            return False
        else:
            dlg.Destroy()

        # creating location
        try:
            cmdlist = ['g.proj','epsg=%s' % epsgcode,'datumtrans=-1']
            p = cmd.Command(cmdlist)
            dtoptions = p.module_stdout.read()
            if dtoptions != None:
                dtrans = ''
                # open a dialog to select datum transform number
                dlg = wx.TextEntryDialog(self.wizard, dtoptions,
                                         caption='Select the number of a datum transformation to use',
                                         defaultValue='1',
                                         style=wx.TE_WORDWRAP|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|
                                         wx.RESIZE_BORDER|wx.VSCROLL|
                                         wx.OK|wx.CANCEL)

                if dlg.ShowModal() == wx.ID_CANCEL:
                    dlg.Destroy()
                    return False
                else:
                    dtrans = dlg.GetValue()
                    if dtrans != '':
                        dlg.Destroy()
                    else:
                        wx.MessageBox('You must select a datum transform')
                        return False

                cmdlist = ['g.proj','-c','epsg=%s' % epsgcode,'location=%s' % location,'datumtrans=%s' % dtrans]
            else:
                cmdlist = ['g.proj','-c','epsg=%s' % epsgcode,'location=%s' % location,'datumtrans=1']

            cmd.Command(cmdlist)
            return True

        except StandardError, e:
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: %s " % str(e),
                                   "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def FileCreate(self):
        """
        Create a new location from a georeferenced file
        """
        georeffile = self.filepage.georeffile
        location = self.startpage.location

        cmdlist = []

        dlg = wx.MessageDialog(self.wizard, "New location '%s' will be created georeferenced to file '%s'"\
                               % (location, georeffile), "Create new location from georeferenced file?",
                               wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_NO:
            dlg.Destroy()
            return False
        else:
            dlg.Destroy()

        if not os.path.isfile(georeffile):
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: could not find file %s" % georeffile,
                                   "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if not georeffile:
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: georeferenced file not set",
                    "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # creating location
        try:
            cmdlist = ['g.proj','-c','georef=%s' % georeffile,'location=%s' % location]
            cmd.Command(cmdlist)
            return True

        except StandardError, e:
            dlg = wx.MessageDialog(self.wizard, "Could not create new location: %s " % str(e),
                                   "Could not create location",  wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

if __name__ == "__main__":
    gWizard = GWizard(None,  "")
    GRASSStartUp = GWizard.StartUp(0)
    GRASSStartUp.MainLoop()
    #app.MainLoop()
