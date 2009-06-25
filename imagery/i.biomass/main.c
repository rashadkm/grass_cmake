
/****************************************************************************
 *
 * MODULE:       i.biomass
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a map of biomass growth
 *               
 *
 * COPYRIGHT:    (C) 2002-2009 by the GRASS Development Team
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

double solar_day(double lat, double doy, double tsw);
double biomass(double apar, double solar_day, double evap_fr,
        double light_use_ef);

int main(int argc, char *argv[]) 
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4, *input5, *input6;
    struct Option *output1;
    struct History history;	/*metadata */
    struct Colors colors;
    char *result1;	/*output raster name */
    int infd_fpar, infd_luf, infd_lat;
    int infd_doy, infd_tsw, infd_wa;
    int outfd1;
    char *fpar, *luf, *lat, *doy, *tsw, *wa;
    void *inrast_fpar, *inrast_luf, *inrast_lat;
    void *inrast_doy, *inrast_tsw, *inrast_wa;
    DCELL * outrast1;
    /************************************/ 
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("biomass"));
    G_add_keyword(_("fpar"));
    G_add_keyword(_("yield"));
    module->description =
	_("Computes biomass growth, precursor of crop yield calculation");
    
    /* Define the different options */ 
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = "fpar";
    input1->description = _("Name of fPAR raster map");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = "luf";
    input2->description =
	_("Name of light use efficiency raster map (UZB:cotton=1.9)");

    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = "lat";
    input3->description = _("Name of degree latitude raster map [dd.ddd]");

    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = "doy";
    input4->description = _("Name of Day of Year raster map [1-366]");

    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = "tsw";
    input5->description =
	_("Name of single-way transmissivity raster map [0.0-1.0]");

    input6 = G_define_standard_option(G_OPT_R_INPUT);
    input6->key = "wa";
    input6->description =
	_("Value of water availability raster map [0.0-1.0]");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description =
	_("Name for output daily biomass growth raster map [kg/ha/d]");
    
    /********************/ 
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    fpar = input1->answer;
    luf = input2->answer;
    lat = input3->answer;
    doy = input4->answer;
    tsw = input5->answer;
    wa = input6->answer;
    result1 = output1->answer;
    
    /***************************************************/ 
    if ((infd_fpar = Rast_open_cell_old(fpar, "")) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), fpar);
    inrast_fpar = Rast_allocate_d_buf();

    if ((infd_luf = Rast_open_cell_old(luf, "")) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), luf);
    inrast_luf = Rast_allocate_d_buf();
    
    if ((infd_lat = Rast_open_cell_old(lat, "")) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), lat);
    inrast_lat = Rast_allocate_d_buf();
    
    if ((infd_doy = Rast_open_cell_old(doy, "")) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), doy);
    inrast_doy = Rast_allocate_d_buf();

    if ((infd_tsw = Rast_open_cell_old(tsw, "")) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), tsw);
    inrast_tsw = Rast_allocate_d_buf();
    
    if ((infd_wa = Rast_open_cell_old(wa, "")) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), wa);
    inrast_wa = Rast_allocate_d_buf();
    
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast1 = Rast_allocate_d_buf();
    
    /* Create New raster files */ 
    if ((outfd1 = Rast_open_raster_new(result1, DCELL_TYPE)) < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), result1);
     
    /* Process pixels */ 
    for (row = 0; row < nrows; row++)
    {
	DCELL d;
	DCELL d_fpar;
	DCELL d_luf;
	DCELL d_lat;
	DCELL d_doy;
	DCELL d_tsw;
	DCELL d_solar;
	DCELL d_wa;
	G_percent(row, nrows, 2);
	
        /* read input maps */ 
        if (Rast_get_d_raster_row(infd_fpar, inrast_fpar, row)< 0)
	    G_fatal_error(_("Unable to read from <%s> row %d"),fpar,row);
	if (Rast_get_d_raster_row(infd_luf,inrast_luf,row)<0)
	    G_fatal_error(_("Unable to read from <%s> row %d"),luf,row);
	if (Rast_get_d_raster_row(infd_lat, inrast_lat, row) < 0)
	    G_fatal_error(_("Unable to read from <%s> row %d"),lat,row);
	if (Rast_get_d_raster_row(infd_doy, inrast_doy, row) < 0)
	    G_fatal_error(_("Unable to read from <%s> row %d"),doy,row);
	if (Rast_get_d_raster_row(infd_tsw, inrast_tsw, row) < 0)
	    G_fatal_error(_("Unable to read from <%s> row %d"),tsw,row);
	if (Rast_get_d_raster_row(infd_wa,inrast_wa,row)<0)
	    G_fatal_error(_("Unable to read from <%s> row %d"),wa,row); 
        /*process the data */ 
        for (col = 0; col < ncols; col++)
        {
            d_fpar = ((DCELL *) inrast_fpar)[col];
            d_luf = ((DCELL *) inrast_luf)[col];
            d_lat = ((DCELL *) inrast_lat)[col];
            d_doy = ((DCELL *) inrast_doy)[col];
            d_tsw = ((DCELL *) inrast_tsw)[col];
            d_wa = ((DCELL *) inrast_wa)[col];
	    if (Rast_is_d_null_value(&d_fpar) ||
		 Rast_is_d_null_value(&d_luf) ||
		 Rast_is_d_null_value(&d_lat) || 
                 Rast_is_d_null_value(&d_doy) ||
		 Rast_is_d_null_value(&d_tsw) ||
		 Rast_is_d_null_value(&d_wa)) 
		Rast_set_d_null_value(&outrast1[col], 1);
	    else {
		d_solar = solar_day(d_lat, d_doy, d_tsw);
		d = biomass(d_fpar,d_solar,d_wa,d_luf);
		outrast1[col] = d;
	    }
        }
	if (Rast_put_d_raster_row(outfd1, outrast1) < 0)
	    G_fatal_error(_("Failed writing raster map <%s>"), result1);
    }
    
    /* Color table for biomass */ 
    Rast_init_colors(&colors);
    Rast_add_color_rule(0, 0, 0, 0, 1, 255, 255, 255, &colors);
    G_free(inrast_fpar);
    G_free(inrast_luf);
    G_free(inrast_lat);
    G_free(inrast_doy);
    G_free(inrast_tsw);
    G_free(inrast_wa);
    G_free(outrast1);
    Rast_close_cell(infd_fpar);
    Rast_close_cell(infd_luf);
    Rast_close_cell(infd_lat);
    Rast_close_cell(infd_doy);
    Rast_close_cell(infd_tsw);
    Rast_close_cell(infd_wa);
    Rast_close_cell(outfd1);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);

    exit(EXIT_SUCCESS);
}


