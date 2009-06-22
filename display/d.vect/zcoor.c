/* Print z coordinate value for each node */

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/Vect.h>
#include <grass/display.h>
#include <grass/display_raster.h>
#include "local_proto.h"
#include "plot.h"

int zcoor(struct Map_info *Map, int type, LATTR *lattr)
{
    int num, el;
    double xl, yl, zl;
    struct line_pnts *Points;
    struct line_cats *Cats;
    char text[50];

    G_debug(1, "display zcoor:");
    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    D_RGB_color(lattr->color.R, lattr->color.G, lattr->color.B);
    R_text_size(lattr->size, lattr->size);
    if (lattr->font)
	R_font(lattr->font);
    if (lattr->enc)
	R_encoding(lattr->enc);

    Vect_rewind(Map);


    num = Vect_get_num_nodes(Map);
    G_debug(1, "n_nodes = %d", num);

    /* Nodes */
    for (el = 1; el <= num; el++) {
	if (!Vect_node_alive(Map, el))
	    continue;
	Vect_get_node_coor(Map, el, &xl, &yl, &zl);
	G_debug(3, "node = %d", el);

	sprintf(text, "%.2f", zl);
	show_label(&xl, &yl, lattr, text);
    }

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    return 0;
}
