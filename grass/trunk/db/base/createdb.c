#include "dbmi.h"
#include "gis.h"
#include "codes.h"

struct {
	char *driver, *database, *location;
} parms;

void parse_command_line();

int
main(int argc, char *argv[])
{
    dbDriver *driver;
    dbHandle handle;
    int stat;

    parse_command_line (argc, argv);

    driver = db_start_driver (parms.driver);
    if (driver == NULL)
    {
	fprintf (stderr, "Can't run driver %s\n", parms.driver);
	exit(1);
    }
    db_init_handle (&handle);
    db_set_handle (&handle, parms.database, parms.location);
    stat = db_create_database (driver, &handle);
    db_shutdown_driver (driver);

    exit(stat == DB_OK ? OK : ERROR);
}

void
parse_command_line(int argc, char *argv[])
{
    struct Option *driver, *database, *location;
    struct GModule *module;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]) ;

    driver 		= G_define_option();
    driver->key 	= "driver";
    driver->type 	= TYPE_STRING;
    driver->options     = db_list_drivers();
    driver->required 	= YES;
    driver->description = "driver name";

    database 		= G_define_option();
    database->key 	= "database";
    database->type 	= TYPE_STRING;
    database->required 	= YES;
    database->description = "database name";

    location 		= G_define_option();
    location->key 	= "location";
    location->type 	= TYPE_STRING;
    location->required 	= YES;
    location->description = "database location";

    /* Set description */
    module              = G_define_module();
    module->description = ""\
    "Create an empty database.";


    if(G_parser(argc, argv))
	exit(ERROR);

    parms.driver	= driver->answer;
    parms.database	= database->answer;
    parms.location	= location->answer;
}
