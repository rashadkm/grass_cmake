#include "dbmi.h"
#include <sys/types.h>
#include <sys/stat.h>

int
db_isdir (path)
    char *path;
{
    struct stat x;

    if (stat(path, &x) != 0)
	return DB_FAILED;
    return ((x.st_mode & S_IFDIR) ? DB_OK : DB_FAILED);
}
