#include "dbmi.h"

void
db_init_index (index)
    dbIndex *index;
{
    db_init_string (&index->indexName);
    db_init_string (&index->tableName);
    index->numColumns = 0;
    index->columnNames = NULL;
    index->unique = 0;
}

void
db_free_index (index)
    dbIndex *index;
{
    db_free_string (&index->indexName);
    db_free_string (&index->tableName);
    if (index->numColumns > 0)
	db_free_string_array (index->columnNames, index->numColumns);
    db_init_index(index);
}

int
db_alloc_index_columns (index, ncols)
    dbIndex *index;
    int ncols;
{
    index->columnNames = db_alloc_string_array (ncols);
    if (index->columnNames == NULL)
	return db_get_error_code();
    index->numColumns = ncols;

    return DB_OK;
}

dbIndex *
db_alloc_index_array (count)
    int count;
{
    dbIndex *list;
    int i;

    list = (dbIndex *) db_calloc (count, sizeof(dbIndex));
    if (list)
    {
	for (i = 0; i < count; i++)
	    db_init_index (&list[i]);
    }
    return list;
}

void
db_free_index_array (list, count)
    dbIndex *list;
    int count;
{
    int i;

    if (list)
    {
	for (i = 0; i < count; i++)
	    db_free_index (&list[i]);
	free (list);
    }
}

int
db_set_index_name (index, name)
    dbIndex *index;
    char *name;
{
    return db_set_string (&index->indexName, name);
}

char *
db_get_index_name (index)
    dbIndex *index;
{
    return db_get_string (&index->indexName);
}

int
db_set_index_table_name (index, name)
    dbIndex *index;
    char *name;
{
    return db_set_string (&index->tableName, name);
}

char *
db_get_index_table_name (index)
    dbIndex *index;
{
    return db_get_string (&index->tableName);
}

int
db_get_index_number_of_columns (index)
    dbIndex *index;
{
    return index->numColumns;
}

int
db_set_index_column_name (index, column_num, name)
    dbIndex *index;
    int column_num;
    char *name;
{
    if (column_num < 0 || column_num >= index->numColumns)
    {
	db_error ("db_set_index_column_name(): invalid column number");
	return db_get_error_code();
    }
    return db_set_string (&index->columnNames[column_num], name);
}

char *
db_get_index_column_name (index, column_num)
    dbIndex *index;
    int column_num;
{
    if (column_num < 0 || column_num >= index->numColumns)
    {
	db_error ("db_get_index_column_name(): invalid column number");
	return ( (char *) NULL);
    }
    return db_get_string (&index->columnNames[column_num]);
}

db_set_index_type_unique (index)
    dbIndex *index;
{
    index->unique = 1;
}

db_set_index_type_non_unique (index)
    dbIndex *index;
{
    index->unique = 0;
}

db_test_index_type_unique (index)
    dbIndex *index;
{
    return index->unique != 0;
}

db_print_index(fd, index)
    FILE *fd;
    dbIndex *index;
{
    int i, nCols;

    fprintf(fd, "Name: %s\n", db_get_index_name(index));
    if( db_test_index_type_unique(index))
      fprintf(fd, "Unique: true\n");
    else
      fprintf(fd, "Unique: false\n");
    fprintf(fd, "Table: %s\n", db_get_index_table_name(index));
    nCols = db_get_index_number_of_columns(index);
    fprintf(fd, "Number of columns: %d\nColumns:\n", nCols);
    for (i = 0; i < nCols; i++) {
	fprintf(fd, "  %s\n", db_get_index_column_name(index, i));
    }
}
