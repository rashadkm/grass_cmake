/*
**  Written by H. Mitasova, I. Kosinovsky, D. Gerdes Fall 1993 
**  Copyright  H. Mitasova, I. Kosinovsky, D.Gerdes  
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "gis.h"

#include "interpf.h"

static double  smallest_segment( struct multtree *, int);

int IL_interp_segments_2d (
    struct interp_params *params,
    struct tree_info *info,    /* info for the quad tree */
    struct multtree *tree,    /* current leaf of the quad tree */
    struct BM *bitmask,                      /* bitmask */
    double zmin,
    double zmax,                        /* min and max input z-values */
    double *zminac,
    double *zmaxac,                  /* min and max interp. z-values */
    double *gmin,
    double *gmax,                      /* min and max inperp. slope val.*/
    double *c1min,
    double *c1max,
    double *c2min,
    double *c2max,      /* min and max interp. curv. val.*/
    double *ertot,                           /* total interplating func. error*/
    int totsegm,                          /* total number of segments */
    int offset1,                          /* offset for temp file writing */
    double dnorm
)
/*
Recursively processes each segment in a tree by
  a) finding points from neighbouring segments so that the total number of
     points is between KMIN and KMAX2 by calling tree function MT_get_region().
  b) creating and solving the system of linear equations using these points
     and interp() by calling matrix_create() and G_ludcmp().
  c) checking the interpolating function values at points by calling
     check_points().
  d) computing grid for this segment using points and interp() by calling
     grid_calc().
*/
    
{
    double          xmn, xmx, ymn, ymx, distx, disty, distxp, distyp, temp1,
                    temp2;
    int             i, npt, nptprev, MAXENC;
    struct quaddata *data;
    static int         cursegm = 0;
    static double          *b = NULL;
    static int             *indx = NULL;
    static double          **matrix = NULL;
    double ew_res, ns_res;
    static int first_time = 1;
    static double smseg;
    int    MINPTS;
    double pr;
    struct triple *point;
    struct triple skip_point;
    int m_skip, skip_index,j,k;

/* find the size of the smallest segment once */
    if (first_time) {
      smseg = smallest_segment(info->root,4);
/*      fprintf(stderr, "smseg=%lf, first=%d,\n", smseg, first_time);*/
      first_time = 0;
    }
    ns_res = (((struct quaddata *) (info->root->data))->ymax -
              ((struct quaddata *) (info->root->data))->y_orig)/params->nsizr;
    ew_res = (((struct quaddata *) (info->root->data))->xmax -
              ((struct quaddata *) (info->root->data))->x_orig)/params->nsizc;

    if (tree == NULL)
	return -1;
    if (tree->data == NULL)
	return -1;
    if (((struct quaddata *)(tree->data))->points == NULL)
    {
      for (i=0;i<4;i++) {
        IL_interp_segments_2d(params,info,tree->leafs[i],
          bitmask,zmin,zmax,zminac,zmaxac,gmin,gmax,
          c1min,c1max,c2min,c2max,ertot,totsegm,offset1,dnorm);
      }       
      return 1;
    }
    else
    {
        distx = (((struct quaddata *)(tree->data))->n_cols 
                    * ew_res) * 0.1;
	disty = (((struct quaddata *)(tree->data))->n_rows 
                    * ns_res) * 0.1;
	distxp = 0;
	distyp = 0;
	xmn = ((struct quaddata *)(tree->data))->x_orig;
	xmx = ((struct quaddata *)(tree->data))->xmax;  
	ymn = ((struct quaddata *)(tree->data))->y_orig;
	ymx = ((struct quaddata *)(tree->data))->ymax; 
	i = 0;
	MAXENC = 0;
/* data is a window with zero points; some fields don't make sence in this case
   so they are zero (like resolution,dimentions */
/* CHANGE */  
/* Calcutaing kmin for surrent segment (depends on the size) */
/*****if (smseg <= 0.00001) MINPTS=params->kmin; else {} ***/
        pr = pow(2.,(xmx-xmn)/smseg-1.);
        MINPTS = params->kmin*(pr/(1+params->kmin*pr/params->KMAX2));
/* fprintf(stderr,"MINPTS=%d, KMIN=%d, KMAX=%d, pr=%lf, smseg=%lf, DX=%lf \n", MINPTS,params->kmin,params->KMAX2,pr,smseg,xmx-xmn); */

        data = (struct quaddata *)quad_data_new(xmn-distx,ymn-disty,xmx+distx,
               ymx+disty,0,0,0,params->KMAX2);
	npt = MT_region_data (info,info->root,data,params->KMAX2,4);

	while ((npt < MINPTS) || (npt > params->KMAX2))
	{
	    if (i >= 70)
	    {
                fprintf(stderr,"Warning: taking too long to find points for interpolation--please change the region to area where your points are. Continuing calculations...\n");
		break;
	    }
	    i++;
	    if (npt > params->KMAX2)
/* decrease window */
	    {
		MAXENC = 1;
		nptprev = npt;
		temp1 = distxp;
		distxp = distx;
		distx = distxp - fabs (distx - temp1) * 0.5;
		temp2 = distyp;
		distyp = disty;
		disty = distyp - fabs (disty - temp2) * 0.5;
/* decrease by 50% of a previous change in window */
	    }
	    else
	    {
		nptprev = npt;
		temp1 = distyp;
		distyp = disty;
		temp2 = distxp;
		distxp = distx;
		if (MAXENC)
		{
		    disty = fabs (disty - temp1) * 0.5 + distyp;
		    distx = fabs (distx - temp2) * 0.5 + distxp;
		}
		else
		{
		    distx += distx;
		    disty += disty;
		}
/* decrease by 50% of extra distance */
	   }
           data->x_orig = xmn-distx;   /* update window */
           data->y_orig = ymn-disty;
           data->xmax = xmx+distx;
           data->ymax = ymx+disty;
           data->n_points = 0;
	   npt = MT_region_data (info,info->root,data,params->KMAX2,4);
	}
	/* show before to catch 0% */
	if (totsegm != 0)
	{
	  G_percent (cursegm, totsegm, 1);
	}
        data->n_rows = ((struct quaddata *)(tree->data))->n_rows;
        data->n_cols = ((struct quaddata *)(tree->data))->n_cols; 

/* for printing out overlapping segments */
        ((struct quaddata *)(tree->data))->x_orig = xmn-distx; 
        ((struct quaddata *)(tree->data))->y_orig = ymn-disty; 
        ((struct quaddata *)(tree->data))->xmax = xmx+distx; 
        ((struct quaddata *)(tree->data))->ymax = ymx+disty; 

        data->x_orig = xmn;
        data->y_orig = ymn;
        data->xmax = xmx;
        data->ymax = ymx;

        if (!matrix) {
          if (!(matrix = G_alloc_matrix(params->KMAX2+1,params->KMAX2+1))) {
            fprintf(stderr,"Cannot allocate memory for matrix\n");
            return -1;
          }
        }
        if (!indx) {
          if (!(indx = G_alloc_ivector(params->KMAX2+1))) {
            fprintf(stderr,"Cannot allocate memory for indx\n");
            return -1;
          }
        }
        if (!b) {
          if (!(b = G_alloc_vector(params->KMAX2+3))) {
            fprintf(stderr,"Cannot allocate memory for b\n");
            return -1;
          }
        }
	if (!(point = (struct triple *) G_malloc (sizeof (struct triple) * data->n_points)))
	{
		fprintf (stderr, "Cannot allocate memory for point\n");
		return -1;
	}
/*normalize the data so that the side of average segment is about 1m */
        for (i = 0; i < data->n_points; i++)
        {
	  data->points[i].x = (data->points[i].x-data->x_orig) / dnorm;
	  point[i].x = data->points[i].x;/*cv stuff*/
	  data->points[i].y = (data->points[i].y-data->y_orig) / dnorm;
	  point[i].y = data->points[i].y;/*cv stuff*/
	  point[i].z = data->points[i].z;/*cv stuff*/

/* commented out by Helena january 1997 as this is not necessary
 	  data->points[i].z = data->points[i].z / dnorm;
          if (params->rsm < 0.) data->points[i].sm = data->points[i].sm / dnorm;
*/
        }
	
        /* cv stuff */
    if (params->cv)
            m_skip = data->n_points;
    else
            m_skip = 1;

 for(skip_index=0;skip_index<m_skip;skip_index++) {
      j = 0;
      skip_point.x = point[skip_index].x;
      skip_point.y = point[skip_index].y;
      skip_point.z = point[skip_index].z;
      for (k=0;k<m_skip;k++) {
        if (k!=skip_index && params->cv) {
          data->points[j].x = point[k].x;
          data->points[j].y = point[k].y;
          data->points[j].z = point[k].z;
          j++;
        }
     }

        if (!params->cv){
        if (params->matrix_create(params,data->points,data->n_points,
                                       matrix,indx) < 0)  return -1;
        }
        else {
                if (params->matrix_create(params,data->points,data->n_points-1,
                                        matrix,indx) < 0)  return -1;
        }

        if (!params->cv) {
        for (i = 0; i < data->n_points; i++)
          b[i+1] = data->points[i].z;
        b[0] = 0.;
        G_lubksb(matrix,data->n_points+1,indx,b);
        params->check_points(params,data,b,ertot,zmin,dnorm,skip_point);
        } else
        {
                for (i = 0; i < data->n_points-1; i++)
                  b[i+1] = data->points[i].z;
                  b[0] = 0.;
                  G_lubksb(matrix,data->n_points,indx,b);
                  params->check_points(params,data,b,ertot,zmin,dnorm,skip_point);
        }

        } /*cv loop */
        
	if(!params->cv)
        if ((params->Tmp_fd_z!=NULL)||(params->Tmp_fd_dx!=NULL)||
            (params->Tmp_fd_dy!=NULL)||(params->Tmp_fd_xx!=NULL)||
            (params->Tmp_fd_yy!=NULL)||(params->Tmp_fd_xy!=NULL)) {

          if(params->grid_calc(params,data,bitmask,
            zmin,zmax,zminac,zmaxac,gmin,gmax,
            c1min,c1max,c2min,c2max,ertot,b,offset1,dnorm)<0)
              return -1;
        }

	/* show after to catch 100% */
	cursegm++;
if (totsegm < cursegm) fprintf(stderr,"%d %d\n",totsegm,cursegm);
        if (totsegm != 0)
        {
          G_percent (cursegm, totsegm, 1);
        }
/*
        G_free_matrix(matrix);
        G_free_ivector(indx);
        G_free_vector(b);
*/
        free(data->points);
        free(data);
    }
    return 1;
}

static double smallest_segment (struct multtree *tree, int n_leafs)
{
    static int first_time = 1;
    int ii;
    static double minside;
    double side;

    if (tree == NULL)
	return 0;
    if (tree->data == NULL)
	return 0;
    if (tree->leafs != NULL) 
    {
      for (ii=0;ii<n_leafs;ii++)  {
        side = smallest_segment(tree->leafs[ii],n_leafs);
        if (first_time) {
          minside = side;
          first_time = 0;
/*          fprintf(stderr, "FIRST,side=%lf, minside=%lf,\n", side, minside); */
        }
        if (side < minside) minside = side;
/*        fprintf(stderr, "SEC side=%lf, minside=%lf,\n", side, minside); */
      }
    }
    else
    {
      side = ((struct quaddata *)(tree->data))->xmax -
             ((struct quaddata *)(tree->data))->x_orig;
      return side;
    }
/*    fprintf(stderr, "OUT side=%lf, minside=%lf,\n", side, minside);*/
    return minside;
}



