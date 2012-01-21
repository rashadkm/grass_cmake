#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	t.time.rel
# AUTHOR(S):	Soeren Gebbert
#
# PURPOSE:	Set the relative valid time point or interval for maps of type raster, vector and raster3d
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Set the relative valid time point or interval for maps of type raster, vector and raster3d
#% keywords: time
#% keywords: absolute
#% keywords: raster
#% keywords: vector
#% keywords: raster3d
#%end

#%option
#% key: input
#% type: string
#% description: Name(s) of existing raster, raster3d or vector map(s)
#% required: no
#% multiple: yes
#%end

#%option
#% key: start
#% type: integer
#% description: The valid integer start value for all maps, or file in case the start time is located in the input file 
#% required: no
#% multiple: no
#%end

#%option
#% key: end
#% type: integer
#% description: The valid integer end value for all maps, or file in case the start time is located in the input file 
#% required: no
#% multiple: no
#%end

#%option
#% key: unit
#% type: string
#% description: The unit of the relative time
#% required: no
#% multiple: no
#% options: years,months,days,hours,minutes,seconds
#% answer: days
#%end

#%option
#% key: increment
#% type: integer
#% description: Increment between maps for valid time interval creation 
#% required: no
#% multiple: no
#%end

#%option
#% key: file
#% type: string
#% description: Input file with map names, one per line
#% required: no
#% multiple: no
#%end

#%option
#% key: type
#% type: string
#% description: Input map type
#% required: no
#% options: rast,rast3d,vect
#% answer: rast
#%end

#%option
#% key: fs
#% type: string
#% description: The field separator character of the input file
#% required: no
#% answer: |
#%end

#%flag
#% key: i
#% description: Create an interval (start and end time) in case an increment is provided
#%end

import grass.script as grass
import grass.temporal as tgis

############################################################################

def main():

    # Get the options
    maps = options["input"]
    file = options["file"]
    start = options["start"]
    end = options["end"]
    increment = options["increment"]
    fs = options["fs"]
    type = options["type"]
    unit = options["unit"]
    interval = flags["i"]

    # Make sure the temporal database exists
    tgis.create_temporal_database()
    # Set valid absolute time to maps
    tgis.assign_valid_time_to_maps(type=type, maps=maps, ttype="relative", \
                                   start=start, end=end, unit=unit, file=file, increment=increment, \
                                   dbif=None, interval=interval, fs=fs)
    
if __name__ == "__main__":
    options, flags = grass.parser()
    main()

