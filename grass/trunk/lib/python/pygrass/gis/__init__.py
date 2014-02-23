# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7

from __future__ import (nested_scopes, generators, division, absolute_import,
                        with_statement, print_function, unicode_literals)
from os import listdir
from os.path import join, exists, isdir
import shutil
import ctypes as ct
import fnmatch

from grass import script
#from grass.script import setup
#
#
#GISBASE = "/home/pietro/docdat/src/gis/grass/grass70/dist.x86_64-unknown-linux-gnu"
#LOCATION = "nc_basic_spm_grass7'"
#GISDBASE = "/home/pietro/docdat/gis"
#MAPSET = "sqlite"
#GUI = "wxpython"
#
#setup.init(GISBASE, GISDBASE, LOCATION, MAPSET)
script.gisenv()

import grass.lib.gis as libgis
from grass.pygrass.functions import getenv
from grass.pygrass.errors import GrassError
from . import region


#write dec to check if user have permissions or not

ETYPE = {'rast': libgis.G_ELEMENT_RASTER,
         'rast3d': libgis.G_ELEMENT_RASTER3D,
         'vect': libgis.G_ELEMENT_VECTOR,
         'oldvect': libgis.G_ELEMENT_OLDVECTOR,
         'asciivect': libgis.G_ELEMENT_ASCIIVECTOR,
         'icon': libgis.G_ELEMENT_ICON,
         'labels': libgis.G_ELEMENT_LABEL,
         'sites': libgis.G_ELEMENT_SITE,
         'region': libgis.G_ELEMENT_REGION,
         'region3d': libgis.G_ELEMENT_REGION3D,
         'group': libgis.G_ELEMENT_GROUP,
         'view3d': libgis.G_ELEMENT_3DVIEW}


CHECK_IS = {"GISBASE": libgis.G_is_gisbase,
            "GISDBASE": lambda x: True,
            "LOCATION_NAME": libgis.G_is_location,
            "MAPSET": libgis.G_is_mapset}


def _check(value, path, type):
    if value and CHECK_IS[type](join(path, value)):
        return value
    elif value is '':
        return getenv(type)
    else:
        raise GrassError("%s <%s> not found." % (type.title(),
                                                 join(path, value)))


def set_current_mapset(mapset, location=None, gisdbase=None):
    libgis.G_setenv('MAPSET', mapset)
    if location:
        libgis.G_setenv('LOCATION_NAME', location)
    if gisdbase:
        libgis.G_setenv('GISDBASE', gisdbase)


def make_mapset(mapset, location=None, gisdbase=None):
    res = libgis.G_make_mapset(gisdbase, location, mapset)
    if res == -1:
        raise GrassError("I cannot create a new mapset.")
    elif res == -2:
        raise GrassError("Illegal name.")


class Gisdbase(object):
    """Return Gisdbase object. ::

        >>> from grass.script.core import gisenv
        >>> gisdbase = Gisdbase()
        >>> gisdbase.name == gisenv()['GISDBASE']
        True

    """
    def __init__(self, gisdbase=''):
        self.name = gisdbase

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = _check(name, '', "GISDBASE")

    name = property(fget=_get_name, fset=_set_name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Gisdbase(%s)' % self.name

    def __getitem__(self, location):
        """Return a Location object. ::

            >>> from grass.script.core import gisenv
            >>> loc_env = gisenv()['LOCATION_NAME']
            >>> gisdbase = Gisdbase()
            >>> loc_py = gisdbase[loc_env]
            >>> loc_env == loc_py.name
            True

        ..
        """
        if location in self.locations():
            return Location(location, self.name)
        else:
            raise KeyError('Location: %s does not exist' % location)

    def __iter__(self):
        for loc in self.locations():
            yield Location(loc, self.name)

    def new_location(self):
        if libgis.G__make_location() != 0:
            raise GrassError("I cannot create a new mapset.")

    def locations(self):
        """Return a list of locations that are available in the gisdbase: ::

            >>> gisdbase = Gisdbase()
            >>> gisdbase.locations()                     # doctest: +ELLIPSIS
            [...]

        ..
        """
        locations = []
        for loc in listdir(self.name):
            if libgis.G_is_location(join(self.name, loc)):
                locations.append(loc)
        locations.sort()
        return locations


class Location(object):
    """Location object ::

        >>> from grass.script.core import gisenv
        >>> location = Location()
        >>> location                                      # doctest: +ELLIPSIS
        Location(...)
        >>> location.gisdbase == gisenv()['GISDBASE']
        True
        >>> location.name == gisenv()['LOCATION_NAME']
        True
    """
    def __init__(self, location='', gisdbase=''):
        self.gisdbase = gisdbase
        self.name = location

    def _get_gisdb(self):
        return self._gisdb

    def _set_gisdb(self, gisdb):
        self._gisdb = _check(gisdb, '', "GISDBASE")

    gisdbase = property(fget=_get_gisdb, fset=_set_gisdb)

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = _check(name, self._gisdb, "LOCATION_NAME")

    name = property(fget=_get_name, fset=_set_name)

    def __getitem__(self, mapset):
        if mapset in self.mapsets():
            return Mapset(mapset)
        else:
            raise KeyError('Mapset: %s does not exist' % mapset)

    def __iter__(self):
        lpath = self.path()
        return (m for m in listdir(lpath)
                if (isdir(join(lpath, m)) and _check(m, lpath, "MAPSET")))

    def __len__(self):
        return len(self.mapsets())

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Location(%r)' % self.name

    def mapsets(self, pattern=None, permissions=True):
        """Return a list of the available mapsets. ::

            >>> location = Location()
            >>> location.mapsets()
            ['PERMANENT', 'user1']
        """
        mapsets = [mapset for mapset in self]
        if permissions:
            mapsets = [mapset for mapset in mapsets
                       if libgis.G__mapset_permissions(mapset)]
        if pattern:
            return fnmatch.filter(mapsets, pattern)
        return mapsets

    def path(self):
        return join(self.gisdbase, self.name)


class Mapset(object):
    """Mapset ::

        >>> mapset = Mapset()
        >>> mapset
        Mapset('user1')
        >>> mapset.gisdbase                               # doctest: +ELLIPSIS
        '/home/...'
        >>> mapset.location
        'nc_basic_spm_grass7'
        >>> mapset.name
        'user1'
    """
    def __init__(self, mapset='', location='', gisdbase=''):
        self.gisdbase = gisdbase
        self.location = location
        self.name = mapset
        self.visible = VisibleMapset(self.name, self.location, self.gisdbase)

    def _get_gisdb(self):
        return self._gisdb

    def _set_gisdb(self, gisdb):
        self._gisdb = _check(gisdb, '', "GISDBASE")

    gisdbase = property(fget=_get_gisdb, fset=_set_gisdb)

    def _get_loc(self):
        return self._loc

    def _set_loc(self, loc):
        self._loc = _check(loc, self._gisdb, "LOCATION_NAME")

    location = property(fget=_get_loc, fset=_set_loc)

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = _check(name, join(self._gisdb, self._loc), "MAPSET")

    name = property(fget=_get_name, fset=_set_name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Mapset(%r)' % self.name

    def glist(self, type, pattern=None):
        """Return a list of grass types like:

            * 'asciivect',
            * 'group',
            * 'icon',
            * 'labels',
            * 'oldvect',
            * 'rast',
            * 'rast3d',
            * 'region',
            * 'region3d',
            * 'sites',
            * 'vect',
            * 'view3d'

        ::

            >>> mapset = Mapset('PERMANENT')
            >>> rast = mapset.glist('rast')
            >>> rast.sort()
            >>> rast                                      # doctest: +ELLIPSIS
            ['basins', 'elevation', ...]
            >>> mapset.glist('rast', pattern='el*')
            ['elevation_shade', 'elevation']
        """
        if type not in ETYPE:
            str_err = "Type %s is not valid, valid types are: %s."
            raise TypeError(str_err % (type, ', '.join(ETYPE.keys())))
        clist = libgis.G_list(ETYPE[type], self.gisdbase,
                              self.location, self.name)
        elist = []
        for el in clist:
            el_name = ct.cast(el, ct.c_char_p).value
            if el_name:
                elist.append(el_name)
            else:
                if pattern:
                    return fnmatch.filter(elist, pattern)
                return elist

    def is_current(self):
        return (self.name == libgis.G_getenv('MAPSET') and
                self.location == libgis.G_getenv('LOCATION_NAME') and
                self.gisdbase == libgis.G_getenv('GISDBASE'))

    def current(self):
        """Set the mapset as current"""
        set_current_mapset(self.name, self.location, self.gisdbase)

    def delete(self):
        """Delete the mapset"""
        if self.is_current():
            raise GrassError('The mapset is in use.')
        shutil.rmtree(self.path())

    def path(self):
        return join(self.gisdbase, self.location, self.name)


class VisibleMapset(object):
    def __init__(self, mapset, location='', gisdbase=''):
        self.mapset = mapset
        self.location = Location(location, gisdbase)
        self._list = []
        self.spath = join(self.location.path(), self.mapset, 'SEARCH_PATH')

    def __repr__(self):
        return repr(self.read())

    def __iter__(self):
        for mapset in self.read():
            yield mapset

    def read(self):
        with open(self.spath, "a+") as f:
            lines = f.readlines()
            #lines.remove('')
            if lines:
                return [l.strip() for l in lines]
        lns = ['PERMANENT', ]
        self.write(lns)
        return lns

    def write(self, mapsets):
        with open(self.spath, "w+") as f:
            ms = self.location.mapsets()
            f.write('%s' % '\n'.join([m for m in mapsets if m in ms]))

    def add(self, mapset):
        if mapset not in self.read() and mapset in self.location:
            with open(self.spath, "a+") as f:
                f.write('\n%s' % mapset)
        else:
            raise TypeError('Mapset not found')

    def remove(self, mapset):
        mapsets = self.read()
        mapsets.remove(mapset)
        self.write(mapsets)

    def extend(self, mapsets):
        ms = self.location.mapsets()
        final = self.read()
        final.extend([m for m in mapsets if m in ms and m not in final])
        self.write(final)
