#include <stdio.h>
#include <grass/gis.h>
#include "raster3d_intern.h"

/*--------------------------------------------------------------------------*/

/* the standard g3d file format is used to store the mask values. a NULL-value
   is stored for values which are masked out and a "0." is stored for values 
   which are not masked out. to improve compression, the precision is set to 
   0 and RLE encoding is used.
 */

/*--------------------------------------------------------------------------*/

static int Rast3d_maskMapExistsVar = 0;
static RASTER3D_Map *Rast3d_maskMap;

/*--------------------------------------------------------------------------*/
static void dummy(void)
{
    return;
}


static float RASTER3D_MASKNUMmaskValue;

/* Call to dummy() to match void return type of Rast3d_setNullValue() */
#define RASTER3D_MASKNUM(map,Xmask,Ymask,Zmask,VALUEmask,TYPEmask) \
\
   (RASTER3D_MASKNUMmaskValue = Rast3d_getMaskFloat (map, Xmask, Ymask, Zmask), \
    ((Rast3d_isNullValueNum (&RASTER3D_MASKNUMmaskValue, FCELL_TYPE)) ? \
      Rast3d_setNullValue (VALUEmask, 1, TYPEmask) : dummy()))

/*--------------------------------------------------------------------------*/

int Rast3d_maskClose()
{
    /* No Idea if this is correct return value */
    if (!Rast3d_maskMapExistsVar)
	return 1;

    Rast3d_maskMapExistsVar = 0;

    if (!Rast3d_closeCell(Rast3d_maskMap)) {
	Rast3d_error("Rast3d_maskClose: error closing mask");

	return 0;
    }

    return 1;
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 *  Returns 1 if the 3d mask file exists.
 *
 *  \return int
 */

int Rast3d_maskFileExists(void)
{
    return G_find_file_misc(RASTER3D_DIRECTORY, RASTER3D_CELL_ELEMENT, RASTER3D_MASK_MAP, G_mapset()) != NULL;
}

/*--------------------------------------------------------------------------*/

static int maskOpenOldCacheDefault = RASTER3D_USE_CACHE_DEFAULT;

int Rast3d_maskOpenOld(void)
{
    RASTER3D_Region region;

    /* No Idea if this is correct return value */
    if (Rast3d_maskMapExistsVar)
	return 1;

    Rast3d_maskMapExistsVar = Rast3d_maskFileExists();

    if (!Rast3d_maskMapExistsVar)
	return 1;

    if ((Rast3d_maskMap = Rast3d_openCellOld(RASTER3D_MASK_MAP, G_mapset(),
				       RASTER3D_DEFAULT_WINDOW, FCELL_TYPE,
				       maskOpenOldCacheDefault))
	== NULL) {
	Rast3d_error("Rast3d_maskOpenOld: cannot open mask");

	return 0;
    }

    Rast3d_getRegionStructMap(Rast3d_maskMap, &region);
    Rast3d_setWindowMap(Rast3d_maskMap, &region);

    return 1;
}

/*--------------------------------------------------------------------------*/

static float Rast3d_getMaskFloat(RASTER3D_Map * map, int x, int y, int z)
{
    double north, east, top;
    float value;

    north = ((double)map->window.rows - y - 0.5) / (double)map->window.rows *
	(map->window.north - map->window.south) + map->window.south;
    east = ((double)x + 0.5) / (double)map->window.cols *
	(map->window.east - map->window.west) + map->window.west;
    top = ((double)z + 0.5) / (double)map->window.depths *
	(map->window.top - map->window.bottom) + map->window.bottom;

    Rast3d_getRegionValue(Rast3d_maskMap, north, east, top, &value, FCELL_TYPE);
    return value;
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 *  This function should be used to adjust the cache size used for the
 * 3d-mask. First the open 3d-mask is closed and then opened again with 
 * a cache size as specified with <em>cache</em>.
 *  
 *  \param cache
 *  \return 1 ... if successful
 *          0 ... otherwise.
 */

int Rast3d_maskReopen(int cache)
{
    int tmp;

    if (Rast3d_maskMapExistsVar)
	if (!Rast3d_maskClose()) {
	    Rast3d_error("Rast3d_maskReopen: error closing mask");

	    return 0;
	}

    tmp = maskOpenOldCacheDefault;
    maskOpenOldCacheDefault = cache;

    if (!Rast3d_maskOpenOld()) {
	Rast3d_error("Rast3d_maskReopen: error opening mask");

	return 0;
    }

    maskOpenOldCacheDefault = tmp;
    return 1;
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 *  Returns 1 if the cell with cell-coordinates <em>(x, y, z)</em> is masked
 *  out. Returns 0 otherwise.
 *
 *  \param x
 *  \param y
 *  \param z
 *  \return int
 */

int Rast3d_isMasked(RASTER3D_Map * map, int x, int y, int z)
{
    if (!Rast3d_maskMapExistsVar)
	return 0;

    RASTER3D_MASKNUMmaskValue = Rast3d_getMaskFloat(map, x, y, z);
    return (Rast3d_isNullValueNum(&RASTER3D_MASKNUMmaskValue, FCELL_TYPE));
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 * Replaces the value stored in <em>value</em> with the NULL-value if 
 * <em>Rast3d_isMasked (x, y, z)</em> returns 1. Does nothing otherwise.
 * <em>value</em> is assumed to be of<em>type</em>.
 *
 *  \param x
 *  \param y
 *  \param z
 *  \param value
 *  \param type
 *  \return void
 */

void Rast3d_maskNum(RASTER3D_Map * map, int x, int y, int z, void *value, int type)
{
    if (!Rast3d_maskMapExistsVar)
	return;
    RASTER3D_MASKNUM(map, x, y, z, value, type);
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 *  Same as <em>Rast3d_maskNum (x, y, z, value, FCELL_TYPE)</em>.
 *
 *  \param x
 *  \param y
 *  \param z
 *  \param value
 *  \return void
 */

void Rast3d_maskFloat(RASTER3D_Map * map, int x, int y, int z, float *value)
{
    if (!Rast3d_maskMapExistsVar)
	return;
    RASTER3D_MASKNUM(map, x, y, z, value, FCELL_TYPE);
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 * Same as <em>Rast3d_maskNum (x, y, z, value, DCELL_TYPE)</em>.
 *
 *  \param x
 *  \param y
 *  \param z
 *  \param value
 *  \return void
 */

void Rast3d_maskDouble(RASTER3D_Map * map, int x, int y, int z, double *value)
{
    if (!Rast3d_maskMapExistsVar)
	return;
    RASTER3D_MASKNUM(map, x, y, z, value, DCELL_TYPE);
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 *  Replaces the values stored in <em>tile</em> (with <em>tileIndex</em>) for 
 *  which <em>Rast3d_isMasked</em> returns 1 with NULL-values. Does not change
 *  the remaining values. The values are assumed to be of <em>type</em>. 
 *  Whether replacement is performed or not only depends on location of the
 *  cells of the tile and not on the status of the mask for <em>map</em>
 *  (i.e. turned on or off).
 *
 *  \param map
 *  \param tileIndex
 *  \param tile
 *  \param type
 *  \return void
 */

void Rast3d_maskTile(RASTER3D_Map * map, int tileIndex, void *tile, int type)
{
    int nofNum, rows, cols, depths, xRedundant, yRedundant, zRedundant;
    int x, y, z, xLength, yLength, dx, dy, dz, length;

    if (!Rast3d_maskMapExistsVar)
	return;

    nofNum = Rast3d_computeClippedTileDimensions(map, tileIndex,
					      &rows, &cols, &depths,
					      &xRedundant, &yRedundant,
					      &zRedundant);
    Rast3d_tileIndexOrigin(map, tileIndex, &x, &y, &z);

    if (nofNum == map->tileSize) {
	 /*AV*/
	    /* BEGIN OF ORIGINAL CODE */
	    /*
	     *    Rast3d_getTileDimensionsMap (map, &rows, &cols, &depths);
	     */
	     /*AV*/
	    /* BEGIN OF MY CODE */
	    Rast3d_getTileDimensionsMap(map, &cols, &rows, &depths);
	/* END OF MY CODE */
	xRedundant = yRedundant = 0;
    }

    rows += y;
    cols += x;
    depths += z;
    length = Rast3d_length(type);
    xLength = xRedundant * length;
    yLength = map->tileX * yRedundant * length;

    for (dz = z; dz < depths; dz++) {
	for (dy = y; dy < rows; dy++) {
	    for (dx = x; dx < cols; dx++) {
		RASTER3D_MASKNUM(map, dx, dy, dz, tile, type);
		tile += length;
	    }

	    tile += xLength;
	}
	tile += yLength;
    }
}

/*--------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 *  Turns on the mask for <em>map</em>. Do
 * not invoke this function after the first tile has been read since the result
 * might be inconsistent cell-values.
 *
 *  \param map
 *  \return void
 */

void Rast3d_maskOn(RASTER3D_Map * map)
{
    map->useMask = 1;
}


/*!
 * \brief 
 *
 *  Turns off the mask for <em>map</em>.
 * This is the default.  Do not invoke this function after the first tile has
 * been read since the result might be inconsistent cell-values.
 *
 *  \param map
 *  \return void
 */

void Rast3d_maskOff(RASTER3D_Map * map)
{
    map->useMask = 0;
}


/*!
 * \brief 
 *
 *  Returns 1 if the mask for <em>map</em>
 * is turned on. Returns 0 otherwise.
 *
 *  \param map
 *  \return int
 */

int Rast3d_maskIsOn(RASTER3D_Map * map)
{
    return map->useMask;
}


/*!
 * \brief 
 *
 * Returns 1 if the mask for <em>map</em> is turned off. Returns 0 otherwise.
 *
 *  \param map
 *  \return int
 */

int Rast3d_maskIsOff(RASTER3D_Map * map)
{
    return !map->useMask;
}


/*!
 * \brief 
 *
 * Returns the name of the 3d mask file.
 *
 *  \return char * 
 */

const char *Rast3d_maskFile(void)
{
    return RASTER3D_MASK_MAP;
}


/*!
 * \brief 
 *
 * Returns 1 if the 3d mask is loaded.
 *
 *  \return int
 */

int Rast3d_maskMapExists(void)
{
    return Rast3d_maskMapExistsVar;
}
