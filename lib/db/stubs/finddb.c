#include "dbmi.h"

db_driver_find_database (handle, found)
    dbHandle *handle;
    int *found;
{
    db_procedure_not_implemented("db_find_database");
    return DB_FAILED;
}
