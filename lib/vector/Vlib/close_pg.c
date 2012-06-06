/*!
   \file lib/vector/Vlib/close_pg.c

   \brief Vector library - Close map (PostGIS)

   Higher level functions for reading/writing/manipulating vectors.

   (C) 2011 by the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2). Read the file COPYING that comes with GRASS for details.

   \author Martin Landa <landa.martin gmail.com>
 */

#include <stdlib.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#ifdef HAVE_POSTGRES
#include "pg_local_proto.h"
#endif

/*!
   \brief Close vector map (PostGIS layer) on level 1

   \param Map pointer to Map_info structure

   \return 0 on success
   \return non-zero on error
 */
int V1_close_pg(struct Map_info *Map)
{
#ifdef HAVE_POSTGRES
    int i;
    struct Format_info_pg *pg_info;

    G_debug(3, "V2_close_pg() name = %s mapset = %s", Map->name, Map->mapset);

    if (!VECT_OPEN(Map))
        return -1;

    pg_info = &(Map->fInfo.pg);
    if (Map->mode == GV_MODE_WRITE || Map->mode == GV_MODE_RW)
        Vect__write_head(Map);

    /* close connection */
    if (pg_info->res) {
        char stmt[DB_SQL_MAX];

        PQclear(pg_info->res);
        pg_info->res = NULL;

        sprintf(stmt, "CLOSE %s_%s%p",
                pg_info->schema_name, pg_info->table_name, pg_info->conn);
        if (execute(pg_info->conn, stmt) == -1) {
            G_warning(_("Unable to close cursor"));
            return -1;
        }
        execute(pg_info->conn, "COMMIT");
    }

    PQfinish(pg_info->conn);

    /* close DB connection (for atgtributes) */
    if (pg_info->dbdriver) {
        db_close_database_shutdown_driver(pg_info->dbdriver);
    }

    /* free allocated space */
    for (i = 0; i < pg_info->cache.lines_alloc; i++) {
        Vect_destroy_line_struct(pg_info->cache.lines[i]);
    }
    if (pg_info->cache.lines)
        G_free(pg_info->cache.lines);

    G_free(pg_info->db_name);
    G_free(pg_info->schema_name);
    G_free(pg_info->geom_column);
    G_free(pg_info->fid_column);

    if (pg_info->toposchema_name)
        G_free(pg_info->toposchema_name);

    if (pg_info->topogeom_column)
        G_free(pg_info->topogeom_column);

    return 0;
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}

/*!
   \brief Close vector map (PostGIS layer) on topological level (write out fidx file)

   \param Map pointer to Map_info structure

   \return 0 on success
   \return non-zero on error
 */
int V2_close_pg(struct Map_info *Map)
{
#ifdef HAVE_POSTGRES
    G_debug(3, "V2_close_pg() name = %s mapset = %s", Map->name, Map->mapset);

    if (!VECT_OPEN(Map))
        return -1;

    if (Map->fInfo.pg.toposchema_name) /* no fidx file for PostGIS topology */
        return 0;

    /* write fidx for maps in the current mapset */
    if (Vect_save_fidx(Map, &(Map->fInfo.pg.offset)) != 1)
        G_warning(_("Unable to save feature index file for vector map <%s>"),
                  Map->name);

    G_free(Map->fInfo.pg.offset.array);

    return 0;
#else
    G_fatal_error(_("GRASS is not compiled with PostgreSQL support"));
    return -1;
#endif
}
