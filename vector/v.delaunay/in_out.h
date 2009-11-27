#ifndef IN_OUT_H
#define IN_OUT_H

int read_sites(int mode3d, int complete_map, struct Map_info* map_in,
	       struct bound_box Box, int);
void output_edges(struct vertex *sites_sorted[], unsigned int n, int mode3d,
		  int Type, struct Map_info map_out);
void output_triangles(struct vertex *sites_sorted[], unsigned int n,
		      int mode3d, int Type, struct Map_info map_out);
void remove_duplicates(struct vertex *list[], unsigned int *size);
#endif
