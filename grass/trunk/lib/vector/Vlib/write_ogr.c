/*!
   \file lib/vector/Vlib/write_ogr.c

   \brief Vector library - write vector feature (OGR format)

   Higher level functions for reading/writing/manipulating vectors.

   Inspired by v.out.ogr's code.

   \todo OGR version of V2__delete_area_cats_from_cidx_nat()
   \todo function to delete corresponding entry in fidx
   \todo OGR version of V2__add_area_cats_to_cidx_nat
   \todo OGR version of V2__add_line_to_topo_nat

   (C) 2009-2011 by the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2). Read the file COPYING that comes with GRASS for details.

   \author Martin Landa <landa.martin gmail.com>
 */

#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#ifdef HAVE_OGR
#include <ogr_api.h>

static int sqltype_to_ogrtype(int);
static int write_attributes(dbDriver *, int, const struct field_info *,
			    OGRLayerH, OGRFeatureH);

static void V2__add_line_to_topo_ogr(struct Map_info *Map, int line,
				     const struct line_pnts *points,
				     const struct line_cats *cats)
{
    int first, s, i;
    int type, area, side;

    struct Plus_head *plus;
    struct P_line *Line;
    
    struct bound_box box, abox;
    
    G_debug(3, "V2__add_line_to_topo_ogr(): line = %d", line);

    plus = &(Map->plus);
    Line = plus->Line[line];
    type = Line->type;

    if (plus->built >= GV_BUILD_AREAS &&
	type == GV_BOUNDARY) {	
	struct P_topo_b *topo = (struct P_topo_b *)Line->topo;
	
	if (topo->N1 != topo->N2) {
	    G_warning(_("Boundary is not closed. Skipping."));
	    return;
	}
	
	/* Build new areas/isles */
	for (s = 0; s < 2; s++) {
	    side = (s == 0 ? GV_LEFT : GV_RIGHT);
	    area = Vect_build_line_area(Map, line, side);
	    if (area > 0) {	/* area */
		Vect_get_area_box(Map, area, &box);
		if (first) {
		    Vect_box_copy(&abox, &box);
		    first = FALSE;
		}
		else
		    Vect_box_extend(&abox, &box);
	    }
	    else if (area < 0) {
		/* isle -> must be attached -> add to abox */
		Vect_get_isle_box(Map, -area, &box);
		if (first) {
		    Vect_box_copy(&abox, &box);
		    first = FALSE;
		}
		else
		    Vect_box_extend(&abox, &box);
	    }
	    G_debug(4, "Vect_build_line_area(): -> area = %d", area);
	}

	/* Attach centroid/isle to the new area */
	if (plus->built >= GV_BUILD_ATTACH_ISLES)
	    Vect_attach_isles(Map, &abox);
	if (plus->built >= GV_BUILD_CENTROIDS)
	    Vect_attach_centroids(Map, &abox);
    }
    
    /* Add category index */
    for (i = 0; i < cats->n_cats; i++) {
	dig_cidx_add_cat_sorted(plus, cats->field[i], cats->cat[i], line,
				type);
    }
    
    return;
}

/*!
  \brief Writes feature on level 1 (OGR interface)

  Note:
   - centroids are not supported in OGR, pseudotopo holds virtual
     centroids
   - boundaries are not supported in OGR, pseudotopo treats polygons
     as boundaries
     
  \todo How to deal with OGRNullFID ?
  
  \param Map pointer to Map_info structure
  \param type feature type
  \param points pointer to line_pnts structure (feature geometry) 
  \param cats pointer to line_cats structure (feature categories)
  
  \return feature offset into file
  \return -1 on error
*/
off_t V1_write_line_ogr(struct Map_info *Map, int type,
			const struct line_pnts *points,
			const struct line_cats *cats)
{
    int i, cat, ret;

    struct field_info *Fi;
    struct Format_info_ogr *fInfo;
    
    off_t offset;
    
    OGRGeometryH       Ogr_geometry;
    OGRFeatureH        Ogr_feature;
    OGRFeatureDefnH    Ogr_featuredefn;
    OGRwkbGeometryType Ogr_geom_type;

    if (!Map->fInfo.ogr.layer) {
	/* create OGR layer if doesn't exist */
	if (V2_open_new_ogr(Map, type) < 0)
	    return -1;
    }

    cat = -1; /* no attributes to be written */
    if (cats->n_cats > 0 && Vect_get_num_dblinks(Map) > 0) {
	/* check for attributes */
	Fi = Vect_get_dblink(Map, 0);
	if (Fi) {
	    if (!Vect_cat_get(cats, Fi->number, &cat))
		G_warning(_("No category defined for layer %d"), Fi->number);
	    if (cats->n_cats > 1) {
		G_warning(_("Feature has more categories, using "
			    "category %d (from layer %d)"),
			  cat, cats->field[0]);
	    }
	}
    }
    
    fInfo = &(Map->fInfo.ogr);
    Ogr_featuredefn = OGR_L_GetLayerDefn(fInfo->layer);
    Ogr_geom_type = OGR_FD_GetGeomType(Ogr_featuredefn);
    
    /* determine matching OGR feature geometry type */
    if (type & (GV_POINT | GV_KERNEL)) {
	if (Ogr_geom_type != wkbPoint &&
	    Ogr_geom_type != wkbPoint25D) {
	    G_warning(_("Feature is not a point. Skipping."));
	    return -1;
	}
	Ogr_geometry = OGR_G_CreateGeometry(wkbPoint);
    }
    else if (type & GV_LINE) {
	if (Ogr_geom_type != wkbLineString &&
	    Ogr_geom_type != wkbLineString25D) {
	    G_warning(_("Feature is not a line. Skipping."));
	    return -1;
	}
	Ogr_geometry = OGR_G_CreateGeometry(wkbLineString);
    }
    else if (type & GV_BOUNDARY) {
	if (Ogr_geom_type != wkbPolygon) {
	    G_warning(_("Feature is not a polygon. Skipping."));
	    return -1;
	}
	Ogr_geometry = OGR_G_CreateGeometry(wkbPolygon);
    }
    else if (type & GV_FACE) {
	if (Ogr_geom_type != wkbPolygon25D) {
	    G_warning(_("Feature is not a face. Skipping."));
	    return -1;
	}
	Ogr_geometry = OGR_G_CreateGeometry(wkbPolygon25D);
    }
    else {
	G_warning(_("Unsupported feature type (%d)"), type);
	return -1;
    }

    G_debug(3, "V1_write_line_ogr(): type = %d", type);

    if (Ogr_geom_type == wkbPolygon || Ogr_geom_type == wkbPolygon25D) {
	/* create exterior ring */
	OGRGeometryH Ogr_ring;
	int npoints;
	
	npoints = points->n_points - 1;
	Ogr_ring = OGR_G_CreateGeometry(wkbLinearRing);
	if (points->x[0] != points->x[npoints] ||
	    points->y[0] != points->y[npoints] ||
	    points->z[0] != points->z[npoints]) {
	    G_warning(_("Boundary is not closed. Skipping."));
	    return -1;
	}
	
	/* add points */
	for (i = 0; i < points->n_points; i++) {
	    OGR_G_AddPoint(Ogr_ring, points->x[i], points->y[i],
			   points->z[i]);
	}
	OGR_G_AddGeometry(Ogr_geometry, Ogr_ring);
    }
    else {
	for (i = 0; i < points->n_points; i++) {
	    OGR_G_AddPoint(Ogr_geometry, points->x[i], points->y[i],
			   points->z[i]);
	}
    }
    
    G_debug(4, "   n_points = %d", points->n_points);

    /* create feature & set geometry */
    Ogr_feature = OGR_F_Create(Ogr_featuredefn);
    OGR_F_SetGeometry(Ogr_feature, Ogr_geometry);

    /* write attributes */
    if (cat > -1 && fInfo->dbdriver) {
	write_attributes(fInfo->dbdriver,
			 cat, Fi, fInfo->layer, Ogr_feature);
	G_free(Fi);
    }
    /* write feature into layer */
    ret = OGR_L_CreateFeature(fInfo->layer, Ogr_feature);

    /* update offset array */
    if (fInfo->offset_num >= fInfo->offset_alloc) {
	fInfo->offset_alloc += 1000;
	fInfo->offset = (int *) G_realloc(fInfo->offset,
					  fInfo->offset_alloc *
					  sizeof(int));
    }

    offset = fInfo->offset_num;
    
    fInfo->offset[fInfo->offset_num++] = (int) OGR_F_GetFID(Ogr_feature);
    if (Ogr_geom_type == wkbPolygon || Ogr_geom_type == wkbPolygon25D) {
	/* register exterior ring in offset array */
	fInfo->offset[fInfo->offset_num++] = 0; 
    }
      
    /* destroy */
    OGR_G_DestroyGeometry(Ogr_geometry);
    OGR_F_Destroy(Ogr_feature);
    
    if (ret != OGRERR_NONE)
	return -1;
    
    G_debug(3, "V1_write_line_ogr(): -> offset = %lu", (unsigned long) offset);

    return offset;
}

/*!
  \brief Writes feature on level 2

  \param Map pointer to Map_info structure
  \param type feature type
  \param points pointer to line_pnts structure (feature geometry) 
  \param cats pointer to line_cats structure (feature categories)
  
  \return feature offset into file
  \return -1 on error
*/
off_t V2_write_line_ogr(struct Map_info *Map, int type,
			const struct line_pnts *points, const struct line_cats *cats)
{
    int line;
    off_t offset;
    struct Plus_head *plus;
    struct bound_box box;

    line = 0;
    plus = &(Map->plus);
    
    G_debug(3, "V2_write_line_ogr()");
    
    offset = V1_write_line_ogr(Map, type, points, cats);
    if (offset < 0)
	return -1;
    
    /* Update topology */
    if (plus->built >= GV_BUILD_BASE) {
	dig_line_box(points, &box);
	line = dig_add_line(plus, type, points, &box, offset);
	G_debug(3, "\tline added to topo with line = %d", line);
	if (line == 1)
	    Vect_box_copy(&(plus->box), &box);
	else
	    Vect_box_extend(&(plus->box), &box);

	if (type == GV_BOUNDARY) {
	    int ret, cline;
	    long FID;
	    double x, y;
	    
	    struct bound_box box;
	    struct line_pnts *CPoints;

	    /* add virtual centroid to pseudo-topology */
	    ret = Vect_get_point_in_poly(points, &x, &y);
	    if (ret == 0) {
		CPoints = Vect_new_line_struct();
		Vect_append_point(CPoints, x, y, 0.0);
		
		FID = Map->fInfo.ogr.offset[offset];

		dig_line_box(CPoints, &box);
		cline = dig_add_line(plus, GV_CENTROID,
				     CPoints, &box, FID);
		G_debug(4, "\tCentroid: x = %f, y = %f, cat = %lu, line = %d",
			x, y, FID, cline);	  
		dig_cidx_add_cat(plus, 1, (int) FID,
				 cline, GV_CENTROID);
		
		Vect_destroy_line_struct(CPoints);
	    }
	    else {
		G_warning(_("Unable to calculate centroid for area"));
	    }
	}
	V2__add_line_to_topo_ogr(Map, line, points, cats);
    }


    G_debug(3, "updated lines : %d , updated nodes : %d", plus->uplist.n_uplines,
	    plus->uplist.n_upnodes);

    /* returns int line, but is defined as off_t for compatibility with
     * Write_line_array in write.c */
    
    return line;

}

/*!
  \brief Rewrites feature at the given offset (level 1)
  
  \param Map pointer to Map_info structure
  \param offset feature offset
  \param type feature type
  \param points feature geometry
  \param cats feature categories
  
  \return feature offset (rewriten feature)
  \return -1 on error
*/
off_t V1_rewrite_line_ogr(struct Map_info *Map,
			  int line,
			  int type,
			  off_t offset,
			  const struct line_pnts *points, const struct line_cats *cats)
{
    if (type != V1_read_line_ogr(Map, NULL, NULL, offset)) {
	G_warning(_("Unable to rewrite feature (incompatible feature types)"));
	return -1;
    }

    /* delete old */
    V1_delete_line_ogr(Map, offset);

    return V1_write_line_ogr(Map, type, points, cats);
}

/*!
  \brief Rewrites feature to 'coor' file (topology level) - internal use only
  
  \param Map pointer to Map_info structure
  \param line feature id
  \param type feature type
  \param offset unused
  \param points feature geometry
  \param cats feature categories
  
  \return offset where line was rewritten
  \return -1 on error
*/
off_t V2_rewrite_line_ogr(struct Map_info *Map, int line, int type, off_t offset,
			  const struct line_pnts *points, const struct line_cats *cats)
{
    if (type != V2_read_line_ogr(Map, NULL, NULL, line)) {
	G_warning(_("Unable to rewrite feature (incompatible feature types)"));
	return -1;
    }

    V2_delete_line_ogr(Map, line);

    return V2_write_line_ogr(Map, type, points, cats);
}

/*!
  \brief Deletes feature at the given offset (level 1)
  
  \param Map pointer Map_info structure
  \param offset feature offset
  
  \return  0 on success
  \return -1 on error
*/
int V1_delete_line_ogr(struct Map_info *Map, off_t offset)
{
    G_debug(3, "V1_delete_line_ogr(), offset = %lu", (unsigned long) offset);

    if (!Map->fInfo.ogr.layer) {
	G_warning(_("OGR layer not defined"));
	return -1;
    }
    
    if (offset >= Map->fInfo.ogr.offset_num)
	return -1;
    
    if (OGR_L_DeleteFeature(Map->fInfo.ogr.layer, Map->fInfo.ogr.offset[offset]) != OGRERR_NONE)
	return -1;
    
    return 0;
}

/*!
  \brief Deletes feature (topology level) -- internal use only
  
  \param pointer to Map_info structure
  \param line feature id
  
  \return 0 on success
  \return -1 on error
*/
int V2_delete_line_ogr(struct Map_info *Map, int line)
{
    int ret, i, type, first;
    struct P_line *Line;
    struct Plus_head *plus;
    static struct line_cats *Cats = NULL;
    static struct line_pnts *Points = NULL;

    G_debug(3, "V2_delete_line_ogr(), line = %d", line);

    type = first = 0;
    Line = NULL;
    plus = &(Map->plus);

    if (plus->built >= GV_BUILD_BASE) {
	Line = Map->plus.Line[line];

	if (Line == NULL)
	    G_fatal_error(_("Attempt to delete dead feature"));
	type = Line->type;
    }

    if (!Cats) {
	Cats = Vect_new_cats_struct();
    }
    if (!Points) {
	Points = Vect_new_line_struct();
    }

    type = V2_read_line_ogr(Map, Points, Cats, line);

    /* Update category index */
    if (plus->update_cidx) {

	for (i = 0; i < Cats->n_cats; i++) {
	    dig_cidx_del_cat(plus, Cats->field[i], Cats->cat[i], line, type);
	}
    }
    /* Update fidx */

    /* delete the line from coor */
    ret = V1_delete_line_ogr(Map, Line->offset);

    if (ret == -1) {
	return ret;
    }

    /* Update topology */
    if (plus->built >= GV_BUILD_AREAS && type == GV_BOUNDARY) {
	/* TODO */
	/* remove centroid together with boundary (is really an OGR polygon) */
    }
    /* Delete reference from area */
    if (plus->built >= GV_BUILD_CENTROIDS && type == GV_CENTROID) {
	/* for OGR mapsets, virtual centroid will be removed when polygon is removed */
    }

    /* delete the line from topo */
    dig_del_line(plus, line, Points->x[0], Points->y[0], Points->z[0]);

    /* Rebuild areas/isles and attach centroids and isles */
    if (plus->built >= GV_BUILD_AREAS && type == GV_BOUNDARY) {
	/* maybe not needed VERIFY */
    }
    return ret;
}

int write_attributes(dbDriver *driver, int cat, const struct field_info *Fi,
		     OGRLayerH Ogr_layer, OGRFeatureH Ogr_feature)
{
    int j, ogrfieldnum;
    char buf[2000];
    int ncol, sqltype, ctype, ogrtype, more;
    const char *fidcol, *colname;
    dbTable *table;
    dbString dbstring;
    dbColumn *column;
    dbCursor cursor;
    dbValue *value;

    OGRFieldDefnH hFieldDefn;
    
    G_debug(3, "write_attributes(): cat = %d", cat);

    if (cat < 0) {
	G_warning(_("Feature without category of layer %d"), Fi->number);
	return 0;
    }

    db_init_string(&dbstring);
    
    /* read & set attributes */
    sprintf(buf, "SELECT * FROM %s WHERE %s = %d", Fi->table, Fi->key,
	    cat);
    G_debug(4, "SQL: %s", buf);
    db_set_string(&dbstring, buf);

    /* select data */
    if (db_open_select_cursor(driver, &dbstring, &cursor, DB_SEQUENTIAL) != DB_OK) {
	G_fatal_error(_("Unable to select attributes for category %d"),
		      cat);
    }
    
    if (db_fetch(&cursor, DB_NEXT, &more) != DB_OK) {
	G_fatal_error(_("Unable to fetch data from table <%s>"),
		      Fi->table);
    }
    
    if (!more) {
	G_warning(_("No database record for category %d, "
		    "no attributes will be written"),
		  cat);
	return -1;
    }

    fidcol = OGR_L_GetFIDColumn(Ogr_layer); 

    table = db_get_cursor_table(&cursor);
    ncol = db_get_table_number_of_columns(table);
    for (j = 0; j < ncol; j++) {
	column = db_get_table_column(table, j);
	colname = db_get_column_name(column);
	if (fidcol && *fidcol && strcmp(colname, fidcol) == 0) {
	    /* skip fid column */
	    continue;
	}
	value = db_get_column_value(column);
	/* for debug only */
	db_convert_column_value_to_string(column, &dbstring);	
	G_debug(2, "col %d : val = %s", j,
		db_get_string(&dbstring));
	
	sqltype = db_get_column_sqltype(column);
	ctype = db_sqltype_to_Ctype(sqltype);
	ogrtype = sqltype_to_ogrtype(sqltype);
	G_debug(2, "  colctype = %d", ctype);
	
	ogrfieldnum = OGR_F_GetFieldIndex(Ogr_feature, colname);
	if (ogrfieldnum < 0) {
	    /* create field if not exists */
	    hFieldDefn = OGR_Fld_Create(colname, ogrtype);
	    if (OGR_L_CreateField(Ogr_layer, hFieldDefn, TRUE) != OGRERR_NONE)
		G_warning(_("Unable to create field <%s>"), colname);
	    ogrfieldnum = OGR_F_GetFieldIndex(Ogr_feature, colname);
	}
	    
	/* Reset */
	OGR_F_UnsetField(Ogr_feature, ogrfieldnum);
	
	/* prevent writing NULL values */
	if (!db_test_value_isnull(value)) {
	    switch (ctype) {
	    case DB_C_TYPE_INT:
		OGR_F_SetFieldInteger(Ogr_feature, ogrfieldnum,
				      db_get_value_int(value));
		break;
	    case DB_C_TYPE_DOUBLE:
		OGR_F_SetFieldDouble(Ogr_feature, ogrfieldnum,
				     db_get_value_double(value));
		break;
	    case DB_C_TYPE_STRING:
		OGR_F_SetFieldString(Ogr_feature, ogrfieldnum,
				     db_get_value_string(value));
		break;
	    case DB_C_TYPE_DATETIME:
		db_convert_column_value_to_string(column,
						  &dbstring);
		OGR_F_SetFieldString(Ogr_feature, ogrfieldnum,
				     db_get_string(&dbstring));
		break;
	    }
	}
    }

    db_close_cursor (&cursor);
    
    db_free_string(&dbstring);
    
    return 1;
}

int sqltype_to_ogrtype(int sqltype)
{
    int ctype, ogrtype;

    ctype = db_sqltype_to_Ctype(sqltype);
    
    switch(ctype) {
    case DB_C_TYPE_INT:
	ogrtype = OFTInteger;
	break;
    case DB_C_TYPE_DOUBLE:
	ogrtype = OFTReal;
	break;
    case DB_C_TYPE_STRING:
	ogrtype = OFTString;
	break;
    case DB_C_TYPE_DATETIME:
	ogrtype = OFTString;
	break;
    default:
	ogrtype = OFTString;
	break;
    }
    
    return ogrtype;
}

#endif /* HAVE_OGR */
