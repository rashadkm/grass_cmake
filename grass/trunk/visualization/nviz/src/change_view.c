
/* change_view:
 ** callbacks for movement & perspective adjustments
 */

/*
 * added return values and test for position *REALLY* changed
 * in: 
 *	Nchange_position_cmd()
 *	Nchange_height_cmd()
 *	Nchange_height_cmd()
 *	Nchange_exag_cmd()
 *	Pierre de Mouveaux (24 oct. 1999) p_de_mouveaux@hotmail.com
 */

 /*
  added return values and test for position *REALLY* changed
  in: 
	Nchange_position_cmd()
	Nchange_height_cmd()
	Nchange_height_cmd()
	Nchange_exag_cmd()
	Pierre de Mouveaux (24 oct. 1999)
 */

#include "interface.h"
#include <stdlib.h>
int 
Nchange_persp_cmd(data, interp, argc, argv)
     Nv_data *data;
     Tcl_Interp *interp;                 /* Current interpreter. */
     int argc;                           /* Number of arguments. */
     char **argv;                        /* Argument strings. */

{
  int fov, persp;
  if (argc != 2)
    return (TCL_ERROR);
  persp = atoi(argv[1]);
  
  fov = (int)(10 * persp);
  GS_set_fov(fov);
  Nquick_draw_cmd(data, interp);
  
  return 0;

  return 0;
}

normalize (v)
     float *v;
{
  float len;
  
  len = sqrt (v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
  v[0] /= len;
  v[1] /= len;
  v[2] /= len;
}
/**********************************************************************/

int
Nchange_position_cmd(data, interp, argc, argv)
     Nv_data *data;
     Tcl_Interp *interp;                 /* Current interpreter. */
     int argc;                           /* Number of arguments. */
     char **argv;                        /* Argument strings. */

{
  float xpos, ypos, from[3];
  float tempx, tempy;


  xpos = atof (argv[1]);
  xpos = (xpos < 0) ? 0 : (xpos > 1.0) ? 1.0 : xpos;
  ypos = 1.0 - atof (argv[2]);
  ypos = (ypos < 0) ? 0 : (ypos > 1.0) ? 1.0 : ypos;


  GS_get_from(from);

  tempx = xpos * RANGE - RANGE_OFFSET;
  tempy = ypos * RANGE - RANGE_OFFSET;

  if ((from[X]!=tempx) || (from[Y]!=tempy)) {

    from[X] = tempx;
    from[Y] = tempy;

    GS_moveto(from);
  /*

     if (argc == 4)
     {
     if (atoi(argv[3]))
     {
     normalize (from);
     GS_setlight_position(1, from[X], from[Y], from[Z], 0);
     }
     }
     */
	Nquick_draw_cmd(data, interp);
  }
  return 0;
}

/**********************************************************************/

int
Nchange_height_cmd(data, interp, argc, argv)
     Nv_data *data;
     Tcl_Interp *interp;                 /* Current interpreter. */
     int argc;                           /* Number of arguments. */
     char **argv;                        /* Argument strings. */
{
  float temp;
  float from[3];

  if (argc < 2)
    return (TCL_ERROR);
  
  GS_get_from_real(from);

  if ((temp = (float)atof(argv[1])) != from[Z]) {
    from[Z] = temp;  

    GS_moveto_real(from);

  /*
     if (argc == 3)
     {
     if (atoi(argv[2]))
     {
     normalize (from);
     GS_setlight_position(1, from[X], from[Y], from[Z], 0);
     }
     }
     */
  
    Nquick_draw_cmd(data,interp);
  }
   return (0);
}

Nset_light_to_view_cmd (data, interp, argc, argv)
     Nv_data *data;
     Tcl_Interp *interp;                 /* Current interpreter. */
     int argc;                           /* Number of arguments. */
     char **argv;                        /* Argument strings. */
{
  float from[3];
  GS_get_from_real(from);
  normalize (from);
  GS_setlight_position(1, from[X], from[Y], from[Z], 0);
  
    Nquick_draw_cmd(data,interp);
  
  return (0);
}


/**********************************************************************/
/* call whenever a new surface is added, deleted, or exag changes */
update_ranges(dc)
     Nv_data *dc;
{
  float zmin, zmax, exag, texag;
  int nsurfs, i, *surf_list;
  
  GS_get_longdim(&(dc->XYrange));

  dc->Zrange = 0.;
  
  /* Zrange is based on a minimum of Longdim */
  if(GS_global_exag()) {
    exag=GS_global_exag();
    dc->Zrange = dc->XYrange / exag;
  } else {
    exag=1.0;
  }

  GS_get_zrange_nz(&zmin, &zmax); /* actual */

  zmax = zmin + (3.*dc->XYrange/exag);
  zmin = zmin - (2.*dc->XYrange/exag);
  
  if((zmax - zmin) > dc->Zrange)
    dc->Zrange = zmax - zmin;
}

/**********************************************************************/

int
Nchange_exag_cmd(data, interp, argc, argv)
     Nv_data *data;
     Tcl_Interp *interp;                 /* Current interpreter. */
     int argc;                           /* Number of arguments. */
     char **argv;                        /* Argument strings. */
{
  /*int i;*/
  float val;
  float temp;
/*  float from[3];*/
  
  if (argc != 2)
    return (TCL_ERROR);
  val = atof (argv[1]);
  
  temp = GS_global_exag();
  if (val != temp) {
    GS_set_global_exag(val);
    update_ranges(data);
    Nquick_draw_cmd(data,interp);
  }

  return 0;

}

/**********************************************************************/



