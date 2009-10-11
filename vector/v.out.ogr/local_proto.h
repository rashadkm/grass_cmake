#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>

#include "ogr_api.h"
#include "cpl_string.h"

struct Options {
    struct Option *input, *dsn, *layer, *type, *format,
	*field, *dsco, *lco;
};

struct Flags {
    struct Flag *cat, *esristyle, *poly, *update, *nocat;
};

/* args.c */
void parse_args(int, char **,
		struct Options*, struct Flags *);

/* attributes.c */
int mk_att(int cat, struct field_info *Fi, dbDriver *Driver,
	   int ncol, int doatt, int nocat, OGRFeatureH Ogr_feature, int *, int *);

/* list.c */
char *OGR_list_write_drivers();
