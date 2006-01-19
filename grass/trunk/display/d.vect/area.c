/* Author: Radim Blazek
*
* added color support: Markus Neteler, Martin Landa
*/
#include <string.h>
#include "gis.h"
#include "Vect.h"
#include "display.h"
#include "raster.h"
#include "plot.h"
#include "local_proto.h"
#include "colors.h"
#include "dbmi.h"
#include "glocale.h"

int darea ( struct Map_info *Map, struct cat_list *Clist, int bcolor, int fcolor, 
	     int chcat, int id_flag, int table_colors_flag, int cats_color_flag,
	     struct Cell_head *window, char *rgb_column) {

    int    num, area, isle, n_isles, n_points;
    double xl, yl;
    struct line_pnts *Points, *IPoints;
    struct line_cats *Cats;
    int cat, centroid = 0;
    int red, grn, blu;

    struct field_info *fi=NULL;
    dbDriver *driver = NULL;
    dbCatValArray cvarr;
    dbCatVal *cv_rgb = NULL;
    int nrec;

    int i, rgb = 0;  /* 0|1 */
    char colorstring[12]; /* RRR:GGG:BBB */
    unsigned char which;

    G_debug (1, "display areas:");
    Points = Vect_new_line_struct ();
    IPoints = Vect_new_line_struct ();
    Cats = Vect_new_cats_struct ();

    if( table_colors_flag ) {
      /* for reading RRR:GGG:BBB color strings from table */

      if ( rgb_column == NULL || strlen(rgb_column) == 0 )
	G_fatal_error(_("Color definition column not specified."));

      db_CatValArray_init (&cvarr);     

      fi = Vect_get_field (Map, Clist -> field);
      if (fi == NULL) {
	G_fatal_error (_("Cannot read field info"));
      }
      
      driver = db_start_driver_open_database(fi->driver, fi->database);
      if (driver == NULL)
	G_fatal_error (_("Cannot open database %s by driver %s"), fi->database, fi->driver);

      nrec = db_select_CatValArray(driver, fi->table, fi->key, 
				   rgb_column, NULL, &cvarr);

      G_debug (3, "nrec (%s) = %d", rgb_column, nrec);

      if (cvarr.ctype != DB_C_TYPE_STRING)
	G_fatal_error (_("Color definition column (%s) not a string. "
	    "Column must be of form RRR:GGG:BBB where RGB values range 0-255."), rgb_column);


      if ( nrec < 0 )
	G_fatal_error (_("Cannot select data (%s) from table"), rgb_column);

      G_debug(2, "\n%d records selected from table", nrec);

      db_close_database_shutdown_driver(driver);

      for ( i = 0; i < cvarr.n_values; i++ ) {
	G_debug (4, "cat = %d  %s = %s", cvarr.value[i].cat, rgb_column,
		 db_get_string(cvarr.value[i].val.s));

	/* test for background color */
	if (test_bg_color (db_get_string(cvarr.value[i].val.s))) {
	  G_warning (_("Category <%d>: Area fill color and background color are the same!"),
		     cvarr.value[i].cat);
	}
      }
    }
    
    num = Vect_get_num_areas(Map);
    G_debug (2, "n_areas = %d", num);
    
    for ( area = 1; area <= num; area++ ) {
	int i;
	BOUND_BOX box;
        G_debug (3, "area = %d", area);

	if ( !Vect_area_alive (Map, area) ) continue;
	
	/* Check box */
	Vect_get_area_box (Map, area, &box);
	if ( box.N < window->south || box.S > window->north || 
		box.E < window->west || box.W > window->east) {

	    if ( window->proj != PROJECTION_LL )
		continue;
	    else {   /* out of bounds for -180 to 180, try 0 to 360 as well */
		if ( box.N < window->south || box.S > window->north )
		    continue;
		if ( box.E+360 < window->west || box.W+360 > window->east )
		    continue;
	    }
	}

        if ( chcat ) /* check category: where_opt or cat_opt used */
        { 
	     if ( id_flag ) {
		 if ( !(Vect_cat_in_cat_list (area, Clist)) )
		     continue;
	     } else {
		 int found = 0;

		 centroid = Vect_get_area_centroid ( Map, area ); 
		 G_debug (3, "centroid = %d", centroid);
		 if ( centroid < 1 ) continue;
		 Vect_read_line (Map, Points, Cats, centroid );
		 
		 for ( i = 0; i < Cats->n_cats; i++ ) {
		     G_debug (3, "  centroid = %d, field = %d, cat = %d", centroid, 
			                 Cats->field[i], Cats->cat[i]);

		     if ( Cats->field[i] == Clist->field && Vect_cat_in_cat_list ( Cats->cat[i], Clist) ) {
			 found = 1;
			 break;
		     }
		 }
		 if (!found) continue;
	     } /* end else */
        } /* end if id_flag */
        G_debug (3, "display area %d", area);

        /* fill */
	Vect_get_area_points ( Map, area, Points );   
        G_debug (3, "n_points = %d", Points->n_points);
  
	n_points = Points->n_points;
	xl = Points->x[n_points-1];
	yl = Points->y[n_points-1];
	n_isles = Vect_get_area_num_isles ( Map, area );   
        for ( i = 0; i < n_isles; i++) {
	    isle = Vect_get_area_isle ( Map, area, i );   
	    Vect_get_isle_points ( Map, isle, IPoints );
	    Vect_append_points ( Points, IPoints, GV_FORWARD);
	    Vect_append_point ( Points, xl, yl, 0.0 ); /* ??? */
	}

	cat = Vect_get_area_cat ( Map, area, Clist -> field );

	if (!Vect_get_area_centroid (Map, area) && cat == -1) {
	  continue;
	}

	if( table_colors_flag ) {
	  centroid = Vect_get_area_centroid ( Map, area );
	  if( cat >= 0 ) {
	    G_debug (3, "display area %d, centroid %d, cat %d", area, centroid, cat);
	    
	    /* Read RGB colors from db for current area # */
	    if (db_CatValArray_get_value (&cvarr, cat, &cv_rgb) != DB_OK) {
	      rgb = 0;
	    }
	    else {
	      sprintf (colorstring, "%s", db_get_string(cv_rgb -> val.s));
	      
	      if (strlen(colorstring) != 0) {
		
		G_debug(3, "area %d: colorstring: %s", area, colorstring);
		
		if ( G_str_to_color(colorstring, &red, &grn, &blu) == 1) {
		  rgb = 1;
		  G_debug (3, "area:%d  cat %d r:%d g:%d b:%d", area, cat, red, grn, blu);
		} 
		else { 
		  rgb = 0;
		  G_warning (_("Error in color definition column (%s), area %d "
			       "with cat %d: colorstring [%s]"), 
			     rgb_column, area, cat, colorstring);
		} 
	      }
	      else {
		G_warning (_("Error in color definition column (%s), area %d with cat %d"), 
			  rgb_column, area, cat);
		rgb = 0;
	      }
	    }
	  } /* end if cat */
	  else {
	    rgb = 0;
	  } 
	} /* end if table_colors_flag */
 	
	/* random colors */
	if( cats_color_flag ) {
	    centroid = Vect_get_area_centroid ( Map, area );
	    if( cat >= 0 ) {
	      G_debug (3, "display area %d, centroid %d, cat %d", area, centroid, cat);
	      /* fetch color number from category */
	      which = (cat % palette_ncolors);
	      G_debug(3,"cat:%d which color:%d r:%d g:%d b:%d",cat, which,palette[which].R,palette[which].G,palette[which].B);
	      rgb = 1;
	      red = palette[which].R;
	      grn = palette[which].G;
	      blu = palette[which].B;
	    }
	    else {
	      rgb = 0;
	    }
	}
	
	if ( fcolor > -1 ) {
	  if (!table_colors_flag && !cats_color_flag) {
	    R_color(fcolor);
	    G_plot_polygon ( Points->x, Points->y, Points->n_points);
	  }
	  else {
	    if (rgb) {
	      R_RGB_color ((unsigned char) red, (unsigned char) grn, (unsigned char) blu);
	    }
	    else {
	      R_color (fcolor);
	    }
	    if (cat >= 0) {
	      G_plot_polygon ( Points->x, Points->y, Points->n_points);
	    }
	  }
	}

	/* boundary */
	if ( bcolor > -1 ) {
	    int i, j;
	    Vect_get_area_points ( Map, area, Points );   
	    if (rgb) {
	      R_RGB_color ((unsigned char) red, (unsigned char) grn, (unsigned char) blu);
	    }
	    else {
	      R_color (bcolor);
	    }
	    for ( i = 0; i < Points->n_points - 1; i++) { 
		G_plot_line (Points->x[i], Points->y[i], Points->x[i+1], Points->y[i+1]);
	    }
	    for ( i = 0; i < n_isles; i++) {
		isle = Vect_get_area_isle ( Map, area, i );   
		Vect_get_isle_points ( Map, isle, Points );
		for ( j = 0; j < Points->n_points - 1; j++) { 
		    G_plot_line (Points->x[j], Points->y[j], Points->x[j+1], Points->y[j+1]);
		}
	    }
	}
    } /* end for */

    Vect_destroy_line_struct (Points);
    Vect_destroy_line_struct (IPoints);
    Vect_destroy_cats_struct (Cats);

    return 0;
}
