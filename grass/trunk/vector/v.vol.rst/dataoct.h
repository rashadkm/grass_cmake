#define NWT  1 
#define NET  2 
#define SWT  3
#define SET  4 
#define NWB  5 
#define NEB  6 
#define SWB  7 
#define SEB  8 

#define NUMLEAFS 8

struct quadruple   {
  double x;
  double y;
  double z;
  double w;
  double sm;
};

struct octdata {
  double x_orig;
  double y_orig;
  double z_orig;
  int    n_rows;
  int    n_cols;
  int    n_levs;
  int    n_points;
  struct quadruple  *points;
 }; 


struct quadruple *point_new();
struct octdata *data_new (); 
int oct_compare();
int oct_add_data();
int oct_division_check();
struct octdata ** oct_divide_data();
int oct_intersect();
int oct_get_points();



