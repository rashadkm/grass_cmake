/*
* $Id$
*/

/*  Gv.c 
    Bill Brown, USACERL  
    December 1993
    Uses GRASS routines!
*/
#include <stdlib.h>
#include "gis.h"
#include "Vect.h"

#include "gstypes.h"

#define TRAK_MEM

#ifdef TRAK_MEM
static int Tot_mem = 0;
#endif

/* This loads to memory.  
The other alternative may be to load to a tmp file. */
geoline *Gv_load_vect(char *grassname, int *nlines)
{
    struct Map_info map;
    struct line_pnts *points;
    char            *mapset;
    geoline *top, *gln, *prev;
    int np, ret, i, n, nl=0, polygon, area;
    struct Cell_head  wind;

    /* TODO: handle error messages */

    if (NULL == (mapset = G_find_vector2(grassname,"")))
    {
	fprintf(stderr,"Can't find vector file %s.\n",grassname);
	
	return(NULL);
    }

    if (1 > Vect_open_old (&map, grassname, mapset))
    {
	fprintf(stderr,"Can't open vector file %s.\n",grassname);
	
	return(NULL);
    }
    
    if (NULL == (top=gln=(geoline *)malloc(sizeof(geoline))))
    {
	fprintf(stderr,"Can't malloc.\n");
	
	return(NULL);
    }
    
    #ifdef TRAK_MEM
    {
    	Tot_mem+=sizeof(geoline);
    }
    #endif

    points = Vect_new_line_struct ();

    G_get_set_window (&wind) ;
    Vect_set_constraint_region(&map,wind.north,wind.south,wind.east,wind.west,
	                       PORT_DOUBLE_MAX, -PORT_DOUBLE_MAX);

    /* Decide if lines or polygons */
    /* TODO: this is far from optimal */
    ret = Vect_read_next_line(&map, points, NULL);
    if ( ret == GV_BOUNDARY && Vect_level(&map) >= 2 && Vect_is_3d(&map) ) {
       	polygon = 1;
    } else { 
	polygon = 0;
    }
    
    Vect_rewind ( &map );
    
    if ( !polygon ) {
	if (map.head.with_z == WITHOUT_Z)
	{
	    G_debug(3, "Vector 2D non polygon layer");
	    while (-2 != (ret = Vect_read_next_line(&map, points, NULL)))
	    {
		G_debug(3, "read line 2d : type = %d", ret);

		if ( ret & ( GV_LINE | GV_BOUNDARY ) )
		{ 
		    nl++;
		    
		    gln->dims = 2;
		    gln->npts = np = points->n_points;
	    
		    if (NULL == (gln->p2=(Point2 *)calloc(np, sizeof(Point2))))
		    {
			fprintf(stderr,"Can't calloc.\n"); /* CLEAN UP */
		    
			return(NULL);
		    }
	
		    #ifdef TRAK_MEM
		    {
			Tot_mem+=(np*sizeof(Point2));
		    }
		    #endif
		
		    for (i=0; i < np; i++)
		    {
			gln->p2[i][X] = points->x[i];
			gln->p2[i][Y] = points->y[i];
		    }
		
		    if (NULL == (gln->next=(geoline *)malloc (sizeof(geoline))))
		    {
			fprintf(stderr,"Can't malloc.\n"); /* CLEAN UP */
		    
			return(NULL);
		    }

		    #ifdef TRAK_MEM
		    {
			Tot_mem+=sizeof(geoline);
		    }
		    #endif
		
		    prev = gln;
		    gln = gln->next;
		}
	    }
	} 
	else  /* vector is 3D > read with z coors to Point3 */
	{
	    G_debug(3, "Vector 3D non polygon layer");
	    while (-2 != (ret = Vect_read_next_line(&map, points, NULL)))
	    {
		    
		G_debug(3, "read line 3d : type = %d", ret);
		
		if ( ret & ( GV_LINE | GV_BOUNDARY ) )
		{ 
		    nl++;
		    gln->dims = 3;
		    gln->npts = np = points->n_points;
	    
		    if (NULL == (gln->p3=(Point3 *)calloc(np, sizeof(Point3))))
		    {
			fprintf(stderr,"Can't calloc.\n"); /* CLEAN UP */
		    
			return(NULL);
		    }
	
		    #ifdef TRAK_MEM
		    {
			Tot_mem+=(np*sizeof(Point3));
		    }
		    #endif
		
		    for (i=0; i < np; i++)
		    {
			gln->p3[i][X] = points->x[i];
			gln->p3[i][Y] = points->y[i];
			gln->p3[i][Z] = points->z[i];
		    }
		
		    if (NULL == (gln->next=(geoline *)malloc (sizeof(geoline))))
		    {
			fprintf(stderr,"Can't malloc.\n"); /* CLEAN UP */
		    
			return(NULL);
		    }

		    #ifdef TRAK_MEM
		    {
			Tot_mem+=sizeof(geoline);
		    }
		    #endif
		
		    prev = gln;
		    gln = gln->next;
		}
	    }
	}
    } else { /* read polygons */
	G_debug(3, "Vector polygon layer.");
	n = Vect_get_num_areas (&map);
	G_debug(3, " nareas = %d", n);
	for ( area = 1; area <= n ; area++ ) {
	    G_debug(3, " area %d", area);

	    Vect_get_area_points ( &map, area, points ); 
	    if ( map.head.with_z ) {
		gln->dims = -3;
		gln->npts = np = points->n_points;
	    
		if (NULL == (gln->p3=(Point3 *)calloc(np, sizeof(Point3))))
		{
		    fprintf(stderr,"Can't calloc.\n"); /* CLEAN UP */
		
		    return(NULL);
		}
    
		#ifdef TRAK_MEM
		{
		    Tot_mem+=(np*sizeof(Point3));
		}
		#endif
	    
		for (i=0; i < np; i++)
		{
		    gln->p3[i][X] = points->x[i];
		    gln->p3[i][Y] = points->y[i];
		    gln->p3[i][Z] = points->z[i];
		}
	    
		if (NULL == (gln->next=(geoline *)malloc (sizeof(geoline))))
		{
		    fprintf(stderr,"Can't malloc.\n"); /* CLEAN UP */
		
		    return(NULL);
		}

		#ifdef TRAK_MEM
		{
		    Tot_mem+=sizeof(geoline);
		}
		#endif
	    
		prev = gln;
		gln = gln->next;
	    }
	}
	nl = n;
    }
    
    prev->next = NULL;
    free(gln);
    
    #ifdef TRAK_MEM
    {
    	Tot_mem-=sizeof(geoline);
    }
    #endif
    
    Vect_close (&map);

    fprintf(stderr,"Vector file %s loaded.\n",grassname);
    *nlines = nl;

    #ifdef TRAK_MEM
    {
    	fprintf(stderr,"Total vect memory = %d Kbytes\n", Tot_mem/1000);
    }
    #endif
    
    return(top);
}

void add_Vectmem(int plus)
{
    #ifdef TRAK_MEM
    {
    	Tot_mem+=plus;
    }
    #endif
    
    return;
}

void sub_Vectmem(int minus)
{
    #ifdef TRAK_MEM
    {
    	Tot_mem-=minus;
    }
    #endif
    
    return;
}

void show_Vectmem(void)
{
    #ifdef TRAK_MEM
    {
    	fprintf(stderr,"Total vect memory = %d Kbytes\n", Tot_mem/1000);
    }
    #endif
    
    return;
}


