#include "gis.h"
#include <unistd.h>
#include <string.h>

static int nlines = 100;

int show_cat (int width, int mwidth,
    char *name, char *mapset, int cat, char *label,
    int terse, char *fs, RASTER_MAP_TYPE map_type)
{
    char *fname;
    char buf[100];
    CELL cell_val;

    cell_val = cat;
    if(map_type != CELL_TYPE)
       sprintf(buf, ", quant  ");
    else
       sprintf(buf, " ");
    if (terse)
    {
	fname = G_fully_qualified_name(name,mapset);
	if(G_is_c_null_value(&cell_val))
	{
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%s%s%sNull%s%s\n", fname, buf, fs, fs, label);
	    fprintf (stderr, "%s%s%sNull%s%s\n", fname, buf, fs, fs, label);
	}
	else
	{
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%s%s%s%d%s%s\n", fname, buf, fs, cat, fs, label);
	    fprintf (stderr, "%s%s%s%d%s%s\n", fname, buf, fs, cat, fs, label);
	}
    }
    else
    {
	if(G_is_c_null_value(&cell_val))
	{
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%*s in %-*s%s (Null)%s\n", width, name, mwidth, mapset, buf, label);
	    fprintf (stderr, "%*s in %-*s%s (Null)%s\n", width, name, mwidth, mapset, buf, label);
	}
	else
	{
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%*s in %-*s%s (%d)%s\n", width, name, mwidth, mapset, buf, cat, label);
	    fprintf (stderr, "%*s in %-*s%s (%d)%s\n", width, name, mwidth, mapset, buf, cat, label);
        }
    }
    nlines += 1;

    return 0;
}

int show_dval (int width, int mwidth,
	char *name, char *mapset, DCELL dval, char *label,
	int terse, char *fs)
{
    DCELL dcell_val;
    char *fname;

    dcell_val = dval;
    if (terse)
    {
	fname = G_fully_qualified_name(name,mapset);
	if(G_is_d_null_value(&dcell_val))
	{
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%s, actual %sNull%s%s\n", fname, fs, fs, label);
	    fprintf (stderr, "%s, actual %sNull%s%s\n", fname, fs, fs, label);
	}
	else
	{
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%s, actual %s%f%s%s\n", fname, fs, dval, fs, label);
	    fprintf (stderr, "%s, actual %s%f%s%s\n", fname, fs, dval, fs, label);
	}
    }
    else
    {
	if(G_is_d_null_value(&dcell_val))
        {
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%*s in %-*s, actual  (Null)%s\n", width, name, mwidth, mapset, label);
	    fprintf (stderr, "%*s in %-*s, actual  (Null)%s\n", width, name, mwidth, mapset, label);
	}
	else
        {
	    if (!isatty(fileno(stdout)))
	        fprintf (stdout, "%*s in %-*s, actual  (%f)%s\n", width, name, mwidth, mapset, dval, label);
	    fprintf (stderr, "%*s in %-*s, actual  (%f)%s\n", width, name, mwidth, mapset, dval, label);
	}
    }
    nlines += 1;

    return 0;
}

int show_utm (double north, double east,
	struct Cell_head *window, int terse, int button, char *fs)
{
    char e[50], n[50];

    if (window->proj == PROJECTION_LL && !isatty (fileno (stdout)))
    {
	/* format in decimal rather than d.m.s */
	G_format_northing (north, n, -1);
	G_format_easting  (east,  e, -1);
    }
    else
    {
	G_format_northing (north, n, window->proj);
	G_format_easting  (east,  e, window->proj);
    }

    if (terse)
    {
	if (!isatty(fileno(stdout)))
	    fprintf (stdout, "\n%s%s%s%s%d\n", e, fs, n, fs, button);
	fprintf (stderr, "\n%s%s%s%s%d\n", e, fs, n, fs, button);
    }
    else
    {
	if (window->proj != PROJECTION_LL)
	{
	    strcat (n, "(N)");
	    strcat (e, "(E)");
	}

	if (!isatty(fileno(stdout)))
	    fprintf (stdout, "\n%s %s\n", e, n);
	fprintf (stderr, "\n%s %s\n", e, n);
    }
    nlines += 2;

    return 0;
}

int show_buttons (int once)
{
    if (once)
    {
	fprintf (stderr, "\nClick mouse button on desired location\n\n");
	nlines = 3;
    }
    else if (nlines >= 18)	/* display prompt every screen full */
    {
	fprintf (stderr, "\n");
	fprintf (stderr, "Buttons\n");
	fprintf (stderr, " Left:  what's here\n");
	fprintf (stderr, " Right: quit\n");
	nlines = 4;
    }

    return 0;
}
