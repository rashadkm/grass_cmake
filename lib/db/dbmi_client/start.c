#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include "dbmi.h"

#define READ  0
#define WRITE 1

extern char *getenv();

/* setenv() is not portable, putenv() is POSIX */
int setenv_ (const char *name, const char *value, int overwrite) {
    /* Allocate more space each call */
    char *buffer;
    int len;

    if (!overwrite && getenv(name)) return 0;
    len = strlen(name) + strlen(value) + 2;
    buffer = (char *) G_malloc (len);
    sprintf (buffer, "%s=%s", name, value);
    return putenv (buffer);
}

/*!
 \fn 
 \brief 
 \return 
 \param 
*/
dbDriver *
db_start_driver(name)
    char *name;
{
    dbDriver *driver;
    dbDbmscap *list, *cur;
    char *startup;
    int p1[2], p2[2];
    int pid;
    int stat;
    dbConnection connection;
    char buf[2000];

    /* Set some enviroment variables which are later read by driver.
     * This is necessary when application is running without GISRC file and all
     * gis variables are set by application. 
     * Even if GISRC is set, application may change some variables during runtime,
     * if for example reads data from different gdatabase, location or mapset*/
    
    /* setenv() is not portable, putenv() is POSIX */
    if (  G_get_gisrc_mode() == G_GISRC_MODE_MEMORY ) {
	putenv("GISRC_MODE_MEMORY=1"); /* to tell driver that it must read variables */
	
	if ( G__getenv ( "DEBUG" ) ) {
	    sprintf (buf, "DEBUG=%s", G__getenv ( "DEBUG" ) );
	    putenv(buf);
	} else {
	    putenv("DEBUG=0");
	}

	sprintf (buf, "GISDBASE=%s", G__getenv("GISDBASE") );
	putenv(buf);
	sprintf (buf, "LOCATION_NAME=%s", G__getenv("LOCATION_NAME") );
	putenv(buf);
	sprintf (buf, "MAPSET=%s", G__getenv("MAPSET") );
	putenv(buf);
    }
    
/* read the dbmscap file */
    if(NULL == (list = db_read_dbmscap()))
	return (dbDriver *) NULL;

/* if name is empty use connection.driverName, added by RB 4/2000 */
    if( name == '\0' )
    {
	db_get_connection( &connection );
	if(NULL == (name = connection.driverName) )
	   return (dbDriver *) NULL;
    }

/* find this system name */
    for (cur = list; cur; cur = cur->next)
	if (strcmp (cur->driverName, name) == 0)
	    break;
    if (cur == NULL)
    {
	char msg[256];

	db_free_dbmscap (list);
	sprintf (msg, "%s: no such driver available", name );
	db_error (msg);
	return (dbDriver *) NULL;
    }

/* allocate a driver structure */
    driver = (dbDriver *) db_malloc (sizeof(dbDriver));
    if (driver == NULL)
    {
	db_free_dbmscap (list);
	return (dbDriver *) NULL;
    }
    
/* copy the relevant info from the dbmscap entry into the driver structure */
    db_copy_dbmscap_entry (&driver->dbmscap, cur);
    startup = driver->dbmscap.startup;

/* free the dbmscap list */
    db_free_dbmscap (list);

/* run the driver as a child process and create pipes to its stdin, stdout */

/* open the pipes */
    if ((pipe(p1) < 0 ) || (pipe(p2) < 0 ))
    {
        db_syserror ("can't open any pipes");
	return (dbDriver *) NULL;
    }

/* create a child */
    if ((pid = fork()) < 0)
    {
        db_syserror ("can't create fork");
	return (dbDriver *) NULL;
    }

    if (pid > 0)        /* parent */
    {
        close(p1[READ]);
        close(p2[WRITE]);

/* record driver process id in driver struct */
        driver->pid = pid;

/* convert pipes to FILE* */
	driver->send = fdopen (p1[WRITE], "w");
	driver->recv = fdopen (p2[READ],  "r");

/* most systems will have to use unbuffered io to get the send/recv to work */
#ifndef USE_BUFFERED_IO
	setbuf (driver->send, NULL);
	setbuf (driver->recv, NULL);
#endif

	db__set_protocol_fds (driver->send, driver->recv);
	if(db__recv_return_code(&stat) !=DB_OK || stat != DB_OK)
	    driver =  NULL;
	return driver;
    }
    else        /* child process */
    {
        close(p1[WRITE]);
        close(p2[READ]);

        close (0);
        close (1);

        if (dup(p1[READ]) != 0)
        {
            db_syserror("dup r");
            _exit(127) ;
        }

        if (dup(p2[WRITE]) != 1)
        {
            db_syserror("dup w");
            _exit(127) ;
        }

	execl ("/bin/sh", "sh", "-c", startup, 0);

        db_syserror ("execl");
	return NULL; /* to keep lint, et. al. happy */
    }
}
