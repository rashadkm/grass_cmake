#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	t.rast.list
# AUTHOR(S):	Soeren Gebbert
#               
# PURPOSE:	List registered maps of a space time raster dataset 
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: List registered maps of a space time raster dataset 
#% keywords: temporal
#% keywords: raster
#% keywords: list
#%end

#%option G_OPT_STRDS_INPUT
#%end

#%option
#% key: order
#% type: string
#% description: Order the space time dataset by category. 
#% required: no
#% multiple: yes
#% options: id,name,creator,mapset,temporal_type,creation_time,start_time,end_time,north,south,west,east,nsres,ewres,cols,rows,number_of_cells,min,max 
#% answer: start_time
#%end

#%option
#% key: columns
#% type: string
#% description: Select columns to be printed to stdout 
#% required: no
#% multiple: yes
#% options: id,name,creator,mapset,temporal_type,creation_time,start_time,end_time,north,south,west,east,nsres,ewres,cols,rows,number_of_cells,min,max 
#% answer: name,mapset,start_time,end_time
#%end

#%option G_OPT_T_WHERE
#%end

#%option
#% key: method
#% type: string
#% description: Which method should be used for data listing
#% required: no
#% multiple: no
#% options: cols,comma,delta,deltagaps,gran
#% answer: cols
#%end

#%option
#% key: fs
#% type: string
#% description: The field separator character between the columns, default is tabular "\t"
#% required: no
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
    columns = options["columns"]
    order = options["order"]
    where = options["where"]
    separator = options["fs"]
    method = options["method"]
    header = flags["h"]

    # Make sure the temporal database exists
    tgis.create_temporal_database()

    tgis.list_maps_of_stds("strds", input, columns, order, where, separator, method, header)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
