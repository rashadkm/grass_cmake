#include "dbmi.h"
#include "macros.h"

static int valid_cursor();

/*!
 \fn 
 \brief 
 \return 
 \param 
*/
int
db_d_fetch()
{
    dbToken token;
    dbCursor *cursor;
    int stat;
    int more;
    int position;

/* get the arg(s) */
    DB_RECV_TOKEN(&token);
    DB_RECV_INT(&position);
    cursor = (dbCursor *) db_find_token(token);
    if (!valid_cursor(cursor, position))
    {
	DB_SEND_FAILURE();
	return DB_FAILED;
    }

/* call the procedure */
    stat = db_driver_fetch (cursor, position, &more);

/* send the return code */
    if (stat != DB_OK)
    {
	DB_SEND_FAILURE();
	return DB_OK;
    }
    DB_SEND_SUCCESS();

/* results */
    DB_SEND_INT (more);
    if (more)
    {
	DB_SEND_TABLE_DATA (cursor->table);
    }
    return DB_OK;
}

static
valid_cursor (cursor, position)
    dbCursor *cursor;
{
    if (cursor == NULL)
	return 0;
    if(!db_test_cursor_type_fetch(cursor))
    {
	db_error ("not a fetchable cursor");
	return 0;
    }
    if (position != DB_NEXT && !db_test_cursor_mode_scroll(cursor))
    {
	db_error ("not a scrollable cursor");
	return 0;
    }
    return 1;
}
