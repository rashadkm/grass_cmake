#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Rast.h>
#include <grass/glocale.h>
#include "local_proto.h"

/* 
 * do_histogram() - Creates histogram for CELL
 *
 * RETURN: EXIT_SUCCESS / EXIT_FAILURE
 */
int do_histogram(const char *name)
{
    CELL *cell;
    struct Cell_head cellhd;
    struct Cell_stats statf;
    int nrows, ncols;
    int row;
    int fd;

    if (Rast_get_cellhd(name, "", &cellhd) < 0)
	G_fatal_error(_("Unable to read header for <%s>"), name);

    G_set_window(&cellhd);
    if ((fd = Rast_open_cell_old(name, "")) < 0)
	G_fatal_error(_("Unable to open <%s>"), name);

    nrows = G_window_rows();
    ncols = G_window_cols();
    cell = Rast_allocate_cell_buf();

    Rast_init_cell_stats(&statf);
    for (row = 0; row < nrows; row++) {
	if (Rast_get_map_row_nomask(fd, cell, row) < 0) {
	    G_warning(_("Unable to read row %d"), row);
	    break;
	}

	Rast_update_cell_stats(cell, ncols, &statf);
    }

    if (row == nrows)
	Rast_write_histogram_cs(name, &statf);

    Rast_free_cell_stats(&statf);
    Rast_close_cell(fd);
    G_free(cell);

    if (row < nrows)
	return -1;

    return 0;
}
