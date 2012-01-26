#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	tr.out.vtk
# AUTHOR(S):	Soeren Gebbert
#               
# PURPOSE:	Export space time raster dataset as VTK time series
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Export space time raster dataset as VTK time series
#% keywords: dataset
#% keywords: spacetime
#% keywords: raster
#% keywords: export
#% keywords: VTK
#%end

#%option
#% key: input
#% type: string
#% description: Name of a space time raster dataset
#% required: yes
#% multiple: no
#%end

#%option
#% key: expdir
#% type: string
#% description: Path to the export directory
#% required: yes
#% multiple: no
#%end

#%option G_OPT_R_INPUT
#% key: elevation
#% type: string
#% description: Elevation raster map
#% required: no
#% multiple: no
#%end

#%option
#% key: where
#% type: string
#% description: A where statement for selected listing e.g: (start_time < '2001-01-01' and end_time > '2001-01-01')
#% required: no
#% multiple: no
#%end

#%option
#% key: null
#% type: double
#% description: Value to represent no data cell
#% required: no
#% multiple: no
#% answer: -10.0
#%end

#%flag
#% key: p
#% description: Create VTK point data instead of VTK cell data (if no elevation map is given)
#%end

#%flag
#% key: c
#% description: Correct the coordinates to fit the VTK-OpenGL precision
#%end

#%flag
#% key: g
#% description: Export files using the space time dataset granularity for equidistant time between maps, where statement will be ignored
#%end



import os
import grass.script as grass
import grass.temporal as tgis

############################################################################

def main():

    # Get the options
    input = options["input"]
    elevation = options["elevation"]
    expdir = options["expdir"]
    where = options["where"]
    null = options["null"]
    use_pdata = flags["p"]
    coorcorr = flags["c"]
    use_granularity = flags["g"]

    # Make sure the temporal database exists
    tgis.create_temporal_database()

    if not os.path.exists(expdir): 
        grass.fatal(_("Export directory <%s> not found.") % expdir)

    os.chdir(expdir)

    mapset =  grass.gisenv()["MAPSET"]

    if input.find("@") >= 0:
        id = input
    else:
        id = input + "@" + mapset

    sp = tgis.space_time_raster_dataset(id)
    
    if sp.is_in_db() == False:
        grass.fatal(_("Dataset <%s> not found in temporal database") % (id))

    sp.select()

    if use_granularity:
	# Attention: A list of lists of maps will be returned
        maps = sp.get_registered_maps_as_objects_by_granularity()
        # Create a NULL map in case of granularity support
        null_map = "temporary_null_map_%i" % os.getpid()
        grass.mapcalc("%s = null()" % (null_map))
    else:
        maps = sp.get_registered_maps_as_objects(where, "start_time", None)

    # To have scalar values with the same name, we need to copy the raster maps using a single name
    map_name = "%s_%i" % (sp.base.get_name(), os.getpid())

    count = 0
    if maps:
        for map in maps:
	    if use_granularity:
		id = map[0].get_map_id()
	    else:
		id = map.get_map_id()
            # None ids will be replaced by NULL maps
            if id == None:
                id = null_map
            
            grass.run_command("g.copy", rast="%s,%s" % (id, map_name), overwrite=True)
            out_name = "%6.6i_%s.vtk" % (count, sp.base.get_name()) 

            mflags=""
            if use_pdata:
                mflags += "p"
            if coorcorr:
                mflags += "c"

            # Export the raster map with r.out.vtk
            if elevation:
                ret = grass.run_command("r.out.vtk", flags=mflags, null=null, input=map_name, elevation=elevation, output=out_name, overwrite=grass.overwrite())
            else:
                ret = grass.run_command("r.out.vtk", flags=mflags, null=null, input=map_name, output=out_name, overwrite=grass.overwrite())

            if ret != 0:
                grass.fatal(_("Unable to export raster map <%s>" % name))

            count += 1

    if use_granularity:
        grass.run_command("g.remove", rast=null_map)
    grass.run_command("g.remove", rast=map_name)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
