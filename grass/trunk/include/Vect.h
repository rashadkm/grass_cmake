#ifndef GRASS_VECT_H
#define GRASS_VECT_H
#include "vect/digit.h"

/*   ANSI prototypes for the libes/vect32/Vlib functions */
/*
struct dig_head *Vect__get_default_out_head (void);
struct dig_head *Vect__get_default_in_head (void);
struct dig_head *Vect__get_default_port_head (void);
*/
int Vect_close (struct Map_info *);
int V1_close (struct Map_info *);
int V2_close (struct Map_info *);
int V2_tmp_close (int);
int V2_tmp_open (int);
int Vect_set_constraint_region (struct Map_info *, double, double, double, double);
int Vect_set_constraint_type (struct Map_info *, int);
int Vect_remove_constraints (struct Map_info *);
int Vect_get_area_points (struct Map_info *, int, struct line_pnts *);
int Vect_get_isle_points (struct Map_info *, int, struct line_pnts *);
int Vect_print_header (struct Map_info *);
int Vect__init_head (struct dig_head *);
int Vect_copy_head_data (struct dig_head *, struct dig_head *);
int Vect_level (struct Map_info *);
int Vect_P_init (char *, char *, struct Map_info *);
int Vect__P_writeable (int);
char *Vect__P_init (struct Map_info *, char *, char *);
char *Vect__P_init_new_plus (struct Map_info *, char *);
int V2_num_lines (struct Map_info *);
int V2_num_areas (struct Map_info *);
/*
int V2_line_att (struct Map_info *, int);
int V2_area_att (struct Map_info *, int);
*/
int V2_get_area (struct Map_info *, int, P_AREA **);
int V2_get_area_bbox (struct Map_info *, int, double *, double *, double *, double *);
int V2_get_line_bbox (struct Map_info *, int, double *, double *, double *, double *);
struct line_pnts *Vect_new_line_struct (void);
struct line_cats *Vect_new_cats_struct (void);
struct cat_list *Vect_new_cat_list (void);
struct line_pnts *Vect__new_line_struct (void);
struct line_cats *Vect__new_cats_struct (void);
int Vect_destroy_line_struct (struct line_pnts *);
int Vect_destroy_cats_struct (struct line_cats *);
int Vect_destroy_cat_list (struct cat_list *);
int Vect_copy_xy_to_pnts (struct line_pnts *, double *, double *, int);
int Vect_copy_xyz_to_pnts (struct line_pnts *, double *, double *, double *, int);
int Vect_reset_line (struct line_pnts *);
int Vect_append_point (struct line_pnts *, double, double);
int Vect_append_3d_point (struct line_pnts *, double, double, double);
int Vect_cat_set (struct line_cats *, GRASS_V_FIELD, GRASS_V_CAT);
int Vect_cat_get (struct line_cats *, GRASS_V_FIELD, GRASS_V_CAT *);
int Vect_cat_del (struct line_cats *, GRASS_V_FIELD);
int Vect_reset_cats (struct line_cats *);
int Vect_str_to_cat_list (char *, struct cat_list *);
int Vect_array_to_cat_list (int *, int, struct cat_list *);
int Vect_cat_in_cat_list (GRASS_V_CAT, struct cat_list *);
struct field_info *Vect_get_field_info (char *, char *, int);
int Vect_cat_in_array (GRASS_V_CAT, int *, int);
int Vect_copy_pnts_to_xy (struct line_pnts *, double *, double *, int *);
int Vect_copy_pnts_to_xyz (struct line_pnts *, double *, double *, double *, int *);
int Vect_type_to_code (int);
int Vect_code_to_type (int);
int Vect_set_open_level (int);
int Vect_open_old (struct Map_info *, char *, char *);
int Vect_open_new (struct Map_info *, char *, int);
int Vect__open_update_1 (struct Map_info *, char *);
int V1_open_old (struct Map_info *, char *, char *);
int V1_open_new (struct Map_info *, char *, int);
int V1__open_update_1 (struct Map_info *, char *);
int V2_open_old (struct Map_info *, char *, char *);
int V2__open_new_1 (struct Map_info *, char *, int);
int V2_open_update (struct Map_info *, char *);
int V2_open_new_plus (struct Map_info *, char *);
int V2__init_for_create_plus (struct Map_info *, char *);
int V2__open_update_1 (struct Map_info *, char *);
int V2__setup_for_digit (struct Map_info *, char *);
int Vect_get_point_in_area (struct Map_info *, int, double *, double *);
int Vect__intersect_line_with_poly (struct line_pnts *, double, struct line_pnts *);
int Vect_get_point_in_poly (struct line_pnts *, double *, double *);
int Vect_find_poly_centroid (struct line_pnts *, double *, double *);
int Vect_point_in_islands (struct Map_info *, int, double, double);
int Vect_get_point_in_poly_isl (struct line_pnts *, struct line_pnts **, int, double *, double *);
int Vect_init (void);
/*
int Vect__write_head_binary (struct Map_info *, struct dig_head *);
int Vect__read_head_binary (struct Map_info *, struct dig_head *);
*/
int Vect__write_head (struct Map_info *);
int Vect__read_head (struct Map_info *);
int Vect__Read_line (struct Map_info *, struct line_pnts *, struct line_cats *, long);
long Vect__Write_line (struct Map_info *, int type, struct line_pnts *, struct line_cats *);
int Vect__Rewrite_line (struct Map_info *, long, int, struct line_pnts *, struct line_cats *);
int dig_Rd_P_node (struct Map_info *, struct P_node *, FILE *);
int dig_Wr_P_node (struct Map_info *, struct P_node *, FILE *);
int dig_Rd_P_line (struct Map_info *, struct P_line *, FILE *);
int dig_Wr_P_line (struct Map_info *, struct P_line *, FILE *);
int dig_Rd_P_area (struct Map_info *, struct P_area *, FILE *);
int dig_Wr_P_area (struct Map_info *, struct P_area *, FILE *);
int dig_Rd_P_isle (struct Map_info *, struct P_isle *, FILE *);
int dig_Wr_P_isle (struct Map_info *, struct P_isle *, FILE *);
int dig_Rd_P_att (struct Map_info *, struct P_att *, FILE *);
int dig_Wr_P_att (struct Map_info *, struct P_att *, FILE *);
int dig_Rd_Plus_head (struct Map_info *, struct Plus_head *, FILE *);
int dig_Wr_Plus_head (struct Map_info *, struct Plus_head *, FILE *);
int Vect_read_next_line (struct Map_info *, struct line_pnts *, struct line_cats *);
int V1_read_line (struct Map_info *, struct line_pnts *, struct line_cats *, long);
int V1_read_next_line (struct Map_info *, struct line_pnts *, struct line_cats *);
int V2_read_line (struct Map_info *, struct line_pnts *, struct line_cats *, int);
int V2_read_next_line (struct Map_info *, struct line_pnts *, struct line_cats *);
int V__map_overlap (struct Map_info *, double, double, double, double);
int Vect_rewind (struct Map_info *);
int V1_rewind (struct Map_info *);
int V2_rewind (struct Map_info *);
/*
int Vect__get_window (struct Map_info *, double *, double *, double *, double *);
*/
long Vect_write_line (struct Map_info *, int type, struct line_pnts *, struct line_cats *);
int Vect_x__Read_line (struct Map_info *, struct line_pnts *, struct line_cats *, long);
long Vect_x__Write_line (struct Map_info *, int, struct line_pnts *, struct line_cats *);
int Vect_x__Rewrite_line (struct Map_info *, long, int, struct line_pnts *, struct line_cats *);
int Vect_x__Mem_Read_line (struct line_pnts *, long);
int Vect_x__Mem_Read_line (struct line_pnts *, long);
/*
int Vect_x_write_head_binary (struct Map_info *, struct dig_head *);
int Vect_x_read_head_binary (struct Map_info *, struct dig_head *);
*/
char *Vect_support_name (void);

#endif
