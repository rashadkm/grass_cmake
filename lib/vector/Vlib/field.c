/*
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
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <fnmatch.h> 
#include "Vect.h"
#include "gis.h"

int replace (char *, char *, char *, int);

/*!
 \fn struct field_info *Vect_get_field_info (    char *m,     char *ms,     int  field)
 \brief get information about link to database
 \return ADD
 \param pointer to map name, pointer to mapset name, category field
*/
struct field_info
*Vect_get_field_info (
    char *m,       /* pointer to map name */		
    char *ms,      /* pointer to mapset name */		
    int  field)    /* category field */
{
    int  i;	
    struct field_info *fi;
    FILE *fd;
    char files[2][1024],msets[2][200];
    char buf[1024];
    char *map, tmp1[1024], tmp2[1024];
    char md[1024], mp[1024], mpset[1024];
    char tab[1024], col[1024], db[1024], drv[1024];
    char m_tab[1024], m_col[1024], m_db[1024], m_drv[1024];
    int  fld;
    char *c;
    int  ndef, row, rule, nfiles;
    int  matched;
    
    G_debug (1, "Vect_get_field_info(): map = %s, mapset = %s", m, ms);
    
    fi = NULL;
    
    if ( ms == NULL || strlen(ms) == 0 )
       ms = G_mapset();	    
    
    if ( !(G__name_is_fully_qualified(m, tmp1, tmp2)) )
        map = G_fully_qualified_name ( m, ms );
    
    G_debug (1, "map = %s", map);
    sprintf ( files[0], "%s/%s/DB", G_location_path(), G_mapset());
    strcpy ( msets[0], G_mapset() );
    nfiles = 1;

    G_debug (1, "file 1 = %s", files[0]);
    if ( strcmp ( ms, G_mapset() ) != 0 )
      {
        sprintf ( files[1], "%s/%s/DB", G_location_path(), ms);
	strcpy ( msets[1], ms );
        nfiles = 2;
      }

    G_debug (1, "nfiles = %d", nfiles);
    matched = FALSE;
    for (i=nfiles-1; i >= 0; i--)
      {
        fd = fopen ( files[i], "r" );
        if ( fd == NULL )
          { 
            sprintf ( buf, "Cannot open vector database definition file %s", files[i]);
            G_warning ( buf );
	    return (NULL);      
          }	
    
        row = 0;
        rule = 0;
        while (fgets (buf, 1023, fd) != NULL)
          {
	    row++;      
            G_chop ( buf ); 
            G_debug (1, "DB: %s", buf);

	    c = (char *) strchr ( buf, '#');
	    if ( c != NULL ) *c = '\0';

	    if ( strlen(buf) == 0 ) continue;
	    
	    ndef = sscanf ( buf, "%s %d %s %s %s %s", md, &fld, tab, col, db, drv);
	
	    if ( ndef < 3 || (ndef < 6 && rule < 1 ) )
	      {
                sprintf ( buf, "Error in rule on row %d in %s", row, files[i]);
                G_warning ( buf );
	        continue;
	      }
	
	    rule++;
            if ( !(G__name_is_fully_qualified(md, mp, mpset)) )
	      {
                strcpy ( mpset, msets[i] );
                strcpy ( md, G_fully_qualified_name(md, mpset) );
	      }
		
	    if ( fnmatch ( md, map, 0) == 0 && field == fld )
	      {
                strcpy (m_tab, tab);
                strcpy (m_col, col);
                strcpy (m_db, db);
                strcpy (m_drv, drv);
	        matched = TRUE;
	      }
          }
        fclose (fd);
      }
    
    if ( matched )		  
      {
        /* replace variables */
        replace ( m_tab, m, ms, field );
        replace ( m_col, m, ms, field );
        replace ( m_db, m, ms, field );
        replace ( m_drv, m, ms, field );
		
        fi = (struct field_info *) malloc( sizeof(struct field_info) );
	fi->table = G_store ( m_tab );
	fi->key = G_store ( m_col );
	fi->database = G_store ( m_db );
	fi->driver = G_store ( m_drv );
      }

    G_debug (1, "Field info is read");
    return (fi);
}

int replace ( char *str, char *map, char *mapset, int field )
{
    char *c;
    char buf[1024];
    
    strcpy ( buf, str );
    c = (char *) strstr ( buf, "$GISDBASE" );
    if ( c != NULL )
      {
        *c = '\0';	      
        sprintf (str, "%s%s%s", buf, G_gisdbase(), c+9);
      }

    strcpy ( buf, str );
    c = (char *) strstr ( buf, "$LOCATION" );
    if ( c != NULL )
      {
        *c = '\0';	      
        sprintf (str, "%s%s%s", buf, G_location(), c+9);
      }
    
    strcpy ( buf, str );
    c = (char *) strstr ( buf, "$MAPSET" );
    if ( c != NULL )
      {
        *c = '\0';	      
        sprintf (str, "%s%s%s", buf, mapset, c+7);
      }
    
    strcpy ( buf, str );
    c = (char *) strstr ( buf, "$MAP" );
    if ( c != NULL )
      {
        *c = '\0';	      
        sprintf (str, "%s%s%s", buf, map, c+4 );
      }

    strcpy ( buf, str );
    c = (char *) strstr ( buf, "$FIELD" );
    if ( c != NULL )
      {
        *c = '\0';	      
        sprintf (str, "%s%d%s", buf, field, c+6 );
      }
    
    return (1);
}


