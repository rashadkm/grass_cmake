
/****************************************************************************
 *
 * MODULE:       r.uslek
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Transforms percentage of texture (sand/clay/silt)
 *               into USDA 1951 (p209) soil texture classes and then
 *               into USLE soil erodibility factor (K) as an output
 *
 * COPYRIGHT:    (C) 2002-2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
     
    
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#define POLYGON_DIMENSION 20

double tex2usle_k(int texture, double om_in);
int prct2tex(double sand_input, double clay_input, double silt_input);
double point_in_triangle(double point_x, double point_y, double point_z,
			 double t1_x, double t1_y, double t1_z, double t2_x,
			 double t2_y, double t2_z, double t3_x, double t3_y,
			 double t3_z);
    
int main(int argc, char *argv[]) 
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4, *output1;
    struct History history;	/*metadata */

    char *result;		/*output raster name */
    int infd_psand, infd_psilt, infd_pclay, infd_pomat;
    int outfd;
    char *psand, *psilt, *pclay, *pomat;
    void *inrast_psand, *inrast_psilt, *inrast_pclay, *inrast_pomat;
    DCELL *outrast;
    
    /************************************/ 
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("soil"));
    G_add_keyword(_("erosion"));
    G_add_keyword(_("USLE"));
    module->description = _("USLE Soil Erodibility Factor (K)");
    
    /* Define the different options */ 
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = "psand";
    input1->description = _("Name of the Soil sand fraction map [0.0-1.0]");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = "pclay";
    input2->description = _("Name of the Soil clay fraction map [0.0-1.0]");

    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = "psilt";
    input3->description = _("Name of the Soil silt fraction map [0.0-1.0]");

    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = "pomat";
    input4->description = _("Name of the Soil Organic Matter map [0.0-1.0]");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->key = "usle_k";
    output1->description = _("Name of the output USLE K factor map [t.ha.hr/ha.MJ.mm]");

    /********************/ 
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    psand = input1->answer;
    pclay = input2->answer;
    psilt = input3->answer;
    pomat = input4->answer;
    result = output1->answer;
    
    /***************************************************/ 
    infd_psand = Rast_open_old(psand, "");
    inrast_psand = Rast_allocate_d_buf();
    
    infd_psilt = Rast_open_old(psilt, "");
    inrast_psilt = Rast_allocate_d_buf();
    
    infd_pclay = Rast_open_old(pclay, "");
    inrast_pclay = Rast_allocate_d_buf();
    
    infd_pomat = Rast_open_old(pomat, "");
    inrast_pomat = Rast_allocate_d_buf();
    /***************************************************/ 
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = Rast_allocate_d_buf();
    
    /* Create New raster files */ 
    outfd = Rast_open_new(result, DCELL_TYPE);
    
    /* Process pixels */ 
    for (row = 0; row < nrows; row++)
    {
	DCELL d;
	DCELL d_sand;
	DCELL d_clay;
	DCELL d_silt;
	DCELL d_om;
	G_percent(row, nrows, 2);
	
	/* read soil input maps */ 
	if (Rast_get_d_row(infd_psand, inrast_psand, row) < 0)
	    G_fatal_error(_("Unable to read raster map <%s> row %d"),
			  psand, row);
	if (Rast_get_d_row(infd_psilt, inrast_psilt, row) < 0)
	    G_fatal_error(_("Unable to read raster map <%s> row %d"),
			  psilt, row);
	if (Rast_get_d_row(infd_pclay, inrast_pclay, row) < 0)
	    G_fatal_error(_("Unable to read raster map <%s> row %d"),
			  pclay, row);
	if (Rast_get_d_row(infd_pomat, inrast_pomat, row) < 0)
	    G_fatal_error(_("Unable to read raster map <%s> row %d"),
			  pomat, row);
	
        /*process the data */ 
	for (col = 0; col < ncols; col++)
	{
	    d_sand = ((DCELL *) inrast_psand)[col];
	    d_silt = ((DCELL *) inrast_psilt)[col];
	    d_clay = ((DCELL *) inrast_pclay)[col];
            d_om = ((DCELL *) inrast_pomat)[col];
	    if (Rast_is_d_null_value(&d_sand) || 
                Rast_is_d_null_value(&d_clay) ||
		Rast_is_d_null_value(&d_silt)) 
		    Rast_set_d_null_value(&outrast[col], 1);
	    else {
                /***************************************/ 
		/* In case some map input not standard */
		if ((d_sand + d_clay + d_silt) != 1.0) 
		    Rast_set_d_null_value(&outrast[col], 1);
		/* if OM==NULL then make it 0.0 */
		else if (Rast_is_d_null_value(&d_om))
		    d_om = 0.0;	
		else {
                    /************************************/ 
		    /* convert to usle_k                */ 
		    d = (double)prct2tex(d_sand, d_clay, d_silt);
		    d = tex2usle_k((int)d, d_om);
		    outrast[col] = d;
                }
	    }
	}
	if (Rast_put_d_row(outfd, outrast) < 0)
	    G_fatal_error(_("Failed writing raster map <%s> row %d"),
			  result, row);
    }
    G_free(inrast_psand);
    G_free(inrast_psilt);
    G_free(inrast_pclay);
    G_free(inrast_pomat);
    Rast_close(infd_psand);
    Rast_close(infd_psilt);
    Rast_close(infd_pclay);
    Rast_close(infd_pomat);
    G_free(outrast);
    Rast_close(outfd);
    
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);
    
    exit(EXIT_SUCCESS);
}
