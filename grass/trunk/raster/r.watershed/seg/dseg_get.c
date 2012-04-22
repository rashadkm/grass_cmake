#include <grass/gis.h>
#include <grass/segment.h>
#include "Gwater.h"

int dseg_get(DSEG * dseg, double *value, GW_LARGE_INT row, GW_LARGE_INT col)
{
    if (segment_get(&(dseg->seg), (DCELL *) value, row, col) < 0) {
	G_warning("dseg_get(): could not read segment file");
	return -1;
    }
    return 0;
}
