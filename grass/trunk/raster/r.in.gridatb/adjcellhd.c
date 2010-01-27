#include <grass/raster.h>

#include "local_proto.h"


int adjcellhd(struct Cell_head *cellhd)
{
    int retval;


    retval = 0;

    Rast_set_window(cellhd);

    if (cellhd->rows != G_window_rows()) {
	retval = 2;
    }

    if (cellhd->cols != G_window_cols()) {
	retval = 3;
    }

    return (retval);
}
