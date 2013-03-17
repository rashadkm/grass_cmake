/*!
   \file lib/vector/Vlib/header_finfo.c

   \brief Vector library - header manipulation (relevant for external
   formats)

   Higher level functions for reading/writing/manipulating vectors.

   (C) 2001-2010, 2012 by the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2). Read the file COPYING that comes with GRASS for details.

   \author Original author CERL, probably Dave Gerdes or Mike Higgins.
   \author Update to GRASS 5.7 Radim Blazek and David D. Gray.
   \author Update to GRASS 7 (OGR/PostGIS support) by Martin Landa <landa.martin gmail.com>
*/

#include <grass/vector.h>
#include <grass/glocale.h>

/*!
   \brief Get datasource name (relevant only for non-native formats)

   Returns:
    - datasource name for OGR format (GV_FORMAT_OGR and GV_FORMAT_OGR_DIRECT)
    - database name for PostGIS format (GV_FORMAT_POSTGIS)
   
   \param Map pointer to Map_info structure

   \return string containing OGR/PostGIS datasource name
   \return NULL on error (map format is native)
 */
const char *Vect_get_finfo_dsn_name(const struct Map_info *Map)
{
    if (Map->format == GV_FORMAT_OGR ||
        Map->format == GV_FORMAT_OGR_DIRECT) {
#ifndef HAVE_OGR
        G_warning(_("GRASS is not compiled with OGR support"));
#endif
        return Map->fInfo.ogr.dsn;
    }
    else if (Map->format == GV_FORMAT_POSTGIS) {
#ifndef HAVE_POSTGRES
        G_warning(_("GRASS is not compiled with PostgreSQL support"));
#endif
        return Map->fInfo.pg.db_name;
    }
    
    G_warning(_("Native vector format detected for <%s>"),
              Vect_get_full_name(Map));
    
    return NULL;
}

/*!
   \brief Get layer name (relevant only for non-native formats)

   Returns:
    - layer name for OGR format (GV_FORMAT_OGR and GV_FORMAT_OGR_DIRECT)
    - table name for PostGIS format (GV_FORMAT_POSTGIS) including schema (\<schema\>.\<table\>)

   Note: allocated string should be freed by G_free()

   \param Map pointer to Map_info structure

   \return string containing layer name
   \return NULL on error (map format is native)
 */
char *Vect_get_finfo_layer_name(const struct Map_info *Map)
{
    char *name;
    
    name = NULL;
    if (Map->format == GV_FORMAT_OGR ||
        Map->format == GV_FORMAT_OGR_DIRECT) {
#ifndef HAVE_OGR
        G_warning(_("GRASS is not compiled with OGR support"));
#endif
        name = G_store(Map->fInfo.ogr.layer_name);
    }
    else if (Map->format == GV_FORMAT_POSTGIS) {
#ifndef HAVE_POSTGRES
        G_warning(_("GRASS is not compiled with PostgreSQL support"));
#endif
        G_asprintf(&name, "%s.%s", Map->fInfo.pg.schema_name,
                   Map->fInfo.pg.table_name);
    }
    else {
        G_warning(_("Native vector format detected for <%s>"),
                  Vect_get_full_name(Map));
    }
    
    return name;
}

/*!
  \brief Get format info (relevant only for non-native formats)

  \param Map pointer to Map_info structure
  
  \return string containing name of OGR format
  \return "PostgreSQL" for PostGIS format (GV_FORMAT_POSTGIS)
  \return NULL on error (or on missing OGR/PostgreSQL support)
*/
const char *Vect_get_finfo_format_info(const struct Map_info *Map)
{
    if (Map->format == GV_FORMAT_OGR ||
        Map->format == GV_FORMAT_OGR_DIRECT) {
#ifndef HAVE_OGR
        G_warning(_("GRASS is not compiled with OGR support"));
#else
        if (!Map->fInfo.ogr.ds)
            return NULL;

        return OGR_Dr_GetName(OGR_DS_GetDriver(Map->fInfo.ogr.ds));
#endif
    }
    else if (Map->format == GV_FORMAT_POSTGIS) {
#ifndef HAVE_OGR
        G_warning(_("GRASS is not compiled with PostgreSQL support"));
#else
        return "PostgreSQL";
#endif
    }
    
    return NULL;
}

/*!
  \brief Get geometry type (relevant only for non-native formats)

  Note: All inner spaces are removed, function returns feature type in
  lowercase.

  \param Map pointer to Map_info structure

  \return allocated string containing geometry type info
  (point, linestring, polygon, ...)
  \return NULL on error (map format is native)
*/
const char *Vect_get_finfo_geometry_type(const struct Map_info *Map)
{
    char *ftype, *ftype_tmp;
    
    ftype_tmp = ftype = NULL;
    if (Map->format == GV_FORMAT_OGR ||
        Map->format == GV_FORMAT_OGR_DIRECT) {
#ifndef HAVE_OGR
    G_warning(_("GRASS is not compiled with OGR support"));
#else
    OGRwkbGeometryType Ogr_geom_type;
    OGRFeatureDefnH    Ogr_feature_defn;
    
    if (!Map->fInfo.ogr.layer)
        return NULL;

    Ogr_feature_defn = OGR_L_GetLayerDefn(Map->fInfo.ogr.layer);
    Ogr_geom_type = wkbFlatten(OGR_FD_GetGeomType(Ogr_feature_defn));
    
    ftype_tmp = G_store(OGRGeometryTypeToName(Ogr_geom_type));
#endif
    }
    else if (Map->format == GV_FORMAT_POSTGIS) {
#ifndef HAVE_POSTGRES
        G_warning(_("GRASS is not compiled with PostgreSQL support"));
#else
        char stmt[DB_SQL_MAX];
        
        const struct Format_info_pg *pg_info;
        
        PGresult *res;
                
        pg_info = &(Map->fInfo.pg);
        sprintf(stmt, "SELECT type FROM geometry_columns "
                "WHERE f_table_schema = '%s' AND f_table_name = '%s'",
                pg_info->schema_name, pg_info->table_name);
        G_debug(2, "SQL: %s", stmt);
        
        res = PQexec(pg_info->conn, stmt);
        if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
            PQntuples(res) != 1) {
            G_debug(1, "Unable to get feature type: %s",
                    PQresultErrorMessage(res));
            return NULL;
        }
        ftype_tmp = G_store(PQgetvalue(res, 0, 0));
        PQclear(res);
#endif
    }
    
    if (!ftype_tmp)
        return NULL;

    ftype = G_str_replace(ftype_tmp, " ", "");
    G_free(ftype_tmp);
    G_str_to_lower(ftype);

    return ftype;
}

/*!
  \brief Get header info for non-native formats

  Prints a warning for native format.
  
  \param Map pointer to Ma_info structure
  
  \return pointer to Format_info structure
*/
const struct Format_info* Vect_get_finfo(const struct Map_info *Map)
{
    if (Map->format == GV_FORMAT_NATIVE)
        G_warning(_("Native vector format detected for <%s>"),
                  Vect_get_full_name(Map));
    
    return &(Map->fInfo);
}
