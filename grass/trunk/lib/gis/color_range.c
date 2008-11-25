#include <math.h>
#include <grass/gis.h>

void G_set_color_range(CELL min, CELL max, struct Colors *colors)
{
    if (min < max) {
	colors->cmin = (DCELL) min;
	colors->cmax = (DCELL) max;
    }
    else {
	colors->cmin = (DCELL) max;
	colors->cmax = (DCELL) min;
    }
}

void G_set_d_color_range(DCELL min, DCELL max, struct Colors *colors)
{
    if (min < max) {
	colors->cmin = min;
	colors->cmax = max;
    }
    else {
	colors->cmin = max;
	colors->cmax = min;
    }
}

/* returns min and max category in the range or huge numbers
   if the co,lor table is defined on floating cell values and
   not on categories */


/*!
 * \brief
 *
 *  \param G_get_color_range
 *  \return int
 */

void G_get_color_range(CELL * min, CELL * max, const struct Colors *colors)
{
    if (!colors->is_float) {
	*min = (CELL) floor(colors->cmin);
	*max = (CELL) ceil(colors->cmax);
    }
    else {
	*min = -255 * 255 * 255;
	*max = 255 * 255 * 255;
    }
}

/* returns min and max values in the range */
void G_get_d_color_range(DCELL * min, DCELL * max, const struct Colors *colors)
{
    *min = colors->cmin;
    *max = colors->cmax;
}
