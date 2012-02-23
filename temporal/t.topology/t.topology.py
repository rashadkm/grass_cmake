#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	t.topology
# AUTHOR(S):	Soeren Gebbert
#               
# PURPOSE:	List and modify temporal topology of a space time dataset
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: List and modify temporal topology of a space time dataset
#% keywords: temporal
#% keywords: topology
#%end

#%option G_OPT_STDS_INPUT
#%end

#%option G_OPT_STDS_TYPE
#%end

#%option G_OPT_T_WHERE
#%end

#%flag
#% key: m
#% description: Print temporal relation matrix and exit
#%end

import grass.script as grass
import grass.temporal as tgis

############################################################################

def main():

    # Get the options
    name = options["input"]
    type = options["type"]
    where = options["where"]
    tmatrix = flags['m']

    # Make sure the temporal database exists
    tgis.create_temporal_database()

    #Get the current mapset to create the id of the space time dataset
    if name.find("@") >= 0:
        id = name
    else:
        mapset =  grass.gisenv()["MAPSET"]
        id = name + "@" + mapset

    sp = tgis.dataset_factory(type, id)

    if sp.is_in_db() == False:
        grass.fatal("Dataset <" + name + "> not found in temporal database")
        
    # Insert content from db
    sp.select()

    # Get ordered map list
    maps = sp.get_registered_maps_as_objects(where=where, order="start_time", dbif=None)

    if tmatrix:
        matrix = sp.print_temporal_relation_matrix(maps)
        return

    sp.base.print_info()

    #      0123456789012345678901234567890
    print " +-------------------- Temporal topology -------------------------------------+"
    if where:
        print " | Is subset of dataset: ...... True"
    else:
        print " | Is subset of dataset: ...... False"

    check = sp.check_temporal_topology(maps)
    if check:
        #      0123456789012345678901234567890
        print " | Temporal topology is: ...... valid"                
    else:
        #      0123456789012345678901234567890
        print " | Temporal topology is: ...... invalid"                

    dict = sp.count_temporal_types(maps)
 
    for key in dict.keys():
        if key == "interval":
            #      0123456789012345678901234567890
            print " | Number of intervals: ....... %s" % (dict[key])
        if key == "point":
            print " | Number of points: .......... %s" % (dict[key])
        if key == "invalid":
            print " | Invalid time stamps: ....... %s" % (dict[key])

    #      0123456789012345678901234567890
    print " | Number of gaps: ............ %i" % sp.count_gaps(maps)                

    if sp.is_time_absolute():
        gran = tgis.compute_absolute_time_granularity(maps)
    else:
        gran = tgis.compute_relative_time_granularity(maps)
    print " | Granularity: ............... %s" % str(gran)

    print " +-------------------- Topological relations ---------------------------------+"
    dict = sp.count_temporal_relations(maps)

    for key in dict.keys():
        if key == "equivalent":
            #      0123456789012345678901234567890
            print " | Equivalent: ................ %s" % (dict[key])
        if key == "during":
            print " | During: .................... %s" % (dict[key])
        if key == "contains":
            print " | Contains: .................. %s" % (dict[key])
        if key == "overlaps":
            print " | Overlaps: .................. %s" % (dict[key])
        if key == "overlapped":
            print " | Overlapped: ................ %s" % (dict[key])
        if key == "after":
            print " | After: ..................... %s" % (dict[key])
        if key == "before":
            print " | Before: .................... %s" % (dict[key])
        if key == "starts":
            print " | Starts: .................... %s" % (dict[key])
        if key == "finishes":
            print " | Finishes: .................. %s" % (dict[key])
        if key == "started":
            print " | Started: ................... %s" % (dict[key])
        if key == "finished":
            print " | Finished: .................. %s" % (dict[key])
        if key == "follows":
            print " | Follows: ................... %s" % (dict[key])
        if key == "precedes":
            print " | Precedes: .................. %s" % (dict[key])
    print " +----------------------------------------------------------------------------+"

if __name__ == "__main__":
    options, flags = grass.parser()
    main()

