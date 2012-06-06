/*!
   \file lib/vector/Vlib/open_pg.c

   \brief Vector library - Open PostGIS layer as vector map layer

   Higher level functions for reading/writing/manipulating vectors.

   (C) 2011-2012 by the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2). Read the file COPYING that comes with GRASS for details.

   \author Martin Landa <landa.martin gmail.com>
*/

#include <string.h>
#include <stdlib.h>

#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#ifdef HAVE_POSTGRES
#include "pg_local_proto.h"

struct edge_data {
    int id;
    int start_node;
    int end_node;
    int left_face;
    int right_face;
};

static char *get_key_column(struct Format_info_pg *);
static SF_FeatureType ftype_from_string(const char *);
static int drop_table(struct Format_info_pg *);
static int check_schema(const struct Format_info_pg *);
static int create_table(struct Format_info_pg *, const struct field_info *);
static void connect_db(struct Format_info_pg *);
static int check_topo(struct Format_info_pg *, struct Plus_head *);
static int parse_bbox(const char *, struct bound_box *);
static int num_of_records(const struct Format_info_pg *, const char *);
static int read_p_node(struct Plus_head *, int, int, struct Format_info_pg *);
static int read_p_line(struct Plus_head *, int, const struct edge_data *);
static int read_p_area(struct Plus_head *, int, int, struct Format_info_pg *);
static int load_plus_head(struct Format_info_pg *, struct Plus_head *);
#endif

/*!
   \brief Open vector map - PostGIS feature table (level 1 - without topology)

   \todo Check database instead of geometry_columns

   \param[in,out] Map pointer to Map_info structure
   \param update TRUE for write mode, otherwise read-only

   \return 0 success
   \return -1 error
 */
int V1_open_old_pg(struct Map_info *Map, int update)
{
#ifdef HAVE_POSTGRES
    int found;

    char stmt[DB_SQL_MAX];

    PGresult *res;

    struct Format_info_pg *pg_info;

    G_debug(2, "V1_open_old_pg(): update = %d", update);
    
    pg_info = &(Map->fInfo.pg);
    if (!pg_info->conninfo) {
        G_warning(_("Connection string not defined"));
        return -1;
    }

    if (!pg_info->table_name) {
        G_warning(_("PostGIS feature table not defined"));
        return -1;
    }

    G_debug(1, "V1_open_old_pg(): conninfo='%s' table='%s'",
            pg_info->conninfo, pg_info->table_name);

    /* connect database */
    if (!pg_info->conn)
        connect_db(pg_info);
    
    /* get DB name */
    pg_info->db_name = G_store(PQdb(pg_info->conn));
    if (!pg_info->db_name) {
        G_warning(_("Unable to get database name"));
        return -1;
    }

    /* get fid and geometry column */
    sprintf(stmt, "SELECT f_geometry_column, coord_dimension, srid, type "
            "FROM geometry_columns WHERE f_table_schema = '%s' AND "
            "f_table_name = '%s'", pg_info->schema_name, pg_info->table_name);
    G_debug(2, "SQL: %s", stmt);

    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK)
        G_fatal_error("%s\n%s", _("No feature tables found in database."),
                      PQresultErrorMessage(res));

    found = PQntuples(res) > 0 ? TRUE : FALSE;
    if (found) {
        /* geometry column */
        pg_info->geom_column = G_store(PQgetvalue(res, 0, 0));
        G_debug(3, "\t-> table = %s column = %s", pg_info->table_name,
                pg_info->geom_column);
        /* fid column */
        pg_info->fid_column = get_key_column(pg_info);
        /* coordinates dimension */
        pg_info->coor_dim = atoi(PQgetvalue(res, 0, 1));
        /* SRS ID */
        pg_info->srid = atoi(PQgetvalue(res, 0, 2));
        /* feature type */
        pg_info->feature_type = ftype_from_string(PQgetvalue(res, 0, 3));
    }
    PQclear(res);

    /* no feature in cache */
    pg_info->cache.fid = -1;

    if (!found) {
        G_warning(_("Feature table <%s> not found in 'geometry_columns'"),
                  pg_info->table_name);
        return -1;
    }

    /* check for topo schema */
    check_topo(pg_info, &(Map->plus));
    
    return 0;
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}

/*!
   \brief Open vector map - PostGIS feature table (level 2 - feature index)

   \param[in,out] Map pointer to Map_info structure

   \return 0 success
   \return -1 error
 */
int V2_open_old_pg(struct Map_info *Map)
{
#ifdef HAVE_POSTGRES
    struct Format_info_pg *pg_info;
    
    G_debug(3, "V2_open_old_pg(): name = %s mapset = %s", Map->name,
            Map->mapset);

    pg_info = &(Map->fInfo.pg);
    
    if (pg_info->toposchema_name)
        /* no fidx file needed for PostGIS topology access */
        return 0;
    
    if (Vect_open_fidx(Map, &(pg_info->offset)) != 0) {
        G_warning(_("Unable to open feature index file for vector map <%s>"),
                  Vect_get_full_name(Map));
        G_zero(&(pg_info->offset), sizeof(struct Format_info_offset));
    }

    return 0;
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}

/*!
   \brief Prepare PostGIS database for creating new feature table
   (level 1)

   \todo To implement

   \param[out] Map pointer to Map_info structure
   \param name name of PostGIS feature table to create
   \param with_z WITH_Z for 3D vector data otherwise WITHOUT_Z

   \return 0 success
   \return -1 error 
 */
int V1_open_new_pg(struct Map_info *Map, const char *name, int with_z)
{
#ifdef HAVE_POSTGRES
    char stmt[DB_SQL_MAX];

    struct Format_info_pg *pg_info;

    PGresult *res;

    G_debug(2, "V1_open_new_pg(): name = %s with_z = %d", name, with_z);

    pg_info = &(Map->fInfo.pg);
    if (!pg_info->conninfo) {
        G_warning(_("Connection string not defined"));
        return -1;
    }

    if (!pg_info->table_name) {
        G_warning(_("PostGIS feature table not defined"));
        return -1;
    }

    G_debug(1, "V1_open_new_pg(): conninfo='%s' table='%s'",
            pg_info->conninfo, pg_info->table_name);

    /* connect database */
    pg_info->conn = PQconnectdb(pg_info->conninfo);
    G_debug(2, "   PQconnectdb(): %s", pg_info->conninfo);
    if (PQstatus(pg_info->conn) == CONNECTION_BAD)
        G_fatal_error("%s\n%s",
                      _("Connection ton PostgreSQL database failed."),
                      PQerrorMessage(pg_info->conn));

    /* get DB name */
    pg_info->db_name = G_store(PQdb(pg_info->conn));
    if (!pg_info->db_name) {
        G_warning(_("Unable to get database name"));
        return -1;
    }

    /* if schema not defined, use 'public' */
    if (!pg_info->schema_name) {
        pg_info->schema_name = G_store("public");
    }

    /* if fid_column not defined, use 'ogc_fid' */
    if (!pg_info->fid_column) {
        pg_info->fid_column = G_store("ogc_fid");
    }

    /* if geom_column not defined, use 'wkb_geometry' */
    if (!pg_info->geom_column) {
        pg_info->geom_column = G_store("wkb_geometry");
    }

    /* check if feature table already exists */
    sprintf(stmt, "SELECT * FROM pg_tables "
            "WHERE schemaname = '%s' AND tablename = '%s'",
            pg_info->schema_name, pg_info->table_name);
    G_debug(2, "SQL: %s", stmt);

    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK)
        G_fatal_error("%s\n%s", _("No feature tables found in database."),
                      PQresultErrorMessage(res));

    if (PQntuples(res) > 0) {
        /* table found */
        if (G_get_overwrite()) {
            G_warning(_("PostGIS layer <%s.%s> already exists and will be overwritten"),
                      pg_info->schema_name, pg_info->table_name);
            if (drop_table(pg_info) == -1) {
                G_warning(_("Unable to delete PostGIS layer <%s>"),
                          pg_info->table_name);
                return -1;
            }
        }
        else {
            G_fatal_error(_("PostGIS layer <%s.%s> already exists in database '%s'"),
                          pg_info->schema_name, pg_info->table_name,
                          pg_info->db_name);
            return -1;
        }
    }

    /* no feature in cache */
    pg_info->cache.fid = -1;

    /* unknown feature type */
    pg_info->feature_type = SF_UNKNOWN;

    PQclear(res);

    return 0;
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}

/*!
   \brief Create new PostGIS layer in given database (level 2)

   V1_open_new_pg() is required to be called before this function.

   List of currently supported types:
   - GV_POINT     (SF_POINT)
   - GV_LINE      (SF_LINESTRING)
   - GV_BOUNDARY  (SF_POLYGON)
   \param[in,out] Map pointer to Map_info structure
   \param type feature type (GV_POINT, GV_LINE, ...)

   \return 0 success
   \return -1 error 
 */
int V2_open_new_pg(struct Map_info *Map, int type)
{
#ifdef HAVE_POSTGRES
    int ndblinks;

    struct Format_info_pg *pg_info;
    struct field_info *Fi;
    struct Key_Value *projinfo, *projunits;

    Fi = NULL;

    pg_info = &(Map->fInfo.pg);
    if (!pg_info->conninfo) {
        G_warning(_("Connection string not defined"));
        return -1;
    }

    if (!pg_info->table_name) {
        G_warning(_("PostGIS feature table not defined"));
        return -1;
    }

    G_debug(1, "V2_open_new_pg(): conninfo='%s' table='%s' -> type = %d",
            pg_info->conninfo, pg_info->table_name, type);

    /* get spatial reference */
    projinfo = G_get_projinfo();
    projunits = G_get_projunits();
    pg_info->srid = 0;          /* TODO */
    // Ogr_spatial_ref = GPJ_grass_to_osr(projinfo, projunits);
    G_free_key_value(projinfo);
    G_free_key_value(projunits);

    /* determine geometry type */
    switch (type) {
    case GV_POINT:
        pg_info->feature_type = SF_POINT;
        break;
    case GV_LINE:
        pg_info->feature_type = SF_LINESTRING;
        break;
    case GV_BOUNDARY:
        pg_info->feature_type = SF_POLYGON;
        break;
    default:
        G_warning(_("Unsupported geometry type (%d)"), type);
        return -1;
    }

    /* coordinate dimension */
    pg_info->coor_dim = Vect_is_3d(Map) ? 3 : 2;

    /* create new PostGIS table */
    ndblinks = Vect_get_num_dblinks(Map);
    if (ndblinks > 0) {
        Fi = Vect_get_dblink(Map, 0);
        if (Fi) {
            if (ndblinks > 1)
                G_warning(_("More layers defined, using driver <%s> and "
                            "database <%s>"), Fi->driver, Fi->database);
        }
        else {
            G_warning(_("Database connection not defined. "
                        "Unable to write attributes."));
        }
    }

    if (create_table(pg_info, Fi) == -1) {
        G_warning(_("Unable to create new PostGIS table"));
        return -1;
    }

    if (Fi)
        G_free(Fi);

    return 0;
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}

/*!
  \brief Read full-topology for PostGIS links
  
  Note: Only 2D topological primitives are currently supported
  
  \param[in,out] Map pointer to Map_info structure
  \param head_only TRUE to read only header
  
  \return 0 on success
  \return 1 topology layer does not exist
  \return -1 on error
*/
int Vect_open_topo_pg(struct Map_info *Map, int head_only)
{
#ifdef HAVE_POSTGRES
    struct Plus_head *plus;
    struct Format_info_pg *pg_info;
    
    plus = &(Map->plus);
    pg_info = &(Map->fInfo.pg);
    
    /* check for topo schema */
    if (check_topo(pg_info, plus) != 0)
        return 1;
    
    /* free and init plus structure */
    dig_init_plus(plus);
    
    return load_plus(pg_info, plus, head_only);
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}

#ifdef HAVE_POSTGRES
/*!
  \brief Get key column for feature table

  \param pg_info pointer to Format_info_pg
   
  \return string buffer with key column name
  \return NULL on missing key column
*/
char *get_key_column(struct Format_info_pg *pg_info)
{
    char *key_column;
    char stmt[DB_SQL_MAX];

    PGresult *res;

    sprintf(stmt,
            "SELECT kcu.column_name "
            "FROM INFORMATION_SCHEMA.TABLES t "
            "LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc "
            "ON tc.table_catalog = t.table_catalog "
            "AND tc.table_schema = t.table_schema "
            "AND tc.table_name = t.table_name "
            "AND tc.constraint_type = 'PRIMARY KEY' "
            "LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu "
            "ON kcu.table_catalog = tc.table_catalog "
            "AND kcu.table_schema = tc.table_schema "
            "AND kcu.table_name = tc.table_name "
            "AND kcu.constraint_name = tc.constraint_name "
            "WHERE t.table_schema = '%s' AND t.table_name = '%s'",
            pg_info->schema_name, pg_info->table_name);
    G_debug(2, "SQL: %s", stmt);

    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != 1 || strlen(PQgetvalue(res, 0, 0)) < 1) {
        G_warning(_("No key column detected."));
        if (res)
            PQclear(res);
        return NULL;
    }
    key_column = G_store(PQgetvalue(res, 0, 0));

    PQclear(res);

    return key_column;
}

/*!
  \brief Get simple feature type from string

  \param type string

  \return SF type
*/
SF_FeatureType ftype_from_string(const char *type)
{
    SF_FeatureType sf_type;
    
    if (G_strcasecmp(type, "POINT") == 0)
        return SF_POINT;
    else if (G_strcasecmp(type, "LINESTRING") == 0)
        return SF_LINESTRING;
    else if (G_strcasecmp(type, "POLYGON") == 0)
        return SF_POLYGON;
    else if (G_strcasecmp(type, "MULTIPOINT") == 0)
        return SF_MULTIPOINT;
    else if (G_strcasecmp(type, "MULTILINESTRING") == 0)
        return SF_MULTILINESTRING;
    else if (G_strcasecmp(type, "MULTIPOLYGON") == 0)
        return SF_MULTIPOLYGON;
    else if (G_strcasecmp(type, "GEOMETRYCOLLECTION") == 0)
        return SF_GEOMETRYCOLLECTION;
    else
        return SF_UNKNOWN;
    
    G_debug(3, "ftype_from_string(): type='%s' -> %d", type, sf_type);
    
    return sf_type;
}

/*!
  \brief Drop feature table

  \param pg_info pointer to Format_info_pg

  \return -1 on error
  \return 0 on success
*/
int drop_table(struct Format_info_pg *pg_info)
{
    char stmt[DB_SQL_MAX];

    sprintf(stmt, "DROP TABLE \"%s\".\"%s\"",
            pg_info->schema_name, pg_info->table_name);
    G_debug(2, "SQL: %s", stmt);

    if (execute(pg_info->conn, stmt) == -1) {
        return -1;
    }
    return 0;
}

/*!
  \brief Creates new schema for feature table if not exists

  \param pg_info pointer to Format_info_pg

  \return -1 on error
  \return 0 on success
*/
int check_schema(const struct Format_info_pg *pg_info)
{
    int i, found, nschema;
    char stmt[DB_SQL_MAX];

    PGresult *result;

    /* add geometry column */
    sprintf(stmt, "SELECT nspname FROM pg_namespace");
    G_debug(2, "SQL: %s", stmt);
    result = PQexec(pg_info->conn, stmt);

    if (!result || PQresultStatus(result) != PGRES_TUPLES_OK) {
        PQclear(result);
        execute(pg_info->conn, "ROLLBACK");
        return -1;
    }

    found = FALSE;
    nschema = PQntuples(result);
    for (i = 0; i < nschema && !found; i++) {
        if (strcmp(pg_info->schema_name, PQgetvalue(result, i, 0)) == 0)
            found = TRUE;
    }

    PQclear(result);

    if (!found) {
        sprintf(stmt, "CREATE SCHEMA %s", pg_info->schema_name);
        if (execute(pg_info->conn, stmt) == -1) {
            execute(pg_info->conn, "ROLLBACK");
            return -1;
        }
        G_warning(_("Schema <%s> doesn't exist, created"),
                  pg_info->schema_name);
    }

    return 0;
}

/*!
  \brief Create new feature table

  \param pg_info pointer to Format_info_pg
  \param Fi pointer to field_info

  \return -1 on error
  \return 0 on success
*/
int create_table(struct Format_info_pg *pg_info, const struct field_info *Fi)
{
    int spatial_index, primary_key;
    char stmt[DB_SQL_MAX], *geom_type;

    PGresult *result;

    /* by default create spatial index & add primary key */
    spatial_index = primary_key = TRUE;
    if (G_find_file2("", "PG", G_mapset())) {
        FILE *fp;
        const char *p;

        struct Key_Value *key_val;

        fp = G_fopen_old("", "PG", G_mapset());
        if (!fp) {
            G_fatal_error(_("Unable to open PG file"));
        }
        key_val = G_fread_key_value(fp);
        fclose(fp);

        /* disable spatial index ? */
        p = G_find_key_value("spatial_index", key_val);
        if (p && G_strcasecmp(p, "off") == 0)
            spatial_index = FALSE;
        /* disable primary key ? */
        p = G_find_key_value("primary_key", key_val);
        if (p && G_strcasecmp(p, "off") == 0)
            primary_key = FALSE;
    }

    /* create schema if not exists */
    if (G_strcasecmp(pg_info->schema_name, "public") != 0) {
        if (check_schema(pg_info) != 0)
            return -1;
    }

    /* prepare CREATE TABLE statement */
    sprintf(stmt, "CREATE TABLE \"%s\".\"%s\" (%s SERIAL",
            pg_info->schema_name, pg_info->table_name, pg_info->fid_column);

    if (Fi) {
        /* append attributes */
        int col, ncols, sqltype, length, ctype;
        char stmt_col[DB_SQL_MAX];
        const char *colname;

        dbString dbstmt;
        dbHandle handle;
        dbDriver *driver;
        dbCursor cursor;
        dbTable *table;
        dbColumn *column;

        db_init_string(&dbstmt);
        db_init_handle(&handle);

        pg_info->dbdriver = driver = db_start_driver(Fi->driver);
        if (!driver) {
            G_warning(_("Unable to start driver <%s>"), Fi->driver);
            return -1;
        }
        db_set_handle(&handle, Fi->database, NULL);
        if (db_open_database(driver, &handle) != DB_OK) {
            G_warning(_("Unable to open database <%s> by driver <%s>"),
                      Fi->database, Fi->driver);
            db_close_database_shutdown_driver(driver);
            pg_info->dbdriver = NULL;
            return -1;
        }

        /* describe table */
        db_set_string(&dbstmt, "select * from ");
        db_append_string(&dbstmt, Fi->table);
        db_append_string(&dbstmt, " where 0 = 1");

        if (db_open_select_cursor(driver, &dbstmt,
                                  &cursor, DB_SEQUENTIAL) != DB_OK) {
            G_warning(_("Unable to open select cursor: '%s'"),
                      db_get_string(&dbstmt));
            db_close_database_shutdown_driver(driver);
            pg_info->dbdriver = NULL;
            return -1;
        }

        table = db_get_cursor_table(&cursor);
        ncols = db_get_table_number_of_columns(table);

        G_debug(3,
                "copying attributes: driver = %s database = %s table = %s cols = %d",
                Fi->driver, Fi->database, Fi->table, ncols);

        for (col = 0; col < ncols; col++) {
            column = db_get_table_column(table, col);
            colname = db_get_column_name(column);
            sqltype = db_get_column_sqltype(column);
            ctype = db_sqltype_to_Ctype(sqltype);
            length = db_get_column_length(column);

            G_debug(3, "\tcolumn = %d name = %s type = %d length = %d",
                    col, colname, sqltype, length);

            if (strcmp(pg_info->fid_column, colname) == 0) {
                /* skip fid column if exists */
                G_debug(3, "\t%s skipped", pg_info->fid_column);
                continue;
            }

            /* append column */
            sprintf(stmt_col, ",%s %s", colname, db_sqltype_name(sqltype));
            strcat(stmt, stmt_col);
            if (ctype == DB_C_TYPE_STRING) {
                /* length only for string columns */
                sprintf(stmt_col, "(%d)", length);
                strcat(stmt, stmt_col);
            }
        }

        db_free_string(&dbstmt);
    }
    strcat(stmt, ")");          /* close CREATE TABLE statement */

    /* begin transaction (create table) */
    if (execute(pg_info->conn, "BEGIN") == -1) {
        return -1;
    }

    /* create table */
    G_debug(2, "SQL: %s", stmt);
    if (execute(pg_info->conn, stmt) == -1) {
        execute(pg_info->conn, "ROLLBACK");
        return -1;
    }

    /* add primary key ? */
    if (primary_key) {
        sprintf(stmt, "ALTER TABLE \"%s\".\"%s\" ADD PRIMARY KEY (%s)",
                pg_info->schema_name, pg_info->table_name,
                pg_info->fid_column);
        G_debug(2, "SQL: %s", stmt);
        if (execute(pg_info->conn, stmt) == -1) {
            execute(pg_info->conn, "ROLLBACK");
            return -1;
        }
    }

    /* determine geometry type (string) */
    switch (pg_info->feature_type) {
    case (SF_POINT):
        geom_type = "POINT";
        break;
    case (SF_LINESTRING):
        geom_type = "LINESTRING";
        break;
    case (SF_POLYGON):
        geom_type = "POLYGON";
        break;
    default:
        G_warning(_("Unsupported feature type %d"), pg_info->feature_type);
        execute(pg_info->conn, "ROLLBACK");
        return -1;
    }

    /* add geometry column */
    sprintf(stmt, "SELECT AddGeometryColumn('%s', '%s', "
            "'%s', %d, '%s', %d)",
            pg_info->schema_name, pg_info->table_name,
            pg_info->geom_column, pg_info->srid,
            geom_type, pg_info->coor_dim);
    G_debug(2, "SQL: %s", stmt);
    result = PQexec(pg_info->conn, stmt);

    if (!result || PQresultStatus(result) != PGRES_TUPLES_OK) {
        PQclear(result);
        execute(pg_info->conn, "ROLLBACK");
        return -1;
    }

    /* create index ? */
    if (spatial_index) {
        sprintf(stmt,
                "CREATE INDEX %s_%s_idx ON \"%s\".\"%s\" USING GIST (%s)",
                pg_info->table_name, pg_info->geom_column,
                pg_info->schema_name, pg_info->table_name,
                pg_info->geom_column);
        G_debug(2, "SQL: %s", stmt);

        if (execute(pg_info->conn, stmt) == -1) {
            execute(pg_info->conn, "ROLLBACK");
            return -1;
        }
    }

    /* close transaction (create table) */
    if (execute(pg_info->conn, "COMMIT") == -1) {
        return -1;
    }

    return 0;
}

/*!
  \brief Establish PG connection (pg_info->conninfo)

  \param pg_info pointer to Format_info_pg
*/
void connect_db(struct Format_info_pg *pg_info)
{
    pg_info->conn = PQconnectdb(pg_info->conninfo);
    G_debug(2, "   PQconnectdb(): %s", pg_info->conninfo);
    if (PQstatus(pg_info->conn) == CONNECTION_BAD)
        G_fatal_error("%s\n%s",
                      _("Connection ton PostgreSQL database failed."),
                      PQerrorMessage(pg_info->conn));
}

/*!
  \brief Check for topology schema (pg_info->toposchema_name)

  \param pg_info pointer to Format_info_pg

  \return 0 schema exists
  \return 1 schema doesn't exists
 */
int check_topo(struct Format_info_pg *pg_info, struct Plus_head *plus)
{
    char stmt[DB_SQL_MAX];
    
    PGresult *res;
    
    /* connect database */
    if (!pg_info->conn)
        connect_db(pg_info);
    
    if (pg_info->toposchema_name)
        return 0;
    
    /* check if topology layer/schema exists */
    sprintf(stmt,
            "SELECT t.name,t.hasz,l.feature_column FROM topology.layer "
            "AS l JOIN topology.topology AS t ON l.topology_id = t.id "
            "WHERE schema_name = '%s' AND table_name = '%s'",
            pg_info->schema_name, pg_info->table_name);
    G_debug(2, "SQL: %s", stmt);
    
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != 1) {
        G_debug(1, "Topology layers for '%s.%s' not found (%s)",
                pg_info->schema_name, pg_info->table_name,
                PQerrorMessage(pg_info->conn));
        if (res)
            PQclear(res);
        return 1;
    }

    pg_info->toposchema_name = G_store(PQgetvalue(res, 0, 0));
    pg_info->topogeom_column = G_store(PQgetvalue(res, 0, 2));

    G_debug(1, "PostGIS topology detected: schema = %s column = %s",
            pg_info->toposchema_name, pg_info->topogeom_column);
    
    /* check for 3D */
    if (strcmp(PQgetvalue(res, 0, 1), "t") == 0)
        plus->with_z = WITH_Z;
    PQclear(res);
    
    return 0;
}

/*!
  \brief Parse BBOX string
  
  \param value string buffer
  \param[out] bbox pointer to output bound_box struct

  \return 0 on success
  \return -1 on error
*/
int parse_bbox(const char *value, struct bound_box *bbox)
{
    unsigned int i;
    size_t length, prefix_length;
    char **tokens, **tokens_coord, *coord;
    
    prefix_length = strlen("box3d(");
    if (G_strncasecmp(value, "box3d(", prefix_length) != 0)
        return -1;
    
    /* strip off "bbox3d(...)" */
    length = strlen(value);
    coord = G_malloc(length - prefix_length);
    for (i = prefix_length; i < length; i++)
        coord[i-prefix_length] = value[i];
    coord[length-prefix_length-1] = '\0';
    
    tokens = G_tokenize(coord, ",");
    G_free(coord);
    
    if (G_number_of_tokens(tokens) != 2) {
        G_free_tokens(tokens);
        return -1;
    }
    
    /* parse bbox LL corner */
    tokens_coord = G_tokenize(tokens[0], " ");
    if (G_number_of_tokens(tokens_coord) != 3) {
        G_free_tokens(tokens);
        G_free_tokens(tokens_coord);
    }
    bbox->W = atof(tokens_coord[0]);
    bbox->S = atof(tokens_coord[1]);
    bbox->B = atof(tokens_coord[2]);
    
    G_free_tokens(tokens_coord);
    
    /* parse bbox UR corner */
    tokens_coord = G_tokenize(tokens[1], " ");
    if (G_number_of_tokens(tokens_coord) != 3) {
        G_free_tokens(tokens);
        G_free_tokens(tokens_coord);
    }
    bbox->E = atof(tokens_coord[0]);
    bbox->N = atof(tokens_coord[1]);
    bbox->T = atof(tokens_coord[2]);
    
    G_free_tokens(tokens_coord);
    G_free_tokens(tokens);
    
    return 0;
}

/*!
  \brief Get number of records for given SQL statement

  \param stmt string buffer with SQL statement
  
  \return number of returned records
  \return -1 on error
*/
int num_of_records(const struct Format_info_pg *pg_info,
                   const char *stmt)
{
    int result;
    PGresult *res;

    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != 1) {
        G_warning(_("Unable to get number of records for:\n%s"), stmt);
        if (res)
            PQclear(res);
        return -1;
    }
    result = atoi(PQgetvalue(res, 0, 0));
    PQclear(res);
    
    return result;
}

/*!
  \brief Read P_node structure
  
  See dig_Rd_P_node() for reference.
  
  \param plus pointer to Plus_head structure
  \param n index (starts at 1)
  \param id node id (table "node")
  \param pg_info pointer to Format_info_pg sttucture

  \return 0 on success
  \return -1 on failure
*/
int read_p_node(struct Plus_head *plus, int n, int id,
                struct Format_info_pg *pg_info)
{
    int i, cnt;
    char stmt[DB_SQL_MAX];
    
    struct P_node *node;
    
    PGresult *res;
    
    /* get lines connected to the node */
    sprintf(stmt,
            "SELECT edge_id,'s' as node,"
            "ST_Azimuth(ST_StartPoint(geom), ST_PointN(geom, 2)) AS angle"
            " FROM \"%s\".edge WHERE start_node = %d UNION ALL "
            "SELECT edge_id,'e' as node,"
            "ST_Azimuth(ST_EndPoint(geom), ST_PointN(geom, ST_NumPoints(geom) - 1)) AS angle"
            " FROM \"%s\".edge WHERE end_node = %d"
            " ORDER BY angle DESC",
            pg_info->toposchema_name, id,
            pg_info->toposchema_name, id);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK) {
        G_warning(_("Unable to read node %d"), id);
        if (res)
            PQclear(res);
        return -1;
    }
    cnt = PQntuples(res);
    
    if (cnt == 0) { /* dead ??? */
        plus->Node[n] = NULL;
        return 0;
    }

    node = dig_alloc_node();
    node->n_lines = cnt;
    G_debug(4, "read_p_node(): id = %d, n_lines = %d", id, cnt);
    
    if (dig_node_alloc_line(node, node->n_lines) == -1)
        return -1;

    /* lines / angles */
    for (i = 0; i < node->n_lines; i++) {
        node->lines[i] = atoi(PQgetvalue(res, i, 0));
        if (strcmp(PQgetvalue(res, i, 1), "s") != 0) {
            /* end node */
            node->lines[i] *= -1;
        }
        node->angles[i] = M_PI / 2 - atof(PQgetvalue(res, i, 2));
        /* angles range <-PI; PI> */
        if (node->angles[i] > M_PI)
            node->angles[i] = node->angles[i] - 2 * M_PI;
        if (node->angles[i] < -1.0 * M_PI)
            node->angles[i] = node->angles[i] + 2 * M_PI;
        G_debug(5, "\tline = %d angle = %f", node->lines[i],
                node->angles[i]);
    }
    PQclear(res);
    
    /* ???
    if (plus->with_z)
    if (0 >= dig__fread_port_P(&n_edges, 1, fp))
    */
    
    /* get node coordinates */
    sprintf(stmt,
            "SELECT ST_X(geom),ST_Y(geom),ST_Z(geom) FROM \"%s\".node "
            "WHERE node_id = %d",
            pg_info->toposchema_name, id);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != 1) {
        G_warning(_("Unable to read node %d"), id);
        if (res)
            PQclear(res);
        return -1;
    }
    node->x = atof(PQgetvalue(res, 0, 0));
    node->y = atof(PQgetvalue(res, 0, 1));
    if (plus->with_z)
        node->z = atof(PQgetvalue(res, 0, 2));
    else
        node->z = 0;
    PQclear(res);

    plus->Node[n] = node;
    
    return 0;
}

/*!
  \brief Read P_line structure
  
  See dig_Rd_P_line() for reference.
  
  Supported feature types:
   - GV_POINT
   - GV_LINE
   - GV_BOUNDARY
  
  \param plus pointer to Plus_head structure
  \param n index (starts at 1)
  \param data edge data (id, start/end node, left/right face, ...)
  \param pg_info pointer to Format_info_pg sttucture

  \return 0 on success
  \return -1 on failure
*/
int read_p_line(struct Plus_head *plus, int n,
                const struct edge_data *data)
{
    int tp;
    struct P_line *line;
    
    if (data->start_node == 0 && data->end_node == 0) {
        if (data->left_face == 0)
            tp = GV_POINT;
        else
            tp = GV_CENTROID;
    }
    else if (data->left_face == 0 && data->right_face == 0) {
        tp = GV_LINE;
    }
    else {
        tp = GV_BOUNDARY;
    }
    
    if (tp == 0) { /* dead ??? */
        plus->Line[n] = NULL;
        return 0;
    }

    line = dig_alloc_line();
    
    /* type & offset ( = id) */
    line->type = tp;
    line->offset = data->id;
    G_debug(4, "read_p_line(): id/offset = %d type = %d", data->id, line->type);
    
    /* topo */
    if (line->type == GV_POINT) {
        line->topo = NULL;
    }
    else {
        line->topo = dig_alloc_topo(line->type);

        /* lines */
        if (line->type == GV_LINE) {
            struct P_topo_l *topo = (struct P_topo_l *)line->topo;
            
            topo->N1 = data->start_node;
            topo->N2 = data->end_node;
        }
        /* boundaries */
        else if (line->type == GV_BOUNDARY) {
            struct P_topo_b *topo = (struct P_topo_b *)line->topo;
            
            topo->N1    = data->start_node;
            topo->N2    = data->end_node;
            topo->left  = data->left_face == 0 ? -1 : data->left_face;
            topo->right = data->right_face == 0 ? -1 : data->right_face;
        }
        /* centroids */
        else if (line->type == GV_CENTROID) {
            struct P_topo_c *topo = (struct P_topo_c *)line->topo;
            
            topo->area  = data->left_face;
        }
        /* TODO: faces | kernels */
    }

    plus->Line[n] = line;
    
    return 0;
}

/*!
  \brief Read P_area structure
  
  See dig_Rd_P_area() for reference.
  
  \param plus pointer to Plus_head structure
  \param n index (starts at 1)
  \param face_id face id (see 'face' table)
  \param pg_info pointer to Format_info_pg sttucture

  \return 0 on success
  \return -1 on failure
*/
int read_p_area(struct Plus_head *plus, int n, int face_id, struct Format_info_pg *pg_info)
{
    int i, cnt;
    char stmt[DB_SQL_MAX];

    PGresult *res;
    struct P_area *area;

    sprintf(stmt,
            "SELECT edge from ST_GetFaceEdges('%s', %d)",
            pg_info->toposchema_name, face_id);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK) {
        G_warning(_("Unable to read face %d"), face_id);
        if (res)
            PQclear(res);
        return -1;
    }
    
    cnt = PQntuples(res);
    if (cnt == 0) { /* dead */
        plus->Area[n] = NULL;
        return 0;
    }
    
    area = dig_alloc_area();

    /* boundaries */
    area->n_lines = cnt;
    if (dig_area_alloc_line(area, area->n_lines) == -1)
        return -1;
    area->lines = (plus_t *)G_realloc(area->lines, sizeof(plus_t) * area->n_lines);
    for (i = 0; i < area->n_lines; i++) {
        /* GRASS   Topo model: lines in clockwise order
           PosTGIS Topo model: lines in counter clockwise order */
        area->lines[i] = -1 * atoi(PQgetvalue(res, i, 0));
    }

    /* isles */
    /* TODO */

    /* centroid */
    area->centroid = plus->n_lines - plus->n_clines + i;
    
    plus->Area[n] = area;
    
    PQclear(res);
    
    return 0;
}

/*!
  \brief Read topo (from PostGIS topology schema) header info only

  \param[in,out] plus pointer to Plus_head struct

  \return 0 on success
  \return -1 on error
*/
int load_plus_head(struct Format_info_pg *pg_info, struct Plus_head *plus)
{
    char stmt[DB_SQL_MAX];
    
    PGresult *res;
    
    plus->off_t_size = -1;
    
    /* get map bounding box */
    sprintf(stmt,
            "SELECT ST_3DExtent(%s) FROM \"%s\".\"%s\"",
            pg_info->topogeom_column, pg_info->schema_name, pg_info->table_name);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != 1) {
        G_warning(_("Unable to get map bounding box from topology"));
        if (res)
            PQclear(res);
        return -1;
    }
    if (parse_bbox(PQgetvalue(res, 0, 0), &(plus->box)) != 0) {
        G_warning(_("Unable to parse map bounding box:\n%s"),
                  PQgetvalue(res, 0, 0));
        return -1;
    }
    PQclear(res);
    
    /* number of topological primitives */
    /* nodes
       note: isolated nodes are registered in GRASS Topology model */
    sprintf(stmt,
            "SELECT COUNT(DISTINCT node) FROM (SELECT start_node AS node "
            "FROM \"%s\".edge GROUP BY start_node UNION ALL SELECT end_node "
            "AS node FROM \"%s\".edge GROUP BY end_node) AS foo",
            pg_info->toposchema_name, pg_info->toposchema_name);
    plus->n_nodes = num_of_records(pg_info, stmt);
    G_debug(3, "Vect_open_topo_pg(): n_nodes=%d", plus->n_nodes);
    /* lines (edges in PostGIS Topology model) */
    sprintf(stmt,
            "SELECT COUNT(*) FROM \"%s\".edge",
            pg_info->toposchema_name);
    /* + isolated nodes as points
       + centroids */
    plus->n_lines = num_of_records(pg_info, stmt); 
    /* areas (faces in PostGIS Topology model) */
    sprintf(stmt,
            "SELECT COUNT(*) FROM \"%s\".face WHERE mbr IS NOT NULL",
            pg_info->toposchema_name);
    plus->n_areas = num_of_records(pg_info, stmt);
    G_debug(3, "Vect_open_topo_pg(): n_areas=%d", plus->n_areas);
    /* TODO: n_isles | n_volumes | n_holes */
    
    /* number of features group by type */
    /* points */
    sprintf(stmt,
            "SELECT COUNT(*) FROM \"%s\".node WHERE node_id NOT IN "
            "(SELECT node FROM (SELECT start_node AS node FROM \"%s\".edge "
            "GROUP BY start_node UNION ALL SELECT end_node AS node FROM "
            "\"%s\".edge GROUP BY end_node) AS foo)",
            pg_info->toposchema_name, pg_info->toposchema_name,
            pg_info->toposchema_name);
    plus->n_plines = num_of_records(pg_info, stmt);
    G_debug(3, "Vect_open_topo_pg(): n_plines=%d", plus->n_plines);
    /* lines */
    sprintf(stmt,
            "SELECT COUNT(*) FROM \"%s\".edge WHERE "
            "left_face = 0 AND right_face = 0",
            pg_info->toposchema_name);
    plus->n_llines = num_of_records(pg_info, stmt);
    G_debug(3, "Vect_open_topo_pg(): n_llines=%d", plus->n_llines);
    /* boundaries */
    sprintf(stmt,
            "SELECT COUNT(*) FROM \"%s\".edge WHERE "
            "left_face != 0 OR right_face != 0",
            pg_info->toposchema_name);
    plus->n_blines = num_of_records(pg_info, stmt);
    G_debug(3, "Vect_open_topo_pg(): n_blines=%d", plus->n_blines);
    /* centroids */
    sprintf(stmt,
            "SELECT COUNT(*) FROM \"%s\".face WHERE mbr IS NOT NULL",
            pg_info->toposchema_name);
    plus->n_clines = num_of_records(pg_info, stmt);
    G_debug(3, "Vect_open_topo_pg(): n_clines=%d", plus->n_clines);
    /* TODO: nflines | n_klines */

    /* lines - register isolated nodes as points and centroids */
    plus->n_lines += plus->n_plines + plus->n_clines;
    G_debug(3, "Vect_open_topo_pg(): n_lines=%d", plus->n_lines);

    return 0;
}

/*!
  \brief Read topo info (from PostGIS topology schema)

  \param pg_info pointer to Format_info_pg
  \param[in,out] plus pointer to Plus_head struct
  \param head_only TRUE to read only header info
  
  \return 0 on success
  \return -1 on error
*/
int load_plus(struct Format_info_pg *pg_info, struct Plus_head *plus,
              int head_only)
{
    int i, id, ntuples;
    char stmt[DB_SQL_MAX];
    struct edge_data line_data;
    
    PGresult *res;
  
    if (load_plus_head(pg_info, plus) != 0)
        return -1;

    if (head_only)
        return 0;
    
    /* read nodes (GRASS Topo)
       note: standalone nodes are ignored
    */
    sprintf(stmt,
            "SELECT node_id FROM \"%s\".node WHERE node_id IN "
            "(SELECT node FROM (SELECT start_node AS node FROM \"%s\".edge "
            "GROUP BY start_node UNION ALL SELECT end_node AS node FROM "
            "\"%s\".edge GROUP BY end_node) AS foo)",
            pg_info->toposchema_name, pg_info->toposchema_name,
            pg_info->toposchema_name);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != plus->n_nodes) {
        G_warning(_("Unable to read nodes"));
        if (res)
            PQclear(res);
        return -1;
    }

    G_debug(3, "load_plus(): n_nodes = %d", plus->n_nodes);
    dig_alloc_nodes(plus, plus->n_nodes);
    for (i = 1; i <= plus->n_nodes; i++) {
        id = atoi(PQgetvalue(res, i - 1, 0));
        read_p_node(plus, i, id, pg_info);
    }
    PQclear(res);

    /* read lines (GRASS Topo)
       - standalone nodes -> points
       - edges -> lines/boundaries
    */
    G_debug(3, "load_plus(): n_lines = %d", plus->n_lines);
    dig_alloc_lines(plus, plus->n_lines); 
    
    /* read PostGIS Topo standalone nodes */
    sprintf(stmt,
            "SELECT node_id FROM \"%s\".node WHERE node_id NOT IN "
            "(SELECT node FROM (SELECT start_node AS node FROM \"%s\".edge "
            "GROUP BY start_node UNION ALL SELECT end_node AS node FROM "
            "\"%s\".edge GROUP BY end_node) AS foo)",
            pg_info->toposchema_name, pg_info->toposchema_name,
            pg_info->toposchema_name);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) > plus->n_plines) {
        G_warning(_("Unable to read lines"));
        if (res)
            PQclear(res);
        return -1;
    }
    
    ntuples = PQntuples(res); /* plus->n_plines */
    G_zero(&line_data, sizeof(struct edge_data));
    for (i = 0; i < ntuples; i++) {
        /* process standalone nodes (PostGIS Topo) */
        line_data.id = atoi(PQgetvalue(res, i, 0));
        read_p_line(plus, i + 1, &line_data);
    }
    PQclear(res);
    
    /* read PostGIS Topo edges */
    sprintf(stmt,
            "SELECT edge_id,start_node,end_node,left_face,right_face "
            "FROM \"%s\".edge",
            pg_info->toposchema_name);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) > plus->n_lines) {
        G_warning(_("Unable to read lines"));
        if (res)
            PQclear(res);
        return -1;
    }

    ntuples = PQntuples(res);
    for (i = 0; i < ntuples; i++) {
        /* process edges (PostGIS Topo) */
        line_data.id         = atoi(PQgetvalue(res, i, 0));
        line_data.start_node = atoi(PQgetvalue(res, i, 1));
        line_data.end_node   = atoi(PQgetvalue(res, i, 2));
        line_data.left_face  = atoi(PQgetvalue(res, i, 3));
        line_data.right_face = atoi(PQgetvalue(res, i, 4));
        read_p_line(plus, plus->n_plines + i + 1, &line_data);
    }
    PQclear(res);
    
    /* read areas (GRASS Topo) */
    sprintf(stmt,
            "SELECT face_id from \"%s\".face WHERE mbr IS NOT NULL",
            pg_info->toposchema_name);
    G_debug(2, "SQL: %s", stmt);
    res = PQexec(pg_info->conn, stmt);
    if (!res || PQresultStatus(res) != PGRES_TUPLES_OK ||
        PQntuples(res) != plus->n_areas) {
        G_warning(_("Unable to read areas"));
        if (res)
            PQclear(res);
        return -1;
    }
    
    G_debug(3, "load_plus(): n_areas = %d", plus->n_areas);
    dig_alloc_areas(plus, plus->n_areas);
    G_zero(&line_data, sizeof(struct edge_data));
    for (i = 1; i <= plus->n_areas; i++) {
        line_data.id = line_data.left_face = atoi(PQgetvalue(res, i - 1, 0));
        read_p_area(plus, i, line_data.id, pg_info);
        /* add centroids */
        read_p_line(plus, plus->n_lines - plus->n_clines + i, &line_data);
    }
    PQclear(res);
    
    /* read isle (GRASS Topo) */

    return 0;
}
#endif
