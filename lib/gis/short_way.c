/**
 * \file short_way.c
 *
 * \brief Shortest path functions.
 *
 * This program is free software under the GNU General Public License
 * (>=v2). Read the file COPYING that comes with GRASS for details.
 *
 * \author GRASS GIS Development Team
 *
 * \date 1999-2006
 */

#include <grass/gis.h>


/**
 * \fn int G_shortest_way (double *east1, double *east2)
 *
 * \brief Shortest way between two eastings.
 *
 * For lat-lon projection (<i>PROJECTION_LL</i>), <b>east1</b>, 
 * <b>east2</b> are changed so that they are no more than 180 degrees 
 * apart. Their true locations are not changed. For all other 
 * projections, this function does nothing.
 *
 * \param[in] east1
 * \param[in] east2
 * \return always returns 0
 */

int G_shortest_way (double *east1,double *east2)
{
    if (G_projection() == PROJECTION_LL)
    {
	if (*east1 > *east2)
	    while ((*east1-*east2) > 180)
		*east2 += 360;
	else if (*east2 > *east1)
	    while ((*east2-*east1) > 180)
		*east1 += 360;
    }

    return 0;
}
