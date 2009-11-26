#!/usr/bin/env python

############################################################################
#
# MODULE:       v.db.join
# AUTHOR(S):    Markus Neteler
#               Converted to Python by Glynn Clements
# PURPOSE:      Join a table to a map table
# COPYRIGHT:    (C) 2007-2009 by Markus Neteler and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Allows to join a table to a vector map table.
#% keywords: vector
#% keywords: database
#% keywords: attribute table
#%End

#%option
#% key: map
#% type: string
#% key_desc : name
#% gisprompt: old,vector,vector
#% description: Vector map to which to join other table
#% required : yes
#% guidependency: layer,column
#%end

#%option
#% key: layer
#% type: integer
#% description: Layer where to join
#% answer: 1
#% required : no
#% gisprompt: old_layer,layer,layer
#% guidependency: column
#%end

#%option
#% key: column
#% type: string
#% description: Join column in map table
#% required : yes
#% gisprompt: old_dbcolumn,dbcolumn,dbcolumn
#%end

#%option
#% key: otable
#% type: string
#% description: Other table name
#% required : yes
#% gisprompt: old_dbtable,dbtable,dbtable
#% guidependency: ocolumn
#%end

#%option
#% key: ocolumn
#% type: string
#% description: Join column in other table
#% required : yes
#% gisprompt: old_dbcolumn,dbcolumn,dbcolumn
#%end

import sys
import os
import string
import grass.script as grass

def main():
    map = options['map']
    layer = options['layer']
    column = options['column']
    otable = options['otable']
    ocolumn = options['ocolumn']

    f = grass.vector_layer_db(map, layer)

    maptable = f['table']
    database = f['database']
    driver = f['driver']

    if driver == 'dbf':
	grass.fatal(_("JOIN is not supported for tables stored in DBF format."))

    if not maptable:
	grass.fatal(_("There is no table connected to this map. Cannot join any column."))

    if not grass.vector_columns(map, layer).has_key(column):
	grass.fatal(_("Column <%> not found in table <%s> at layer <%s>") % (column, map, layer))

    cols = grass.db_describe(otable, driver = driver, database = database)['cols']

    select = "SELECT $colname FROM $otable WHERE $otable.$ocolumn=$table.$column"
    template = string.Template("UPDATE $table SET $colname=(%s);" % select)

    for col in cols:
	colname = col[0]
	if len(col) > 2:
	    coltype = "%s(%s)" % (col[1], col[2])
	else:
	    coltype = "%s" % col[1]
	colspec = "%s %s" % (colname, coltype)

	if grass.run_command('v.db.addcolumn', map = map, columns = colspec, layer = layer) != 0:
	    grass.fatal(_("Error creating column <%s>.") % colname)

	stmt = template.substitute(table = maptable, column = column,
				   otable = otable, ocolumn = ocolumn,
				   colname = colname)

	if grass.write_command('db.execute', stdin = stmt, input = '-', database = database, driver = driver) != 0:
	    grass.fatal(_("Error filling column <%s>.") % colname)

    # write cmd history:
    grass.vector_history(map)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
