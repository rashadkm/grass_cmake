#!/usr/bin/env python
############################################################################
#
# MODULE:    g.gui.tplot.py
# AUTHOR(S): Luca Delucchi
# PURPOSE:   Temporal Plot Tool is a wxGUI component (based on matplotlib)
#            the user to see in a plot the values of one or more temporal
#            datasets for a queried point defined by a coordinate pair.
# COPYRIGHT: (C) 2014 by Luca Delucchi, and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

#%module
#% description: Allows the user to see in a plot the values of one or more temporal raser datasets for a queried point defined by a coordinate pair. Also allows to plot data of vector dataset for a defined categories and attribut.
#% keywords: general
#% keywords: GUI
#% keywords: temporal
#%end

#%option G_OPT_STVDS_INPUTS
#% key: stvds
#% required: no
#%end

#%option G_OPT_STRDS_INPUTS
#% key: strds
#% required: no
#%end

#%option G_OPT_M_COORDS
#% required: no
#%end

#TODO use option G_OPT_V_CATS
#%option
#% key: cats
#% label: Categories of vectores features
#% description: To use only with stvds
#% required: no
#%end


#%option
#% key: attr
#% label: Name of attribute
#% description: Name of attribute which represent data for plotting
#% required: no
#%end

#%option G_OPT_F_OUTPUT
#% required: no
#% label: Name for output file
#% description: Add extension to specify format (.png, .pdf, .svg)
#%end

#%option
#% key: size
#% type: string
#% label: The size for output image
#% description: It works only with output parameter
#% required: no
#%end

import grass.script as gscript
from core.giface import StandaloneGrassInterface


def main():
    options, flags = gscript.parser()

    import wx
    from core.utils import _
    try:
        from tplot.frame import TplotFrame
    except ImportError as e:
        gscript.fatal(e.message)
    rasters = None
    if options['strds']:
        rasters = options['strds'].strip().split(',')
    vectors = None
    attr = None
    if options['stvds']:
        vectors = options['stvds'].strip().split(',')
        if not options['attr']:
            gscript.fatal(_("With stvds you have to use also 'attr' option"))
        else:
            attr = options['attr']
    coords = options['coordinates'].strip().split(',')
    output = options['output']

    app = wx.App()
    frame = TplotFrame(parent=None, giface=StandaloneGrassInterface())
    frame.SetDatasets(rasters, vectors, coords, None, attr)
    if output:
        frame.OnRedraw()
        if options['size']:
            sizes = options['size'].strip().split(',')
            sizes = [int(s) for s in sizes]
            frame.canvas.SetSize(sizes)
        if output.split('.')[-1].lower() == 'png':
            frame.canvas.print_png(output)
        if output.split('.')[-1].lower() in ['jpg', 'jpeg']:
            frame.canvas.print_jpg(output)
        if output.split('.')[-1].lower() in ['tif', 'tiff']:
            frame.canvas.print_tif(output)
    else:
        frame.Show()
        app.MainLoop()

if __name__ == '__main__':
    main()
