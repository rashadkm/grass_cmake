#ifndef __LOCAL_PROTO_V_OUT_POSTGIS__
#define __LOCAL_PROTO_V_OUT_POSTGIS__

#include <grass/vector.h>

struct params {
    struct Option *input, *layer, *dsn, *olayer;
};

struct flags {
    struct Flag *table, *topo;
};

/* create.c */
void create_table(struct Map_info *, struct Map_info *);
char *create_pgfile(const char *, const char *, int);

/* options.c */
void define_options(struct params *, struct flags *);

#endif /* __LOCAL_PROTO_V_OUT_POSTGIS__ */
