#!/usr/bin/env python
#
############################################################################
#
# MODULE:       v.db.update
# AUTHOR(S):    Moritz Lennert
#               extensions by Markus Neteler
#               Converted to Python by Glynn Clements
# PURPOSE:      interface to db.execute to update a column in the attribute table connected to a given map
# COPYRIGHT:    (C) 2005,2007,2008 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#%  description: Allows to update a column in the attribute table connected to a vector map.
#%  keywords: vector, database, attribute table
#%End
#%option
#% key: map
#% type: string
#% gisprompt: old,vector,vector
#% description: Vector map to edit the attribute table for
#% required : yes
#%end
#%option
#% key: layer
#% type: integer
#% gisprompt: old_layer,layer,layer
#% description: Layer to which the table to be changed is connected
#% answer: 1
#% required : no
#%end
#%option
#% key: column
#% type: string
#% gisprompt: old_dbcolumn,dbcolumn,dbcolumn
#% description: Column to update
#% required : yes
#%end
#%option
#% key: value
#% type: string
#% description: Value to update the column with, can be (combination of) other column(s)
#% required : no
#%end
#%option
#% key: qcolumn
#% type: string
#% gisprompt: old_dbcolumn,dbcolumn,dbcolumn
#% description: Column to query
#% required : no
#%end
#%option
#% key: where
#% type: string
#% description: WHERE conditions for update, without 'where' keyword (e.g. cat=1 or col1/col2>1)
#% required : no
#%end

import sys
import os
from grass.script import all as grass

def main():
    map = options['map']
    layer = options['layer']
    column = options['column']
    value = options['value']
    qcolumn = options['qcolumn']
    where = options['where']

    mapset = grass.gisenv()['MAPSET']

    # does map exist in CURRENT mapset?
    if not grass.find_file(map, element = 'vector', mapset = mapset)['file']:
	grass.fatal("Vector map '$GIS_OPT_MAP' not found in current mapset")

    try:
        f = grass.vector_db(map)[int(layer)]
    except KeyError:
	grass.fatal('There is no table connected to this map. Run v.db.connect or v.db.addtable first.')

    table = f['table']
    database = f['database']
    driver = f['driver']

    # checking column types
    try:
        coltype = grass.vector_columns(map, layer)[column]
    except KeyError:
	grass.fatal('Column <%s> not found' % column)

    if qcolumn:
	if value:
	    grass.fatal('value= and qcolumn= are mutually exclusive')
	# special case: we copy from another column
	value = qcolumn
    else:
	if not value:
	    grass.fatal('Either value= or qcolumn= must be given')
	# we insert a value
	if coltype.upper() not in ["INTEGER", "DOUBLE PRECISION"]:
	    value = "'%s'" % value

    cmd = "UPDATE %s SET %s=%s" % (table, column, value)
    if where:
	cmd += " WHERE " + where

    grass.write_command('db.execute', database = database, driver = driver, stdin = cmd)

    # write cmd history:
    grass.vector_history(map)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
