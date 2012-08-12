#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	t.rast.univar
# AUTHOR(S):	Soeren Gebbert
#
# PURPOSE:	Calculates univariate statistics from the non-null cells for each registered raster map of a space time raster dataset
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Calculates univariate statistics from the non-null cells for each registered raster map of a space time raster dataset.
#% keywords: temporal
#% keywords: statistics
#% keywords: raster
#%end

#%option G_OPT_STRDS_INPUT
#%end

#%option G_OPT_T_WHERE
#%end

#%option
#% key: fs
#% type: string
#% description: Field separator character between the output columns
#% required: no
#% answer: |
#%end

#%flag
#% key: e
#% description: Calculate extended statistics
#%end

#%flag
#% key: h
#% description: Print column names
#%end

import grass.script as grass
import grass.temporal as tgis

############################################################################


def main():

    # Get the options
    input = options["input"]
    where = options["where"]
    extended = flags["e"]
    header = flags["h"]
    fs = options["fs"]

    # Make sure the temporal database exists
    tgis.create_temporal_database()

    tgis.print_gridded_dataset_univar_statistics(
        "strds", input, where, extended, header, fs)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
