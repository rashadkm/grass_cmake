"""!@package grass.temporal

@brief GRASS Python scripting module (temporal GIS functions)

Temporal GIS base classes to be used in other
Python temporal gis packages.

This packages includes all base classes to store basic information like id, name,
mapset creation and modification time as well as sql serialization and de-serialization
and the sql database interface.

Usage:

@code
import grass.temporal as tgis

rbase = tgis.raster_base(ident="soil")
...
@endcode

(C) 2008-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

from core import *

###############################################################################

class dict_sql_serializer(object):
    def __init__(self):
        self.D = {}
    def serialize(self, type, table, where=None):
	"""!Convert the internal dictionary into a string of semicolon separated SQL statements
	   The keys are the column names and the values are the row entries

	   @type must be SELECT. INSERT, UPDATE
	   @table The name of the table to select, insert or update
	   @where The optional where statement
	   @return the sql string
	"""

	sql = ""
	args = []

	# Create ordered select statement
	if type == "SELECT":
	    sql += 'SELECT '
	    count = 0
            for key in self.D.keys():
		if count == 0:
                    sql += ' %s ' % key
		else:
                    sql += ' , %s ' % key
		count += 1
            sql += ' FROM ' + table + ' '
	    if where:
	        sql += where
            sql += ";\n"

	# Create insert statement
	if type =="INSERT":
	    count = 0
	    sql += 'INSERT INTO ' + table + ' ('
            for key in self.D.keys():
		if count == 0:
                    sql += ' %s ' % key
		else:
                    sql += ' ,%s ' % key
		count += 1

	    count = 0
	    sql += ') VALUES ('
            for key in self.D.keys():
		if count == 0:
		    if dbmi.paramstyle == "qmark":
			sql += '?'
		    else:
			sql += '%s'
		else:
		    if dbmi.paramstyle == "qmark":
			sql += ' ,?'
		    else:
			sql += ' ,%s'
		count += 1
		args.append(self.D[key])
	    sql += ') '

	    if where:
	        sql += where
            sql += ";\n"

	# Create update statement for existing entries
	if type =="UPDATE":
	    count = 0
	    sql += 'UPDATE ' + table + ' SET '
            for key in self.D.keys():
		# Update only entries which are not None
		if self.D[key] != None:
		    if count == 0:
			if dbmi.paramstyle == "qmark":
			    sql += ' %s = ? ' % key
			else:
			    sql += ' %s ' % key
			    sql += '= %s '
		    else:
			if dbmi.paramstyle == "qmark":
			    sql += ' ,%s = ? ' % key
			else:
			    sql += ' ,%s ' % key
			    sql += '= %s '
		    count += 1
	            args.append(self.D[key])
	    if where:
	        sql += where
            sql += ";\n"

	# Create update statement for all entries
	if type =="UPDATE ALL":
	    count = 0
	    sql += 'UPDATE ' + table + ' SET '
            for key in self.D.keys():
                if count == 0:
		    if dbmi.paramstyle == "qmark":
			sql += ' %s = ? ' % key
		    else:
			sql += ' %s ' % key
			sql += '= %s '
                else:
		    if dbmi.paramstyle == "qmark":
	                sql += ' ,%s = ? ' % key
		    else:
			sql += ' ,%s ' % key
			sql += '= %s '
                count += 1
                args.append(self.D[key])
	    if where:
	        sql += where
            sql += ";\n"

    	return sql, tuple(args)

    def deserialize(self, row):
	"""!Convert the content of the dbmi dictionary like row into the internal dictionary

           @param row: The dictionary like row to store in the internal dict
        """
	self.D = {}
	for key in row.keys():
	    self.D[key] = row[key]

    def clear(self):
	"""!Initialize the internal storage"""
	self.D = {}

    def print_self(self):
        print self.D

    def test(self):
        t = dict_sql_serializer()
	t.D["id"] = "soil@PERMANENT"
	t.D["name"] = "soil"
	t.D["mapset"] = "PERMANENT"
	t.D["creator"] = "soeren"
	t.D["creation_time"] = datetime.now()
	t.D["modification_time"] = datetime.now()
	t.D["revision"] = 1
	sql, values = t.serialize(type="SELECT", table="raster_base")
	print sql, '\n', values
	sql, values = t.serialize(type="INSERT", table="raster_base")
	print sql, '\n', values
	sql, values = t.serialize(type="UPDATE", table="raster_base")
	print sql, '\n', values

###############################################################################

class sql_database_interface(dict_sql_serializer):
    """!This class represents the SQL database interface

       Functions to insert, select and update the internal structure of this class
       in the temporal database are implemented. The following DBMS are supported:
       * sqlite via the sqlite3 standard library
       * postgresql via psycopg2

       This is the base class for raster, raster3d, vector and space time datasets
       data management classes:
       * Identification information (base)
       * Spatial extent
       * Temporal extent
       * Metadata
    """
    def __init__(self, table=None, ident=None):
        """!Constructor of this class

           @param table: The name of the table
           @param ident: The identifier (primary key) of this object in the database table
        """
        dict_sql_serializer.__init__(self)

        self.table = table # Name of the table, set in the subclass
        self.ident = ident

    def get_table_name(self):
        """!Return the name of the table in which the internal data are inserted, updated or selected"""
        return self.table

    def connect(self):
        """!Connect to the DBMI to execute SQL statements

           Supported backends are sqlite3 and postgresql
        """
        init = get_temporal_dbmi_init_string()
        #print "Connect to",  self.database
        if dbmi.__name__ == "sqlite3":
	    self.connection = dbmi.connect(init, detect_types=dbmi.PARSE_DECLTYPES|dbmi.PARSE_COLNAMES)
	    self.connection.row_factory = dbmi.Row
            self.connection.isolation_level = None
	    self.cursor = self.connection.cursor()
            self.cursor.execute("PRAGMA synchronous = OFF")
            self.cursor.execute("PRAGMA journal_mode = MEMORY")
        elif dbmi.__name__ == "psycopg2":
	    self.connection = dbmi.connect(init)
	    #self.connection.set_isolation_level(dbmi.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
	    self.cursor = self.connection.cursor(cursor_factory=dbmi.extras.DictCursor)

    def close(self):
        """!Close the DBMI connection"""
        #print "Close connection to",  self.database
	self.connection.commit()
        self.cursor.close()


    def _mogrify_sql_statement(self, content, dbif=None):
        """!Return the SQL statement and arguments as executable SQL string
        """
        sql = content[0]
        args = content[1]

        if dbmi.__name__ == "psycopg2":
            if len(args) == 0:
                return sql
            else:
                if dbif:
                    try:
                        return dbif.cursor.mogrify(sql, args)
                    except:
                        print sql, args
                        raise
                else:
                    self.connect()
                    statement = self.cursor.mogrify(sql, args)
                    self.close()
                    return statement
                    
        elif dbmi.__name__ == "sqlite3":
            if len(args) == 0:
                return sql
            else:
                # Unfortunately as sqlite does not support 
                # the transformation of sql strings and qmarked or
                # named arguments we must make our hands dirty
                # and do it by ourself. :(
                # Doors are open for SQL injection because of the 
                # limited python sqlite3 implementation!!!
                pos = 0
                count = 0
                maxcount = 100
                statement = sql

                while count < maxcount:
                    pos = statement.find("?", pos + 1)
                    if pos == -1:
                        break
                    
                    if args[count] == None:
                        statement = "%sNULL%s"%(statement[0:pos], statement[pos+1:])
                    elif isinstance(args[count], (int, long)):
                        statement = "%s%d%s"%(statement[0:pos], args[count],statement[pos+1:])
                    elif isinstance(args[count], float):
                        statement = "%s%f%s"%(statement[0:pos], args[count],statement[pos+1:])
                    else:
                        # Default is a string, this works for datetime objects too
                        statement = "%s\'%s\'%s"%(statement[0:pos], str(args[count]),statement[pos+1:])
                    count += 1

                return statement

    def get_delete_statement(self):
        """!Return the delete string"""
	return "DELETE FROM " + self.get_table_name() + " WHERE id = \'" + str(self.ident) + "\';\n"

    def delete(self, dbif=None):
        """!Delete the entry of this object from the temporal database"""
	sql = self.get_delete_statement()
        #print sql
        
        if dbif:
            dbif.cursor.execute(sql)
        else:
            self.connect()
            self.cursor.execute(sql)
            self.close()

    def get_is_in_db_statement(self):
        """Return the selection string"""
	return "SELECT id FROM " + self.get_table_name() + " WHERE id = \'" + str(self.ident) + "\';\n"

    def is_in_db(self, dbif=None):
        """!Check if this object is present in the temporal database

           @param dbif: The database interface to be used
        """

	sql = self.get_is_in_db_statement()
        #print sql

        if dbif:
            dbif.cursor.execute(sql)
            row = dbif.cursor.fetchone()
        else:
            self.connect()
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.close()

	# Nothing found
	if row == None:
	    return False

	return True

    def get_select_statement(self):
        """!Return the sql statement and the argument list in database specific style"""
	return self.serialize("SELECT", self.get_table_name(), "WHERE id = \'" + str(self.ident) + "\'")
    
    def get_select_statement_mogrified(self, dbif=None):
        """!Return the select statement as mogrified string"""
        return self._mogrify_sql_statement(self.get_select_statement(), dbif)
                
    def select(self, dbif=None):
        """!Select the content from the temporal database and store it
           in the internal dictionary structure

           @param dbif: The database interface to be used
        """
	sql, args = self.get_select_statement()
	#print sql
	#print args

        if dbif:
            if len(args) == 0:
                dbif.cursor.execute(sql)
            else:
                dbif.cursor.execute(sql, args)
            row = dbif.cursor.fetchone()
        else:
            self.connect()
            if len(args) == 0:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, args)
            row = self.cursor.fetchone()
            self.close()

	# Nothing found
	if row == None:
	    return False

	if len(row) > 0:
	    self.deserialize(row)
	else:
            core.fatal(_("Object <%s> not found in the temporal database") % self.get_id())

	return True

    def get_insert_statement(self):
        """!Return the sql statement and the argument list in database specific style"""
	return self.serialize("INSERT", self.get_table_name())
    
    def get_insert_statement_mogrified(self, dbif=None):
        """!Return the insert statement as mogrified string"""
        return self._mogrify_sql_statement(self.get_insert_statement(), dbif)

    def insert(self, dbif=None):
        """!Serialize the content of this object and store it in the temporal
           database using the internal identifier

           @param dbif: The database interface to be used
        """
	sql, args = self.get_insert_statement()
	#print sql
	#print args

        if dbif:
            dbif.cursor.execute(sql, args)
        else:
            self.connect()
            self.cursor.execute(sql, args)
            self.close()

    def get_update_statement(self):
        """!Return the sql statement and the argument list in database specific style"""
	return self.serialize("UPDATE", self.get_table_name(), "WHERE id = \'" + str(self.ident) + "\'")

    def get_update_statement_mogrified(self,dbif=None):
        """!Return the update statement as mogrified string"""
        return self._mogrify_sql_statement(self.get_update_statement(), dbif)

    def update(self, dbif=None):
        """!Serialize the content of this object and update it in the temporal
           database using the internal identifier

           Only object entries which are exists (not None) are updated

           @param dbif: The database interface to be used
        """
	if self.ident == None:
	    raise IOError("Missing identifer");

	sql, args = self.get_update_statement()
	#print sql
	#print args

        if dbif:
            dbif.cursor.execute(sql, args)
        else:
            self.connect()
            self.cursor.execute(sql, args)
            self.close()

    def get_update_all_statement(self):
        """!Return the sql statement and the argument list in database specific style"""
	return self.serialize("UPDATE ALL", self.get_table_name(), "WHERE id = \'" + str(self.ident) + "\'")

    def get_update_all_statement_mogrified(self, dbif=None):
        """!Return the update all statement as mogrified string"""
        return self._mogrify_sql_statement(self.get_update_all_statement(), dbif)

    def update_all(self, dbif=None):
        """!Serialize the content of this object, including None objects, and update it in the temporal
           database using the internal identifier

           @param dbif: The database interface to be used
        """
	if self.ident == None:
	    raise IOError("Missing identifer");

	sql, args = self.get_update_all_statement()
	#print sql
	#print args

        if dbif:
            dbif.cursor.execute(sql, args)
        else:
            self.connect()
            self.cursor.execute(sql, args)
            self.close()

###############################################################################

class dataset_base(sql_database_interface):
    """!This is the base class for all maps and spacetime datasets storing basic identification information"""
    def __init__(self, table=None, ident=None, name=None, mapset=None, creator=None, ctime=None,\
		    mtime=None, ttype=None, revision=1):

	sql_database_interface.__init__(self, table, ident)

	self.set_id(ident)
        if ident != None and name == None and mapset == None:
            if ident.find("@") >= 0:
                name, mapset = ident.split("@")
            if name.find(":") >= 0:
                name, layer = ident.split(":")
	self.set_name(name)
	self.set_mapset(mapset)
	self.set_creator(creator)
	self.set_ctime(ctime)
	self.set_ttype(ttype)
	#self.set_mtime(mtime)
	#self.set_revision(revision)

    def set_id(self, ident):
	"""!Convenient method to set the unique identifier (primary key)

           @param ident: The unique identifier should be a combination of the dataset name, layer name and the mapset name@mapset
        """
	self.ident = ident
	self.D["id"] = ident

    def set_name(self, name):
	"""!Set the name of the dataset

           @param name: The name of the dataset
        """
	self.D["name"] = name

    def set_mapset(self, mapset):
	"""!Set the mapset of the dataset

           @param mapsets: The name of the mapset in which this dataset is stored
        """
	self.D["mapset"] = mapset

    def set_layer(self, layer):
	"""!Convenient method to set the layer of the map (part of primary key)
	
	   Layer are currently supported for vector maps

           @param layer: The layer of the map
        """
	self.D["layer"] = layer

    def set_creator(self, creator):
	"""!Set the creator of the dataset

           @param creator: The name of the creator
        """
	self.D["creator"] = creator

    def set_ctime(self, ctime=None):
	"""!Set the creation time of the dataset, if nothing set the current time is used

           @param ctime: The current time of type datetime
        """
	if ctime == None:
            self.D["creation_time"] = datetime.now()
	else:
            self.D["creation_time"] = ctime

    def set_ttype(self, ttype):
	"""!Set the temporal type of the dataset: absolute or relative, if nothing set absolute time will assumed

           @param ttype: The temporal type of the dataset "absolute or relative"
        """
	if ttype == None or (ttype != "absolute" and ttype != "relative"):
	    self.D["temporal_type"] = "absolute"
        else:
	    self.D["temporal_type"] = ttype

#    def set_mtime(self, mtime=None):
#	"""!Set the modification time of the map, if nothing set the current time is used"""
#	if mtime == None:
#            self.D["modification_time"] = datetime.now()
#	else:
#            self.D["modification_time"] = mtime

#    def set_revision(self, revision=1):
#	"""!Set the revision of the map: if nothing set revision 1 will assumed"""
#	self.D["revision"] = revision

    def get_id(self):
	"""!Convenient method to get the unique identifier (primary key)
        
	   @return None if not found
	"""
	if self.D.has_key("id"):
	    return self.D["id"]
        else:
	    return None

    def get_map_id(self):
	"""!Convenient method to get the unique map identifier without layer information

           @param return the name of the vector map as name@mapset
        """
        id = self.get_id()
        if id.find(":") >= 0:
	    # Remove the layer identifier from the id
	    return id.split("@")[0].split(":")[0] + "@" + id.split("@")[1]
	else:
	    return id
	    
    def get_layer(self):
	"""!Convenient method to get the layer of the map (part of primary key)
	
	   Layer are currently supported for vector maps
        
	   @return None if not found
	"""
	if self.D.has_key("layer"):
	    return self.D["layer"]
        else:
	    return None

    def get_name(self):
	"""!Get the name of the dataset
	   @return None if not found"""
	if self.D.has_key("name"):
	    return self.D["name"]
        else:
	    return None

    def get_mapset(self):
	"""!Get the name of mapset of this dataset
	   @return None if not found"""
	if self.D.has_key("mapset"):
	    return self.D["mapset"]
        else:
	    return None

    def get_creator(self):
	"""!Get the creator of the dataset
	   @return None if not found"""
	if self.D.has_key("creator"):
	    return self.D["creator"]
        else:
	    return None

    def get_ctime(self):
	"""!Get the creation time of the dataset, datatype is datetime
	   @return None if not found"""
	if self.D.has_key("creation_time"):
	    return self.D["creation_time"]
        else:
	    return None

    def get_ttype(self):
	"""!Get the temporal type of the map
	   @return None if not found"""
	if self.D.has_key("temporal_type"):
	    return self.D["temporal_type"]
        else:
	    return None

#    def get_mtime(self):
#	"""!Get the modification time of the map, datatype is datetime
#	   @return None if not found"""
#	if self.D.has_key("modification_time"):
#	    return self.D["modification_time"]
#       else:
#	    return None

#    def get_revision(self):
#	"""!Get the revision of the map
#	   @return None if not found"""
#	if self.D.has_key("revision"):
#	    return self.D["revision"]
#       else:
#	    return None

    def print_info(self):
        """!Print information about this class in human readable style"""
        #      0123456789012345678901234567890
        print " +-------------------- Basic information -------------------------------------+"
        print " | Id: ........................ " + str(self.get_id())
        print " | Name: ...................... " + str(self.get_name())
        print " | Mapset: .................... " + str(self.get_mapset())
        if self.get_layer():
	    print " | Layer:...................... " + str(self.get_layer())
        print " | Creator: ................... " + str(self.get_creator())
        print " | Creation time: ............. " + str(self.get_ctime())
#        print " | Modification time: ......... " + str(self.get_mtime())
        print " | Temporal type: ............. " + str(self.get_ttype())
#        print " | Revision in database: ...... " + str(self.get_revision())
        
    def print_shell_info(self):
        """!Print information about this class in shell style"""
        print "id=" + str(self.get_id())
        print "name=" + str(self.get_name())
        print "mapset=" + str(self.get_mapset())
        if self.get_layer():
	    print "layer=" + str(self.get_layer())
        print "creator=" + str(self.get_creator())
        print "creation_time=" + str(self.get_ctime())
#        print "modification_time=" + str(self.get_mtime())
        print "temporal_type=" + str(self.get_ttype())
#        print "revision=" + str(self.get_revision())

###############################################################################

class raster_base(dataset_base):
    def __init__(self, ident=None, name=None, mapset=None, creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        dataset_base.__init__(self, "raster_base", ident, name, mapset, creator, creation_time,\
	            modification_time, temporal_type, revision)

class raster3d_base(dataset_base):
    def __init__(self, ident=None, name=None, mapset=None, creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        dataset_base.__init__(self, "raster3d_base", ident, name, mapset, creator, creation_time,\
	            modification_time, temporal_type, revision)

class vector_base(dataset_base):
    def __init__(self, ident=None, name=None, mapset=None, layer=None, creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        dataset_base.__init__(self, "vector_base", ident, name, mapset, creator, creation_time,\
	            modification_time, temporal_type, revision)

	self.set_id(ident)
        if ident != None and name == None and mapset == None:
            if ident.find("@") >= 0:
                name, mapset = ident.split("@")
            if layer == None:
		if name.find(":") >= 0:
		    name, layer = name.split(":")
	self.set_name(name)
	self.set_mapset(mapset)
	# Layer currently only in use by vector maps
	self.set_layer(layer)

###############################################################################

class stds_base(dataset_base):
    def __init__(self, table=None, ident=None, name=None, mapset=None, semantic_type=None, creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        dataset_base.__init__(self, table, ident, name, mapset, creator, creation_time,\
	            modification_time, temporal_type, revision)

	self.set_semantic_type(semantic_type)

    def set_semantic_type(self, semantic_type):
	"""!Set the semantic type of the space time dataset"""
	self.D["semantic_type"] = semantic_type

    def get_semantic_type(self):
	"""!Get the semantic type of the space time dataset
	   @return None if not found"""
	if self.D.has_key("semantic_type"):
	    return self.D["semantic_type"]
        else:
	    return None

    def print_info(self):
        """!Print information about this class in human readable style"""
        dataset_base.print_info(self)
        #      0123456789012345678901234567890
        print " | Semantic type:.............. " + str(self.get_semantic_type())

    def print_shell_info(self):
        """!Print information about this class in shell style"""
        dataset_base.print_shell_info(self)
        print "semantic_type=" + str(self.get_semantic_type())

###############################################################################

class strds_base(stds_base):
    def __init__(self, ident=None, name=None, mapset=None, semantic_type=None,  creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        stds_base.__init__(self, "strds_base", ident, name, mapset, semantic_type, creator, creation_time,\
	            modification_time, temporal_type, revision)

class str3ds_base(stds_base):
    def __init__(self, ident=None, name=None, mapset=None, semantic_type=None,  creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        stds_base.__init__(self, "str3ds_base", ident, name, mapset, semantic_type, creator, creation_time,\
	            modification_time, temporal_type, revision)

class stvds_base(stds_base):
    def __init__(self, ident=None, name=None, mapset=None, semantic_type=None,  creator=None, creation_time=None,\
		    modification_time=None, temporal_type=None, revision=1):
        stds_base.__init__(self, "stvds_base", ident, name, mapset, semantic_type, creator, creation_time,\
	            modification_time, temporal_type, revision)

###############################################################################

def init_dbif(dbif):
    """!This method checks if the database interface exists, if not a new one 
        will be created and True will be returned

        Usage code sample:
        dbif, connect = self._init_dbif(dbif)
        if connect:
            dbif.close()
    """
    if dbif == None:
        dbif = sql_database_interface()
        dbif.connect()
        return dbif, True

    return dbif, False

###############################################################################

def execute_transaction(statement, dbif=None):
    """!Execute a transactional SQL statement

        The BEGIN and END TRANSACTION statements will be added automatically
        to the sql statement

        @param statement The executable SQL statement or SQL script
        @param dbif The database interface, if None a new db interface will be created temporary
    """
    dbif, connect = init_dbif(dbif)

    sql_script = ""
    sql_script += "BEGIN TRANSACTION;\n"
    sql_script += statement
    sql_script += "END TRANSACTION;"
    try:
        if dbmi.__name__ == "sqlite3":
            dbif.cursor.executescript(statement)
        else:
            dbif.cursor.execute(statement)
        dbif.connection.commit()
    except:
        if connect == True:
            dbif.close()
        core.error(_("Unable to execute transaction:\n %s") % (statement))
        raise

    if connect:
        dbif.close()
