/****************************************************************
 *
 * MODULE:     v.edit
 *
 * AUTHOR(S):  GRASS Development Team
 *             Jachym Cepicky <jachym  les-ejk cz>
 *
 * PURPOSE:    This module edits vector maps. It is inteded to be mainly
 * 	       used by the the new v.digit GUI.
 *
 * COPYRIGHT:  (C) 2002-2006 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 * TODO:       
 ****************************************************************/

#include "global.h"

/* 
 * Set maxdistance 
 * This code comes from v.what/main.c
 */
double max_distance(double maxdistance)
{
    struct Cell_head window;
    double x;
    double ew_dist1, ew_dist2, ns_dist1, ns_dist2;
    double xres, yres, maxd;
    char nsres[30], ewres[30];

    if (maxdistance == 0.0) {
        G_get_window (&window);
        G_format_resolution  (window.ew_res,  ewres,  x);
        G_format_resolution  (window.ns_res,  nsres,  x);
        ew_dist1 = G_distance(window.east, window.north, window.west, window.north);
        /* EW Dist at South Edge */
        ew_dist2 = G_distance(window.east, window.south, window.west, window.south);
        /* NS Dist at East edge */
        ns_dist1 = G_distance(window.east, window.north, window.east, window.south);
        /* NS Dist at West edge */
        ns_dist2 = G_distance(window.west, window.north, window.west, window.south);
        xres = ((ew_dist1 + ew_dist2) / 2) / window.cols;
        yres = ((ns_dist1 + ns_dist2) / 2) / window.rows;
        if (xres > yres) maxd = xres; else maxd = yres;
    }
    else {
        maxd = maxdistance;
    }

    return maxd;
}
