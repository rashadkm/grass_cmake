#include "dbmi.h"

db_driver_list_tables (names, count, system)
    dbString **names;
    int *count;
    int system;
{
    db_procedure_not_implemented("db_list_tables");
    return DB_FAILED;
}
