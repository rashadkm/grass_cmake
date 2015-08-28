# -*- coding: utf-8 -*-
from __future__ import (nested_scopes, generators, division, absolute_import,
                        with_statement, print_function, unicode_literals)
import os
import ctypes
import numpy as np

#
# import GRASS modules
#
from grass.script import fatal, warning
from grass.script import core as grasscore

import grass.lib.gis as libgis
import grass.lib.raster as libraster
import grass.lib.rowio as librowio

libgis.G_gisinit('')

#
# import pygrass modules
#
from grass.pygrass.errors import OpenError, must_be_open
from grass.pygrass.gis.region import Region
from grass.pygrass import utils

#
# import raster classes
#
from grass.pygrass.raster.abstract import RasterAbstractBase
from grass.pygrass.raster.raster_type import TYPE as RTYPE, RTYPE_STR
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.raster.segment import Segment
from grass.pygrass.raster.rowio import RowIO

test_raster_name="Raster_test_map"

class RasterRow(RasterAbstractBase):
    """Raster_row_access": Inherits: "Raster_abstract_base" and implements
    the default row access of the Rast library.

        * Implements row access using row id
        * The get_row() method must accept a Row object as argument that will
          be used for value storage, so no new buffer will be allocated
        * Implements sequential writing of rows
        * Implements indexed value read only access using the [row][col]
          operator
        * Implements the [row] read method that returns a new Row object
        * Writing is limited using the put_row() method which accepts a
          Row as argument
        * No mathematical operation like __add__ and stuff for the Raster
          object (only for rows), since r.mapcalc is more sophisticated and
          faster

        Examples:

        >>> elev = RasterRow(test_raster_name)
        >>> elev.exist()
        True
        >>> elev.is_open()
        False
        >>> elev.open()
        >>> elev.is_open()
        True
        >>> elev.has_cats()
        True
        >>> elev.mode
        u'r'
        >>> elev.mtype
        'CELL'
        >>> elev.num_cats()
        16
        >>> elev.info.range
        (11, 44)
        >>> elev.info.cols
        4
        >>> elev.info.rows
        4

        >>> elev.hist.read()
        >>> elev.hist.title = "A test map"
        >>> elev.hist.write()
        >>> elev.hist.title
        'A test map'
        >>> elev.hist.keyword
        'This is a test map'

        Each Raster map have an attribute call ``cats`` that allow user
        to interact with the raster categories.

        >>> elev.cats             # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [('A', 11, None),
         ('B', 12, None),
        ...
         ('P', 44, None)]

        Open a raster map using the *with statement*:

        >>> with RasterRow(test_raster_name) as elev:
        ...     for row in elev:
        ...         row
        Buffer([11, 21, 31, 41], dtype=int32)
        Buffer([12, 22, 32, 42], dtype=int32)
        Buffer([13, 23, 33, 43], dtype=int32)
        Buffer([14, 24, 34, 44], dtype=int32)

        >>> elev.is_open()
        False

    """
    def __init__(self, name, mapset='', *args, **kargs):
        super(RasterRow, self).__init__(name, mapset, *args, **kargs)

    # mode = "r", method = "row",
    @must_be_open
    def get_row(self, row, row_buffer=None):
        """Private method that return the row using the read mode
            call the `Rast_get_row` C function.

            :param row: the number of row to obtain
            :type row: int
            :param row_buffer: Buffer object instance with the right dim and type
            :type row_buffer: Buffer

            >>> elev = RasterRow(test_raster_name)
            >>> elev.open()
            >>> elev[0]
            Buffer([11, 21, 31, 41], dtype=int32)
            >>> elev.get_row(0)
            Buffer([11, 21, 31, 41], dtype=int32)

        """
        if row_buffer is None:
            row_buffer = Buffer((self._cols,), self.mtype)
        libraster.Rast_get_row(self._fd, row_buffer.p, row, self._gtype)
        return row_buffer

    @must_be_open
    def put_row(self, row):
        """Private method to write the row sequentially.

        :param row: a Row object to insert into raster
        :type row: Buffer object
        """
        libraster.Rast_put_row(self._fd, row.p, self._gtype)

    def open(self, mode=None, mtype=None, overwrite=None):
        """Open the raster if exist or created a new one.

        :param str mode: Specify if the map will be open with read or write mode
                     ('r', 'w')
        :param str type: If a new map is open, specify the type of the map(`CELL`,
                     `FCELL`, `DCELL`)
        :param bool overwrite: Use this flag to set the overwrite mode of existing
                          raster maps

        if the map already exist, automatically check the type and set:

            * self.mtype

        Set all the privite, attributes:

            * self._fd;
            * self._gtype
            * self._rows and self._cols

        """
        self.mode = mode if mode else self.mode
        self.mtype = mtype if mtype else self.mtype
        self.overwrite = overwrite if overwrite is not None else self.overwrite

        if self.mode == 'r':
            if self.exist():
                self.info.read()
                self.cats.mtype = self.mtype
                self.cats.read()
                self.hist.read()
                self._fd = libraster.Rast_open_old(self.name, self.mapset)
                self._gtype = libraster.Rast_get_map_type(self._fd)
                self.mtype = RTYPE_STR[self._gtype]
            else:
                str_err = _("The map does not exist, I can't open in 'r' mode")
                raise OpenError(str_err)
        elif self.mode == 'w':
            if self.exist():
                if not self.overwrite:
                    str_err = _("Raster map <{0}> already exists"
                                " and will be not overwritten")
                    raise OpenError(str_err.format(self))
            if self._gtype is None:
                raise OpenError(_("Raster type not defined"))
            self._fd = libraster.Rast_open_new(self.name, self._gtype)
        else:
            raise OpenError("Open mode: %r not supported,"
                            " valid mode are: r, w")
        # read rows and cols from the active region
        self._rows = libraster.Rast_window_rows()
        self._cols = libraster.Rast_window_cols()


class RasterRowIO(RasterRow):
    """Raster_row_cache_access": The same as "Raster_row_access" but uses
    the ROWIO library for cached row access
    """
    def __init__(self, name, *args, **kargs):
        self.rowio = RowIO()
        super(RasterRowIO, self).__init__(name, *args, **kargs)

    def open(self, mode=None, mtype=None, overwrite=False):
        """Open the raster if exist or created a new one.

        :param mode: specify if the map will be open with read or write mode
                     ('r', 'w')
        :type mode: str
        :param type: if a new map is open, specify the type of the map(`CELL`,
                     `FCELL`, `DCELL`)
        :type type: str
        :param overwrite: use this flag to set the overwrite mode of existing
                          raster maps
        :type overwrite: bool
        """
        super(RasterRowIO, self).open(mode, mtype, overwrite)
        self.rowio.open(self._fd, self._rows, self._cols, self.mtype)

    @must_be_open
    def close(self):
        """Function to close the raster"""
        self.rowio.release()
        libraster.Rast_close(self._fd)
        # update rows and cols attributes
        self._rows = None
        self._cols = None
        self._fd = None

    @must_be_open
    def get_row(self, row, row_buffer=None):
        """This method returns the row using:

            * the read mode and
            * `rowcache` method

        :param row: the number of row to obtain
        :type row: int
        :param row_buffer: Specify the Buffer object that will be instantiate
        :type row_buffer: Buffer object


            >>> with RasterRowIO(test_raster_name) as elev:
            ...     for row in elev:
            ...         row
            Buffer([11, 21, 31, 41], dtype=int32)
            Buffer([12, 22, 32, 42], dtype=int32)
            Buffer([13, 23, 33, 43], dtype=int32)
            Buffer([14, 24, 34, 44], dtype=int32)

        """
        if row_buffer is None:
            row_buffer = Buffer((self._cols,), self.mtype)
        rowio_buf = librowio.Rowio_get(ctypes.byref(self.rowio.c_rowio), row)
        ctypes.memmove(row_buffer.p, rowio_buf, self.rowio.row_size)
        return row_buffer


class RasterSegment(RasterAbstractBase):
    """Raster_segment_access": Inherits "Raster_abstract_base" and uses the
    segment library for cached randomly reading and writing access.

        * Implements the [row][col] operator for read and write access using
          Segment_get() and Segment_put() functions internally
        * Implements row read and write access with the [row] operator using
          Segment_get_row() Segment_put_row() internally
        * Implements the get_row() and put_row() method  using
          Segment_get_row() Segment_put_row() internally
        * Implements the flush_segment() method
        * Implements the copying of raster maps to segments and vice verse
        * Overwrites the open and close methods
        * No mathematical operation like __add__ and stuff for the Raster
          object (only for rows), since r.mapcalc is more sophisticated and
          faster

    """
    def __init__(self, name, srows=64, scols=64, maxmem=100,
                 *args, **kargs):
        self.segment = Segment(srows, scols, maxmem)
        super(RasterSegment, self).__init__(name, *args, **kargs)

    def _get_mode(self):
        return self._mode

    def _set_mode(self, mode):
        if mode and mode.lower() not in ('r', 'w', 'rw'):
            str_err = _("Mode type: {0} not supported ('r', 'w','rw')")
            raise ValueError(str_err.format(mode))
        self._mode = mode

    mode = property(fget=_get_mode, fset=_set_mode,
                    doc="Set or obtain the opening mode of raster")

    def __setitem__(self, key, row):
        """Return the row of Raster object, slice allowed."""
        if isinstance(key, slice):
            #Get the start, stop, and step from the slice
            return [self.put_row(ii, row)
                    for ii in range(*key.indices(len(self)))]
        elif isinstance(key, tuple):
            x, y = key
            return self.put(x, y, row)
        elif isinstance(key, int):
            if key < 0:  # Handle negative indices
                key += self._rows
            if key >= self._rows:
                raise IndexError(_("Index out of range: %r.") % key)
            return self.put_row(key, row)
        else:
            raise TypeError("Invalid argument type.")

    @must_be_open
    def map2segment(self):
        """Transform an existing map to segment file.
        """
        row_buffer = Buffer((self._cols), self.mtype)
        for row in range(self._rows):
            libraster.Rast_get_row(
                self._fd, row_buffer.p, row, self._gtype)
            self.segment.put_row(row, row_buffer)

    @must_be_open
    def segment2map(self):
        """Transform the segment file to a map.
        """
        row_buffer = Buffer((self._cols), self.mtype)
        for row in range(self._rows):
            row_buffer = self.segment.get_row(row, row_buffer)
            libraster.Rast_put_row(self._fd, row_buffer.p, self._gtype)

    @must_be_open
    def get_row(self, row, row_buffer=None):
        """Return the row using the `segment.get_row` method

        :param row: specify the row number
        :type row: int
        :param row_buffer: specify the Buffer object that will be instantiate
        :type row_buffer: Buffer object

            >>> with RasterSegment(test_raster_name) as elev:
            ...     for row in elev:
            ...         row
            Buffer([11, 21, 31, 41], dtype=int32)
            Buffer([12, 22, 32, 42], dtype=int32)
            Buffer([13, 23, 33, 43], dtype=int32)
            Buffer([14, 24, 34, 44], dtype=int32)

        """
        if row_buffer is None:
            row_buffer = Buffer((self._cols), self.mtype)
        return self.segment.get_row(row, row_buffer)

    @must_be_open
    def put_row(self, row, row_buffer):
        """Write the row using the `segment.put_row` method

        :param row: a Row object to insert into raster
        :type row: Buffer object
        """
        self.segment.put_row(row, row_buffer)

    @must_be_open
    def get(self, row, col):
        """Return the map value using the `segment.get` method

        :param row: Specify the row number
        :type row: int
        :param col: Specify the column number
        :type col: int


            >>> with RasterSegment(test_raster_name) as elev:
            ...     elev.get(0,0)
            ...     elev.get(1,1)
            ...     elev.get(2,2)
            ...     elev.get(3,3)
            11
            22
            33
            44

        """
        return self.segment.get(row, col)

    @must_be_open
    def put(self, row, col, val):
        """Write the value to the map using the `segment.put` method

        :param row: Specify the row number
        :type row: int
        :param col: Specify the column number
        :type col: int
        :param val: Specify the value that will be write to the map cell
        :type val: value
        """
        self.segment.val.value = val
        self.segment.put(row, col)

    def open(self, mode=None, mtype=None, overwrite=None):
        """Open the map, if the map already exist: determine the map type
        and copy the map to the segment files;
        else, open a new segment map.

        :param mode: specify if the map will be open with read, write or
                     read/write mode ('r', 'w', 'rw')
        :type mode: str
        :param mtype: specify the map type, valid only for new maps: CELL,
                      FCELL, DCELL
        :type mtype: str
        :param overwrite: use this flag to set the overwrite mode of existing
                          raster maps
        :type overwrite: bool
        """
        # read rows and cols from the active region
        self._rows = libraster.Rast_window_rows()
        self._cols = libraster.Rast_window_cols()

        self.mode = mode if mode else self.mode
        self.mtype = mtype if mtype else self.mtype
        self.overwrite = overwrite if overwrite is not None else self.overwrite

        if self.exist():
            self.info.read()
            self.cats.mtype = self.mtype
            self.cats.read()
            self.hist.read()
            if ((self.mode == "w" or self.mode == "rw") and
                    self.overwrite is False):
                str_err = _("Raster map <{0}> already exists. Use overwrite.")
                fatal(str_err.format(self))

            # We copy the raster map content into the segments
            if self.mode == "rw" or self.mode == "r":
                self._fd = libraster.Rast_open_old(self.name, self.mapset)
                self._gtype = libraster.Rast_get_map_type(self._fd)
                self.mtype = RTYPE_STR[self._gtype]
                # initialize the segment, I need to determine the mtype of the
                # map
                # before to open the segment
                self.segment.open(self)
                self.map2segment()
                self.segment.flush()
                self.cats.read()
                self.hist.read()

                if self.mode == "rw":
                    warning(_(WARN_OVERWRITE.format(self)))
                    # Close the file descriptor and open it as new again
                    libraster.Rast_close(self._fd)
                    self._fd = libraster.Rast_open_new(
                        self.name, self._gtype)
            # Here we simply overwrite the existing map without content copying
            elif self.mode == "w":
                #warning(_(WARN_OVERWRITE.format(self)))
                self._gtype = RTYPE[self.mtype]['grass type']
                self.segment.open(self)
                self._fd = libraster.Rast_open_new(self.name, self._gtype)
        else:
            if self.mode == "r":
                str_err = _("Raster map <{0}> does not exists")
                raise OpenError(str_err.format(self.name))

            self._gtype = RTYPE[self.mtype]['grass type']
            self.segment.open(self)
            self._fd = libraster.Rast_open_new(self.name, self._gtype)

    @must_be_open
    def close(self, rm_temp_files=True):
        """Close the map, copy the segment files to the map.

        :param rm_temp_files: if True all the segments file will be removed
        :type rm_temp_files: bool
        """
        if self.mode == "w" or self.mode == "rw":
            self.segment.flush()
            self.segment2map()
        if rm_temp_files:
            self.segment.close()
        else:
            self.segment.release()
        libraster.Rast_close(self._fd)
        # update rows and cols attributes
        self._rows = None
        self._cols = None
        self._fd = None


def random_map_only_columns(mapname, mtype, overwrite=True, factor=100):
    region = Region()
    random_map = RasterRow(mapname)
    row_buf = Buffer((region.cols, ), mtype,
                     buffer=(np.random.random(region.cols,) * factor).data)
    random_map.open('w', mtype, overwrite)
    for _ in range(region.rows):
        random_map.put_row(row_buf)
    random_map.close()
    return random_map


def random_map(mapname, mtype, overwrite=True, factor=100):
    region = Region()
    random_map = RasterRow(mapname)
    random_map.open('w', mtype, overwrite)
    for _ in range(region.rows):
        row_buf = Buffer((region.cols, ), mtype,
                         buffer=(np.random.random(region.cols,) * factor).data)
        random_map.put_row(row_buf)
    random_map.close()
    return random_map


def raster2numpy(rastname, mapset=''):
    """Return a numpy array from a raster map

    :param str rastname: the name of raster map
    :parar str mapset: the name of mapset containig raster map
    """
    with RasterRow(rastname, mapset=mapset, mode='r') as rast:
        return np.array(rast)


def numpy2raster(array, mtype, rastname, overwrite=False):
    """Save a numpy array to a raster map

    :param obj array: a numpy array
    :param obj mtype: the datatype of array
    :param str rastername: the name of output map
    :param bool overwrite: True to overwrite existing map
    """
    reg = Region()
    if (reg.rows, reg.cols) != array.shape:
        msg = "Region and array are different: %r != %r"
        raise TypeError(msg % ((reg.rows, reg.cols), array.shape))
    with RasterRow(rastname, mode='w', mtype=mtype, overwrite=overwrite) as new:
        newrow = Buffer((array.shape[1],), mtype=mtype)
        for row in array:
            newrow[:] = row[:]
            new.put_row(newrow)

if __name__ == "__main__":

    import doctest
    from grass.pygrass import utils
    from grass.pygrass.modules import Module
    Module("g.region", n=40, s=0, e=40, w=0, res=10)
    Module("r.mapcalc", expression="%s = row() + (10 * col())"%(test_raster_name),
                             overwrite=True)
    Module("r.support", map=test_raster_name,
                        title="A test map",
                        history="Generated by r.mapcalc",
                        description="This is a test map")
    cats="""11:A
            12:B
            13:C
            14:D
            21:E
            22:F
            23:G
            24:H
            31:I
            32:J
            33:K
            34:L
            41:M
            42:n
            43:O
            44:P"""
    Module("r.category", rules="-", map=test_raster_name,
           stdin_=cats, separator=":")

    doctest.testmod()

    """Remove the generated vector map, if exist"""
    mset = utils.get_mapset_raster(test_raster_name, mapset='')
    if mset:
        Module("g.remove", flags='f', type='raster', name=test_raster_name)
