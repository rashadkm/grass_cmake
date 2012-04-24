"""!@package grass.temporal

@brief GRASS Python scripting module (temporal GIS functions)

Temporal GIS related functions to be used in temporal GIS Python library package.

Usage:

@code
import grass.temporal as tgis

tgis.print_temporal_relations(maps)
...
@endcode

(C) 2008-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""
from abstract_map_dataset import *
from datetime_math import *

class temporal_topology_builder(object):
    """!This class is designed to build the temporal topology based on a list of maps
    
	Example:
	
	# We have a space time raster dataset and build a map list
	# from all registered maps ordered by start time
	maps = strds.get_registered_maps_as_objects()
	
	# Now lets build the temporal topology of the maps in the list
	tb = temporal_topology_builder()
	tb.build(maps, True)
	
	for _map in tb:
	    _map.print_temporal_topology_info()
	    _follows = _map.get_follows()
	    if _follows:
		for f in _follows:
		    f.print_temporal_topology_info()
	    
	# Using the next and previous methods, we can iterate over the 
	# topological related maps in this way
	
	_first = tb.get_first()
	
	while _first:
	    _first.print_temporal_topology_info()
	    _first = _first.next()
	
	# Dictionary like accessed
	_map = tb["name@mapset"]
	       
    
    """
    def __init__(self):
	self._reset()
        
    def _reset(self):
        self._store = {}
        self._first = None

    def _set_first(self, first):
        self._first = first
        self._insert(first)        
        
    def _detect_first(self):
	if len(self) > 0:
	    _prev = self._store.values()[0]
	    while _prev != None:
		self._first = _prev
		_prev = _prev.prev()
		
    def _insert(self, t):
        self._store[t.get_id()] = t
        
    def get_first(self):
	"""!Return the first map with the earliest start time
	
	   @return The map with the earliest start time
	"""
	return self._first
	
    def build(self, maps, is_sorted = False):
	"""!Build the temporal topology structure
	
	   This method builds the temporal topology based on all maps in the provided map list.
	   The temporal topology structure of each map, defined in class temporal_map_relations,
	   will be reseted and rebuild. 
	   
	   After building the temporal topology the modified map objects can be accessed 
	   in the same way as a dictionary using there id. The implemented iterator assures 
	   the chronological iteration over the maps.
	   
	   
	   @param maps: A list of abstract_dataset objects with initiated temporal extent
	   @param is_sorted Set to True if the map list is sorted by start time, sorting will dramatically reduce computation time
	"""
	for _map in maps:
	    _map.reset_temporal_topology()
	
	for i in xrange(len(maps)):
	    if is_sorted:
		offset = i + 1
		found_next = False
	    else:
		offset = 0
		# Needed for "next" computation 
		start0, end0 = maps[i].get_valid_time()
	    
	    for j in xrange(offset, len(maps)):
		
		# Do not build topology of the same maps
		if maps[i] == maps[j]:
		    continue
		
		# Get the temporal relationship
		relation = maps[j].temporal_relation(maps[i])
		
		# We can skip several relationships if not sorted
		if not is_sorted:
		    if relation == "before":
			continue
		    if relation == "precedes":
			continue
		    if relation == "overlapped":
			continue
		    if relation == "finished":
			continue
		
		# Build the next reference
		if is_sorted:
		    if not found_next and relation != "equivalent" and relation != "started":
			maps[i].set_next(maps[j])
			found_next = True
		else: 
		    start2, end2 = maps[j].get_valid_time()
		    if maps[i].next():
			start1, end1 = maps[i].next().get_valid_time()
			if start2 > start0 and start2 < start1:
			    maps[i].set_next(maps[j])
		    else:
			if start2 > start0:
			    maps[i].set_next(maps[j])
			    
		# The start time of map j is equal or later than map i
		if relation == "equivalent":
		    maps[j].append_equivalent(maps[i])
		    maps[i].append_equivalent(maps[j])
		elif relation == "follows":
		    maps[j].append_follows(maps[i])
		    maps[i].append_precedes(maps[j])
		elif relation == "during" or relation == "starts" or relation == "finishes":
		    maps[j].append_during(maps[i])
		    maps[i].append_contains(maps[j])
		elif relation == "started":
		    # Consider equal start time, in case "started" map j contains map i
		    maps[j].append_contains(maps[i])
		    maps[i].append_during(maps[j])
		elif relation == "overlaps":
		    maps[j].append_overlaps(maps[i])
		    maps[i].append_overlapped(maps[j])

		# Break if the last map follows
		if relation == "follows":
		    if j < len(maps) - 1:
			relation = maps[j + 1].temporal_relation(maps[i])
			if relation == "after":
			    break
		# Break if the the next map is after
		if relation == "after":
		    break 
	
	# Build the previous pointer and store the map internally
	for _map in maps:
	    _next = _map.next()
	    if _next:
		_next.set_prev(_map)
	    _map.set_temporal_topology_build_true()
	    self._insert(_map)
	
	# Detect the first map
	self._detect_first()
	
    def __iter__(self):
        _start = self._first
        while _start != None:
            yield _start
            _start = _start.next()

    def __getitem__(self, index):
        return self._store[index.get_id()]

    def __len__(self):
        return len(self._store)

    def __contains__(self, _map):
        return _map in self._store.values()


def print_temporal_relations(maps1, maps2):
    """!Print the temporal relation matrix of the temporal ordered map lists maps1 and maps2
       to stdout.
	
	@param maps1: a ordered by start_time list of map objects with initiated temporal extent
	@param maps2: a ordered by start_time list of map objects with initiated temporal extent
    """
    
    identical = False
    use_id = True
    
    if maps1 == maps2:
	identical = True
	use_id = False

    for i in range(len(maps1)):
	if identical == True:
	    start = i + 1
	else:
	    start = 0
	for j in range(start, len(maps2)):
	    relation = maps1[j].temporal_relation(maps2[i])

	    if use_id == False:
		print maps2[j].base.get_name(), relation, maps1[i].base.get_name()
	    else:
		print maps2[j].base.get_id(), relation, maps1[i].base.get_id()

	    # Break if the last map follows
	    if relation == "follows":
		if j < len(maps1) - 1:
		    relation = maps1[j + 1].temporal_relation(maps2[i])
		    if relation == "after":
			break
	    # Break if the the next map is after
	    if relation == "after":
		break

def get_temporal_relation_matrix(maps1, maps2):
    """!Return the temporal relation matrix of two map lists

	Booth map lists must be ordered by start time

	The temporal relationship matrix includes the temporal relations between
	the two map lists. Returned is a nested dict representing 
	a sparse (upper right side in case maps1 == maps2) relationship matrix.
	
	@param maps1: A sorted (start_time) list of abstract_dataset objects with initiated temporal extent
	@param maps2: A sorted (start_time) list of abstract_dataset objects with initiated temporal extent
    """

    matrix = {}
    identical = False
    
    if maps1 == maps2:
	identical = True

    for i in range(len(maps1)):
	if identical == True:
	    start = i + 1
	else:
	    start = 0
	    
	row = {}
	    
	for j in range(start, len(maps2)):
	    relation = maps1[j].temporal_relation(maps2[i])

	    row[maps2[j].base.get_id()] = relation 

	    # Break if the last map follows
	    if relation == "follows":
		if j < len(maps1) - 1:
		    relation = maps1[j + 1].temporal_relation(maps2[i])
		    if relation == "after":
			break
	    # Break if the the next map is after
	    if relation == "after":
		break

	matrix[maps1[i].base.get_id()] = row

    return matrix

def count_temporal_relations(maps1, maps2):
    """!Count the temporal relations between the two lists of maps

	The map lists must be ordered by start time. Temporal relations are counted 
	by analyzing the sparse (upper right side in case maps1 == maps2) temporal relationships matrix.

	@param maps1: A sorted (start_time) list of abstract_dataset objects with initiated temporal extent
	@param maps2: A sorted (start_time) list of abstract_dataset objects with initiated temporal extent
	@return A dictionary with counted temporal relationships
    """
    
    tcount = {}
    identical = False
    
    if maps1 == maps2:
	identical = True

    for i in range(len(maps1)):
	if identical == True:
	    start = i + 1
	else:
	    start = 0
	for j in range(start, len(maps2)):
	    relation = maps1[j].temporal_relation(maps2[i])

	    if relation == "before":
		continue
	    
	    if tcount.has_key(relation):
		tcount[relation] = tcount[relation] + 1
	    else:
		tcount[relation] = 1

	    # Break if the last map follows
	    if relation == "follows":
		if j < len(maps1) - 1:
		    relation = maps1[j + 1].temporal_relation(maps2[i])
		    if relation == "after":
			break
	    # Break if the the next map is after
	    if relation == "after":
		break  

    return tcount

