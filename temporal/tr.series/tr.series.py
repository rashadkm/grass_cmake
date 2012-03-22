#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	tr.series
# AUTHOR(S):	Soeren Gebbert
#
# PURPOSE:	Perform different aggregation algorithms from r.series on all or a selected subset of raster maps in a space time raster dataset
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Perform different aggregation algorithms from r.series on all or a subset of raster maps in a space time raster dataset
#% keywords: temporal
#% keywords: series
#%end

#%option G_OPT_STRDS_INPUT
#%end

#%option
#% key: method
#% type: string
#% description: Aggregate operation to be peformed on the raster maps
#% required: yes
#% multiple: no
#% options: average,count,median,mode,minimum,min_raster,maximum,max_raster,stddev,range,sum,variance,diversity,slope,offset,detcoeff,quart1,quart3,perc90,quantile,skewness,kurtosis
#% answer: average
#%end

#%option
#% key: order
#% type: string
#% description: Sort the maps by category.
#% required: no
#% multiple: yes
#% options: id, name, creator, mapset, creation_time, modification_time, start_time, end_time, north, south, west, east, min, max
#% answer: id
#%end

#%option G_OPT_T_WHERE
#%end

#%option G_OPT_R_OUTPUT
#%end

#%flag
#% key: t
#% description: Assign the space time raster dataset start and end time to the output map
#%end

import grass.script as grass
import grass.temporal as tgis

############################################################################

def main():

    # Get the options
    input = options["input"]
    output = options["output"]
    method = options["method"]
    order = options["order"]
    where = options["where"]
    add_time = flags["t"]

    # Make sure the temporal database exists
    tgis.create_temporal_database()

    if input.find("@") >= 0:
        id = input
    else:
        mapset =  grass.gisenv()["MAPSET"]
        id = input + "@" + mapset

    sp = tgis.space_time_raster_dataset(id)

    if sp.is_in_db() == False:
        grass.fatal(_("Space time raster dataset <%s> not found in temporal database") % (id))

    sp.select()

    rows = sp.get_registered_maps("id", where, order, None)

    if rows:
        # Create the r.series input file
        filename = grass.tempfile(True)
        file = open(filename, 'w')

        for row in rows:
            string = "%s\n" % (row["id"])
            file.write(string)
        
        file.close()

        ret = grass.run_command("r.series", flags="z", file=filename, output=output, overwrite=grass.overwrite(), method=method)

        if ret == 0 and add_time:
            if sp.is_time_absolute():
                start_time, end_time, tz = sp.get_absolute_time()
            else:
                start_time, end_time = sp.get_relative_time()
                
            # Create the time range for the output map
            if output.find("@") >= 0:
                id = output
            else:
                mapset =  grass.gisenv()["MAPSET"]
                id = output + "@" + mapset

            map = sp.get_new_map_instance(id)
            map.load()

            if sp.is_time_absolute():
                map.set_absolute_time(start_time, end_time, tz)
                map.write_absolute_time_to_file()
            else:
                map.set_relative_time(start_time, end_time)
                map.write_relative_time_to_file()

            # Register the map in the temporal database
            if map.is_in_db():
                map.update()
            else:
                map.insert()

if __name__ == "__main__":
    options, flags = grass.parser()
    main()

