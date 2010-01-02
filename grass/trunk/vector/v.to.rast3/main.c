
/****************************************************************************
 *
 * MODULE:       v.to.rast3
 * AUTHOR(S):    Original s.to.rast3: Jaro Hofierka, Geomodel s.r.o. (original contributor)
 *               9/2005 Upgrade to GRASS 6 by Radim Blazek
 *               Soeren Gebbert <soeren.gebbert gmx.de>
 *               OGR support by Martin Landa <landa.martin gmail.com>
 * PURPOSE:      Converts vector points to 3D raster
 * COPYRIGHT:    (C) 1999-2010 by the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2). Read the file COPYING that
 *               comes with GRASS for details.
 *
 *****************************************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/G3d.h>
#include <grass/vector.h>
#include <grass/dbmi.h>

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *in_opt, *out_opt, *field_opt, *col_opt;
    int field;
    G3D_Region region;

    struct Map_info Map;
    struct line_pnts *Points;
    struct line_cats *Cats;
    void *map = NULL;

    int nlines, line, nrec, ctype;

    struct field_info *Fi;
    dbDriver *Driver;
    dbCatValArray cvarr;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("volume"));
    G_add_keyword(_("conversion"));
    module->description = _("Converts a vector map "
			    "(only points) into a 3D raster map.");

    in_opt = G_define_standard_option(G_OPT_V_INPUT);

    field_opt = G_define_standard_option(G_OPT_V_FIELD);

    out_opt = G_define_standard_option(G_OPT_R3_OUTPUT);

    col_opt = G_define_standard_option(G_OPT_DB_COLUMN);
    col_opt->required = YES;
    col_opt->description = _("Name or attrbitute column (data type must be numeric)");
    
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    G3d_getWindow(&region);
    G3d_readWindow(&region, NULL);

    Vect_set_open_level(2);
    Vect_open_old2(&Map, in_opt->answer, "", field_opt->answer);
    field = Vect_get_field_number(&Map, field_opt->answer);

    db_CatValArray_init(&cvarr);
    Fi = Vect_get_field(&Map, field);
    if (Fi == NULL)
	G_fatal_error(_("Database connection not defined for layer <%s>"), field_opt->answer);

    Driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (Driver == NULL)
	G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		      Fi->database, Fi->driver);

    /* Note: do not check if the column exists in the table because it may be expression */

    nrec = db_select_CatValArray(Driver, Fi->table, Fi->key,
				 col_opt->answer, NULL, &cvarr);

    G_debug(2, "nrec = %d", nrec);
    if (nrec < 0)
	G_fatal_error(_("Unable to select data from table"));

    ctype = cvarr.ctype;
    if (ctype != DB_C_TYPE_INT && ctype != DB_C_TYPE_DOUBLE)
	G_fatal_error(_("Column type not supported"));

    db_close_database_shutdown_driver(Driver);

    map = G3d_openCellNew(out_opt->answer, FCELL_TYPE,
			  G3D_USE_CACHE_DEFAULT, &region);

    if (map == NULL)
	G_fatal_error(_("Unable to create output map"));

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    nlines = Vect_get_num_lines(&Map);
    for (line = 1; line <= nlines; line++) {
	int type, cat, depth, row, col, ret;
	double value;
	
	G_percent(line, nlines, 2);
	
	type = Vect_read_line(&Map, Points, Cats, line);
	if (!(type & GV_POINT))
	    continue;

	Vect_cat_get(Cats, field, &cat);
	if (cat < 0) {
	    continue;
	}

	if (Points->x[0] < region.west || Points->x[0] > region.east
	    || Points->y[0] < region.south || Points->y[0] > region.north
	    || Points->z[0] < region.bottom || Points->z[0] > region.top) {
	    continue;
	}

	/*Because the g3d lib is row oriented and counts therefore from north to south,
	 * we have to do the same here*/
	row = (int)floor((region.north - Points->y[0]) / region.ns_res);
	col = (int)floor((Points->x[0] - region.west) / region.ew_res);
	depth = (int)floor((Points->z[0] - region.bottom) / region.tb_res);

	if (ctype == DB_C_TYPE_INT) {
	    int ivalue;

	    ret = db_CatValArray_get_value_int(&cvarr, cat, &ivalue);
	    value = ivalue;
	}
	else if (ctype == DB_C_TYPE_DOUBLE) {
	    ret = db_CatValArray_get_value_double(&cvarr, cat, &value);
	}

	if (ret != DB_OK) {
	    G_warning(_("No record for line (cat = %d)"), cat);
	    continue;
	}

	G_debug(3, "col,row,depth,val: %d %d %d %f", col, row, depth, value);

	G3d_putFloat(map, col, row, depth, (float)value);
    }

    Vect_close(&Map);

    if (!G3d_closeCell(map))
	G_fatal_error(_("Unable to close new 3d raster map"));
    
    exit(EXIT_SUCCESS);
}
