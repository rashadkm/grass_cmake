/*****************************************************************************
*
* MODULE:       DBF driver 
*   	    	
* AUTHOR(S):    Radim Blazek
*
* PURPOSE:      Simple driver for reading and writing dbf files     
*
* COPYRIGHT:    (C) 2000 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*   	    	License (>=v2). Read the file COPYING that comes with GRASS
*   	    	for details.
*
*****************************************************************************/
#include <stdlib.h>
#include <grass/dbmi.h>
#include <grass/gis.h>
#include "globals.h"
#include "proto.h"

int
db__driver_close_cursor (dbCursor *dbc)

{
    cursor *c;

    /* get my cursor via the dbc token */
    c = (cursor *) db_find_token(db_get_cursor_token(dbc));
    if (c == NULL)
	return DB_FAILED;

    /* free_cursor(cursor) */
    free_cursor(c);

    return DB_OK;
}


cursor * alloc_cursor()
{
    cursor     *c;

    /* allocate the cursor */
    c = (cursor *) db_malloc(sizeof(cursor));
    if (c == NULL)
    {
        append_error ("cannot alloc new cursor");
        return c; 
    } 
    
    /* tokenize it */
    c->token = db_new_token(c);
    if (c->token < 0)       
    {
	free_cursor (c);
	c = NULL;
	append_error ("cannot tokenize new cursor\n");
    }

    return c;
}

void free_cursor( cursor *c)
{
    db_drop_token(c->token);
    sqpFreeStmt( c->st );  
    G_free (c);  
}


