#include <rpc/types.h>
#include <rpc/xdr.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include "G3d.h"

/*--------------------------------------------------------------------------*/

static unsigned char clearMask[9] = 
                                {255, 128, 192, 224, 240, 248, 252, 254, 255};

/*---------------------------------------------------------------------------*/

static void
G3d_float2xdrFloat (f, xdrf)

     float *f, *xdrf;

{
  XDR xdrEncodeStream;

  xdrmem_create (&xdrEncodeStream, (caddr_t) xdrf, 4, XDR_ENCODE);

  if (! xdr_setpos (&xdrEncodeStream, 0))
    G3d_fatalError ("G3d_float2xdrFloat: positioning xdr failed");

  if (! xdr_float (&xdrEncodeStream, f))
      G3d_fatalError ("G3d_float2xdrFloat: writing xdr failed");
  
  xdr_destroy (&xdrEncodeStream);
}
     
/*---------------------------------------------------------------------------*/

static void
G3d_double2xdrDouble (d, xdrd)

     double *d, *xdrd;

{
  XDR xdrEncodeStream;

  xdrmem_create (&xdrEncodeStream, (caddr_t)xdrd, 8, XDR_ENCODE);

  if (! xdr_setpos (&xdrEncodeStream, 0))
    G3d_fatalError ("G3d_double2xdrDouble: positioning xdr failed");

  if (! xdr_double (&xdrEncodeStream, d))
      G3d_fatalError ("G3d_double2xdrDouble: writing xdr failed");
  
  xdr_destroy (&xdrEncodeStream);
}
     
/*---------------------------------------------------------------------------*/

static void
G3d_truncFloat (f, p)

     float *f;
     int p;
    
{
  unsigned char *c;

  if ((p == -1) || (p >= 23)) return;

  c = (unsigned char *) f;

  c++;
  if (p <= 7) {
    *c++ &= clearMask[(p + 1) % 8];
    *c++ = 0;
    *c = 0;
    return;
  }

  c++;
  if (p <= 15) {
    *c++ &= clearMask[(p + 1) % 8];
    *c = 0;
    return;
  }

  c++;
  *c &= clearMask[(p + 1) % 8];
  return;
}

/*---------------------------------------------------------------------------*/

static void
G3d_truncDouble (d, p)

     double *d;
     int p;
    
{
  unsigned char *c;

  if ((p == -1) || (p >= 52)) return;

  c = (unsigned char *) d;

  c++;
  if (p <= 4) {
    *c++ &= clearMask[(p + 4) % 8];
    *c++ = 0;
    *c++ = 0;
    *c++ = 0;
    *c++ = 0;
    *c++ = 0;
    *c = 0;
    return;
  }

  c++;
  if (p <= 12) {
    *c++ &= clearMask[(p + 4) % 8];
    *c++ = 0;
    *c++ = 0;
    *c++ = 0;
    *c++ = 0;
    *c = 0;
    return;
  }

  c++;
  if (p <= 20) {
    *c++ &= clearMask[(p + 4) % 8];
    *c++ = 0;
    *c++ = 0;
    *c++ = 0;
    *c = 0;
    return;
  }

  c++;
  if (p <= 28) {
    *c++ &= clearMask[(p + 4) % 8];
    *c++ = 0;
    *c++ = 0;
    *c = 0;
    return;
  }

  c++;
  if (p <= 36) {
    *c++ &= clearMask[(p + 4) % 8];
    *c++ = 0;
    *c = 0;
    return;
  }

  c++;
  if (p <= 44) {
    *c++ &= clearMask[(p + 4) % 8];
    *c = 0;
    return;
  }

  c++;
  *c &= clearMask[(p + 4) % 8];
  return;
}

/*---------------------------------------------------------------------------*/

static void
G3d_float2Double (f, d)

     float *f;
     double *d;
    
{
  unsigned char *c1, *c2, sign, c;
  int e;

  c1 = (unsigned char *) f;
  c2 = (unsigned char *) d;

  sign = (*c1 & (unsigned char) 128);
  e = (((*c1 & (unsigned char) 127) << 1) | 
       ((*(c1 + 1) & (unsigned char) 128) >> 7));

  if ((*c1 != 0) || (*(c1 + 1) != 0) || (*(c1 + 2) != 0) || (*(c1 + 3) != 0))
    e += 1023 - 127;
  c = e / 16;

  *c2++ = (sign | c);
  
  c1++;

  c = e % 16;
  *c2 = (c << 4);
  *c2++ |= ((*c1 & (unsigned char) 127) >> 3);

  *c2 = ((*c1++ & (unsigned char) 7) << 5);
  *c2++ |= (*c1 >> 3);

  *c2 = ((*c1++ & (unsigned char) 7) << 5);
  *c2++ |= (*c1 >> 3);

  *c2++ = ((*c1 & (unsigned char) 7) << 5);

  *c2++ = (unsigned char) 0;
  *c2++ = (unsigned char) 0;
  *c2 = (unsigned char) 0;
}

/*---------------------------------------------------------------------------*/

static int
G3d_compareFloats (f1, p1, f2, p2)

     float *f1;
     int p1;
     float *f2;
     int p2;
     
{
  unsigned char *c1, *c2;
  float xdrf1, xdrf2;

  if (G3d_isNullValueNum (f1, G3D_FLOAT)) 
    return G3d_isNullValueNum (f2, G3D_FLOAT);

  G3d_float2xdrFloat (f1, &xdrf1);
  G3d_float2xdrFloat (f2, &xdrf2);

  c1 = (unsigned char *) &xdrf1;
  c2 = (unsigned char *) &xdrf2;

/*   printf ("%d %d (%d %d %d %d) (%d %d %d %d) %d\n", p1, p2, *c1, *(c1 + 1), *(c1 + 2), *(c1 + 3), *c2, *(c2 + 1), *(c2 + 2), *(c2 + 3), *f1 == *f2); */

  if ((p1 != -1) && (p1 < 23) && ((p1 < p2) || (p2 == -1))) 
    G3d_truncFloat (&xdrf2, p1);
  if ((p2 != -1) && (p2 < 23) && ((p2 < p1) || (p1 == -1))) 
    G3d_truncFloat (&xdrf1, p2);

/*   printf ("%d %d (%d %d %d %d) (%d %d %d %d) %d\n", p1, p2, *c1, *(c1 + 1), *(c1 + 2), *(c1 + 3), *c2, *(c2 + 1), *(c2 + 2), *(c2 + 3), *f1 == *f2); */

  return (*c1 == *c2) && (*(c1 + 1) == *(c2 + 1)) && (*(c1 + 2) == *(c2 + 2))
                      && (*(c1 + 3) == *(c2 + 3));
}


/*---------------------------------------------------------------------------*/

static int
G3d_compareDoubles (d1, p1, d2, p2)

     double *d1;
     int p1;
     double *d2;
     int p2;

{
  unsigned char *c1, *c2;
  double xdrd1, xdrd2;

  if (G3d_isNullValueNum (d1, G3D_DOUBLE)) 
    return G3d_isNullValueNum (d2, G3D_DOUBLE);

  G3d_double2xdrDouble (d1, &xdrd1);
  G3d_double2xdrDouble (d2, &xdrd2);

  c1 = (unsigned char *) &xdrd1;
  c2 = (unsigned char *) &xdrd2;

/*    printf ("%d %d (%d %d %d %d %d %d %d %d) (%d %d %d %d %d %d %d %d)\n", p1, p2, *c1, *(c1 + 1), *(c1 + 2), *(c1 + 3), *(c1 + 4), *(c1 + 5), *(c1 + 6), *(c1 + 7), *c2, *(c2 + 1), *(c2 + 2), *(c2 + 3), *(c2 + 4), *(c2 + 5), *(c2 + 6), *(c2 + 7));  */

  if ((p1 != -1) && (p1 < 52) && ((p1 < p2) || (p2 == -1))) 
    G3d_truncDouble (&xdrd2, p1);
  if ((p2 != -1) && (p2 < 52) && ((p2 < p1) || (p1 == -1))) 
    G3d_truncDouble (&xdrd1, p2);

/*    printf ("%d %d (%d %d %d %d %d %d %d %d) (%d %d %d %d %d %d %d %d)\n", p1, p2, *c1, *(c1 + 1), *(c1 + 2), *(c1 + 3), *(c1 + 4), *(c1 + 5), *(c1 + 6), *(c1 + 7), *c2, *(c2 + 1), *(c2 + 2), *(c2 + 3), *(c2 + 4), *(c2 + 5), *(c2 + 6), *(c2 + 7));  */

  return (*c1 == *c2) && (*(c1 + 1) == *(c2 + 1)) && (*(c1 + 2) == *(c2 + 2))
                      && (*(c1 + 3) == *(c2 + 3)) && (*(c1 + 4) == *(c2 + 4))
		      && (*(c1 + 5) == *(c2 + 5)) && (*(c1 + 6) == *(c2 + 6))
		      && (*(c1 + 7) == *(c2 + 7));
}


/*---------------------------------------------------------------------------*/

static int
G3d_compareFloatDouble (f, p1, d, p2)

     float *f;
     int p1;
     double *d;
     int p2;
     
{
  unsigned char *c1, *c2;
  float xdrf, fTmp;
  double xdrd, xdrd2, dTmp;
  
  if (G3d_isNullValueNum (f, G3D_FLOAT)) 
    return G3d_isNullValueNum (d, G3D_DOUBLE);

  /* need this since assigning a double to a float actually may change the */
  /* bit pattern. an example (in xdr format) is the double*/
  /* (63 237 133 81 81 108 3 32) which truncated to 23 bits precision should */
  /* become (63 237 133 81 64 0 0 0). however assigned to a float it becomes */
  /* (63 237 133 81 96 0 0 0). */
  fTmp = *d;
  dTmp = fTmp;

  G3d_float2xdrFloat (f, &xdrf);
  G3d_float2Double (&xdrf, &xdrd2);
  G3d_double2xdrDouble (&dTmp, &xdrd);

  c1 = (unsigned char *) &xdrd2;
  c2 = (unsigned char *) &xdrd;

/*      printf ("%d %d (%d %d %d %d) (%d %d %d %d %d %d %d %d) (%d %d %d %d %d %d %d %d)\n", p1, p2, *((unsigned char *) &xdrf), *(((unsigned char *) &xdrf) + 1), *(((unsigned char *) &xdrf) + 2), *(((unsigned char *) &xdrf) + 3), *c1, *(c1 + 1), *(c1 + 2), *(c1 + 3), *(c1 + 4), *(c1 + 5), *(c1 + 6), *(c1 + 7), *c2, *(c2 + 1), *(c2 + 2), *(c2 + 3), *(c2 + 4), *(c2 + 5), *(c2 + 6), *(c2 + 7));  */


  if (((p1 != -1) && ((p1 < p2) || (p2 == -1))) ||
      ((p1 == -1) && ((p2 > 23) || (p2 == -1))))
    G3d_truncDouble (&xdrd, (p1 != -1 ? p1 : 23));
  if ((p2 != -1) && (p2 < 23) && ((p2 < p1) || (p1 == -1))) 
    G3d_truncDouble (&xdrd2, p2);
  
/*   printf ("%d %d (%d %d %d %d) (%d %d %d %d %d %d %d %d) (%d %d %d %d %d %d %d %d)\n", p1, p2, *((unsigned char *) &xdrf), *(((unsigned char *) &xdrf) + 1), *(((unsigned char *) &xdrf) + 2), *(((unsigned char *) &xdrf) + 3), *c1, *(c1 + 1), *(c1 + 2), *(c1 + 3), *(c1 + 4), *(c1 + 5), *(c1 + 6), *(c1 + 7), *c2, *(c2 + 1), *(c2 + 2), *(c2 + 3), *(c2 + 4), *(c2 + 5), *(c2 + 6), *(c2 + 7));  */

  return (*c1 == *c2) && (*(c1 + 1) == *(c2 + 1)) && (*(c1 + 2) == *(c2 + 2))
                      && (*(c1 + 3) == *(c2 + 3)) && (*(c1 + 4) == *(c2 + 4))
		      && (*(c1 + 5) == *(c2 + 5)) && (*(c1 + 6) == *(c2 + 6))
		      && (*(c1 + 7) == *(c2 + 7));
}

/*---------------------------------------------------------------------------*/

static void
compareFilesNocache (map, map2)

     void *map, *map2; 

{
  double n1 = 0, n2 = 0;
  double *n1p, *n2p;
  float *f1p, *f2p;
  int x, y, z, correct;
  int p1, p2;
  int tileX, tileY, tileZ, typeIntern, typeIntern2;
  int nx, ny, nz;

  p1 = G3d_tilePrecisionMap (map);
  p2 = G3d_tilePrecisionMap (map2);

  G3d_getTileDimensionsMap (map, &tileX, &tileY, &tileZ);
  G3d_getNofTilesMap (map2, &nx, &ny, &nz);
  typeIntern = G3d_tileTypeMap (map);
  typeIntern2 = G3d_tileTypeMap (map2);

  n1p = &n1; f1p = (float *) &n1;
  n2p = &n2; f2p = (float *) &n2;

  for (z = 0; z < nz * tileZ; z++) {
    printf ("comparing: z = %d\n", z);

    for (y = 0; y < ny * tileY; y++) {
      for (x = 0; x < nx * tileX; x++) {

	G3d_getBlock (map, x, y, z, 1, 1, 1, (char *)n1p, typeIntern);
	G3d_getBlock (map2, x, y, z, 1, 1, 1, (char *)n2p, typeIntern2);

	if (typeIntern == G3D_FLOAT)
	{
	  if (typeIntern2 == G3D_FLOAT)
	    correct = G3d_compareFloats (f1p, p1, f2p, p2);
	  else
	    correct = G3d_compareFloatDouble (f1p, p1, n2p, p2);
	}
	else
	{
	  if (typeIntern2 == G3D_FLOAT)
	    correct = G3d_compareFloatDouble (f2p, p2, n1p, p1);
	  else
	    correct = G3d_compareDoubles (n1p, p1, n2p, p2);
	}

	if (! correct) 
	{
	  int xTile, yTile, zTile, xOffs, yOffs, zOffs;

	  G3d_coord2tileCoord (map2, x, y, z, &xTile, &yTile, &zTile, 
			       &xOffs, &yOffs, &zOffs);
	  printf ("(%d %d %d) (%d %d %d) (%d %d %d) %.20f %.20f\n", 
		  x, y, z, xTile, yTile, zTile, xOffs, yOffs, zOffs,
		  *n1p, *n2p);
	  G3d_fatalError ("compareFilesNocache: files don't match\n");
	}
      }
    }
  }

  printf ("Files are identical up to precision.\n");
}

/*---------------------------------------------------------------------------*/


/*!
 * \brief 
 *
 * Compares the cell-values of file <em>f1</em> in mapset
 * <em>mapset1</em> and file <em>f2</em> in mapset <em>mapset2</em>.
 * The values are compared up to precision.
 * Terminates in error if the files don't match.
 * This function uses the more advanced features of the cache.
 * The source code can be found in <em>filecompare.c</em>.
 *
 *  \param f1
 *  \param mapset1
 *  \param f2
 *  \param mapset2
 *  \return void
 */

void
G3d_compareFiles (f1, mapset1, f2, mapset2)

     char *f1, *f2;
     char *mapset1, *mapset2;

{
  void *map, *map2; 
  double n1 = 0, n2 = 0;
  double *n1p, *n2p;
  float *f1p, *f2p;
  int x, y, z, correct;
  int p1, p2;
  int rows, cols, depths;
  int tileX, tileY, tileZ, typeIntern, typeIntern2, tileX2, tileY2, tileZ2;
  int nx, ny, nz;

  printf ("\nComparing %s and %s\n", f1, f2);

  map = G3d_openCellOld (f1, mapset1, G3D_DEFAULT_WINDOW,
			 G3D_TILE_SAME_AS_FILE, G3D_USE_CACHE_DEFAULT);
  if (map == NULL) 
    G3d_fatalError ("G3d_compareFiles: error in G3d_openCellOld");

  G3d_printHeader (map);

  map2 = G3d_openCellOld (f2, mapset2, G3D_DEFAULT_WINDOW, 
			  G3D_TILE_SAME_AS_FILE, G3D_USE_CACHE_DEFAULT);
  if (map2 == NULL) 
    G3d_fatalError ("G3d_compareFiles: error in G3d_openCellOld");

  G3d_printHeader (map2);

  typeIntern = G3d_tileTypeMap (map);
  typeIntern2 = G3d_tileTypeMap (map2);

  p1 = G3d_tilePrecisionMap (map);
  p2 = G3d_tilePrecisionMap (map2);

  G3d_getTileDimensionsMap (map, &tileX, &tileY, &tileZ);
  G3d_getTileDimensionsMap (map2, &tileX2, &tileY2, &tileZ2);
  G3d_getNofTilesMap (map2, &nx, &ny, &nz);
  G3d_getCoordsMap (map, &rows, &cols, &depths);

  if ((! G3d_tileUseCacheMap (map)) || (! G3d_tileUseCacheMap (map2))) {
    compareFilesNocache (map, map2);
    G3d_closeCell (map);
    G3d_closeCell (map2);
    return;
  }

  n1p = &n1; f1p = (float *) &n1;
  n2p = &n2; f2p = (float *) &n2;

  G3d_autolockOn (map);  
  G3d_autolockOn (map2);  
  G3d_minUnlocked (map, cols / tileX + 1); 

  G3d_getCoordsMap (map2, &rows, &cols, &depths);
  G3d_minUnlocked (map2, cols / tileX + 1); 

  G3d_getCoordsMap (map, &rows, &cols, &depths);
  for (z = 0; z < depths; z++) 
  {
    printf ("comparing: z = %d\n", z);

    if ((z % tileZ) == 0)
    {
      if (! G3d_unlockAll (map))
	G3d_fatalError ("G3d_compareFiles: error in G3d_unlockAll");
    }
    if ((z % tileZ2) == 0)
    {
      if (! G3d_unlockAll (map2))
	G3d_fatalError ("G3d_compareFiles: error in G3d_unlockAll");
    }
    
    for (y = 0; y < rows; y++)
    {
      for (x = 0; x < cols; x++) 
      {
	G3d_getValueRegion (map, x, y, z, (char *)n1p, typeIntern);
	G3d_getValueRegion (map2, x, y, z, (char *)n2p, typeIntern2);

	G3d_isNullValueNum (n1p, typeIntern);
	G3d_isNullValueNum (n2p, typeIntern2);
	
	if (typeIntern == G3D_FLOAT)
	{
	  if (typeIntern2 == G3D_FLOAT)
	    correct = G3d_compareFloats (f1p, p1, f2p, p2);
	  else
	    correct = G3d_compareFloatDouble (f1p, p1, n2p, p2);
	}
	else
	{
	  if (typeIntern2 == G3D_FLOAT)
	    correct = G3d_compareFloatDouble (f2p, p2, n1p, p1);
	  else
	    correct = G3d_compareDoubles (n1p, p1, n2p, p2);
	}
	
	if (! correct) 
	{
	  int xTile, yTile, zTile, xOffs, yOffs, zOffs;

	  G3d_coord2tileCoord (map2, x, y, z, &xTile, &yTile, &zTile, 
			       &xOffs, &yOffs, &zOffs);
	  G3d_fatalError ("G3d_compareFiles: files don't match\n");
	}
      }
    }
  }
  
  printf ("Files are identical up to precision.\n");
  G3d_closeCell (map);
  G3d_closeCell (map2);
}
