#include <stdlib.h>

#include <grass/raster.h>
#include <grass/imagery.h>
#include <grass/glocale.h>

#include "bouman.h"
#include "region.h"

int read_block(DCELL *** img,	/* img[band][row[col] */
	       struct Region *region, struct files *files)
{
    int band, row, col;

    for (band = 0; band < files->nbands; band++) {
	for (row = region->ymin; row < region->ymax; row++) {
	    if (Rast_get_d_row(files->band_fd[band], files->cellbuf, row)
		< 0)
		G_fatal_error(_("Unable to read raster map row %d"),
			      row);
	    for (col = region->xmin; col < region->xmax; col++)
		img[band][row][col] = files->cellbuf[col];
	}
    }

    return 0;
}
