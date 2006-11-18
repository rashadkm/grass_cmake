/* plot.c */
int plot_grid(double, double, double, int, int);
int plot_geogrid(double, struct pj_info, struct pj_info, int, int);
void init_proj(struct pj_info *, struct pj_info *, int);
void get_ll_bounds(double *, double *, double *, double *, struct Cell_head, struct pj_info, struct pj_info);
void check_coords(double, double, double *, double *, int, struct Cell_head, struct pj_info, struct pj_info);
float get_heading(double, double);

/* plotborder.c */
int plot_border(double, double, double);
