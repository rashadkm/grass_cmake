/****************************************************************************
*
* MODULE:       v.transform
* AUTHOR(S):    See below also.
*               Eric G. Miller <egm2@jps.net>
*               Upgrade to 5.1 Radim Blaze
* PURPOSE:      To transform a vector layer's coordinates via a set of tie
*               points.
* COPYRIGHT:    (C) 2002 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*   	    	License (>=v2). Read the file COPYING that comes with GRASS
*   	    	for details.
*
*****************************************************************************/
/*
*  This takes an ascii digit file in one coordinate system and converts
*  the map to another coordinate system.
*  Uses the transform library:  $(TRANSLIB)
*
*  Written during the ice age of Illinois, 02/16/90, by the GRASS team, -mh.
*
*  Modified by Dave Gerdes  1/90  for dig_head stuff
*  Modified by Radim Blazek to work on binary files
*/
#define MAIN

#include <string.h>
#include "trans.h"
#include "gis.h"
#include "Vect.h"
#include "dbmi.h"
#include "local_proto.h"

int main (int argc, char *argv[])
{
    int    i, n, tbtype, ret;
    struct file_info  Current, Trans, Coord ;
    struct GModule *module;
    struct Option *old, *new, *pointsfile;
    struct Flag *quiet_flag;
    char   *mapset, mon[4], date[40], buf[1000];
    struct Map_info Old, New;
    int    day, yr; 
    struct field_info *Fi, *Fin;

    G_gisinit(argv[0]) ;

    module = G_define_module();
    module->description = "Transforms an vector map layer from one "
			  "coordinate system into another coordinate system.";

    quiet_flag = G_define_flag();
    quiet_flag->key		= 'y';
    quiet_flag->description = "suppress display of residuals or other information"; 

    old = G_define_option();
    old->key			= "input";
    old->type			= TYPE_STRING;
    old->required			= YES;
    old->multiple			= NO;
    old->gisprompt			= "old,dig,vector";
    old->description		= "vector map to be transformed";
    
    new = G_define_option();
    new->key			= "output";
    new->type			= TYPE_STRING;
    new->required			= YES;
    new->multiple			= NO;
    new->gisprompt			= "new,dig,vector";
    new->description		= "resultant vector map";

    pointsfile = G_define_option();
    pointsfile->key			= "pointsfile";
    pointsfile->type			= TYPE_STRING;
    pointsfile->required		= NO;
    pointsfile->multiple		= NO;
    pointsfile->description		= "file holding transform coordinates";
    
    if (G_parser (argc, argv))
	exit (-1);
    
    strcpy (Current.name, old->answer);
    strcpy (Trans.name, new->answer);
    
    if (pointsfile->answer != NULL)
	strcpy (Coord.name, pointsfile->answer);
    else
	Coord.name[0] = '\0';
    
    /* open coord file */
    if ( Coord.name[0] != '\0' ){
	if ( (Coord.fp = fopen(Coord.name, "r"))  ==  NULL) 
	    G_fatal_error ("Could not open file with coordinates : %s\n", Coord.name) ;
    }
    
    /* open vectors */
    if ( (mapset = G_find_vector2 ( old->answer, "")) == NULL)
	G_fatal_error ("Could not find input vector %s\n", old->answer);
    
    if( Vect_open_old(&Old, old->answer, mapset) < 1)
	G_fatal_error("Could not open input vector %s\n", old->answer);

    if (0 > Vect_open_new (&New, new->answer, Vect_is_3d(&Old) )) {
	Vect_close (&Old);
	G_fatal_error("Could not open output vector %s\n", new->answer);
    }


    /* copy and set header */
    Vect_copy_head_data(&Old, &New);

    sprintf(date,"%s",G_date());
    sscanf(date,"%*s%s%d%*s%d",mon,&day,&yr);
    sprintf(date,"%s %d %d",mon,day,yr);
    Vect_set_date ( &New, date );
    
    Vect_set_person ( &New, G_whoami() );

    sprintf (buf, "transformed from %s", old->answer);
    Vect_set_map_name ( &New, buf);
    
    Vect_set_scale ( &New, 0.0 );
    Vect_set_zone ( &New, 0 );
    Vect_set_thresh ( &New, 0.0 );
    
    create_transform_conversion( &Coord, quiet_flag->answer);

    if (Coord.name[0] != '\0')
	    fclose( Coord.fp) ;
    
    if (!quiet_flag->answer) fprintf (stdout,"\nNow transforming the vectors ...\n") ;
    
    transform_digit_file( &Old, &New) ;

    /* Copy tables */
    if (!quiet_flag->answer) fprintf (stdout,"Copying tables ...\n") ;
    n = Vect_get_num_dblinks ( &Old );
    tbtype = GV_1TABLE;
    if ( n > 1 ) tbtype = GV_MTABLE;
    for ( i = 0; i < n; i++ ) {
	Fi = Vect_get_dblink ( &Old, i );
	if ( Fi == NULL ) {
	    G_warning ( "Cannot get db link info -> cannot copy table." );
	    continue;
	}
	Fin = Vect_default_field_info ( New.name, Fi->number, Fi->name, tbtype );
        G_debug (3, "Copy drv:db:table '%s:%s:%s' to '%s:%s:%s'", 
	              Fi->driver, Fi->database, Fi->table, Fin->driver, Fin->database, Fin->table );
	Vect_map_add_dblink ( &New, Fi->number, Fi->name, Fin->table, Fi->key, Fin->database, Fin->driver);
        
	ret = db_copy_table ( Fi->driver, Fi->database, Fi->table, 
		    Fin->driver, Vect_subst_var(Fin->database,New.name,G_mapset()), Fin->table );
	if ( ret == DB_FAILED ) {
	    G_warning ( "Cannot copy table" );
	    continue;
	}
    }

    Vect_close (&Old);

    if (!quiet_flag->answer) Vect_build (&New, stdout); else Vect_build (&New, NULL);
    Vect_close (&New);

    if (!quiet_flag->answer)
	    fprintf (stdout,"'%s' has finished the transformation of the vectors.\n", argv[0]) ;

    exit(0) ;
}

