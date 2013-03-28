/*!
  \file lib/vector/Vlib/copy.c
  
  \brief Vector library - Copy vector features and attribute tables linked to the map
  
  Higher level functions for reading/writing/manipulating vectors.
  
  (C) 2001-2009, 2012-2013 by the GRASS Development Team
  
  This program is free software under the GNU General Public License
  (>=v2).  Read the file COPYING that comes with GRASS for details.
  
  \author Original author CERL, probably Dave Gerdes or Mike Higgins.
  \author Update to GRASS 5.7 Radim Blazek and David D. Gray.
  \author Update to GRASS 7 by Martin Landa <landa.martin gmail.com> (OGR/PostGIS topology support)
*/

#include <grass/vector.h>
#include <grass/glocale.h>

/*!
  \brief Copy topological elements

  - simple features (None)
  - native topo (GRASS)
  - PostGIS Topo
*/
#define TOPO_NONE   -1
#define TOPO_NATIVE  1
#define TOPO_POSTGIS 2

#ifdef HAVE_POSTGRES
#include "pg_local_proto.h"
#endif

static int copy_lines_1(struct Map_info *, int, struct Map_info *);
static int copy_lines_2(struct Map_info *, int, int, struct Map_info *);
static int copy_nodes(const struct Map_info *, struct Map_info *);
static int is_isle(const struct Map_info *, int);
static int copy_areas(const struct Map_info *, int, struct Map_info *);

/*!
   \brief Copy all alive vector features from input vector map to
   output vector map

   \param In input vector map
   \param[out] Out output vector map

   \return 0 on success
   \return 1 on error
 */
int Vect_copy_map_lines(struct Map_info *In, struct Map_info *Out)
{
    return Vect_copy_map_lines_field(In, -1, Out);
}

/*!
   \brief Copy all alive vector features from given layer from input
   vector map to output vector map

   Note: Try to copy on level 2 otherwise level 1 is used.
   
   \todo Implement V2__write_area_ogr()
   
   \param In input vector map
   \param field layer number (-1 for all layers)
   \param[out] Out output vector map

   \return 0 on success
   \return 1 on error
 */
int Vect_copy_map_lines_field(struct Map_info *In, int field,
                              struct Map_info *Out)
{
    int ret, format, topo;
    
    if (Vect_level(In) < 1)
        G_fatal_error("Vect_copy_map_lines(): %s",
                      _("input vector map is not open"));

    format = Vect_maptype(Out);
    topo = TOPO_NONE;
    if (format == GV_FORMAT_NATIVE)
        topo = TOPO_NATIVE;
    else if (format == GV_FORMAT_POSTGIS && Out->fInfo.pg.toposchema_name)
        topo = TOPO_POSTGIS;
    
    /* Note: sometimes is important to copy on level 2 (pseudotopo
       centroids) and sometimes on level 1 if build take too long time
    */
    if (Vect_level(In) >= 2) {
        /* -> copy features on level 2 */
        if (topo == TOPO_POSTGIS)
            /* PostGIS topology - copy also nodes */
            copy_nodes(In, Out);
        
        /* copy features */
        ret = copy_lines_2(In, field, topo, Out);
        
        if (topo == TOPO_NONE) {
            /* copy areas - external formats and simple features access only */
            copy_areas(In, field, Out);
        }
    }
    else {
        /* -> copy features on level 1 */
        if (topo == TOPO_NONE)
            G_warning(_("Vector map <%s> not open on topological level. "
                        "Areas will be skipped!"), Vect_get_full_name(In));
        
        ret = copy_lines_1(In, field, Out);
    }
    
    return ret;
}

/*!
  \brief Copy vector features on level 1

  \param In input vector map
  \param field layer number (-1 for all layers)
  \param Out output vector map
  
  \return 0 on success
  \return 1 on error
*/
int copy_lines_1(struct Map_info *In, int field, struct Map_info *Out)
{
    int ret, type;
    
    struct line_pnts *Points;
    struct line_cats *Cats;

    Points  = Vect_new_line_struct();
    Cats    = Vect_new_cats_struct();
    
    ret = 0;
    
    Vect_rewind(In);
    while (TRUE) {
        type = Vect_read_next_line(In, Points, Cats);
        if (type == -1) {
            G_warning(_("Unable to read vector map <%s>"),
                      Vect_get_full_name(In));
            ret = 1;
            break;
        }
        else if (type == -2) {      /* EOF */
            break;                  /* free allocated space and return */
        }
        else if (type == 0) {       /* dead line */
            continue;
        }
        
        /* don't skip boundaries if field != -1 */
        if (field != -1 && !(type & GV_BOUNDARY) &&
            Vect_cat_get(Cats, field, NULL) == 0)
            continue;       /* different layer */
        
        Vect_write_line(Out, type, Points, Cats);
    }

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    return ret;
}

/*!
  \brief Copy vector features on level 2

  \param In input vector map
  \param field layer number (-1 for all layers)
  \param topo topo access (none, native, postgis)
  \param Out output vector map
  
  \return 0 on success
  \return 1 on error
*/
int copy_lines_2(struct Map_info *In, int field, int topo, struct Map_info *Out)
{
    int i, type, nlines;
    int ret, left, rite, centroid;

    struct line_pnts *Points, *CPoints;
    struct line_cats *Cats, *CCats;

    Points  = Vect_new_line_struct();
    CPoints = Vect_new_line_struct();
    Cats    = Vect_new_cats_struct();
    CCats   = Vect_new_cats_struct();
    
    ret = 0;
    nlines = Vect_get_num_lines(In);
    if (topo == TOPO_NONE) {
        const char *ftype;

        ftype = Vect_get_finfo_geometry_type(Out);
        G_debug(2, "feature type: %s", ftype ? ftype : "?");
        if (!ftype)
            G_message(_("Copying features..."));
        else 
            G_message(_("Copying features (%s)..."), ftype);
    }
    else
        G_message(_("Copying features..."));    
    
    for (i = 1; i <= nlines; i++) {
        if (!Vect_line_alive(In, i))
            continue;
        
        G_percent(i, nlines, 2);
        type = Vect_read_line(In, Points, Cats, i);
        if (type == -1) {
            G_warning(_("Unable to read vector map <%s>"),
                      Vect_get_full_name(In));
            ret = 1;
            break;          /* free allocated space and return */
        }
        if (type == 0)
            continue;       /* dead line */
        
        if (topo == TOPO_NONE && (type == GV_CENTROID || type == GV_BOUNDARY)) {
            /* OGR/PostGIS layers (simple features): centroids are
               stored in topo polygon defined by areas (topo required)
            */
            continue;
        }

        /* don't skips boundaries if field != -1 */
        if (field != -1) {
            if (type & GV_BOUNDARY) {
                if (Vect_cat_get(Cats, field, NULL) == 0) {
                    int skip_bndry = TRUE;
                    
                    Vect_get_line_areas(In, i, &left, &rite);
                    if (left < 0)
                        left = Vect_get_isle_area(In, abs(left));
                    if (left > 0) {
                        if ((centroid =
                             Vect_get_area_centroid(In, left)) > 0) {
                            Vect_read_line(In, CPoints, CCats, centroid);
                            if (Vect_cat_get(CCats, field, NULL) != 0)
                                skip_bndry = FALSE;
                        }
                    }
                    if (skip_bndry) {
                        if (rite < 0)
                            rite = Vect_get_isle_area(In, abs(rite));
                        if (rite > 0) {
                            if ((centroid =
                                 Vect_get_area_centroid(In, rite)) > 0) {
                                Vect_read_line(In, CPoints, CCats,
                                               centroid);
                                if (Vect_cat_get(CCats, field, NULL) != 0)
                                    skip_bndry = FALSE;
                            }
                        }
                    }
                    if (skip_bndry)
                        continue;
                }
            }
            else if (Vect_cat_get(Cats, field, NULL) == 0)
                continue;   /* different layer */
        }
        
        if (-1 == Vect_write_line(Out, type, Points, Cats)) {
            G_warning(_("Writing new feature failed"));
            return 1;
        }
    }

    Vect_destroy_line_struct(Points);
    Vect_destroy_line_struct(CPoints);
    Vect_destroy_cats_struct(Cats);
    Vect_destroy_cats_struct(CCats);

    return ret;
}

/*!
  \brief Copy nodes as points (PostGIS Topology only)

  \param In input vector map
  \param Out output vector map
  
  \return 0 on success
  \return 1 on error
*/
int copy_nodes(const struct Map_info *In, struct Map_info *Out)
{
    int nnodes, node, with_z;
    double x, y, z;
    struct line_pnts *Points;
    
    Points = Vect_new_line_struct();
    
    with_z = Vect_is_3d(In);
    
    nnodes = Vect_get_num_nodes(In);
    if (nnodes > 0)
        G_message(_("Exporting nodes..."));
    Vect_append_point(Points, 0., 0., 0.);
    for (node = 1; node <= nnodes; node++) {
        G_debug(3, "Exporting GRASS node %d", node);
        
        G_percent(node, nnodes, 5);
        Vect_get_node_coor(In, node, &x, &y, &z);
        Points->x[0] = x;
        Points->y[0] = y;
        if (with_z)
            Points->z[0] = z;
        
#ifdef HAVE_POSTGRES
        if (-1 == V2__write_node_pg(Out, Points)) {
            G_warning(_("Writing node %d failed"), node);
            return 1;
        }
#endif
    }

    Vect_destroy_line_struct(Points);
    
    return 0;
}

/*!
  \brief Check if area forms an isle

  Check for areas that are part of isles which in turn are inside
  another area.

  \param Map pointer to Map_info struct
  \param area area id

  \return TRUE if area forms an isle otherwise FALSE
*/
int is_isle(const struct Map_info *Map, int area)
{
    int i, line, left, right, isle, is_isle;
    
    struct ilist *List;
    
    List = Vect_new_list();
    Vect_get_area_boundaries(Map, area, List);

    is_isle = FALSE;
    /* do we need to check all boundaries ? */
    for (i = 0; i < List->n_values && !is_isle; i++) {
        line = abs(List->value[i]);
        if (1 != Vect_get_line_areas(Map, line, &left, &right))
            continue;
        
        isle = abs(left == area ? right : left);
        
        if (Vect_get_isle_area(Map, isle) > 0)
            is_isle = TRUE;
    }

    G_debug(3, "is_isle(): area %d skip? -> %s", area, is_isle ? "yes" : "no");
    Vect_destroy_list(List);
    
    return is_isle;
}

/*!
  \brief Copy areas as polygons (OGR/PostGIS simple features access only)

  \param In input vector map
  \param field layer number (> 0)
  \param Out output vector map
  
  \return 0 on success
  \return 1 on error
*/
int copy_areas(const struct Map_info *In, int field, struct Map_info *Out)
{
    int i, area, nareas, cat, isle, nisles, nisles_alloc;
    int ogr;
    struct line_pnts *Points, **IPoints;
    struct line_cats *Cats;
    
    ogr = Vect_maptype(Out) == (GV_FORMAT_OGR || GV_FORMAT_OGR_DIRECT);
    
    IPoints = NULL;
    nisles_alloc = 0;
    Points  = Vect_new_line_struct();
    Cats    = Vect_new_cats_struct();

    /* copy areas/polygons */
    nareas = Vect_get_num_areas(In);
    G_message(_("Exporting areas..."));
    for (area = 1; area <= nareas; area++) {
        G_debug(3, "area = %d", area);
        G_percent(area, nareas, 3);

        /* get area category */
        cat = Vect_get_area_cat(In, area, field);
        if (cat < 0) {
            /* no category - check if area forms an isle */
            if (!is_isle(In, area))
                G_warning(_("No category defined for area %d. "
                            "Area not exported."),
                          area);
            continue;
        }
        
        /* get outer ring (area) geometry */
        Vect_get_area_points(In, area, Points);

        Vect_reset_cats(Cats);
        Vect_cat_set(Cats, field, cat);
        
        /* get inner rings (isles) geometry */
        nisles = Vect_get_area_num_isles(In, area);
        if (nisles > nisles_alloc) {
            /* reallocate space for isles */
            IPoints = (struct line_pnts **) G_realloc(IPoints,
                                                      nisles *
                                                      sizeof(struct line_pnts *));
            for (i = nisles_alloc; i < nisles; i++)
                IPoints[i] = Vect_new_line_struct();
            nisles_alloc = nisles;
        }
        G_debug(3, "\tcat=%d, nisles=%d", cat, nisles);
        for (i = 0; i < nisles; i++) {
            isle = Vect_get_area_isle(In, area, i);
            Vect_get_isle_points(In, isle, IPoints[i]);
        }
        
        if (ogr)
            Vect_write_line(Out, GV_BOUNDARY, Points, Cats);
        else {
#if HAVE_POSTGRES
            if (-1 == V2__write_area_pg(Out, Points, Cats,
                                        (const struct line_pnts **) IPoints, nisles)) {
                G_warning(_("Writing area %d failed"), area);
                return 1;
            }
#else
            G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
#endif
        }
    }
    
    /* free allocated space for isles */
    for (i = 0; i < nisles_alloc; i++)
        Vect_destroy_line_struct(IPoints[i]);

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    return 0;
}

/*!
   \brief Copy attribute tables linked to vector map.

   Copy all attribute tables linked to the vector map if
   <em>field</em> is 0, or selected attribute table defined by given
   field if <em>field</em> > 0.

   Notice, that if input vector map has no tables defined, it will
   copy nothing and return 0 (success).

   \param In input vector map
   \param[out] Out output vector map
   \param field layer number (0 for all tables linked to the vector map)

   \return 0 on success
   \return -1 on error
 */
int Vect_copy_tables(const struct Map_info *In, struct Map_info *Out,
                     int field)
{
    int i, n, ret, type;
    struct field_info *Fi, *Fin;
    dbDriver *driver;

    n = Vect_get_num_dblinks(In);

    G_debug(2, "Vect_copy_tables(): copying %d tables", n);

    type = GV_1TABLE;
    if (n > 1)
        type = GV_MTABLE;

    for (i = 0; i < n; i++) {
        Fi = Vect_get_dblink(In, i);
        if (Fi == NULL) {
            G_warning(_("Database connection not defined for layer %d"),
                      In->dblnk->field[i].number);
            return -1;
        }
        if (field > 0 && Fi->number != field)
            continue;

        Fin = Vect_default_field_info(Out, Fi->number, Fi->name, type);
        G_debug(2, "Copy drv:db:table '%s:%s:%s' to '%s:%s:%s'",
                Fi->driver, Fi->database, Fi->table, Fin->driver,
                Fin->database, Fin->table);

        ret =
            Vect_map_add_dblink(Out, Fi->number, Fi->name, Fin->table,
                                Fi->key, Fin->database, Fin->driver);
        if (ret == -1) {
            G_warning(_("Unable to add database link for vector map <%s>"),
                      Out->name);
            return -1;
        }

        ret = db_copy_table(Fi->driver, Fi->database, Fi->table,
                            Fin->driver, Vect_subst_var(Fin->database, Out),
                            Fin->table);
        if (ret == DB_FAILED) {
            G_warning(_("Unable to copy table <%s>"), Fin->table);
            return -1;
        }

        driver =
            db_start_driver_open_database(Fin->driver,
                                          Vect_subst_var(Fin->database, Out));
        if (driver == NULL) {
            G_warning(_("Unable to open database <%s> by driver <%s>"),
                      Fin->database, Fin->driver);
        }
        else {
            if (db_create_index2(driver, Fin->table, Fi->key) != DB_OK)
                G_warning(_("Unable to create index for table <%s>, key <%s>"),
                          Fin->table, Fin->key);

            db_close_database_shutdown_driver(driver);
        }
    }

    return 0;
}

/*!
   \brief Copy attribute table linked to vector map based on type.

   \param In input vector map
   \param[out] Out output vector map
   \param field_in input layer number
   \param field_out output layer number
   \param field_name layer name
   \param type feature type

   \return 0 on success
   \return -1 on error
 */
int Vect_copy_table(const struct Map_info *In, struct Map_info *Out, int field_in,
                    int field_out, const char *field_name, int type)
{
    return Vect_copy_table_by_cats(In, Out, field_in, field_out, field_name,
                                   type, NULL, 0);
}

/*!
   \brief Copy attribute table linked to vector map based on category
   numbers.

   \param In input vector map
   \param[out] Out output vector map
   \param field_in input layer number
   \param field_out output layer number
   \param field_name layer name
   \param type feature type
   \param cats pointer to array of cats or NULL
   \param ncats number of cats in 'cats'

   \return 0 on success
   \return -1 on error
 */
int Vect_copy_table_by_cats(const struct Map_info *In, struct Map_info *Out,
                            int field_in, int field_out, const char *field_name,
                            int type, int *cats, int ncats)
{
    int ret;
    struct field_info *Fi, *Fin;
    const char *name, *key;

    G_debug(2, "Vect_copy_table(): field_in = %d field_out = %d", field_in,
            field_out);

    Fi = Vect_get_field(In, field_in);
    if (Fi == NULL) {
        G_warning(_("Database connection not defined for layer %d"),
                  field_in);
        return -1;
    }

    if (field_name != NULL)
        name = field_name;
    else
        name = Fi->name;

    Fin = Vect_default_field_info(Out, field_out, name, type);
    G_debug(3, "Copy drv:db:table '%s:%s:%s' to '%s:%s:%s'",
            Fi->driver, Fi->database, Fi->table, Fin->driver, Fin->database,
            Fin->table);

    ret =
        Vect_map_add_dblink(Out, Fin->number, Fin->name, Fin->table, Fi->key,
                            Fin->database, Fin->driver);
    if (ret == -1) {
        G_warning(_("Unable to add database link for vector map <%s>"),
                  Out->name);
        return -1;
    }

    if (cats)
        key = Fi->key;
    else
        key = NULL;

    ret = db_copy_table_by_ints(Fi->driver, Fi->database, Fi->table,
                                Fin->driver, Vect_subst_var(Fin->database,
                                                            Out), Fin->table,
                                key, cats, ncats);
    if (ret == DB_FAILED) {
        G_warning(_("Unable to copy table <%s>"), Fin->table);
        return -1;
    }

    return 0;
}
