/*
* $Id$
*
****************************************************************************
*
* MODULE:       Vector library 
*   	    	
* AUTHOR(S):    Original author CERL, probably Dave Gerdes or Mike Higgins.
*               Update to GRASS 5.1 Radim Blazek and David D. Gray.
*
* PURPOSE:      Higher level functions for reading/writing/manipulating vectors.
*
* COPYRIGHT:    (C) 2001 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*   	    	License (>=v2). Read the file COPYING that comes with GRASS
*   	    	for details.
*
*****************************************************************************/
#include "Vect.h"

static int read_next_dummy () { return -1; }

static int (*Read_next_line_array[][3]) () =
{
    { read_next_dummy, V1_read_next_line_nat, V2_read_next_line_nat }
   ,{ read_next_dummy, V1_read_next_line_shp, V2_read_next_line_shp }
#ifdef HAVE_POSTGRES
   ,{ read_next_dummy, V1_read_next_line_post }
#endif
};

static int (*V1_read_line_array[]) () =
{
   V1_read_line_nat 
   , V1_read_line_shp 
#ifdef HAVE_POSTGRES
   , V1_read_line_post 
#endif
};

static int (*V2_read_line_array[]) () =
{
   V2_read_line_nat 
   , V2_read_line_shp 
#ifdef HAVE_POSTGRES
   /*, V2_read_line_post */
#endif
};

static long (*Next_line_offset_array[]) () =
{
   Vect_next_line_offset_nat 
   , Vect_next_line_offset_shp 
#ifdef HAVE_POSTGRES
   /* , Vect_next_line_offset_post */
#endif
};

/*
*   returns: line type
*           -1 on Out of memory
*           -2 on EOF   
*/
int
Vect_read_next_line (Map, line_p, line_c)
     struct Map_info *Map;
     struct line_pnts *line_p;
     struct line_cats *line_c;
{
#ifdef GDEBUG
    G_debug (3, "Vect_read_next_line()");
#endif    
  
    if (!VECT_OPEN (Map))
        return -1;

    return (*Read_next_line_array[Map->format][Map->level]) (Map, line_p, line_c);
}

/*
*   returns: line type
*           -1 on Out of memory
*           -2 on EOF   
*/
int
V1_read_line (Map, line_p, line_c, offset )
     struct Map_info *Map;
     struct line_pnts *line_p;
     struct line_cats *line_c;
     long   offset;
{
#ifdef GDEBUG
    G_debug (3, "V1_read_line()");
#endif    
  
    if (!VECT_OPEN (Map))
        return -1;

    return (*V1_read_line_array[Map->format]) (Map, line_p, line_c, offset);
}

/*
*   returns: line type
*           -1 on Out of memory
*           -2 on EOF   
*/
int
V2_read_line (Map, line_p, line_c, line )
     struct Map_info *Map;
     struct line_pnts *line_p;
     struct line_cats *line_c;
     int    line;
{

#ifdef GDEBUG
    G_debug (3, "V2_read_line()");
#endif    
  
    if (!VECT_OPEN (Map))
        return -1;
    
    return (*V2_read_line_array[Map->format]) (Map, line_p, line_c, line);
}

/*
*  Returns  next line offset
*/
long
Vect_next_line_offset ( struct Map_info *Map )
{
    return (*Next_line_offset_array[Map->format]) (Map);
}

/*
*  Returns: 1 - line alive
*           0 - line is dead
*/
int
Vect_line_alive ( struct Map_info *Map, int line )
{
    if ( Map->plus.Line[line] != NULL ) return 1;
    
    return 0;
}

