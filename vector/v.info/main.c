/***************************************************************
 *
 * MODULE:       v.info
 * 
 * AUTHOR(S):    CERL, updated to 5.1 by Markus Neteler
 *               
 * PURPOSE:      print vector map info
 *               
 * COPYRIGHT:    (C) 2002 by the GRASS Development Team
 *
 *               This program is free software under the 
 *               GNU General Public License (>=v2). 
 *               Read the file COPYING that comes with GRASS
 *               for details.
 *
 **************************************************************/
#include <string.h>
#include <stdlib.h>
#include "gis.h"
#include "Vect.h"

#define printline(x) fprintf (stdout, " | %-74.74s |\n", x)
#define divider(x) \
	fprintf (stdout, " %c", x); \
	for (i = 0; i < 76; i++ ) \
		fprintf ( stdout, "-" ); \
	fprintf (stdout, "%c\n", x)

/* the vector header is here:
   include/vect/dig_structs.h
   
   the vector API is here:
   lib/vector/Vlib/level_two.c
*/

int
main (int argc, char *argv[])
{
  struct GModule *module;
  struct Option *in_opt;
  struct Map_info Map;
  struct dig_head v_head;
  BOUND_BOX box;
  char *mapset, line[200];
  int i;
  int with_z;

  module = G_define_module();
  module->description =
	"Outputs basic information about a user-specified vector map layer.";

  /* get G_OPT_ from include/gis.h */
  in_opt = G_define_standard_option(G_OPT_V_MAP);

  /* is the G_gisinit() position correct here? see also v.clean */
  G_gisinit (argv[0]);
  if (G_parser(argc,argv))
    exit(1);

  /* open input vector */
  if ((mapset = G_find_vector2 (in_opt->answer, "")) == NULL) {
     G_fatal_error ("Could not find input %s\n", in_opt->answer);
  }
    
  Vect_set_open_level (2);
  Vect_open_old (&Map, in_opt->answer, mapset);
  with_z = Vect_is_3d (&Map);
  v_head = Map.head;

  Vect_set_fatal_error (GV_FATAL_PRINT);

  divider ('+');
  sprintf (line, "Mapset:   %-29.29s  Organization: %s", mapset, Vect_get_organization(&Map));
  printline (line);
  sprintf (line, "Layer:    %-29.29s  Source Date: %s", in_opt->answer, Vect_get_map_date(&Map));
  printline (line);
  sprintf (line, "Orig. Scale: 1:%d", Vect_get_scale(&Map));
  printline (line);
  sprintf (line, "Location: %-29.29s  Name of creator: %s", G_location(), Vect_get_person(&Map));
  printline (line);
  sprintf (line, "DataBase: %s", G_gisdbase() );
  printline (line);
  sprintf (line, "Title:    %s", Vect_get_map_name(&Map) );
  printline (line);
  sprintf (line, "Map format: %s",  Vect_maptype_info(&Map) );
  printline (line);

  divider ('|');

  sprintf (line, "  Type of Map:  %s (level: %i)        ", "Vector", Vect_level (&Map));

  printline (line);

  if ( Vect_level (&Map) > 1)
  {
    sprintf (line, "                                         Number of points:     %-9ld", (long)Vect_get_num_primitives(&Map, GV_POINT));
    printline (line);
    sprintf (line, "                                         Number of lines:      %-9ld", (long)Vect_get_num_primitives(&Map, GV_LINE));
    printline (line);
    sprintf (line, "                                         Number of centroids:  %-9ld", (long)Vect_get_num_primitives(&Map, GV_BOUNDARY));
    printline (line);
    sprintf (line, "                                         Number of areas:      %-9ld", (long)Vect_get_num_areas(&Map));
    printline (line);
    sprintf (line, "                                         Number of faces:      %-9ld", (long)Vect_get_num_primitives(&Map, GV_FACE));
    printline (line);
    sprintf (line, "                                         Number of kernels:    %-9ld", (long)Vect_get_num_primitives(&Map, GV_KERNEL));
    printline (line);
    sprintf (line, "                                         Number of islands:    %-9ld", (long)Vect_get_num_islands(&Map));
    printline (line);
    sprintf (line, "                                         Map is 3D:            %d", Vect_is_3d(&Map));
    printline (line);
    sprintf (line, "                                         Number of dblinks:    %-9ld", (long)Vect_get_num_dblinks(&Map));
    printline (line);
  }
  else
  {
    sprintf (line, "                No topology present.");
    printline (line);
  }

  sprintf (line, "  Projection: %s (zone %d)", G_database_projection_name(), G_zone());
  printline (line);

  Vect_get_map_box (&Map, &box );
  sprintf (line, "           N: %-10.3f    S: %-10.3f", box.N, box.S);
  printline (line);
  sprintf (line, "           E: %-10.3f    W: %-10.3f", box.E, box.W);
  printline (line);
  sprintf (line, "           B: %-6.3f    T: %-6.3f", box.B, box.T);
  printline (line);

  printline ("");
  sprintf (line, "  Digitize threshold: %.5f", Vect_get_thresh(&Map));
  printline (line);
  sprintf (line, "  Comments:");
  printline (line);
  sprintf (line, "    %s", v_head.line_3);
  printline (line);
  divider ('+');
  fprintf (stdout, "\n");
 
  Vect_close (&Map);

  return (0);
}

