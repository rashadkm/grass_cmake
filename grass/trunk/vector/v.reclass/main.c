/****************************************************************************
 *
 * MODULE:       v.reclass
 * AUTHOR(S):    R.L. Glenn, USDA, SCS, NHQ-CGIS (original contributor)
 *               GRASS 6 update: Radim Blazek <radim.blazek gmail.com>
 *               Glynn Clements <glynn gclements.plus.com>,
 *               Jachym Cepicky <jachym les-ejk.cz>, Markus Neteler <neteler itc.it>
 * PURPOSE:      
 * COPYRIGHT:    (C) 1999-2007 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#define KEY(x) (G_strcasecmp(key,x)==0)

int inpt (FILE *rulefd, char *buf);
int key_data (char *buf, char **k, char **d);
int reclass ( struct Map_info *In, struct Map_info *Out, int type, int field, dbCatValArray *cvarr, int optiond);

static int cmpcat ( const void *pa, const void *pb)
{
    dbCatVal *p1 = (dbCatVal *) pa;
    dbCatVal *p2 = (dbCatVal *) pb;

    if( p1->cat < p2->cat ) return -1;
    if( p1->cat > p2->cat ) return 1;
    return 0;
}

int 
main (int argc, char *argv[])
{
    struct GModule *module;
 /*    struct Flag *d_flag; */
    struct Option *in_opt, *out_opt, *type_opt, *field_opt, *rules_opt, *col_opt;
    char   *mapset, *key, *data, buf[1024];
    int    rclelem, type, field;
    struct Map_info In, Out;

    struct field_info *Fi;
    dbDriver *Driver;
    dbCatValArray cvarr;

    int i, n, ttype;
	    
    G_gisinit (argv[0]);

    module = G_define_module();
    module->keywords = _("vector, attribute table");
    module->description = "Changes vector category values for an existing vector map "
	    "according to results of SQL queries or a value in attribute table column.";

    in_opt = G_define_standard_option(G_OPT_V_INPUT);

    out_opt =  G_define_standard_option(G_OPT_V_OUTPUT);

    rules_opt = G_define_option();
    rules_opt->key = "rules";
    rules_opt->required = NO;
    rules_opt->type = TYPE_STRING;
    rules_opt->description =  "Full path to the reclass rule file";

    col_opt = G_define_option();
    col_opt->key            = "column";
    col_opt->type           = TYPE_STRING;
    col_opt->required       = NO;
    col_opt->multiple       = NO;
    col_opt->description    = "The name of the column values of which are used as new categories. "
	                      "The column must be type integer.";
    
    type_opt = G_define_standard_option(G_OPT_V_TYPE);
    type_opt->description = "Select type";
    type_opt->options = "point,line,boundary,centroid";
    type_opt->answer = "point,line,boundary,centroid";

    field_opt = G_define_standard_option(G_OPT_V_FIELD);

    if (G_parser(argc, argv)) exit(1);

    type = Vect_option_to_types ( type_opt );
    field = atoi (field_opt->answer);
    
    if ( (!(rules_opt->answer) && !(col_opt->answer)) || 
	 (rules_opt->answer && col_opt->answer) ) { 
	G_fatal_error ( "Either 'rules' or 'col' must be specified.");
    }

    Vect_check_input_output_name ( in_opt->answer, out_opt->answer, GV_FATAL_EXIT );
    
    mapset = G_find_vector2 (in_opt->answer, NULL);
    if(mapset == NULL) G_fatal_error ("Could not find input %s\n", in_opt->answer);
    Vect_set_open_level ( 2 );
    Vect_open_old (&In, in_opt->answer, mapset);
    
    Vect_open_new ( &Out, out_opt->answer, Vect_is_3d (&In) );
    Vect_copy_head_data (&In, &Out);
    Vect_hist_copy (&In, &Out);
    Vect_hist_command ( &Out );

    /* Read column values from database */
    db_CatValArray_init ( &cvarr );

    Fi = Vect_get_field( &In, field);
    if ( Fi == NULL )
	G_fatal_error ("Cannot get layer info for vector map");

    Driver = db_start_driver_open_database ( Fi->driver, Fi->database );
    if (Driver == NULL)
	G_fatal_error("Cannot open database %s by driver %s", Fi->database, Fi->driver);

    if ( col_opt->answer ) {
	int ctype;
        int nrec;

	/* Check column type */
	ctype = db_column_Ctype ( Driver, Fi->table, col_opt->answer );

	if ( ctype == -1 ) {
	    G_fatal_error ("Column <%s> not found", col_opt->answer );
        } 
	else if ( ctype == DB_C_TYPE_INT ) 
	{
	    nrec = db_select_CatValArray ( Driver, Fi->table, Fi->key, col_opt->answer, NULL, &cvarr );
	    G_debug (3, "nrec = %d", nrec );
        } 
	else if ( ctype == DB_C_TYPE_STRING ) 
	{
	    int  i, more, nrows, newval, len;
	    dbString stmt, stmt2;
	    dbString lastval;
	    dbCursor cursor;
	    dbColumn *column;
	    dbValue *value;
	    dbTable *table;
            struct field_info *NewFi;
	    dbDriver *Driver2;

	    db_init_string ( &stmt );
	    db_init_string ( &stmt2 );
	    db_init_string ( &lastval );

	    NewFi = Vect_default_field_info ( &Out, field, NULL, GV_1TABLE );
	    Vect_map_add_dblink ( &Out, field, NULL, NewFi->table, "cat", NewFi->database, NewFi->driver);
	    
	    Driver2 = db_start_driver_open_database ( NewFi->driver, 
		                                      Vect_subst_var(NewFi->database, &Out) );
	    
	    
	    sprintf( buf, "SELECT %s, %s FROM %s ORDER BY %s", Fi->key, col_opt->answer, 
		                                   Fi->table, col_opt->answer);
	    db_set_string ( &stmt, buf);

	    G_debug (3, "  SQL: %s", db_get_string ( &stmt ) );
	    
	    if (db_open_select_cursor(Driver, &stmt, &cursor, DB_SEQUENTIAL) != DB_OK)
		G_fatal_error("Cannot open select cursor: %s", db_get_string ( &stmt ) );

	    nrows = db_get_num_rows ( &cursor );
	    G_debug (3, "  %d rows selected", nrows );
	    if ( nrows < 0 ) G_fatal_error ( "Cannot select records from database");
		
	    db_CatValArray_alloc( &cvarr, nrows );

	    table = db_get_cursor_table (&cursor);

	    /* Check if key column is integer */
	    column = db_get_table_column(table, 0); 
	    ctype = db_sqltype_to_Ctype( db_get_column_sqltype(column) );
	    G_debug (3, "  key type = %d", type );

	    if ( ctype != DB_C_TYPE_INT ) { 
		G_fatal_error ( "Key column type is not integer" ); /* shouldnot happen */
	    }	

	    cvarr.ctype = DB_C_TYPE_INT;
	    
	    /* String column length */
	    column = db_get_table_column(table, 1); 
	    len = db_get_column_length(column);

	    /* Create table */
	    sprintf ( buf, "create table %s (cat integer, %s varchar(%d))", NewFi->table, 
		                       col_opt->answer, len );
	    
	    db_set_string ( &stmt2, buf);

	    if (db_execute_immediate (Driver2, &stmt2) != DB_OK ) {
		Vect_close (&Out);
		db_close_database_shutdown_driver ( Driver );
		db_close_database_shutdown_driver ( Driver2 );
		G_fatal_error ( "Cannot create table: %s", db_get_string (&stmt2) );
	    }

            if ( db_create_index2(Driver2, NewFi->table, "cat" ) != DB_OK )
                G_warning ( "Cannot create index" );

	    if (db_grant_on_table (Driver2, NewFi->table, DB_PRIV_SELECT, DB_GROUP|DB_PUBLIC ) != DB_OK )
	    {
		G_fatal_error ( "Cannot grant privileges on table %s", NewFi->table );
	    }

	    newval = 0;
	    
	    /* fetch the data */
	    for ( i = 0; i < nrows; i++ ) {
		if(db_fetch (&cursor, DB_NEXT, &more) != DB_OK) {
		    G_fatal_error ( "Cannot fetch data" );
		}

		column = db_get_table_column(table, 1);
		value  = db_get_column_value(column);

		if ( i == 0 || strcmp(db_get_value_string(value),db_get_string(&lastval))!=0 ) {
		    newval++;
		    db_set_string ( &lastval, db_get_value_string(value) );
		    G_debug (3, "  newval = %d string = %s", newval, db_get_value_string(value) );

		    db_set_string ( &stmt2, db_get_value_string(value) );
		    db_double_quote_string (&stmt2) ;
		    sprintf ( buf, "insert into %s values (%d, '%s')", NewFi->table, 
					       newval, db_get_string(&stmt2) );
		    
		    db_set_string ( &stmt2, buf);

		    if (db_execute_immediate (Driver2, &stmt2) != DB_OK ) {
			Vect_close (&Out);
			db_close_database_shutdown_driver ( Driver );
			db_close_database_shutdown_driver ( Driver2 );
			G_fatal_error ( "Cannot insert data: %s", db_get_string (&stmt2) );
		    }
		}

		column = db_get_table_column(table, 0); /* first column */
		value  = db_get_column_value(column);
		cvarr.value[i].cat = db_get_value_int(value);

		cvarr.value[i].val.i = newval;
		    
		G_debug (4, "  cat = %d newval = %d", cvarr.value[i].cat, newval );
	    }

	    cvarr.n_values = nrows;

    	    db_close_database_shutdown_driver(Driver2);
	    
	    db_close_cursor(&cursor);
	    db_free_string ( &stmt );
	    db_free_string ( &lastval );

	    qsort( (void *) cvarr.value, nrows, sizeof(dbCatVal), cmpcat);
	} 
        else 
        {	    
	    G_fatal_error ( "Column type must be integer or string." );
	}

    } else {
	int cat;
        char *label, *where;
        FILE *rulefd;

	G_debug (2, "Reading rules");
	
	if ( (rulefd = fopen(rules_opt->answer, "r")) == NULL )
	    G_fatal_error ("Unable to open rule file %s", rules_opt->answer);

	db_CatValArray_alloc ( &cvarr, Vect_get_num_lines(&In) );
	
	cat = 0;
	where = label = NULL;
	while ( inpt(rulefd, buf) ) {
	    if (!key_data(buf, &key, &data)) continue ;

	    G_strip(data);
	    G_debug (3, "key = %s data = %s", key, data);
	    
	    if (KEY("cat")) {	
		if ( cat > 0 ) G_fatal_error ( "Category %d overwritten by %s", cat, data);
		cat = atoi ( data );
		if( cat <= 0 ) G_fatal_error ( "Category '%s' invalid", data);
	    } else if (KEY("label")) {
		if ( label ) G_fatal_error ( "Label '%s' overwritten by '%s'", label, data);
		label = G_store ( data );
	    } else if (KEY("where")) {	
		if ( where ) G_fatal_error ( "Condition '%s' overwritten by '%s'", where, data);
		where = G_store(data);
	    } else {
		G_fatal_error ( "Unknown rule option: '%s'", key );
	    }

	    if ( cat > 0 && where ) {
		int i, over, *cats, ncats;
		dbCatVal *catval;
		
		G_debug (2, "cat = %d, where = '%s'", cat, where);
		if ( !label ) label = where;

		ncats = db_select_int ( Driver, Fi->table, Fi->key, where, &cats);
		if ( ncats == -1 ) G_fatal_error("Cannot select values from database.");
		G_debug (3, "  ncats = %d", ncats);
		

		/* If the category already exists, overwrite it cvarr, set to 0 in cats
		 * and don't add second time */
		over = 0;
		for ( i = 0; i < ncats; i++ ) {
		    if ( db_CatValArray_get_value ( &cvarr, cats[i], &catval ) == DB_OK ) {
			catval->val.i = cat;
			cats[i] = 0;
			over++;
		    }
		}
		if (over > 0) 
		    G_warning ("%d previously set categories overwritten by new category %d.", over, cat);
			
		for ( i = 0; i < ncats; i++ ) {
		    if ( cats[i] <= 0 ) continue;

		    if ( cvarr.n_values == cvarr.alloc ) {
			db_CatValArray_realloc ( &cvarr, (int)10+cvarr.alloc/3 );
		    }
		    G_debug (3, "Add old cat %d", cats[i]);
		    cvarr.value[cvarr.n_values].cat = cats[i];
		    cvarr.value[cvarr.n_values].val.i = cat;
		    cvarr.n_values++;
		}
		
		db_CatValArray_sort ( &cvarr );

		G_free ( cats );
		cat = 0;
		where = label = NULL;
	    }
	}

	if ( cat > 0 || where )
	    G_fatal_error ( "Incomplete rule");
    }

    db_close_database_shutdown_driver(Driver);
    
    /* reclass vector map */    
    rclelem = reclass ( &In, &Out, type, field, &cvarr, 0);

    /* Copy tables */
    n = Vect_get_num_dblinks ( &In );
    for ( i = 0; i < Vect_get_num_dblinks ( &In ); i++ ) {
	Fi = Vect_get_dblink ( &In, i );
	if ( Fi->number == field ) {
	    n--;
	    break;
	}
    }
    if ( n > 1 )
	ttype = GV_MTABLE;
    else 
    	ttype = GV_1TABLE;

    for ( i = 0; i < Vect_get_num_dblinks ( &In ); i++ ) {
	Fi = Vect_get_dblink ( &In, i );
	if ( Fi->number == field ) {
	    continue;
	}

	Vect_copy_table ( &In, &Out, Fi->number, Fi->number, Fi->name, ttype );
    }
    
    Vect_close (&In);

    Vect_build (&Out, stderr);
    Vect_close (&Out);

    G_message(_("%d features reclassed"), rclelem);

    exit(EXIT_SUCCESS);
}




