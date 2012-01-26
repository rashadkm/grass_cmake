# -*- coding: utf-8 -*-
"""!@package grass.temporal

@brief GRASS Python scripting module (temporal GIS functions)

Temporal GIS related functions to be used in temporal GIS Python library package.

Usage:

@code
import grass.temporal as tgis

...
@endcode

(C) 2008-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""
from abstract_dataset import *
from temporal_granularity import *

###############################################################################

class abstract_space_time_dataset(abstract_dataset):
    """Abstract space time dataset class

       This class represents a space time dataset. Convenient functions
       to select, update, insert or delete objects of this type in the SQL
       temporal database exists as well as functions to register or unregister
       raster maps.

       Parts of the temporal logic are implemented in the SQL temporal database,
       like the computation of the temporal and spatial extent as well as the
       collecting of metadata.
    """
    def __init__(self, ident):
	self.reset(ident)
        self.map_counter = 0

    def get_new_map_instance(self, ident=None):
        """Return a new instance of a map dataset which is associated with the type of this class

           @param ident: The unique identifier of the new object
        """
        raise IOError("This method must be implemented in the subclasses")

    def get_map_register(self):
        """Return the name of the map register table"""
        raise IOError("This method must be implemented in the subclasses")

    def set_map_register(self, name):
        """Set the name of the map register table

        This table stores all map names which are registered in this space time dataset.

           @param name: The name of the register table
        """
        raise IOError("This method must be implemented in the subclasses")
 
    def print_self(self):
	"""Print the content of the internal structure to stdout"""
	self.base.print_self()
	if self.is_time_absolute():
	    self.absolute_time.print_self()
        if self.is_time_relative():
	    self.relative_time.print_self()
	self.spatial_extent.print_self()
	self.metadata.print_self()

    def print_info(self):
        """Print information about this class in human readable style"""
        
        if self.get_type() == "strds":
            #                1         2         3         4         5         6         7
            #      0123456789012345678901234567890123456789012345678901234567890123456789012345678
            print ""
            print " +-------------------- Space Time Raster Dataset -----------------------------+"
        if self.get_type() == "str3ds":
            #                1         2         3         4         5         6         7
            #      0123456789012345678901234567890123456789012345678901234567890123456789012345678
            print ""
            print " +-------------------- Space Time Raster3d Dataset ---------------------------+"
        if self.get_type() == "stvds":
            #                1         2         3         4         5         6         7
            #      0123456789012345678901234567890123456789012345678901234567890123456789012345678
            print ""
            print " +-------------------- Space Time Vector Dataset -----------------------------+"
        print " |                                                                            |"
	self.base.print_info()
	if self.is_time_absolute():
	    self.absolute_time.print_info()
        if self.is_time_relative():
	    self.relative_time.print_info()
	self.spatial_extent.print_info()
	self.metadata.print_info()
        print " +----------------------------------------------------------------------------+"

    def print_shell_info(self):
        """Print information about this class in shell style"""
	self.base.print_shell_info()
	if self.is_time_absolute():
	    self.absolute_time.print_shell_info()
        if self.is_time_relative():
	    self.relative_time.print_shell_info()
	self.spatial_extent.print_shell_info()
	self.metadata.print_shell_info()

    def set_initial_values(self, temporal_type, semantic_type, \
                           title=None, description=None):
        """Set the initial values of the space time dataset

           @param temporal_type: The temporal type of this space time dataset (absolute or relative)
           @param semantic_type: The semantic type of this dataset
           @param title: The title
           @param description: The description of this dataset
        """

        if temporal_type == "absolute":
            self.set_time_to_absolute()
        elif temporal_type == "relative":
            self.set_time_to_relative()
        else:
            core.fatal(_("Unknown temporal type \"%s\"") % (temporal_type))

        self.base.set_semantic_type(semantic_type)
        self.metadata.set_title(title)
        self.metadata.set_description(description)

    def get_semantic_type(self):
        """Return the semantic type of this dataset"""
        return self.base.get_semantic_type()

    def get_initial_values(self):
        """Return the initial values: temporal_type, semantic_type, title, description"""
        
        temporal_type = self.get_temporal_type()
        semantic_type = self.base.get_semantic_type()
        title = self.metadata.get_title()
        description = self.metadata.get_description()

        return temporal_type, semantic_type, title, description

    def get_granularity(self):
        """Return the granularity"""
        
        temporal_type = self.get_temporal_type()

        if temporal_type == "absolute":
            granularity   = self.absolute_time.get_granularity()
        elif temporal_type == "relative":
            granularity = self.relative_time.get_granularity()

        return granularity

    def set_granularity(self, granularity):

        temporal_type = self.get_temporal_type()
 
        if temporal_type == "absolute":
            self.set_time_to_absolute()
            self.absolute_time.set_granularity(granularity)
        elif temporal_type == "relative":
            self.set_time_to_relative()
            self.relative_time.set_granularity(granularity)
        else:
            core.fatal(_("Unknown temporal type \"%s\"") % (temporal_type))

    def set_relative_time_unit(self, unit):
        """Set the relative time unit which may be of type: years, months, days, hours, minutes or seconds
        
           All maps registered in a (relative time) space time dataset must have the same unit
        """

        temporal_type = self.get_temporal_type()
 
        if temporal_type == "relative":
            if not self.check_relative_time_unit(unit):
                core.fatal(_("Unsupported temporal unit: %s") % (unit))
            self.relative_time.set_unit(unit)

    def get_map_time(self):
        """Return the type of the map time, interval, point, mixed or invalid"""
        
        temporal_type = self.get_temporal_type()

        if temporal_type == "absolute":
            map_time   = self.absolute_time.get_map_time()
        elif temporal_type == "relative":
            map_time   = self.relative_time.get_map_time()

        return map_time

    def print_temporal_relation_matrix(self, maps):
        """Print the temporal relation matrix of all registered maps to stdout

           The temporal relation matrix includes the temporal relations between
           all registered maps. The relations are strings stored in a list of lists.
           
           @param dbif: The database interface to be used
        """

        for i in range(len(maps)):
            reltations = ""
            count = 0
            for j in range(i + 1, len(maps)):
                relation = maps[j].temporal_relation(maps[i])

                # print maps[j].base.get_name(), maps[i].base.get_name(), relation
                if count == 0:
                    relations = relation
                else:
                    relations += "," + str(relation)
                count += 1
                # Break if the the next map follows
                if relation == "follows":
                    break
                # Break if the the next map is after
                if relation == "after":
                    break
            if i < len(maps) - 1:    
                print maps[i].base.get_name(), relations    
            else:
                print maps[i].base.get_name()

    def get_temporal_relation_matrix(self, maps):
        """Return the temporal relation matrix of all registered maps as list of lists

           The map list must be ordered by start time

           The temporal relation matrix includes the temporal relations between
           all registered maps. The relations are strings stored in a list of lists.
           
           @param maps: a ordered by start_time list of map objects
        """

        matrix = []

        # Create the temporal relation matrix
        # Add the map names first
        row = []
        for map in maps:
            row.append(map.get_id())
        matrix.append(row)

        for mapA in maps:
            row = []
            for mapB in maps:
                row.append(mapA.temporal_relation(mapB))
            matrix.append(row)

        return matrix

    def count_temporal_types(self, maps):
        """Return the temporal type of the registered maps as dictionary

           The map list must be ordered by start time

           The temporal type can be:
           * point    -> only the start time is present
           * interval -> start and end time
           * invalid  -> No valid time point or interval found

           @param maps: A sorted (start_time) list of abstract_dataset objects
        """

        time_invalid = 0
        time_point = 0
        time_interval = 0

        tcount = {}
        for i in range(len(maps)):
            # Check for point and interval data
            if maps[i].is_time_absolute():
                start, end, tz = maps[i].get_absolute_time()
            if maps[i].is_time_relative():
                start, end, unit = maps[i].get_relative_time()

            if start != None and end != None:
                time_interval += 1
            elif start != None and end == None:
                time_point += 1
            else:
                time_invalid += 1

        tcount["point"] = time_point
        tcount["interval"] = time_interval
        tcount["invalid"] = time_invalid

        return tcount

    def count_gaps(self, maps):
        """Count the number of gaps between temporal neighbors
        
           @param maps: A sorted (start_time) list of abstract_dataset objects
           @return The numbers of gaps between temporal neighbors
        """

        gaps = 0

        # Check for gaps
        for i in range(len(maps)):
            if i < len(maps) - 1:
                relation = maps[i + 1].temporal_relation(maps[i])
                if relation == "after":
                    gaps += 1

        return gaps

    def count_temporal_relations(self, maps):
        """Count the temporal relations between the registered maps.

           The map list must be ordered by start time

           @param maps: A sorted (start_time) list of abstract_dataset objects
           @return A dictionary with counted temporal relationships
        """

        tcount = {}
        for i in range(len(maps)):
            # Check for point and interval data
            for j in range(i + 1, len(maps)):
                relation = maps[j].temporal_relation(maps[i])

                if tcount.has_key(relation):
                    tcount[relation] = tcount[relation] + 1
                else:
                    tcount[relation] = 1

                # Break if the the next map follows
                if relation == "follows":
                    break
                # Break if the the next map is after
                if relation == "after":
                    break

        return tcount

    def check_temporal_topology(self, maps=None, dbif=None):
        """Check the temporal topology

           Correct topology means, that time intervals are not overlap or
           that intervals does not contain other intervals. Equal time intervals or
           points of time are not allowed.

           The map list must be ordered by start time

           Allowed and not allowed temporal relationships for correct topology
           after      -> allowed
           before     -> allowed
           follows    -> allowed
           precedes   -> allowed

           equivalent -> not allowed
           during     -> not allowed
           contains   -> not allowed
           overlaps   -> not allowed
           overlapped -> not allowed
           starts     -> not allowed
           finishes   -> not allowed
           started    -> not allowed
           finished   -> not allowed

           @param maps: A sorted (start_time) list of abstract_dataset objects
           @return True if topology is correct
        """
        if maps == None:
            maps = get_registered_maps_as_objects(where=None, order="start_time", dbif=dbif)

        relations = self.count_temporal_relations(maps)

        map_time = self.get_map_time()

        if map_time == "interval" or map_time == "mixed":
            if relations.has_key("equivalent"):
                return False
            if relations.has_key("during"):
                return False
            if relations.has_key("contains"):
                return False
            if relations.has_key("overlaps"):
                return False
            if relations.has_key("overlapped"):
                return False
            if relations.has_key("starts"):
                return False
            if relations.has_key("finishes"):
                return False
            if relations.has_key("started"):
                return False
            if relations.has_key("finished"):
                return False
        elif map_time == "point":
            if relations.has_key("equivalent"):
                return False
        else:
            return False

        return True

    def sample_by_dataset_topology(self, stds, method=None, dbif=None):
        """Sample this space time dataset with the temporal topology of a second space time dataset

           The sample dataset must have "interval" as temporal map type, so all sample maps have valid interval time.
        
           Return all registered maps as ordered (by start_time) object list with 
           "gap" map objects (id==None). Each list entry is a list of map objects
           which are potentially located in temporal relation to the actual granule of the second space time dataset.

           Each entry in the object list is a dict. The actual sampler map and its temporal extent (the actual granule) and
           the list of samples are stored:

           list = self.sample_by_dataset_topology(stds=sampler, method=["during","overlap","contain","equal"])    
           for entry in list:
               granule = entry["granule"]
               maplist = entry["samples"]
               for map in maplist:
                   map.select()
                   map.print_info()

           A valid temporal topology (no overlapping or inclusion allowed) is needed to get correct results in case of gaps
           in the sample dataset. 
    
           Gaps between maps are identified as unregistered maps with id==None.

           The map objects are initialized with the id and the temporal extent of the granule (temporal type, start time, end time).
           In case more map informations are needed, use the select() method for each listed object.

           @param stds: The space time dataset to be used for temporal sampling
           @param method: This option specifies what sample method should be used. In case the registered maps are of temporal point type,
                          only the start time is used for sampling. In case of mixed of interval data the user can chose between:
                          * start: Select maps of which the start time is located in the selection granule
                            map    :        s
                            granule:  s-----------------e

                            map    :        s--------------------e
                            granule:  s-----------------e

                            map    :        s--------e
                            granule:  s-----------------e

                          * during: Select maps which are temporal during the selection granule
                            map    :     s-----------e
                            granule:  s-----------------e

                          * overlap: Select maps which temporal overlap the selection granule
                            map    :     s-----------e
                            granule:        s-----------------e

                            map    :     s-----------e
                            granule:  s----------e

                          * contain: Select maps which temporally contain the selection granule
                            map    :  s-----------------e
                            granule:     s-----------e

                          * equal: Select maps which temporally equal to the selection granule
                            map    :  s-----------e
                            granule:  s-----------e

                          All these methods can be combined. Method must be of type tuple including the identification strings.
           @param dbif: The database interface to be used

           In case nothing found None is returned
        """

        use_start = False
        use_during = False
        use_overlap = False
        use_contain = False
        use_equal = False

        # Initialize the methods
        if method:
            for name in method:
                if name == "start":
                    use_start = True
                if name == "during":
                    use_during = True
                if name == "overlap":
                    use_overlap = True
                if name == "contain":
                    use_contain = True
                if name == "equal":
                    use_equal = True
        else:
            use_during = True
            use_overlap = True
            use_contain = True
            use_equal = True

        if self.get_temporal_type() != stds.get_temporal_type():
            core.error(_("The space time datasets must be of the same temporal type"))
            return None

        if stds.get_map_time() != "interval":
            core.error(_("The temporal map type of the sample dataset must be interval"))
            return None

        # In case points of time are available, disable the interval specific methods
        if self.get_map_time() == "point":
            use_start = True
            use_during = False
            use_overlap = False
            use_contain = False
            use_equal = False

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        obj_list = []
        sample_maps = stds.get_registered_maps_as_objects_with_gaps(where=None, dbif=dbif)
        
        for granule in sample_maps:
            start, end = granule.get_valid_time()

            where = create_temporal_relation_sql_where_statement(start, end, use_start, \
                    use_during, use_overlap, use_contain, use_equal)  

            rows = self.get_registered_maps("id", where, "start_time", dbif)

            result = {}
            result["granule"] = granule
            maplist = None

            if rows:
                maplist = []
                for row in rows:
                    map = self.get_new_map_instance(row["id"])

                    if self.is_time_absolute():
                        map.set_absolute_time(start, end)
                    elif self.is_time_relative():
                        map.set_relative_time(start, end)

                    maplist.append(copy.copy(map))
                result["samples"] = maplist
            else:
                maplist = []
                map = self.get_new_map_instance(None)

                if self.is_time_absolute():
                    map.set_absolute_time(start, end)
                elif self.is_time_relative():
                    map.set_relative_time(start, end)

                maplist.append(copy.copy(map))
                result["samples"] = maplist

            obj_list.append(copy.copy(result))

        if connect == True:
            dbif.close()

        return obj_list

    def get_registered_maps_as_objects_by_granularity(self, gran=None, dbif=None):
        """Return all registered maps as ordered (by start_time) object list with 
           "gap" map objects (id==None) for temporal topological operations using the
           granularity of the space time dataset as increment. Each list entry is a list of map objects
           which are potentially located in the actual granule.

           A valid temporal topology (no overlapping or inclusion allowed) is needed to get correct results. 
    
           The dataset must have "interval" as temporal map type, so all maps have valid interval time.

           Gaps between maps are identified as unregistered maps with id==None.

           The objects are initialized with the id and the temporal extent (temporal type, start time, end time).
           In case more map informations are needed, use the select() method for each listed object.

           @param gran: The granularity to be used 
           @param dbif: The database interface to be used

           In case nothing found None is returned
        """

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        obj_list = []

        if gran == None:
            gran = self.get_granularity()

        start, end = self.get_valid_time()

        while start < end:
            if self.is_time_absolute():
                next = increment_datetime_by_string(start, gran)
            else:
                next = start + gran

            where = "(start_time <= '%s' and end_time >= '%s')" % (start, next)

            rows = self.get_registered_maps("id", where, "start_time", dbif)

            if rows:
                if len(rows) > 1:
                    core.warning(_("More than one map found in a granule. Temporal granularity seems to be invalid or the chosen granularity is not a greatest common divider of all intervals and gaps in the dataset."))
 
                maplist = []
                for row in rows:
                   # Take the first map    
                    map = self.get_new_map_instance(rows[0]["id"])

                    if self.is_time_absolute():
                        map.set_absolute_time(start, next)
                    elif self.is_time_relative():
                        map.set_relative_time(start, next)

                    maplist.append(copy.copy(map))

            	obj_list.append(copy.copy(maplist))

            start = next

        if connect == True:
            dbif.close()

        return obj_list

    def get_registered_maps_as_objects_with_gaps(self, where=None, dbif=None):
        """Return all registered maps as ordered (by start_time) object list with 
           "gap" map objects (id==None) for temporal topological operations

           Gaps between maps are identified as maps with id==None

           The objects are initialized with the id and the temporal extent (temporal type, start time, end time).
           In case more map informations are needed, use the select() method for each listed object.

           @param where: The SQL where statement to select a subset of the registered maps without "WHERE"
           @param dbif: The database interface to be used

           In case nothing found None is returned
        """

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        obj_list = []
        
        maps = self.get_registered_maps_as_objects(where, "start_time", dbif)

        if maps and len(maps) > 0:
            for i in range(len(maps)):
                obj_list.append(maps[i])
                # Detect and insert gaps
                if i < len(maps) - 1:
                    relation = maps[i + 1].temporal_relation(maps[i])
                    if relation == "after":
                        start1, end1 = maps[i].get_valid_time()
                        start2, end2 = maps[i + 1].get_valid_time()
                        end = start2
                        if end1:
                            start = end1
                        else:
                            start = start1

                        map = self.get_new_map_instance(None)

                        if self.is_time_absolute():
                            map.set_absolute_time(start, end)
                        elif self.is_time_relative():
                            map.set_relative_time(start, end)
                        obj_list.append(copy.copy(map))

        if connect == True:
            dbif.close()

        return obj_list

    def get_registered_maps_as_objects(self, where=None, order="start_time", dbif=None):
        """Return all registered maps as ordered object list for temporal topological operations

           The objects are initialized with the id and the temporal extent (temporal type, start time, end time).
           In case more map informations are needed, use the select() method for each listed object.

           @param where: The SQL where statement to select a subset of the registered maps without "WHERE"
           @param order: The SQL order statement to be used to order the objects in the list without "ORDER BY"
           @param dbif: The database interface to be used

           In case nothing found None is returned
        """

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        obj_list = []
        
        rows = self.get_registered_maps("id,start_time,end_time", where, order, dbif)

        count = 0
        if rows:
            for row in rows:
                core.percent(count, len(rows), 1)
                map = self.get_new_map_instance(row["id"])
                if self.is_time_absolute():
                    map.set_absolute_time(row["start_time"], row["end_time"])
                elif self.is_time_relative():
                    map.set_relative_time(row["start_time"], row["end_time"], self.get_relative_time_unit())
                obj_list.append(copy.copy(map))
                count += 1

        core.percent(1, 1, 1)

        if connect == True:
            dbif.close()

        return obj_list

    def get_registered_maps(self, columns=None, where = None, order = None, dbif=None):
        """Return sqlite rows of all registered maps.
        
           In case columns are not specified, each row includes all columns specified in the datatype specific view

           @param columns: Columns to be selected as SQL compliant string
           @param where: The SQL where statement to select a subset of the registered maps without "WHERE"
           @param order: The SQL order statement to be used to order the objects in the list without "ORDER BY"
           @param dbif: The database interface to be used

           In case nothing found None is returned
        """

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        rows = None

        if self.get_map_register():
            # Use the correct temporal table
            if self.get_temporal_type() == "absolute":
                map_view = self.get_new_map_instance(None).get_type() + "_view_abs_time"
            else:
                map_view = self.get_new_map_instance(None).get_type() + "_view_rel_time"

            if columns:
                sql = "SELECT %s FROM %s  WHERE %s.id IN (SELECT id FROM %s)" % (columns, map_view, map_view, self.get_map_register())
            else:
                sql = "SELECT * FROM %s  WHERE %s.id IN (SELECT id FROM %s)" % (map_view, map_view, self.get_map_register())

            if where:
                sql += " AND %s" % (where)
            if order:
                sql += " ORDER BY %s" % (order)

            try:
                dbif.cursor.execute(sql)
                rows = dbif.cursor.fetchall()
            except:
                if connect == True:
                    dbif.close()
                core.error(_("Unable to get map ids from register table <%s>") % (self.get_map_register()))
                raise

        if connect == True:
            dbif.close()

        return rows

    def delete(self, dbif=None):
        """Delete a space time dataset from the temporal database

           This method removes the space time dataset from the temporal database and drops its map register table

           @param dbif: The database interface to be used
        """
        # First we need to check if maps are registered in this dataset and
        # unregister them

        core.verbose(_("Delete space time %s  dataset <%s> from temporal database") % (self.get_new_map_instance(ident=None).get_type(), self.get_id()))

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        # SELECT all needed informations from the database
        self.select(dbif)

        core.verbose(_("Drop map register table: %s") %  (self.get_map_register()))
        if self.get_map_register():
            rows = self.get_registered_maps("id", None, None, dbif)
            # Unregister each registered map in the table
            if rows:
                num_maps = len(rows)
                count = 0
                for row in rows:
	            core.percent(count, num_maps, 1)
                    # Unregister map
                    map = self.get_new_map_instance(row["id"])
                    self.unregister_map(map, dbif)
                    count += 1
	        core.percent(1, 1, 1)
            try:
                # Drop the map register table
                sql = "DROP TABLE " + self.get_map_register()
                dbif.cursor.execute(sql)
                dbif.connection.commit()
            except:
                if connect == True:
                    dbif.close()
                core.error(_("Unable to drop table <%s>") % (self.get_map_register()))
                raise

        # Remove the primary key, the foreign keys will be removed by trigger
        self.base.delete(dbif)
        self.reset(None)

        if connect == True:
            dbif.close()
            
    def register_map(self, map, dbif=None):
        """ Register a map in the space time dataset.

            This method takes care of the registration of a map
            in a space time dataset.

            In case the map is already registered this function will break with a warning
            and return False

           @param dbif: The database interface to be used
        """
        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        if map.is_in_db(dbif) == False:
            dbif.close()
            core.fatal(_("Only maps with absolute or relative valid time can be registered"))
	if map.get_layer():
	    core.verbose(_("Register %s map <%s> with layer %s in space time %s dataset <%s>") %  (map.get_type(), map.get_map_id(), map.get_layer(), map.get_type(), self.get_id()))
	else:
	    core.verbose(_("Register %s map <%s> in space time %s dataset <%s>") %  (map.get_type(), map.get_map_id(), map.get_type(), self.get_id()))

        # First select all data from the database
        map.select(dbif)

        if not map.check_valid_time():
	    if map.get_layer():
		core.fatal(_("Map <%s> with layer %s has invalid time") % map.get_map_id(), map.get_layer())
	    else:
		core.fatal(_("Map <%s> has invalid time") % map.get_map_id())

        map_id = map.base.get_id()
        map_name = map.base.get_name()
        map_mapset = map.base.get_mapset()
        map_register_table = map.get_stds_register()
        map_rel_time_unit = map.get_relative_time_unit()
        map_ttype = map.get_temporal_type()

        #print "Map register table", map_register_table

        # Get basic info
        stds_name = self.base.get_name()
        stds_mapset = self.base.get_mapset()
        stds_register_table = self.get_map_register()
        stds_ttype = self.get_temporal_type()

        # Check temporal types
        if stds_ttype != map_ttype:
	    if map.get_layer():
		core.fatal(_("Temporal type of space time dataset <%s> and map <%s> with layer %s are different") % (self.get_id(), map.get_map_id(), map.get_layer()))
	    else:
		core.fatal(_("Temporal type of space time dataset <%s> and map <%s> are different") % (self.get_id(), map.get_map_id()))

        # In case no map has been registered yet, set the relative time unit from the first map
        if self.metadata.get_number_of_maps() == None and self.map_counter == 0 and self.is_time_relative():
            self.set_relative_time_unit(map_rel_time_unit)
            self.relative_time.update()
            core.verbose(_("Set temporal unit for space time %s dataset <%s> to %s") %  (map.get_type(), self.get_id(), map_rel_time_unit))

        stds_rel_time_unit = self.get_relative_time_unit()

        # Check the relative time unit
        if self.is_time_relative() and (stds_rel_time_unit != map_rel_time_unit):
	    if map.get_layer():
		core.fatal(_("Relative time units of space time dataset <%s> and map <%s> with layer %s are different") % (self.get_id(), map.get_map_id(), map.get_layer()))
	    else:
		core.fatal(_("Relative time units of space time dataset <%s> and map <%s> are different") % (self.get_id(), map.get_map_id()))

        #print "STDS register table", stds_register_table

        if stds_mapset != map_mapset:
            dbif.close()
            core.fatal(_("Only maps from the same mapset can be registered"))

        # Check if map is already registered
        if stds_register_table:
	    if dbmi.paramstyle == "qmark":
		sql = "SELECT id FROM " + stds_register_table + " WHERE id = (?)"
	    else:
		sql = "SELECT id FROM " + stds_register_table + " WHERE id = (%s)"
            dbif.cursor.execute(sql, (map_id,))
            row = dbif.cursor.fetchone()
            # In case of no entry make a new one
            if row and row[0] == map_id:
                if connect == True:
                    dbif.close()
                    
		if map.get_layer():
		    core.warning(_("Map <%s> with layer %s is already registered.") % (map.get_map_id(), map.get_layer()))
		else:
		    core.warning(_("Map <%s> is already registered.") % (map.get_map_id()))
                return False

        # Create tables
        sql_path = get_sql_template_path()

        # We need to create the map raster register table before we can register the map
        if map_register_table == None:
            # Create a unique id
            uuid_rand = "map_" + str(uuid.uuid4()).replace("-", "")

            map_register_table = uuid_rand + "_" + self.get_type() + "_register"
            
            # Read the SQL template
            sql = open(os.path.join(sql_path, "map_stds_register_table_template.sql"), 'r').read()
            # Create the raster, raster3d and vector tables
            sql = sql.replace("GRASS_MAP", map.get_type())
            sql = sql.replace("MAP_NAME", map_name + "_" + map_mapset )
            sql = sql.replace("TABLE_NAME", uuid_rand )
            sql = sql.replace("MAP_ID", map_id)
            sql = sql.replace("STDS", self.get_type())
            try:
		if dbmi.__name__ == "sqlite3":
		    dbif.cursor.executescript(sql)
		else:
		    dbif.cursor.execute(sql)
            except:
                if connect == True:
                    dbif.close()
		if map.get_layer():
		    core.error(_("Unable to create the space time %s dataset register table for map <%s> with layer %s") % \
                            (map.get_type(), map.get_map_id(), map.get_layer()))
                else:
		    core.error(_("Unable to create the space time %s dataset register table for <%s>") % \
                            (map.get_type(), map.get_map_id()))
                raise

            # Set the stds register table name and put it into the DB
            map.set_stds_register(map_register_table)
            map.metadata.update(dbif)
            
            if map.get_layer():
		core.verbose(_("Created register table <%s> for %s map <%s> with layer %s") % \
				(map_register_table, map.get_type(), map.get_map_id(), map.get_layer()))
	    else:
		core.verbose(_("Created register table <%s> for %s map <%s>") % \
				(map_register_table, map.get_type(), map.get_map_id()))

        # We need to create the table and register it
        if stds_register_table == None:
            # Create table name
            stds_register_table = stds_name + "_" + stds_mapset + "_" + map.get_type() + "_register"
            # Read the SQL template
            sql = open(os.path.join(sql_path, "stds_map_register_table_template.sql"), 'r').read()
            # Create the raster, raster3d and vector tables
            sql = sql.replace("GRASS_MAP", map.get_type())
            sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )
            sql = sql.replace("SPACETIME_ID", self.base.get_id())
            sql = sql.replace("STDS", self.get_type())

            sql_script = ""
            sql_script += "BEGIN TRANSACTION;\n"
            sql_script += sql
            sql_script += "\n"
            sql_script += "END TRANSACTION;"
            try:
		if dbmi.__name__ == "sqlite3":
		    dbif.cursor.executescript(sql_script)
		else:
		    dbif.cursor.execute(sql_script)
                dbif.connection.commit()
            except:
                if connect == True:
                    dbif.close()
		if map.get_layer():
		    core.error(_("Unable to create the space time %s dataset register table for map <%s> with layer %s") % \
                            (map.get_type(), map.get_map_id(), map.get_layer()))
                else:
		    core.error(_("Unable to create the space time %s dataset register table for <%s>") % \
                            (map.get_type(), map.get_map_id()))
                raise

            # Set the map register table name and put it into the DB
            self.set_map_register(stds_register_table)
            self.metadata.update(dbif)

            core.verbose(_("Created register table <%s> for space time %s  dataset <%s>") % \
                          (stds_register_table, map.get_type(), self.get_id()))

        # Register the stds in the map stds register table
        # Check if the entry is already there
	if dbmi.paramstyle == "qmark":
	    sql = "SELECT id FROM " + map_register_table + " WHERE id = ?"
	else:
	    sql = "SELECT id FROM " + map_register_table + " WHERE id = %s"
        dbif.cursor.execute(sql, (self.base.get_id(),))
      	row = dbif.cursor.fetchone()

        # In case of no entry make a new one
        if row == None:
	    if dbmi.paramstyle == "qmark":
		sql = "INSERT INTO " + map_register_table + " (id) " + "VALUES (?)"
	    else:
		sql = "INSERT INTO " + map_register_table + " (id) " + "VALUES (%s)"
            #print sql
            dbif.cursor.execute(sql, (self.base.get_id(),))

        # Now put the raster name in the stds map register table
	if dbmi.paramstyle == "qmark":
	    sql = "INSERT INTO " + stds_register_table + " (id) " + "VALUES (?)"
	else:
	    sql = "INSERT INTO " + stds_register_table + " (id) " + "VALUES (%s)"
        #print sql
        dbif.cursor.execute(sql, (map_id,))

        if connect == True:
            dbif.close()
            
        # increase the counter
        self.map_counter += 1

        return True

    def unregister_map(self, map, dbif = None):
        """Unregister a map from the space time dataset.

           This method takes care of the un-registration of a map
           from a space time dataset.

           @param map: The map object to unregister
           @param dbif: The database interface to be used
        """
        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        if map.is_in_db(dbif) == False:
            dbif.close()
            
	    if map.get_layer():
		core.fatal(_("Unable to find map <%s> with layer %s in temporal database") % (map.get_map_id(), map.get_layer()))
	    else:
		core.fatal(_("Unable to find map <%s> in temporal database") % (map.get_map_id()))

	if map.get_layer():
	    core.verbose(_("Unregister %s map <%s> with layer %s") % (map.get_type(), map.get_map_id(), map.get_layer()))
	else:
	    core.verbose(_("Unregister %s map <%s>") % (map.get_type(), map.get_map_id()))

        # First select all data from the database
        map.select(dbif)
        map_id = map.get_id()
        map_register_table = map.get_stds_register()
        stds_register_table = self.get_map_register()

        # Check if the map is registered in the space time raster dataset
	if dbmi.paramstyle == "qmark":
	    sql = "SELECT id FROM " + map_register_table + " WHERE id = ?"
	else:
	    sql = "SELECT id FROM " + map_register_table + " WHERE id = %s"
        dbif.cursor.execute(sql, (self.base.get_id(),))
      	row = dbif.cursor.fetchone()

        # Break if the map is not registered
        if row == None:
	    if map.get_layer():
		core.warning(_("Map <%s> with layer %s is not registered in space time dataset <%s>") %(map.get_map_id(), map.get_layer(), self.base.get_id()))
	    else:
		core.warning(_("Map <%s> is not registered in space time dataset <%s>") %(map.get_map_id(), self.base.get_id()))
            if connect == True:
                dbif.close()
            return False

        # Remove the space time raster dataset from the raster dataset register
        if map_register_table != None:
	    if dbmi.paramstyle == "qmark":
		sql = "DELETE FROM " + map_register_table + " WHERE id = ?"
	    else:
		sql = "DELETE FROM " + map_register_table + " WHERE id = %s"
            dbif.cursor.execute(sql, (self.base.get_id(),))

        # Remove the raster map from the space time raster dataset register
        if stds_register_table != None:
	    if dbmi.paramstyle == "qmark":
		sql = "DELETE FROM " + stds_register_table + " WHERE id = ?"
	    else:
		sql = "DELETE FROM " + stds_register_table + " WHERE id = %s"
            dbif.cursor.execute(sql, (map_id,))

        if connect == True:
            dbif.close()

        # decrease the counter
        self.map_counter -= 1
            
    def update_from_registered_maps(self, dbif = None):
        """This methods updates the spatial and temporal extent as well as
           type specific metadata. It should always been called after maps are registered
           or unregistered/deleted from the space time dataset.

           The update of the temporal extent checks if the end time is set correctly.
           In case the registered maps have no valid end time (None) the maximum start time
           will be used. If the end time is earlier than the maximum start time, it will
           be replaced by the maximum start time.

           An other solution to automate this is to use the deactivated trigger
           in the SQL files. But this will result in a huge performance issue
           in case many maps are registered (>1000).
           
           @param dbif: The database interface to be used
        """
        core.verbose(_("Update metadata, spatial and temporal extent from all registered maps of <%s>") % (self.get_id()))

        # Nothing to do if the register is not present
        if not self.get_map_register():
            return

        connect = False

        if dbif == None:
            dbif = sql_database_interface()
            dbif.connect()
            connect = True

        map_time = None

        use_start_time = False

        # Get basic info
        stds_name = self.base.get_name()
        stds_mapset = self.base.get_mapset()
        sql_path = get_sql_template_path()

        #We create a transaction
        sql_script = ""
        sql_script += "BEGIN TRANSACTION;\n"
        
        # Update the spatial and temporal extent from registered maps
        # Read the SQL template
        sql = open(os.path.join(sql_path, "update_stds_spatial_temporal_extent_template.sql"), 'r').read()
        sql = sql.replace("GRASS_MAP", self.get_new_map_instance(None).get_type())
        sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )
        sql = sql.replace("SPACETIME_ID", self.base.get_id())
        sql = sql.replace("STDS", self.get_type())

        sql_script += sql
        sql_script += "\n"

        # Update type specific metadata
        sql = open(os.path.join(sql_path, "update_" + self.get_type() + "_metadata_template.sql"), 'r').read()
        sql = sql.replace("GRASS_MAP", self.get_new_map_instance(None).get_type())
        sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )
        sql = sql.replace("SPACETIME_ID", self.base.get_id())
        sql = sql.replace("STDS", self.get_type())

        sql_script += sql
        sql_script += "\n"

        sql_script += "END TRANSACTION;"

	if dbmi.__name__ == "sqlite3":
	    dbif.cursor.executescript(sql_script)
	else:
	    dbif.cursor.execute(sql_script)
	    
        # Read and validate the selected end time
        self.select()

        if self.is_time_absolute():
            start_time, end_time, tz = self.get_absolute_time()
        else:
            start_time, end_time, unit = self.get_relative_time()

        # In case no end time is set, use the maximum start time of all registered maps as end time
        if end_time == None:
            use_start_time = True
        else:
            # Check if the end time is smaller than the maximum start time
            if self.is_time_absolute():
                sql = """SELECT max(start_time) FROM GRASS_MAP_absolute_time WHERE GRASS_MAP_absolute_time.id IN
                        (SELECT id FROM SPACETIME_NAME_GRASS_MAP_register);"""
                sql = sql.replace("GRASS_MAP", self.get_new_map_instance(None).get_type())
                sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )
            else:
                sql = """SELECT max(start_time) FROM GRASS_MAP_relative_time WHERE GRASS_MAP_relative_time.id IN
                        (SELECT id FROM SPACETIME_NAME_GRASS_MAP_register);"""
                sql = sql.replace("GRASS_MAP", self.get_new_map_instance(None).get_type())
                sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )

            dbif.cursor.execute(sql)
            row = dbif.cursor.fetchone()

            if row != None:
                # This seems to be a bug in sqlite3 Python driver
		if dbmi.__name__ == "sqlite3":
		    tstring = row[0]
		    # Convert the unicode string into the datetime format
                    if self.is_time_absolute():
                        if tstring.find(":") > 0:
                            time_format = "%Y-%m-%d %H:%M:%S"
                        else:
                            time_format = "%Y-%m-%d"

		        max_start_time = datetime.strptime(tstring, time_format)
                    else:
		        max_start_time = row[0]
		else:
		    max_start_time = row[0]

		if end_time < max_start_time:
		    use_start_time = True
		    
        # Set the maximum start time as end time
        if use_start_time:
            if self.is_time_absolute():
                sql = """UPDATE STDS_absolute_time SET end_time =
               (SELECT max(start_time) FROM GRASS_MAP_absolute_time WHERE GRASS_MAP_absolute_time.id IN
                        (SELECT id FROM SPACETIME_NAME_GRASS_MAP_register)
               ) WHERE id = 'SPACETIME_ID';"""
                sql = sql.replace("GRASS_MAP", self.get_new_map_instance(None).get_type())
                sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )
                sql = sql.replace("SPACETIME_ID", self.base.get_id())
                sql = sql.replace("STDS", self.get_type())
            elif self.is_time_relative():
                sql = """UPDATE STDS_relative_time SET end_time =
               (SELECT max(start_time) FROM GRASS_MAP_relative_time WHERE GRASS_MAP_relative_time.id IN
                        (SELECT id FROM SPACETIME_NAME_GRASS_MAP_register)
               ) WHERE id = 'SPACETIME_ID';"""
                sql = sql.replace("GRASS_MAP", self.get_new_map_instance(None).get_type())
                sql = sql.replace("SPACETIME_NAME", stds_name + "_" + stds_mapset )
                sql = sql.replace("SPACETIME_ID", self.base.get_id())
                sql = sql.replace("STDS", self.get_type())

	    if dbmi.__name__ == "sqlite3":
		dbif.cursor.executescript(sql)
	    else:
		dbif.cursor.execute(sql)

        # Count the temporal map types
        maps = self.get_registered_maps_as_objects(dbif=dbif)
        tlist = self.count_temporal_types(maps)

        if tlist["interval"] > 0 and tlist["point"] == 0 and tlist["invalid"] == 0:
            map_time = "interval"
        elif tlist["interval"] == 0 and tlist["point"] > 0 and tlist["invalid"] == 0:
            map_time = "point"
        elif tlist["interval"] > 0 and tlist["point"] > 0 and tlist["invalid"] == 0:
            map_time = "mixed"
        else:
            map_time = "invalid"

        # Compute the granularity

        if map_time != "invalid":
            # Smallest supported temporal resolution
            if self.is_time_absolute():
                gran = compute_absolute_time_granularity(maps)
            elif self.is_time_relative():
                gran = compute_relative_time_granularity(maps)
        else:
            gran = None

        # Set the map time type and update the time objects
        if self.is_time_absolute():
            self.absolute_time.select(dbif)
            self.metadata.select(dbif)
            if self.metadata.get_number_of_maps() > 0:
                self.absolute_time.set_map_time(map_time)
                self.absolute_time.set_granularity(gran)
            else:
                self.absolute_time.set_map_time(None)
                self.absolute_time.set_granularity(None)
            self.absolute_time.update_all(dbif)
        else:
            self.relative_time.select(dbif)
            self.metadata.select(dbif)
            if self.metadata.get_number_of_maps() > 0:
                self.relative_time.set_map_time(map_time)
                self.relative_time.set_granularity(gran)
            else:
                self.relative_time.set_map_time(None)
                self.relative_time.set_granularity(None)
            self.relative_time.update_all(dbif)

        if connect == True:
            dbif.close()

###############################################################################

def create_temporal_relation_sql_where_statement(start, end, use_start=True, use_during=False, 
                                        use_overlap=False, use_contain=False, use_equal=False):
    """ Create a SQL WHERE statement for temporal relation selection of maps in space time datasets

        @param start: The start time
        @param end: The end time
        @param use_start: Select maps of which the start time is located in the selection granule
                         map    :        s
                         granule:  s-----------------e

                         map    :        s--------------------e
                         granule:  s-----------------e

                         map    :        s--------e
                         granule:  s-----------------e

        @param use_during: during: Select maps which are temporal during the selection granule
                         map    :     s-----------e
                         granule:  s-----------------e

        @param use_overlap: Select maps which temporal overlap the selection granule
                         map    :     s-----------e
                         granule:        s-----------------e

                         map    :     s-----------e
                         granule:  s----------e

        @param use_contain: Select maps which temporally contain the selection granule
                         map    :  s-----------------e
                         granule:     s-----------e

        @param use_equal: Select maps which temporally equal to the selection granule
                         map    :  s-----------e
                         granule:  s-----------e
    """

    where = "("

    if use_start:
        where += "(start_time >= '%s' and start_time < '%s') " % (start, end)

    if use_during:
        if use_start:
            where += " OR "
        where += "((start_time > '%s' and end_time < '%s') OR " % (start, end)
        where += "(start_time >= '%s' and end_time < '%s') OR " % (start, end)
        where += "(start_time > '%s' and end_time <= '%s'))" % (start, end)

    if use_overlap:
        if use_start or use_during:
            where += " OR "

        where += "((start_time < '%s' and end_time > '%s' and end_time < '%s') OR " % (start, start, end)
        where += "(start_time < '%s' and start_time > '%s' and end_time > '%s'))" % (end, start, end)

    if use_contain:
        if use_start or use_during or use_overlap:
            where += " OR "

        where += "((start_time < '%s' and end_time > '%s') OR " % (start, end)
        where += "(start_time <= '%s' and end_time > '%s') OR " % (start, end)
        where += "(start_time < '%s' and end_time >= '%s'))" % (start, end)

    if use_equal:
        if use_start or use_during or use_overlap or use_contain:
            where += " OR "

        where += "(start_time = '%s' and end_time = '%s')" % (start, end)

    where += ")"

    return where


