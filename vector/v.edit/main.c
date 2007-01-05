/****************************************************************
 *
 * MODULE:     v.edit
 *
 * AUTHOR(S):  GRASS Development Team
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
#include <grass/gis.h>
#include <grass/glocale.h>

#define MAIN
#include "global.h"

/* static int error_routine(const char*msg, int fatal); */

int main (int argc, char *argv[])
{
    G_gisinit(argv[0]);
    int ret;
    FILE *output=stdout;

    module = G_define_module();
    module->keywords = _("vector, editing");
    module->description = _("Edits a vector map; allows adding, deleting and modifying objects in a vector map.");

    if(!parser(argc, argv))
	exit(EXIT_FAILURE);

/*     G_set_error_routine(error_routine); */
    mapset = G_find_vector2 (map_opt->answer, G_mapset()); 

    if ( mapset == NULL ) {
	if ( action_mode == MODE_CREATE ) {
	    Vect_open_new (&Map, map_opt->answer, 0 );
	    Vect_build ( &Map, NULL );
	    Vect_close (&Map);
	    Vect_open_update (&Map, map_opt->answer, G_mapset());
	    G_message(_("New empty map created."));
	    Vect_close(&Map);
	    G_debug (1, "Map closed");
	    exit(EXIT_SUCCESS);
	} else {
	    G_message(_("Map does not exist. Add flag -n to create a new map."));
	    exit(EXIT_FAILURE);
	}
    }
    else {
/* 	Vect_set_open_level(2); */
        if (action_mode != MODE_SELECT)
            Vect_open_update (&Map, map_opt->answer, mapset);
        else
            Vect_open_old (&Map, map_opt->answer, mapset);
    }
/*     Vect_set_category_index_update ( &Map ); */

    G_debug (1, "Map opened");

    switch(action_mode) {
      case MODE_ADD:
	G_message(_("Adding new features to vector file ..."));
        if ( ! n_flg->answer )
            read_head(ascii, &Map);
        ret = asc_to_bin(ascii, &Map) ;
	break;
      case MODE_DEL:
	ret = do_del(&Map);
	break;
      case MODE_MOVE:
        ret = do_move(&Map);
        break;
      case MODE_VERTEX:
        ret = do_move_vertex(&Map);
        break;
      case MODE_BREAK:
        ret = do_break(&Map);
        break;
      case MODE_STRAIGHTEN:
        ret = do_remove_vertex(&Map);
        break;
      case MODE_SPLIT:
        ret = do_split(&Map);
        break;
      case MODE_MERGE:
        ret = do_merge(&Map);
        break;
      case MODE_SELECT:
        ret = do_select(&Map);
        break;
      case MODE_CATADD:
        ret = cats(&Map, 0);
        break;
      case MODE_CATDEL:
        ret = cats(&Map, 1);
        break;
      case MODE_COPY:
        ret = do_copy(&Map);
        break;
      case MODE_SNAP:
        ret = do_snap(&Map);
        break;
      default:
	G_warning("Sorry this is not yet implemented");
	ret=0;
	break;
    }

    
    if(ret == 0)
	output=NULL;
    else
	Vect_hist_command(&Map);

    if  (action_mode != MODE_SELECT || t_flg->answer!=0) {
        Vect_build_partial(&Map, GV_BUILD_NONE, NULL);
        Vect_build(&Map, output );
    }

    Vect_close(&Map);
    G_debug(1, "Map closed");

    if(ret)
	exit(EXIT_SUCCESS);
    else
	exit(EXIT_FAILURE);
}
