#include "dbmi.h"

db_driver_open_database (handle)
    dbHandle *handle;
{
    db_procedure_not_implemented("db_open_database");
    return DB_FAILED;
}
