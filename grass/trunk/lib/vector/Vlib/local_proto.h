#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/vector.h>

/* Internal vector library subroutines which are not part of public
   API*/

/* map.c */
int Vect__delete(const char *, int);

/* open.c */
int Vect__open_old(struct Map_info *, const char *, const char *,
                   const char *, int, int, int);
char *Vect__get_path(const struct Map_info *);
char *Vect__get_element_path(const struct Map_info *, const char *);

/* write_nat.c */
int V2__add_line_to_topo_nat(struct Map_info *, off_t, int,
                             const struct line_pnts *, const struct line_cats *, int,
                             int (*external_routine) (const struct Map_info *, int));
int V2__delete_line_from_topo_nat(struct Map_info *, int, int,
                                  const struct line_pnts *, const struct line_cats *);

#endif /* PG_LOCAL_PROTO_H__ */
