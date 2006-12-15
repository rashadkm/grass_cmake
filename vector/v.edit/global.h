#ifndef _V_EDIT_
# define _V_EDIT_

# ifdef MAIN
#  define global
# else
#  define global extern
# endif

# include <stdio.h>
# include <stdlib.h>
# include <grass/gis.h>
# include <grass/Vect.h>
# include <grass/glocale.h>

enum mode {
    MODE_CREATE,
    MODE_ADD,
    MODE_DEL,
    MODE_MOVE,
    MODE_VERTEX,
    MODE_SPLIT,
    MODE_BREAK,
    MODE_MERGE
};

int parser(int argc, char*argv[]);

/* delete.c */
int do_del(struct Map_info *Map);
int delete_categories(struct Map_info *Map);
int delete_coordinates(struct Map_info *Map);
int delete_bbox(struct Map_info *Map);

/* a2b.c */
int asc_to_bin(FILE *, struct Map_info *);

/* move.c */
int do_move(struct Map_info *Map);
int move_categories(struct Map_info *Map);
int move_coordinates(struct Map_info *Map);
int move_bbox(struct Map_info *Map);

/* vertex.c */
int do_move_vertex(struct Map_info *Map);

void cat_max_set ( int field, int cat);
int cat_max_get ( int field );
void cat_init(struct Map_info *Map);
int add_line(struct Map_info *Map, int type, struct line_pnts *Points,
	     int field, int cat);
int attr_new(struct Map_info *Map, int field, int cat, const char *vals);
int attr_edit(struct Map_info *Map, int field, int cat, const char *vals);
int attr_del(struct Map_info *Map, int field, int cat);

global struct Option *input_opt, *map_opt, *tool_opt, *coord_opt, *cat_opt, *move_opt, *at_opt, *bbox_opt, *snap_opt, *fld_opt;
global struct Flag *n_flg, *t_flg, *d_flg, *b_flg, *c_flg, *n_flg;
global struct GModule *module;
global struct Map_info Map;
global enum mode action_mode;
global char *mapset;

global FILE *ascii;


#endif
