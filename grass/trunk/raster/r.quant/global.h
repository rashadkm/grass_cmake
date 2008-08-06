#include <grass/gis.h>

extern struct Quant quant_struct;
extern CELL old_min, old_max;
extern DCELL old_dmin, old_dmax;
extern char *name[GNAME_MAX];	/* input map names */
extern char *mapset[GMAPSET_MAX];	/* input mapsets */
extern int noi;

/* read_rules.c */
int read_range(void);
int report_range(void);
int read_rules(const char *);
