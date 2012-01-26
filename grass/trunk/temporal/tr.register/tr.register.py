#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	tr.register
# AUTHOR(S):	Soeren Gebbert
#
# PURPOSE:	Register raster maps in a space time raster dataset
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Register raster maps in a space time raster dataset
#% keywords: spacetime raster dataset
#% keywords: raster
#%end

#%option
#% key: input
#% type: string
#% description: Name of an existing space time raster dataset
#% required: yes
#% multiple: no
#%end

#%option
#% key: maps
#% type: string
#% description: Name(s) of existing raster map(s)
#% required: no
#% multiple: yes
#%end

#%option
#% key: file
#% type: string
#% description: Input file with raster map names, one per line. Additionally the start time and the end time can be specified per line
#% required: no
#% multiple: no
#%end

#%option
#% key: start
#% type: string
#% description: The valid start date and time of the first raster map, in case the map has no valid time (format absolute: "yyyy-mm-dd HH:MM:SS", format relative 5.0). Use "file" as identifier in case the start time is located in an input file
#% required: no
#% multiple: no
#%end

#%option
#% key: end
#% type: string
#% description: The valid end date and time of the first raster map. Absolute time format is "yyyy-mm-dd HH:MM:SS" and "yyyy-mm-dd", relative time format id double. Use "file" as identifier in case the end time is located in the input file 
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
#% type: string
#% description: Time increment between maps for valid time interval creation (format absolute: NNN seconds, minutes, hours, days, weeks, months, years; format relative is integer: 5), or "file" in case the increment is located in an input file
#% required: no
#% multiple: no
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
    name = options["input"]
    maps = options["maps"]
    file = options["file"]
    fs = options["fs"]
    start = options["start"]
    end = options["end"]
    unit = options["unit"]
    increment = options["increment"]
    interval = flags["i"]

    # Make sure the temporal database exists
    tgis.create_temporal_database()
    # Register maps
    tgis.register_maps_in_space_time_dataset(type="strds", name=name, maps=maps, layer=None, file=file, start=start, end=end, \
                                             unit=unit, increment=increment, dbif=None, interval=interval, fs=fs)
    
if __name__ == "__main__":
    options, flags = grass.parser()
    main()

