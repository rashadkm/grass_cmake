"""!@package grass.script.raster

@brief GRASS Python scripting module (raster functions)

Raster related functions to be used in Python scripts.

Usage:

@code
from grass.script import raster as grass

grass.raster_history(map)
...
@endcode

(C) 2008-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Glynn Clements
@author Martin Landa <landa.martin gmail.com>
"""

import os
import string

from core import *

# add raster history

def raster_history(map):
    """!Set the command history for a raster map to the command used to
    invoke the script (interface to `r.support').

    @param map map name

    @return True on success
    @return False on failure
    """
    current_mapset = gisenv()['MAPSET']
    if find_file(name = map)['mapset'] == current_mapset:
        run_command('r.support', map = map, history = os.environ['CMDLINE'])
        return True
    
    warning(_("Unable to write history for <%(map)s>. "
              "Raster map <%(map)s> not found in current mapset." % { 'map' : map, 'map' : map}))
    return False

# run "r.info -gre ..." and parse output

def raster_info(map):
    """!Return information about a raster map (interface to
    `r.info'). Example:

    \code
    >>> grass.raster_info('elevation')
    {'north': 228500.0, 'timestamp': '"none"', 'min': 55.578792572021499,
    'datatype': 'FCELL', 'max': 156.32986450195301, 'ewres': 10.0,
    'vertical_datum': '', 'west': 630000.0, 'units': '',
    'title': 'South-West Wake county: Elevation NED 10m (elev_ned10m)',
    'east': 645000.0, 'nsres': 10.0, 'south': 215000.0}
    \endcode

    @param map map name
    
    @return parsed raster info
    """

    def float_or_null(s):
        if s == 'NULL':
            return None
        else:
            return float(s)

    s = read_command('r.info', flags = 'gre', map = map)
    kv = parse_key_val(s)
    for k in ['min', 'max']:
	kv[k] = float_or_null(kv[k])
    for k in ['north', 'south', 'east', 'west']:
	kv[k] = float(kv[k])
    for k in ['nsres', 'ewres']:
	kv[k] = float_or_dms(kv[k])
    return kv

# interface to r.mapcalc

def mapcalc(exp, quiet = False, verbose = False, overwrite = False, **kwargs):
    """!Interface to r.mapcalc.

    @param exp expression
    @param kwargs
    """
    t = string.Template(exp)
    e = t.substitute(**kwargs)

    if run_command('r.mapcalc', expression = e,
                   quiet = quiet,
                   verbose = verbose,
                   overwrite = overwrite) != 0:
	fatal(_("An error occurred while running r.mapcalc"))


def mapcalc_start(exp, quiet = False, verbose = False, overwrite = False, **kwargs):
    """!Interface to r.mapcalc, doesn't wait for it to finish, returns Popen object.

    \code
    >>> expr1 = '"%s" = "%s" * 10' % (output, input)
    >>> p1 = grass.mapcalc_start(expr1, stdout = subprocess.PIPE)
    >>> print p1
    <subprocess.Popen object at 0xb7c12f6c>
    >>> # start other jobs now ...
    
    >>> # collect the results and wait for them to finish:
    >>> if not p1.stdout.closed:
    ...     pout1 = p1.communicate()[0]
    >>> p1.wait()
    \endcode

    (maybe stdout = subprocess.PIPE and p1.stdout.closed can be avoided)

    @param exp expression
    @param kwargs
    
    @return Popen object
    """
    t = string.Template(exp)
    e = t.substitute(**kwargs)

    return start_command('r.mapcalc', expression = e,
                        quiet = quiet,
                        verbose = verbose,
                        overwrite = overwrite)
