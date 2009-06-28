#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "globals.h"

/* This routine closes up the cell maps, frees up the row buffers and
   use a less than perfect way of setting the color maps for the output
   to grey scale.  */

int closefiles(char *r_name, char *g_name, char *b_name,
	       int fd_output[3], CELL * rowbuf[3])
{
    int i;
    struct Colors colors;
    struct Range range;
    CELL min, max;
    const char *mapset;

    for (i = 0; i < 3; i++) {
	Rast_close(fd_output[i]);
	G_free(rowbuf[i]);
    }

    mapset = G_mapset();

    Rast_read_range(r_name, mapset, &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_grey_scale_colors(&colors, min, max);
    Rast_write_colors(r_name, mapset, &colors);

    Rast_read_range(g_name, mapset, &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_grey_scale_colors(&colors, min, max);
    Rast_write_colors(g_name, mapset, &colors);

    Rast_read_range(b_name, mapset, &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_grey_scale_colors(&colors, min, max);
    Rast_write_colors(b_name, mapset, &colors);

    return 0;
}
