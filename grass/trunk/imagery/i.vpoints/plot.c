#include <unistd.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/display.h>
#include <grass/symbol.h>
#include <grass/glocale.h>
#include "vectpoints.h"
#include "globals.h"


#define SYM_SIZE 5
#define SYM_NAME "basic/cross1"


int plot (char *name, char *mapset, struct line_pnts *Points)
{
    double *x, *y;
    int i, np;
    int line, nlines, ltype;
    struct Cell_head window;
    struct Map_info P_map;
    SYMBOL *Symb;
    RGBA_Color *linecolor_rgb, *fillcolor_rgb;
    int ix, iy;

    Vect_set_open_level (2);
    Vect_set_fatal_error ( GV_FATAL_RETURN );
    
    if ( 2 > Vect_open_old (&P_map, name, mapset))
    {
	return -1;
    }

    G_get_set_window (&window);

    G_setup_plot ( D_get_d_north(), D_get_d_south(), D_get_d_west(), D_get_d_east(),
	           D_move_abs, D_cont_abs);

    nlines = Vect_get_num_lines (&P_map);

    /* set line and fill color for vector point symbols */
    linecolor_rgb = G_malloc(sizeof(RGB_Color));
    fillcolor_rgb = G_malloc(sizeof(RGB_Color));

    linecolor_rgb->r = standard_colors_rgb[line_color].r;
    linecolor_rgb->g = standard_colors_rgb[line_color].g;
    linecolor_rgb->b = standard_colors_rgb[line_color].b;
    linecolor_rgb->a = RGBA_COLOR_OPAQUE;
    fillcolor_rgb->a = RGBA_COLOR_NONE;


    for ( line = 1; line <= nlines; line++ ) { 
	ltype = Vect_read_line(&P_map, Points, NULL, line );

	if(ltype & GV_POINT) { /* GV_ singular: don't plot centroids, Points only */

	    Symb = S_read( SYM_NAME );

	    if( Symb == NULL ) {
		G_warning(_("Cannot read symbol, cannot display points"));
		return(-1);
	    }
	    else S_stroke( Symb, SYM_SIZE, 0, 0 );

	   ix = (int)(D_u_to_d_col( Points->x[0])+0.5 );
	   iy = (int)(D_u_to_d_row( Points->y[0])+0.5 );

	    D_symbol(Symb, ix, iy, linecolor_rgb, fillcolor_rgb);
	}


	if(ltype & GV_LINES) { /* GV_ plural: both lines and boundaries */

	    np = Points->n_points;
	    x = Points->x;
	    y = Points->y;

	    for(i=1; i < np; i++)
	    {
		G_plot_line(x[0], y[0], x[1], y[1]);
		x++;
		y++;
	    }
	}
    }

    Vect_close ( &P_map );
    G_free(linecolor_rgb);
    G_free(fillcolor_rgb);

    return 0;
}

int plot_warp(char *name, char *mapset, struct line_pnts *Points,
		double E[], double N[], int trans_order)
{
    double *x, *y;
    int i, np;
    int line, nlines, ltype;
    struct Cell_head window;
    struct Map_info P_map;
    SYMBOL *Symb;
    RGBA_Color *linecolor_rgb, *fillcolor_rgb;
    int ix, iy;

    Vect_set_open_level (2);
    Vect_set_fatal_error ( GV_FATAL_RETURN );
    
    if ( 2 > Vect_open_old (&P_map, name, mapset))
    {
	return -1;
    }

    G_get_set_window (&window);

    G_setup_plot ( D_get_d_north(), D_get_d_south(), D_get_d_west(), D_get_d_east(),
	           D_move_abs, D_cont_abs);

    nlines = Vect_get_num_lines (&P_map);

    /* set line and fill color for vector point symbols */
    linecolor_rgb = G_malloc(sizeof(RGB_Color));
    fillcolor_rgb = G_malloc(sizeof(RGB_Color));

    linecolor_rgb->r = standard_colors_rgb[line_color].r;
    linecolor_rgb->g = standard_colors_rgb[line_color].g;
    linecolor_rgb->b = standard_colors_rgb[line_color].b;
    linecolor_rgb->a = RGBA_COLOR_OPAQUE;
    fillcolor_rgb->a = RGBA_COLOR_NONE;


    for ( line = 1; line <= nlines; line++ ) { 
	ltype = Vect_read_line(&P_map, Points, NULL, line );

	if(ltype & GV_POINT) { /* GV_ singular: don't plot centroids, Points only */

	    Symb = S_read( SYM_NAME );

	    if( Symb == NULL ) {
		G_warning(_("Cannot read symbol, cannot display points"));
		return(-1);
	    }
	    else S_stroke( Symb, SYM_SIZE, 0, 0 );

	   ix = (int)(D_u_to_d_col( Points->x[0])+0.5 );
	   iy = (int)(D_u_to_d_row( Points->y[0])+0.5 );

	    D_symbol(Symb, ix, iy, linecolor_rgb, fillcolor_rgb);
	}


	if(ltype & GV_LINES) { /* GV_ plural: both lines and boundaries */

	    np = Points->n_points;
	    x = Points->x;
	    y = Points->y;

	    CRS_georef(x[0], y[0], &x[0], &y[0], E, N, trans_order);

	    for(i=1; i < np; i++)
	    {
		CRS_georef(x[1], y[1], &x[1], &y[1], E, N, trans_order);
		G_plot_line(x[0], y[0], x[1], y[1]);
		x++;
		y++;
	    }
	}
    }

    Vect_close ( &P_map );
    G_free(linecolor_rgb);
    G_free(fillcolor_rgb);

    return 0;
}

