/******************************************************************************
 * These routines support the drawing of multi-band images on the graphics
 * device.  A color lookup table with equal divisions in the red, green, and
 * blue dimensions is created for this purpose.
 *
 * The user sends a red, green, and blue intensity ramp for 256 levels each
 * using the Set_RGB_color() routine.  Subsequent calls to RGB_raster uses
 * this information to convert RGB intensity rasters to a color raster.
 * This is then sent to the routine Raster_int().
 *
 * All intensity values are represented in unsigned (8-byte) values.  That is
 * with values between and including 0 and 255.
 *
 ******************************************************************************
 * Set_RGB_color(r,g,b)
 *     unsigned char r[256], g[256], b[256] ;
 * This contains the desired intensity functions for red, green, and blue.
 * Using the known number of available levels static arrays are filled with
 * which provide easy determination of which real color is associated with
 * any given RGB color intensity cmbination.
 *
 ******************************************************************************
 * RGB_raster(n, nrows, red, grn, blu, withzeros)
 *     int n ;
 *     int nrows ;
 *     unsigned char *red, *grn, *blu ;
 *     int withzeros ;
 * Generates a color Raster_int() call based on the red, grn, and blu array
 * information and the intensity function provided in the last Set_RGB_color()
 * call.
 ******************************************************************************
 */
#include <stdio.h>
#include <stdlib.h>
#include "gis.h"
#include "driverlib.h"

static unsigned char red[256], grn[256], blu[256] ;

int 
Set_RGB_color (unsigned char r[256], unsigned char g[256], unsigned char b[256])
{
	int i ;

	for(i = 0; i < 256; i++)
	{
		red[i] = r[i];
		grn[i] = g[i];
		blu[i] = b[i];
	}

	return 0;
}

int 
RGB_raster (int n, int nrows,
	    unsigned char *r, unsigned char *g, unsigned char *b,
	    unsigned char *nul)
{
	static int *array = NULL ;
	static int array_alloc = 0 ;
	int i ;

	if (n > array_alloc)
	{
		/*  Make sure there is enough space  */
		array_alloc += (n - array_alloc + 0x01FF) & ~0x01FF;
		
		/* Make sure sufficient space is allocated */
		array = G_realloc(array, array_alloc * sizeof(int)) ;
	}

	/* Convert RGB to color number */
	for (i = 0; i < n; i++)
		array[i] = (nul && nul[i])
			? 0
			:_get_lookup_for_color(red[r[i]], grn[g[i]], blu[b[i]]);

	Raster_int(n, nrows, array, !nul, 0);

	return 0;
}
