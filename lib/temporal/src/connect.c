/*!
  \file lib/temporal/src/connect.c
  
  \brief Temporal GIS Library - connect to TGIS DB
  
  (C) 2012 by the GRASS Development Team
  
  This program is free software under the GNU General Public License
  (>=v2). Read the file COPYING that comes with GRASS for details.
  
  \author Soeren Gebbert 
          Code is based on the dbmi library written by 
          Joel Jones (CERL/UIUC) and Radim Blazek
*/
#include <grass/temporal.h>

/*!
  \brief Set default Temporal GIS DB connection settings

  This function sets enviromental variables as TGISDB_DRIVER, TGISDB_DATABASE.

  \param connection pointer to dbConnection with default settings
  
  \return DB_OK
 */
int tgis_set_connection(dbConnection * connection)
{
    if (connection->driverName)
	G_setenv2("TGISDB_DRIVER", connection->driverName, G_VAR_MAPSET);

    if (connection->databaseName)
	G_setenv2("TGISDB_DATABASE", connection->databaseName, G_VAR_MAPSET);

    return DB_OK;
}

/*!
  \brief Get Temporal GIS DB connection settings
  
  \param[out] connection pointer to dbConnection to be modified

  \return DB_OK
 */
int tgis_get_connection(dbConnection * connection)
{
    G_zero(connection, sizeof(dbConnection));
    
    connection->driverName = (char *)G__getenv2("TGISDB_DRIVER", G_VAR_MAPSET);
    connection->databaseName = (char *)G__getenv2("TGISDB_DATABASE", G_VAR_MAPSET);

    return DB_OK;
}
