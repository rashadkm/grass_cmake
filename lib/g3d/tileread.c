
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <rpc/types.h>
#include <rpc/xdr.h>
#include "G3d_intern.h"


/*---------------------------------------------------------------------------*/

static int
G3d_xdrTile2tile (map, tile, rows, cols, depths,
		  xRedundant, yRedundant, zRedundant, nofNum, type)

     G3D_Map *map; 
     char *tile;
     int rows, cols, depths, xRedundant, yRedundant, zRedundant, nofNum;
     int type;

{
  int y, z, xLength, yLength, length;

  if (! G3d_initCopyFromXdr (map, type)) {
    G3d_error ("G3d_xdrTile2tile: error in G3d_initCopyFromXdr");
    return 0;
  }

  if (nofNum == map->tileSize) {
    if (! G3d_copyFromXdr (map->tileSize, tile)) {
      G3d_error ("G3d_xdrTile2tile: error in G3d_copyFromXdr");
      return 0;
    }
    return 1;
  }

  length = G3d_length (type);
  xLength = xRedundant * length;
  yLength = map->tileX * yRedundant * length;

  if (xRedundant) {
    for (z = 0; z < depths; z++) {
      for (y = 0; y < rows; y++) {
	if (! G3d_copyFromXdr (cols, tile)) {
	  G3d_error ("G3d_xdrTile2tile: error in G3d_copyFromXdr");
	  return 0;
	}
	tile += cols * length;
	G3d_setNullValue (tile, xRedundant, type);
	tile += xLength;
      }
      if (yRedundant) {
	G3d_setNullValue (tile, map->tileX * yRedundant, type);
	tile += yLength;
      }
    }
    if (! zRedundant) return 1;

    G3d_setNullValue (tile, map->tileXY * zRedundant, type);
    return 1;
  }

  if (yRedundant) {
    for (z = 0; z < depths; z++) {
      if (! G3d_copyFromXdr (map->tileX * rows, tile)) {
	G3d_error ("G3d_xdrTile2tile: error in G3d_copyFromXdr");
	return 0;
      }
      tile += map->tileX * rows * length;
      G3d_setNullValue (tile, map->tileX * yRedundant, type);
      tile += yLength;
    }
    if (! zRedundant) return 1;

    G3d_setNullValue (tile, map->tileXY * zRedundant, type);
    return 1;
  }

  if (! G3d_copyFromXdr (map->tileXY * depths, tile)) {
    G3d_error ("G3d_xdrTile2tile: error in G3d_copyFromXdr");
    return 0;
  }

  if (! zRedundant) return 1;

  tile += map->tileXY * depths * length;
  G3d_setNullValue (tile, map->tileXY * zRedundant, type);

  return 1;
}

/*---------------------------------------------------------------------------*/

static int
G3d_readTileUncompressed (map, tileIndex, nofNum)

     G3D_Map *map; 
     int tileIndex;
     int nofNum;

{
  int nofBytes;

  nofBytes = nofNum * map->numLengthExtern;
  nofBytes = G3D_MIN (nofBytes, 
		      map->fileEndPtr - map->index[tileIndex]);

  if (read (map->data_fd, xdr, nofBytes) != nofBytes) {
    G3d_error ("G3d_readTileUncompressed: can't read file");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/

static int
G3d_readTileCompressed (map, tileIndex, nofNum)

     G3D_Map *map; 
     int tileIndex;
     int nofNum;

{
  if (! G_fpcompress_readXdrNums (map->data_fd, xdr, nofNum,
				  map->tileLength[tileIndex], 
				  map->precision, tmpCompress, 
				  map->type == G3D_FLOAT)) {
    G3d_error ("G3d_readTileCompressed: error in G_fpcompress_readXdrNums");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
                       /* EXPORTED FUNCTIONS */
/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/

int
G3d_readTile (map, tileIndex, tile, type)

     G3D_Map *map; 
     int tileIndex;
     char *tile;
     int type;

{
  int nofNum, rows, cols, depths, xRedundant, yRedundant, zRedundant;

  if ((tileIndex >= map->nTiles) || (tileIndex < 0))
    G3d_fatalError ("G3d_readTile: tile index out of range");

  if (map->index[tileIndex] == -1) {
    G3d_setNullTileType (map, tile, type);
    return 1;
  }

  nofNum = G3d_computeClippedTileDimensions (map, tileIndex, 
					     &rows, &cols, &depths,
					     &xRedundant, &yRedundant, 
					     &zRedundant);

  if (lseek (map->data_fd, map->index[tileIndex], SEEK_SET) == -1) {
    G3d_error ("G3d_readTile: can't position file");
    return 0;
  }

  if (map->compression == G3D_NO_COMPRESSION) {
    if (! G3d_readTileUncompressed (map, tileIndex, nofNum)) {
      G3d_error ("G3d_readTile: error in G3d_readTileUncompressed");
      return 0;
    }
  } else
    if (! G3d_readTileCompressed (map, tileIndex, nofNum)) {
      G3d_error ("G3d_readTile: error in G3d_readTileCompressed");
      return 0;
    }

  if (! G3d_xdrTile2tile (map, tile, rows, cols, depths,
			  xRedundant, yRedundant, zRedundant, nofNum, type)) {
    G3d_error ("G3d_readTile: error in G3d_xdrTile2tile");
    return 0;
  }

  if (G3d_maskIsOff (map)) return 1;

  G3d_maskTile (map, tileIndex, tile, type);
  return 1;
}

/*---------------------------------------------------------------------------*/

int
G3d_readTileFloat (map, tileIndex, tile)

     G3D_Map *map; 
     int tileIndex;
     char *tile;

{
  if (! G3d_readTile (map, tileIndex, tile, G3D_FLOAT)) {
    G3d_error ("G3d_readTileFloat: error in G3d_readTile");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/

int
G3d_readTileDouble (map, tileIndex, tile)

     G3D_Map *map; 
     int tileIndex;
     char *tile;

{
  if (! G3d_readTile (map, tileIndex, tile, G3D_DOUBLE)) {
    G3d_error ("G3d_readTileDouble: error in G3d_readTile");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/

                      /* CACHE-MODE-ONLY FUNCTIONS */

/*---------------------------------------------------------------------------*/

int
G3d_lockTile (map, tileIndex)

     G3D_Map *map; 
     int tileIndex;

{
  if (! map->useCache) 
    G3d_fatalError ("G3d_lockTile: function invalid in non-cache mode");

  if (! G3d_cache_lock (map->cache, tileIndex)) {
    G3d_error ("G3d_lockTile: error in G3d_cache_lock");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/

int
G3d_unlockTile (map, tileIndex)

     G3D_Map *map; 
     int tileIndex;

{
  if (! map->useCache) 
    G3d_fatalError ("G3d_unlockTile: function invalid in non-cache mode");

  if (! G3d_cache_unlock (map->cache, tileIndex)) {
    G3d_error ("G3d_unlockTile: error in G3d_cache_unlock");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/

int
G3d_unlockAll (map)

     G3D_Map *map; 

{
  if (! map->useCache) 
    G3d_fatalError ("G3d_unlockAll: function invalid in non-cache mode");

  if (! G3d_cache_unlock_all (map->cache)) {
    G3d_error ("G3d_unlockAll: error in G3d_cache_unlock_all");
    return 0;
  }

  return 1;
}

/*---------------------------------------------------------------------------*/

void
G3d_autolockOn (map)

     G3D_Map *map; 

{
  if (! map->useCache) 
    G3d_fatalError ("G3d_autoLockOn: function invalid in non-cache mode");

  G3d_cache_autolock_on (map->cache);
}

/*---------------------------------------------------------------------------*/

void
G3d_autolockOff (map)

     G3D_Map *map; 

{
  if (! map->useCache) 
    G3d_fatalError ("G3d_autoLockOff: function invalid in non-cache mode");

  G3d_cache_autolock_off (map->cache);
}

/*---------------------------------------------------------------------------*/

void
G3d_minUnlocked (map, minUnlocked)

     G3D_Map *map; 
     int minUnlocked;

{
  if (! map->useCache) 
    G3d_fatalError ("G3d_autoLockOff: function invalid in non-cache mode");

  G3d_cache_set_minUnlock (map->cache, 
			   G3d__computeCacheSize (map, minUnlocked));
}

/*---------------------------------------------------------------------------*/

int
G3d_beginCycle (map)

     G3D_Map *map; 

{
  if (! G3d_unlockAll (map)) {
    G3d_fatalError ("G3d_beginCycle: error in G3d_unlockAll");
    return 0;
  }

  G3d_autolockOn (map);
  return 1;
}

/*---------------------------------------------------------------------------*/

int
G3d_endCycle (map)

     G3D_Map *map; 

{
  G3d_autolockOff (map);
  return 1;
}

/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
