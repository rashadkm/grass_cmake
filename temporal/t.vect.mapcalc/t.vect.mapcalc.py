#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.vect.mapcalc
# AUTHOR(S):    Thomas Leppelt, Soeren Gebbert
#
# PURPOSE:      Provide temporal vector algebra to perform spatial an temporal operations
#               for space time datasets by topological relationships to other space time
#               datasets.
# COPYRIGHT:    (C) 2014 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Apply temporal and spatial oeprations on space time vector datasets using temporal vector algebra.
#% keywords: temporal
#% keywords: mapalgebra
#%end

#%option
#% key: expression
#% type: string
#% description: The mapcalc expression for temporal and spatial analysis of space time vector datasets.
#% key_desc: expression
#% required : yes
#%end

#%option
#% key: basename
#% type: string
#% description: The basename of vector maps that are stored within the result space time vector dataset.
#% key_desc: basename
#% required : yes
#%end

#%flag
#% key: s
#% description: Activate spatial topology.
#%end

import grass.script as grass
import grass.temporal as tgis
import sys

def main():
    expression = options['expression']
    basename = options['basename']
    spatial = flags["s"]
    stdstype = "stvds"

    # Check for PLY istallation
    try:
        import ply.lex as lex
        import ply.yacc as yacc
    except:
        grass.fatal(_("Please install PLY (Lex and Yacc Python implementation) to use the temporal algebra modules."))

    tgis.init(True)
    p = tgis.TemporalVectorAlgebraParser(run = True, debug=False, spatial = spatial)
    p.parse(expression, stdstype, basename)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

