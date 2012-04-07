#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:	t.remove
# AUTHOR(S):	Soeren Gebbert
#               
# PURPOSE:	Remove space time datasets from the temporal database
# COPYRIGHT:	(C) 2011 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Remove space time datasets from temporal database
#% keywords: temporal
#% keywords: remove
#%end

#%option G_OPT_STDS_INPUT
#% required: no
#%end

#%option
#% key: file
#% type: string
#% description: Input file with dataset names, one per line
#% required: no
#% multiple: no
#%end

#%option
#% key: type
#% type: string
#% description: Type of the space time dataset, default is strds
#% required: no
#% options: strds, str3ds, stvds
#% answer: strds
#%end

import grass.script as grass
import grass.temporal as tgis

############################################################################

def main():
    
    # Get the options
    datasets = options["input"]
    file = options["file"]
    type = options["type"]

    if datasets and file:
        core.fata(_("%s= and %s= are mutually exclusive") % ("input","file"))

    # Make sure the temporal database exists
    tgis.create_temporal_database()

    dbif = tgis.sql_database_interface_connection()
    dbif.connect()

    dataset_list = []

    # Dataset names as comma separated string
    if datasets:
        if datasets.find(",") == -1:
            dataset_list = (datasets,)
        else:
            dataset_list = tuple(datasets.split(","))

    # Read the dataset list from file
    if file:
        fd = open(file, "r")

        line = True
        while True:
            line = fd.readline()
            if not line:
                break

            line_list = line.split("\n")
            dataset_name = line_list[0]
            dataset_list.append(dataset_name)
    
    mapset =  grass.gisenv()["MAPSET"]
    
    statement = ""

    for name in dataset_list:
        name = name.strip()
        # Check for the mapset in name
        if name.find("@") < 0:
            id = name + "@" + mapset
        else:
            id = name

        sp = tgis.dataset_factory(type, id)

        if sp.is_in_db(dbif) == False:
            dbif.close()
            grass.fatal(_("Space time %s dataset <%s> not found") % (sp.get_new_map_instance(None).get_type(), id))

        statement += sp.delete(dbif=dbif, execute=False)

    # Execute the collected SQL statenents
    dbif.execute_transaction(statement)

    dbif.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    main()

