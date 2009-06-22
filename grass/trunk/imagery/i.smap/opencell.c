#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>


int open_cell_old(const char *name, const char *mapset)
{
    int fd;

    if (mapset == NULL)
	mapset = G_find_cell2(name, "");
    fd = Rast_open_cell_old(name, mapset);
    if (fd >= 0)
	return fd;

    G_fatal_error(_("Unable to open raster map <%s>"), name);

    /* should not get here */
    return -1;
}

int open_cell_new(const char *name)
{
    int fd;

    fd = Rast_open_cell_new(name);
    if (fd >= 0)
	return fd;

    G_fatal_error(_("Unable to create raster map <%s>"), name);

    /* should not get here */
    return -1;
}
