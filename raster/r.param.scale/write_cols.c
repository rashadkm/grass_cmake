
/*****************************************************************************/

/***                                                                       ***/

/***                            write_cols()                               ***/

/***   	         Writes out colour file for morphometric features          ***/

/***               Jo Wood, Project ASSIST, 21st February 1995             ***/

/***                                                                       ***/

/*****************************************************************************/

#include <grass/raster.h>
#include "param.h"


void write_cols(void)
{
    struct Colors colours;

    Rast_init_colors(&colours);

    Rast_add_color_rule(FLAT, 180, 180, 180,	/* White      */
		     PIT, 0, 0, 0, &colours);	/* Black      */
    Rast_add_color_rule(CHANNEL, 0, 0, 255,	/* Blue       */
		     PASS, 0, 255, 0, &colours);	/* Green      */
    Rast_add_color_rule(RIDGE, 255, 255, 0,	/* Yellow     */
		     PEAK, 255, 0, 0, &colours);	/* Red        */

    Rast_write_colors(rast_out_name, G_mapset(), &colours);

    Rast_free_colors(&colours);

}
