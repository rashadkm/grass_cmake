"""
@package preferences

@brief User preferences dialog

Sets default display font, etc.

Classes:
 - PreferencesDialog
 - SetDefaultFont
 - MapsetAccess

(C) 2007-2008 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Michael Barton (Arizona State University)
Martin Landa <landa.martin gmail.com>
"""

import os
import sys
import copy

import wx
import wx.lib.filebrowsebutton as filebrowse
import wx.lib.colourselect as csel
from wx.lib.wordwrap import wordwrap

import gcmd
import grassenv
import utils
from debug import Debug as Debug

class Settings:
    """Generic class where to store settings"""
    def __init__(self):
        #
        # settings filename
        #
        self.fileName = ".grasswx"
        self.filePath = None

        #
        # default settings
        #
        self.defaultSettings = {
            #
            # general
            #
            'general': {
                'mapsetPath'  : { 'selection' : 0 }, # current mapset search path
                'changeOpacityLevel' : { 'enabled' : False }, # show opacity level widget
                },
            #
            # display
            #
            'display': {
                'displayFont' : { 'value' : '' },
                },
            #
            # advanced
            #
            'advanced' : {
                'settingsFile'   : { 'type' : 'gisdbase' }, # gisdbase, location, mapset
                'digitInterface' : { 'type' : 'vdigit' }, # vedit, vdigit
                'iconTheme'      : { 'type' : 'silk' }, # grass, silk
                },
            #
            # Attribute Table Manager
            #
            'atm' : {
            'highlight' : { 'color' : (255, 255, 0, 255), 'width' : 2},
            'leftDbClick' : { 'selection' : 0 },
            },
            #
            # Command
            #
            'cmd': {
            'overwrite' : { 'enabled' : False },
            'closeDlg' : { 'enabled' : False },
            'verbosity' : { 'selection' : 'grassenv' },
            'rasterOverlay' : { 'enabled' : False },
            },
            #
            # vdigit
            #
            'vdigit' : {
                # symbology
                'symbolHighlight'   : { 'enabled' : None,  'color' : (255, 255, 0, 255) }, #yellow
                'symbolPoint'       : { 'enabled' : True,  'color' : (0, 0, 0, 255) }, # black
                'symbolLine'        : { 'enabled' : True,  'color' : (0, 0, 0, 255) }, # black
                'symbolBoundaryNo'  : { 'enabled' : True,  'color' : (126, 126, 126, 255) }, # grey
                'symbolBoundaryOne' : { 'enabled' : True,  'color' : (0, 255, 0, 255) }, # green
                'symbolBoundaryTwo' : { 'enabled' : True,  'color' : (255, 135, 0, 255) }, # orange
                'symbolCentroidIn'  : { 'enabled' : True,  'color' : (0, 0, 255, 255) }, # blue
                'symbolCentroidOut' : { 'enabled' : True,  'color' : (165, 42, 42, 255) }, # brown
                'symbolCentroidDup' : { 'enabled' : True,  'color' : (156, 62, 206, 255) }, # violet
                'symbolNodeOne'     : { 'enabled' : True,  'color' : (255, 0, 0, 255) }, # red
                'symbolNodeTwo'     : { 'enabled' : True,  'color' : (0, 86, 45, 255) }, # dark green
                'symbolVertex'      : { 'enabled' : False, 'color' : (255, 20, 147, 255) }, # deep pink
                # display
                'lineWidth' : { 'value' : 2, 'units' : 'screen pixels' },
                # snapping
                'snapping' : { 'value' : 10, 'units' : 'screen pixels' },
                'snapToVertex' : { 'enabled' : False },
                'backgroundMap' : {'value' : ''},
                # digitize new record
                'addRecord' : { 'enabled' : True },
                'layer' : {'value' : 1 },
                'category' : {'value' : 1 },
                'categoryMode' : {'value' : 'Next to use' },
                # delete existing feature(s)
                'delRecord' : { 'enabled' : True },
                # query tool
                'query'       : { 'type' : 'length', 'box' : True },
                'queryLength' : { 'than' : 'shorter than', 'thresh' : 0 },
                'queryDangle' : { 'than' : 'shorter than', 'thresh' : 0 },
                # select feature (point, line, centroid, boundary)
                'selectFeaturePoint'    : { 'enabled' : True },
                'selectFeatureLine'     : { 'enabled' : True },
                'selectFeatureCentroid' : { 'enabled' : True },
                'selectFeatureBoundary' : { 'enabled' : True },
                'selectThresh'          : { 'value' : 10, 'units' : 'screen pixels'},
                }
            }

        #
        # user settings
        #
        self.userSettings = copy.deepcopy(self.defaultSettings)
        try:
            self.ReadSettingsFile()
        except gcmd.SettingsError, e:
            print >> sys.stderr, e.message

        #
        # internal settings (based on user settings)
        #
        self.internalSettings = {}
        for group in self.userSettings.keys():
            if group == 'vdigit':
                continue # skip digitization settings (separate window frame)
            self.internalSettings[group] = {}
            for key in self.userSettings[group].keys():
                self.internalSettings[group][key] = {}

        self.internalSettings['general']["mapsetPath"]['value'] = self.GetMapsetPath()
        self.internalSettings['general']['mapsetPath']['choices'] = [_('Mapset search path'),
                                                                     _('All available mapsets')]
        self.internalSettings['atm']['leftDbClick']['choices'] = [_('Edit selected record'),
                                                                  _('Display selected')]
        self.internalSettings['advanced']['settingsFile']['choices'] = ['gisdbase',
                                                                        'location',
                                                                        'mapset']
        self.internalSettings['advanced']['iconTheme']['choices'] = ['grass',
                                                                     'silk']
        self.internalSettings['advanced']['digitInterface']['choices'] = ['vedit',
                                                                          'vdigit']
        self.internalSettings['cmd']['verbosity']['choices'] = ['grassenv',
                                                                'verbose',
                                                                'quiet']

    def GetMapsetPath(self):
        """Store mapset search path"""
        all, access = utils.ListOfMapsets()

        if self.Get(group='general', key='mapsetPath', subkey='selection') == 0:
            return access
        else:
            return all
    
    def ReadSettingsFile(self, settings=None):
        """Reads settings file (mapset, location, gisdbase)"""
        if settings is None:
            settings = self.userSettings

        # look for settings file
        # -> mapser
        #  -> location
        #   -> gisdbase
        gisdbase = grassenv.GetGRASSVariable("GISDBASE")
        location_name = grassenv.GetGRASSVariable("LOCATION_NAME")
        mapset_name = grassenv.GetGRASSVariable("MAPSET")

        mapset_file = os.path.join(gisdbase, location_name, mapset_name, self.fileName)
        location_file = os.path.join(gisdbase, location_name, self.fileName)
        gisdbase_file = os.path.join(gisdbase, self.fileName)

        if os.path.isfile(mapset_file):
            self.filePath = mapset_file
        elif os.path.isfile(location_file):
            self.filePath = location_file
        elif os.path.isfile(gisdbase_file):
            self.filePath = gisdbase_file
        
        if self.filePath:
            self.__ReadFile(self.filePath)
            
    def __ReadFile(self, filename, settings=None):
        """Read settings from file to dict"""
        if settings is None:
            settings = self.userSettings

        try:
            file = open(filename, "r")
            for line in file.readlines():
                line = line.rstrip('%s' % os.linesep)
                group, key = line.split(':')[0:2]
                kv = line.split(':')[2:]
                idx = 0
                while idx < len(kv):
                    subkey = kv[idx]
                    value = kv[idx+1]
                    if len(value) == 0:
                        self.Set(group=group, key=key, subkey=subkey, value='')
                    else:
                        # casting
                        if value == 'True':
                            value = True
                        elif value == 'False':
                            value = False
                        elif value == 'None':
                            value = None
                        elif value[0] == '(':
                            tmp = value.replace('(','').replace(')', '').split(',')
                            try:
                                value = tuple(map(int, tmp))
                            except:
                                value = tuple(tmp)
                        else:
                            try:
                                value = int(value)
                            except:
                                pass
                        # Debug.msg(3, 'Settings(): group=%s, key=%s, subkey=%s, value=%s' %
                        #          (group, key, subkey, value))
                        self.Set(group=group, key=key, subkey=subkey, value=value)
                    idx += 2
        finally:
            file.close()

    def SaveToFile(self, settings=None):
        """Save settings to the file"""
        if settings is None:
            settings = self.userSettings
        
        loc = self.Get(group='advanced', key='settingsFile', subkey='type')
        gisdbase = grassenv.GetGRASSVariable("GISDBASE")
        location_name = grassenv.GetGRASSVariable("LOCATION_NAME")
        mapset_name = grassenv.GetGRASSVariable("MAPSET")
        filePath = None
        if loc == 'gisdbase':
            filePath = os.path.join(gisdbase, self.fileName)
        elif loc == 'location':
            filePath = os.path.join(gisdbase, location_name, self.fileName)
        elif loc == 'mapset':
            filePath = os.path.join(gisdbase, location_name, mapset_name, self.fileName)
        
        if filePath is None:
            raise gcmd.SettingsError(_('Uknown settings file location.'))

        try:
            file = open(filePath, "w")
            for group in settings.keys():
                for item in settings[group].keys():
                    file.write('%s:%s:' % (group, item))
                    items = settings[group][item].keys()
                    for idx in range(len(items)):
                        file.write('%s:%s' % (items[idx], settings[group][item][items[idx]]))
                        if idx < len(items) - 1:
                            file.write(':')
                    file.write('%s' % os.linesep)
        except IOError, e:
            raise gcmd.SettingsError(e)
        except:
            raise gcmd.SettingsError('Writing settings to file <%s> failed.' % filePath)

        file.close()

        return filePath

    def Get(self, group, key, subkey=None, internal=False):
        """Get value by key/subkey

        Raise KeyError if key is not found
        
        @param group settings group
        @param key
        @param subkey if not given return dict of key
        
        @return value

        """
        if internal is True:
            settings = self.internalSettings
        else:
            settings = self.userSettings
            
        try:
            if subkey is None:
                return settings[group][key]
            else:
                return settings[group][key][subkey]
        except KeyError:
            raise gcmd.SettingsError("%s %s:%s:%s." % (_("Unable to get value"),
                                                       group, key, subkey))
        
    def Set(self, group, key, subkey, value, internal=False):
        """Set value by key/subkey

        Raise KeyError if key is not found
        
        @param group settings group
        @param key
        @param subkey
        @param value 
        """
        if internal is True:
            settings = self.internalSettings
        else:
            settings = self.userSettings

        try:
            if not settings[group][key].has_key(subkey):
                raise KeyError
            settings[group][key][subkey] = value
        except KeyError:
            raise gcmd.SettingsError("%s '%s:%s:%s'" % (_("Unable to set "), group, key, subkey))

globalSettings = Settings()

class PreferencesDialog(wx.Dialog):
    """User preferences dialog"""
    def __init__(self, parent, title=_("User GUI settings"),
                 settings=globalSettings,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER):
        self.parent = parent # GMFrame
        self.title = title
        wx.Dialog.__init__(self, parent=parent, id=wx.ID_ANY, title=title,
                           style=style)

        self.settings = settings
        # notebook
        notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)

        # dict for window ids
        self.winId = {}

        # create notebook pages
        self.__CreateGeneralPage(notebook)
        self.__CreateDisplayPage(notebook)
        self.__CreateCmdPage(notebook)
        self.__CreateAttributeManagerPage(notebook)
        self.__CreateAdvancedPage(notebook)

        # buttons
        btnDefault = wx.Button(self, wx.ID_ANY, _("Set to default"))
        btnSave = wx.Button(self, wx.ID_SAVE)
        btnApply = wx.Button(self, wx.ID_APPLY)
        btnCancel = wx.Button(self, wx.ID_CANCEL)
        btnSave.SetDefault()

        # bindigs
        btnDefault.Bind(wx.EVT_BUTTON, self.OnDefault)
        btnDefault.SetToolTipString(_("Revert settings to default and apply changes"))
        btnApply.Bind(wx.EVT_BUTTON, self.OnApply)
        btnApply.SetToolTipString(_("Apply changes for this session"))
        btnSave.Bind(wx.EVT_BUTTON, self.OnSave)
        btnSave.SetToolTipString(_("Close dialog and save changes to user settings file"))
        btnSave.SetDefault()
        btnCancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnCancel.SetToolTipString(_("Close dialog and ignore changes"))

        # sizers
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(item=btnDefault, proportion=1,
                     flag=wx.ALL, border=5)
        btnStdSizer = wx.StdDialogButtonSizer()
        btnStdSizer.AddButton(btnCancel)
        btnStdSizer.AddButton(btnSave)
        btnStdSizer.AddButton(btnApply)
        btnStdSizer.Realize()
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(item=notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(item=btnSizer, proportion=0,
                      flag=wx.EXPAND, border=0)
        mainSizer.Add(item=btnStdSizer, proportion=0,
                      flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

        self.SetMinSize(self.GetBestSize())
        self.SetSize((500, 375))

    def __CreateGeneralPage(self, notebook):
        """Create notebook page concerning with symbology settings"""
        panel = wx.Panel(parent=notebook, id=wx.ID_ANY)
        notebook.AddPage(page=panel, text=_("General"))

        border = wx.BoxSizer(wx.VERTICAL)
        box   = wx.StaticBox (parent=panel, id=wx.ID_ANY, label=" %s " % _("General settings"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer (hgap=3, vgap=3)
        gridSizer.AddGrowableCol(0)

        #
        # mapsets path
        #
        row = 0
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Mapsets path:")),
                       flag=wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL,
                       pos=(row, 0))
        mapsetPath = wx.Choice(parent=panel, id=wx.ID_ANY, size=(200, -1),
                                    choices=self.settings.Get(group='general', key='mapsetPath',
                                                              subkey='choices', internal=True),
                                    name="GetSelection")
        mapsetPath.SetSelection(self.settings.Get(group='general', key='mapsetPath', subkey='selection'))
        self.winId['general:mapsetPath:selection'] = mapsetPath.GetId()
        
        gridSizer.Add(item=mapsetPath,
                      flag=wx.ALIGN_RIGHT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 1))
        
        sizer.Add(item=gridSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        border.Add(item=sizer, proportion=0, flag=wx.ALL | wx.EXPAND, border=3)

        #
        # Layer Manager settings
        #
        box   = wx.StaticBox (parent=panel, id=wx.ID_ANY, label=" %s " % _("Layer Manager settings"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer (hgap=3, vgap=3)
        gridSizer.AddGrowableCol(0)

        #
        # show opacily level
        #
        row = 0
        changeOpacityLevel = wx.CheckBox(parent=panel, id=wx.ID_ANY,
                                       label=_("Opacity level editable"),
                                       name='IsChecked')
        changeOpacityLevel.SetValue(self.settings.Get(group='general', key='changeOpacityLevel', subkey='enabled'))
        self.winId['general:changeOpacityLevel:enabled'] = changeOpacityLevel.GetId()

        gridSizer.Add(item=changeOpacityLevel,
                      pos=(row, 0), span=(1, 2))
        
        sizer.Add(item=gridSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        border.Add(item=sizer, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=3)

        panel.SetSizer(border)
        
        return panel

    def __CreateDisplayPage(self, notebook):
        """Create notebook page concerning for display settings"""
        panel = wx.Panel(parent=notebook, id=wx.ID_ANY)
        notebook.AddPage(page=panel, text=_("Display"))

        border = wx.BoxSizer(wx.VERTICAL)
        box   = wx.StaticBox (parent=panel, id=wx.ID_ANY, label=" %s " % _("Font settings"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer (hgap=3, vgap=3)
        gridSizer.AddGrowableCol(0)

        #
        # font settings
        #
        row = 0
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Default font for GRASS displays:")),
                      flag=wx.ALIGN_LEFT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 0))
        fontButton = wx.Button(parent=panel, id=wx.ID_ANY,
                               label=_("Set font"), size=(100, -1))
        gridSizer.Add(item=fontButton,
                      flag=wx.ALIGN_RIGHT |
                       wx.ALIGN_CENTER_VERTICAL,
                       pos=(row, 1))

        sizer.Add(item=gridSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        border.Add(item=sizer, proportion=0, flag=wx.ALL | wx.EXPAND, border=3)

        panel.SetSizer(border)
        
        # bindings
        fontButton.Bind(wx.EVT_BUTTON, self.OnSetFont)
        
        return panel

    def __CreateCmdPage(self, notebook):
        """Create notebook page for commad dialog settings"""
        panel = wx.Panel(parent=notebook, id=wx.ID_ANY)
        notebook.AddPage(page=panel, text=_("Command"))

        border = wx.BoxSizer(wx.VERTICAL)
        box   = wx.StaticBox (parent=panel, id=wx.ID_ANY, label=" %s " % _("Command dialog settings"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer (hgap=3, vgap=3)
        gridSizer.AddGrowableCol(0)

        #
        # command dialog settings
        #
        row = 0
        # overwrite
        overwrite = wx.CheckBox(parent=panel, id=wx.ID_ANY,
                                label=_("Allow output files to overwrite existing files"),
                                name="IsChecked")
        overwrite.SetValue(self.settings.Get(group='cmd', key='overwrite', subkey='enabled'))
        self.winId['cmd:overwrite:enabled'] = overwrite.GetId()

        gridSizer.Add(item=overwrite,
                      pos=(row, 0), span=(1, 2))
        row += 1
        # close
        close = wx.CheckBox(parent=panel, id=wx.ID_ANY,
                            label=_("Close dialog on finish"),
                            name="IsChecked")
        close.SetValue(self.settings.Get(group='cmd', key='closeDlg', subkey='enabled'))
        self.winId['cmd:closeDlg:enabled'] = close.GetId()

        gridSizer.Add(item=close,
                      pos=(row, 0), span=(1, 2))
        row += 1
        # verbosity
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Verbosity level:")),
                      flag=wx.ALIGN_LEFT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 0))
        verbosity = wx.Choice(parent=panel, id=wx.ID_ANY, size=(200, -1),
                              choices=self.settings.Get(group='cmd', key='verbosity', subkey='choices', internal=True),
                              name="GetStringSelection")
        verbosity.SetStringSelection(self.settings.Get(group='cmd', key='verbosity', subkey='selection'))
        self.winId['cmd:verbosity:selection'] = verbosity.GetId()

        gridSizer.Add(item=verbosity,
                      pos=(row, 1))

        sizer.Add(item=gridSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        border.Add(item=sizer, proportion=0, flag=wx.ALL | wx.EXPAND, border=3)

        #
        # raster settings
        #
        box   = wx.StaticBox (parent=panel, id=wx.ID_ANY, label=" %s " % _("Raster settings"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer (hgap=3, vgap=3)
        gridSizer.AddGrowableCol(0)

        #
        # raster overlay
        #
        row = 0
        rasterOverlay = wx.CheckBox(parent=panel, id=wx.ID_ANY,
                                    label=_("Overlay raster maps"),
                                    name='IsChecked')
        rasterOverlay.SetValue(self.settings.Get(group='cmd', key='rasterOverlay', subkey='enabled'))
        self.winId['cmd:rasterOverlay:enabled'] = rasterOverlay.GetId()

        gridSizer.Add(item=rasterOverlay,
                      pos=(row, 0), span=(1, 2))
        
        sizer.Add(item=gridSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        border.Add(item=sizer, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=3)

        panel.SetSizer(border)
        
        return panel

    def __CreateAttributeManagerPage(self, notebook):
        """Create notebook page concerning for 'Attribute Table Manager' settings"""
        panel = wx.Panel(parent=notebook, id=wx.ID_ANY)
        notebook.AddPage(page=panel, text=_("Attribute Table Manager"))

        pageSizer = wx.BoxSizer(wx.VERTICAL)

        #
        # highlighting
        #
        highlightBox = wx.StaticBox(parent=panel, id=wx.ID_ANY,
                                    label=" %s " % _("Highlighting"))
        highlightSizer = wx.StaticBoxSizer(highlightBox, wx.VERTICAL)

        flexSizer = wx.FlexGridSizer (cols=2, hgap=5, vgap=5)
        flexSizer.AddGrowableCol(0)
        label = wx.StaticText(parent=panel, id=wx.ID_ANY, label="Color")
        hlColor = csel.ColourSelect(parent=panel, id=wx.ID_ANY,
                                    colour=self.settings.Get(group='atm', key='highlight', subkey='color'),
                                    size=(25, 25))
        self.winId['atm:highlight:color'] = hlColor.GetId()

        flexSizer.Add(label, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        flexSizer.Add(hlColor, proportion=0, flag=wx.ALIGN_RIGHT | wx.FIXED_MINSIZE)

        label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=_("Line width (in pixels)"))
        hlWidth = wx.SpinCtrl(parent=panel, id=wx.ID_ANY, size=(50, -1),
                              initial=self.settings.Get(group='atm', key='highlight',subkey='width'),
                              min=1, max=1e6)
        self.winId['atm:highlight:width'] = hlWidth.GetId()

        flexSizer.Add(label, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        flexSizer.Add(hlWidth, proportion=0, flag=wx.ALIGN_RIGHT | wx.FIXED_MINSIZE)

        highlightSizer.Add(item=flexSizer,
                           proportion=0,
                           flag=wx.ALL | wx.EXPAND,
                           border=5)

        pageSizer.Add(item=highlightSizer,
                      proportion=0,
                      flag=wx.ALL | wx.EXPAND,
                      border=5)

        #
        # data browser related settings
        #
        dataBrowserBox = wx.StaticBox(parent=panel, id=wx.ID_ANY,
                                    label=" %s " % _("Data browser"))
        dataBrowserSizer = wx.StaticBoxSizer(dataBrowserBox, wx.VERTICAL)

        flexSizer = wx.FlexGridSizer (cols=2, hgap=5, vgap=5)
        flexSizer.AddGrowableCol(0)
        label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=_("Left mouse double click"))
        leftDbClick = wx.Choice(parent=panel, id=wx.ID_ANY,
                                choices=self.settings.Get(group='atm', key='leftDbClick', subkey='choices', internal=True),
                                name="GetSelection")
        leftDbClick.SetSelection(self.settings.Get(group='atm', key='leftDbClick', subkey='selection'))
        self.winId['atm:leftDbClick:selection'] = leftDbClick.GetId()

        flexSizer.Add(label, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        flexSizer.Add(leftDbClick, proportion=0, flag=wx.ALIGN_RIGHT | wx.FIXED_MINSIZE)

        dataBrowserSizer.Add(item=flexSizer,
                           proportion=0,
                           flag=wx.ALL | wx.EXPAND,
                           border=5)

        pageSizer.Add(item=dataBrowserSizer,
                      proportion=0,
                      flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
                      border=3)

        panel.SetSizer(pageSizer)

        return panel

    def __CreateAdvancedPage(self, notebook):
        """Create notebook page concerning with symbology settings"""
        panel = wx.Panel(parent=notebook, id=wx.ID_ANY)
        notebook.AddPage(page=panel, text=_("Advanced"))

        border = wx.BoxSizer(wx.VERTICAL)
        box   = wx.StaticBox (parent=panel, id=wx.ID_ANY, label=" %s " % _("Advanced settings"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer (hgap=3, vgap=3)
        gridSizer.AddGrowableCol(0)

        row = 0

        #
        # place where to store settings
        #
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Place where to store settings:")),
                       flag=wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL,
                       pos=(row, 0))
        settingsFile = wx.Choice(parent=panel, id=wx.ID_ANY, size=(125, -1),
                                 choices=self.settings.Get(group='advanced', key='settingsFile',
                                                           subkey='choices', internal=True),
                                 name='GetStringSelection')
        settingsFile.SetStringSelection(self.settings.Get(group='advanced', key='settingsFile', subkey='type'))
        self.winId['advanced:settingsFile:type'] = settingsFile.GetId()

        gridSizer.Add(item=settingsFile,
                      flag=wx.ALIGN_RIGHT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 1))
        row += 1

        #
        # icon theme
        #
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Icon theme:")),
                       flag=wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL,
                       pos=(row, 0))
        iconTheme = wx.Choice(parent=panel, id=wx.ID_ANY, size=(125, -1),
                              choices=self.settings.Get(group='advanced', key='iconTheme',
                                                        subkey='choices', internal=True),
                              name="GetStringSelection")
        iconTheme.SetStringSelection(self.settings.Get(group='advanced', key='iconTheme', subkey='type'))
        self.winId['advanced:iconTheme:type'] = iconTheme.GetId()

        gridSizer.Add(item=iconTheme,
                      flag=wx.ALIGN_RIGHT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 1))
        
        row += 1
        iconNote = wordwrap(_("Note: Requires GUI restart."),
                            self.GetSize()[0]-50, wx.ClientDC(self))

        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=iconNote),
                      flag=wx.ALIGN_LEFT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 0), span=(1, 2))
        row += 1
        
        #
        # digitization interface
        #
        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=_("Digitization interface:")),
                       flag=wx.ALIGN_LEFT |
                       wx.ALIGN_CENTER_VERTICAL,
                       pos=(row, 0))
        digitInterface = wx.Choice(parent=panel, id=wx.ID_ANY, size=(125, -1),
                                   choices=self.settings.Get(group='advanced', key='digitInterface',
                                                             subkey='choices', internal=True),
                                   name="GetStringSelection")
        digitInterface.SetStringSelection(self.settings.Get(group='advanced', key='digitInterface',
                                                            subkey='type'))
        self.winId['advanced:digitInterface:type'] = digitInterface.GetId()

        gridSizer.Add(item=digitInterface,
                      flag=wx.ALIGN_RIGHT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 1))
        row += 1

        digitNote = wordwrap(_("Note: User can choose from two interfaces for digitization. "
                               "The simple one uses v.edit command on the background. "
                               "Map topology is rebuild on each operation which can "
                               "significantly slow-down response. The vdigit is a native "
                               "interface which uses v.edit functionality, but doesn't "
                               "call the module itself."),
                             self.GetSize()[0]-50, wx.ClientDC(self))

        gridSizer.Add(item=wx.StaticText(parent=panel, id=wx.ID_ANY,
                                         label=digitNote),
                      flag=wx.ALIGN_LEFT |
                      wx.ALIGN_CENTER_VERTICAL,
                      pos=(row, 0), span=(1, 2))

        sizer.Add(item=gridSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        border.Add(item=sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=3)

        panel.SetSizer(border)
        
        return panel

    def OnSetFont(self, event):
        """'Set font' button pressed"""
        dlg = SetDefaultFont(parent=self, id=wx.ID_ANY,
                             title=_('Select default display font'),
                             pos=wx.DefaultPosition, size=wx.DefaultSize,
                             style=wx.DEFAULT_DIALOG_STYLE,
                             encoding=self.parent.encoding)
        if dlg.ShowModal() == wx.ID_CANCEL:
            dlg.Destroy()
            return

        # set default font type, font, and encoding to whatever selected in dialog
        if dlg.font != None:
            self.font = dlg.font
        if dlg.encoding != None:
            self.encoding = dlg.encoding

        dlg.Destroy()

        # set default font and encoding environmental variables
        os.environ["GRASS_FONT"] = self.font
        if self.encoding != None and self.encoding != "ISO-8859-1":
            os.environ["GRASS_ENCODING"] = self.encoding

        event.Skip()

    def OnSave(self, event):
        """Button 'Save' pressed"""
        self.__UpdateSettings()
        file = self.settings.SaveToFile()
        self.parent.goutput.cmd_stdout.write(_('Settings saved to file \'%s\'.') % file)
        self.Close()

    def OnApply(self, event):
        """Button 'Apply' pressed"""
        self.__UpdateSettings()
        self.Close()

    def OnCancel(self, event):
        """Button 'Cancel' pressed"""
        self.Close()

    def OnDefault(self, event):
        """Button 'Set to default' pressed"""
        self.settings.userSettings = copy.deepcopy(self.settings.defaultSettings)
        
        # update widgets
        for gks in self.winId.keys():
            group, key, subkey = gks.split(':')
            value = self.settings.Get(group, key, subkey)
            win = self.FindWindowById(self.winId[gks])
            if win.GetName() in ('GetValue', 'IsChecked'):
                value = win.SetValue(value)
            elif win.GetName() == 'GetSelection':
                value = win.SetSelection(value)
            elif win.GetName() == 'GetStringSelection':
                value = win.SetStringSelection(value)
            else:
                value = win.SetValue(value)


    def __UpdateSettings(self):
        """Update user settings"""
        for item in self.winId.keys():
            group, key, subkey = item.split(':')
            id = self.winId[item]
            win = self.FindWindowById(id)
            if win.GetName() == 'GetValue':
                value = win.GetValue()
            elif win.GetName() == 'GetSelection':
                value = win.GetSelection()
            elif win.GetName() == 'IsChecked':
                value = win.IsChecked()
            elif win.GetName() == 'GetStringSelection':
                value = win.GetStringSelection()
            else:
                value = win.GetValue()
            self.settings.Set(group, key, subkey, value)

class SetDefaultFont(wx.Dialog):
    """
    Opens a file selection dialog to select default font
    to use in all GRASS displays
    """
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE, encoding='ISO-8859-1'):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        if "GRASS_FONT" in os.environ:
            self.font = os.environ["GRASS_FONT"]
        else:
            self.font = None

        self.fontlist = self.GetFonts()

        self.encoding = encoding

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Select Font:", (15, 50))
        box.Add(label, 0, wx.EXPAND|wx.GROW|wx.ALIGN_TOP|wx.RIGHT, 5)
        self.fontlb = wx.ListBox(self, wx.ID_ANY, pos=wx.DefaultPosition,
                                 size=(280,150), choices=self.fontlist,
                                 style=wx.LB_SINGLE|wx.LB_SORT)
        self.Bind(wx.EVT_LISTBOX, self.EvtListBox, self.fontlb)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.EvtListBoxDClick, self.fontlb)
        if self.font:
            self.fontlb.SetStringSelection(self.font, True)
        box.Add(self.fontlb, 0, wx.EXPAND|wx.GROW|wx.ALIGN_RIGHT)
        sizer.Add(box, 0, wx.EXPAND|wx.GROW|wx.ALIGN_RIGHT|wx.ALL, 8)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Character encoding:")
        box.Add(label, 0, wx.ALIGN_RIGHT|wx.RIGHT, 5)
        self.textentry = wx.TextCtrl(self, -1, "", size=(200,-1))
        self.textentry.SetValue(self.encoding)
        box.Add(self.textentry, 0, wx.ALIGN_LEFT)
        self.textentry.Bind(wx.EVT_TEXT, self.OnEncoding)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 8)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)

        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def EvtRadioBox(self, event):
        if event.GetInt() == 0:
            self.fonttype = 'grassfont'
        elif event.GetInt() == 1:
            self.fonttype = 'truetype'

        self.fontlist = self.GetFonts(self.fonttype)
        self.fontlb.SetItems(self.fontlist)

    def OnEncoding(self, event):
        self.encoding = event.GetString()

    def EvtListBox(self, event):
        self.font = event.GetString()
        event.Skip()

    def EvtListBoxDClick(self, event):
        self.font = event.GetString()
        event.Skip()

    def GetFonts(self):
        """
        parses fonts directory or fretypecap file to get a list of fonts for the listbox
        """
        fontlist = []

        cmd = ["d.font", "-l"]

        p = gcmd.Command(cmd, stderr=None)

        dfonts = p.ReadStdOutput()
        dfonts.sort(lambda x,y: cmp(x.lower(), y.lower()))
        for item in range(len(dfonts)):
           # ignore duplicate fonts and those starting with #
           if not dfonts[item].startswith('#') and \
                  dfonts[item] != dfonts[item-1]:
              fontlist.append(dfonts[item])

        return fontlist

class MapsetAccess(wx.Dialog):
    """
    Controls setting options and displaying/hiding map overlay decorations
    """
    def __init__(self, parent, id, title=_('Set/unset access to mapsets in current location'),
                 pos=wx.DefaultPosition, size=(-1, -1),
                 style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        self.all_mapsets, self.accessible_mapsets = utils.ListOfMapsets()
        self.curr_mapset = grassenv.GetGRASSVariable('MAPSET')

        # make a checklistbox from available mapsets and check those that are active
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(parent=self, id=wx.ID_ANY,
                              label=_("Check mapset to make it accessible, uncheck it to hide it.%s"
                                      "Note: PERMANENT and current mapset are always accessible.") % os.linesep)
        sizer.Add(item=label, proportion=0,
                  flag=wx.ALL, border=5)

        self.mapsetlb = wx.CheckListBox(parent=self, id=wx.ID_ANY, pos=wx.DefaultPosition,
                                        size=(350,200), choices=self.all_mapsets)
        self.mapsetlb.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckMapset)
        
        sizer.Add(item=self.mapsetlb, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=5)

        # check all accessible mapsets
        if globalSettings.Get(group='general', key='mapsetPath', subkey='selection') == 1:
            for mset in self.all_mapsets:
                self.mapsetlb.Check(self.all_mapsets.index(mset), True)
        else:
            for mset in self.accessible_mapsets:
                self.mapsetlb.Check(self.all_mapsets.index(mset), True)

        # dialog buttons
        line = wx.StaticLine(parent=self, id=wx.ID_ANY,
                             style=wx.LI_HORIZONTAL)
        sizer.Add(item=line, proportion=0,
                  flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL, border=5)

        btnsizer = wx.StdDialogButtonSizer()
        okbtn = wx.Button(self, wx.ID_OK)
        okbtn.SetDefault()
        btnsizer.AddButton(okbtn)

        cancelbtn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(cancelbtn)
        btnsizer.Realize()

        sizer.Add(item=btnsizer, proportion=0,
                  flag=wx.EXPAND | wx.ALIGN_RIGHT | wx.ALL, border=5)

        # do layout
        self.Layout()
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.SetMinSize(self.GetBestSize())
        
    def OnCheckMapset(self, event):
        """Mapset checked/unchecked"""
        mapset = self.mapsetlb.GetString(event.GetSelection())
        if mapset == 'PERMANENT' or mapset == self.curr_mapset:
            self.mapsetlb.Check(event.GetSelection(), True)
        
    def GetMapsets(self):
        """Get list of checked mapsets"""
        ms = []
        i = 0
        for mset in self.all_mapsets:
            if self.mapsetlb.IsChecked(i):
                ms.append(mset)
            i += 1

        return ms
