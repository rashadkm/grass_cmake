#include "gis.h"

int 
adjust_window (struct Cell_head *window)
{
    char *err, *G_adjust_Cell_head();

    if (err = G_adjust_Cell_head(window,0,0))
    {
	char msg[100];
	sprintf (msg, "Invalid region: %s", err);
        G_fatal_error (msg);
    }

    return 0;
}
