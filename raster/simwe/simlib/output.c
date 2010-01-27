/* output.c (simlib), 20.nov.2002, JH */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
/* #include <grass/site.h> */
#include <grass/bitmap.h>
#include <grass/linkm.h>

#include <grass/waterglobs.h>
#include <grass/glocale.h>

int output_data(int tt, double ft)
{

    FCELL *cell6, *cell7, *cell8;
    FCELL *cell14, *cell15, *cell16;
    int fd6, fd7, fd8;
    int fd14, fd15, fd16;
    int i, iarc, j;
    float gsmax = 0, dismax = 0., gmax = 0., ermax = -1.e+12, ermin = 1.e+12;
    struct Colors colors;
    struct History hist, hist1;	/* hist2, hist3, hist4, hist5 */
    char *depth0 = NULL, *disch0 = NULL, *err0 = NULL;
    char *conc0 = NULL, *flux0 = NULL;
/*    char *erdep0 = NULL, *outwalk0 = NULL; */
    char *erdep0 = NULL;
    char *mapst = NULL;
    char *type;
    char buf[256];
    int ndigit;
    FCELL dat1, dat2;
    float a1, a2;
/*    Site_head walkershead;
    Site *sd;
*/


    ndigit = 2;
    if (timesec >= 10)
	ndigit = 3;
    if (timesec >= 100)
	ndigit = 4;
    if (timesec >= 1000)
	ndigit = 5;
    if (timesec >= 10000)
	ndigit = 6;

/*
    if (outwalk) {
	if (ts == 1) {
	    sprintf(buf, "%s%.*d", outwalk, ndigit, tt);
	    outwalk0 = G_store(buf);
	    fdoutwalk = G_fopen_sites_new(outwalk0);
	}
	else
	    fdoutwalk = G_fopen_sites_new(outwalk);

	if (fdoutwalk == NULL)
	    G_fatal_error("Cannot open %s", outwalk);
	else {
	    char buf[GNAME_MAX + 40];

	    if (NULL == (sd = G_site_new_struct(-1, 2, 0, 1)))
		G_fatal_error("memory allocation failed for site");

	    if (ts == 1)
		walkershead.name = outwalk0;
	    else
		walkershead.name = outwalk;

	    sprintf(buf, "output walkers of %s [raster]", depth);
	    walkershead.desc = G_store(buf);
	    walkershead.time = NULL;
	    walkershead.stime = NULL;
	    walkershead.labels = NULL;
	    walkershead.form = NULL;

	    G_site_put_head(fdoutwalk, &walkershead);

	    for (i = 0; i < nstack; i++) {
		sd->east = (float)stack[i][1];
		sd->north = (float)stack[i][2];
		sd->fcat = (float)stack[i][3];
		G_site_put(fdoutwalk, sd);
	    }
	}
    }
*/
    if (depth) {
	cell6 = Rast_allocate_f_buf();
	if (ts == 1) {
	    sprintf(buf, "%s.%.*d", depth, ndigit, tt);
	    depth0 = G_store(buf);
	    fd6 = Rast_open_fp_new(depth0);
	}
	else
	    fd6 = Rast_open_fp_new(depth);
    }

    if (disch) {
	cell7 = Rast_allocate_f_buf();
	if (ts == 1) {
	    sprintf(buf, "%s.%.*d", disch, ndigit, tt);
	    disch0 = G_store(buf);
	    fd7 = Rast_open_fp_new(disch0);
	}
	else
	    fd7 = Rast_open_fp_new(disch);
    }

    if (err) {
	cell8 = Rast_allocate_f_buf();
	if (ts == 1) {
	    sprintf(buf, "%s.%.*d", err, ndigit, tt);
	    err0 = G_store(buf);
	    fd8 = Rast_open_fp_new(err0);
	}
	else
	    fd8 = Rast_open_fp_new(err);
    }


    if (conc) {
	cell14 = Rast_allocate_f_buf();
	if (ts == 1) {
	    sprintf(buf, "%s.%.*d", conc, ndigit, tt);
	    conc0 = G_store(buf);
	    fd14 = Rast_open_fp_new(conc0);
	}
	else
	    fd14 = Rast_open_fp_new(conc);
    }

    if (flux) {
	cell15 = Rast_allocate_f_buf();
	if (ts == 1) {
	    sprintf(buf, "%s.%.*d", flux, ndigit, tt);
	    flux0 = G_store(buf);
	    fd15 = Rast_open_fp_new(flux0);
	}
	else
	    fd15 = Rast_open_fp_new(flux);
    }

    if (erdep) {
	cell16 = Rast_allocate_f_buf();
	if (ts == 1) {
	    sprintf(buf, "%s.%.*d", erdep, ndigit, tt);
	    erdep0 = G_store(buf);
	    fd16 = Rast_open_fp_new(erdep0);
	}
	else
	    fd16 = Rast_open_fp_new(erdep);
    }


    Rast_set_window(&cellhd);

    if (my != G_window_rows())
	G_fatal_error("OOPS: rows changed from %d to %d\n", mx,
		      G_window_rows());
    if (mx != G_window_cols())
	G_fatal_error("OOPS: cols changed from %d to %d\n", my,
		      G_window_cols());

    for (iarc = 0; iarc < my; iarc++) {
	i = my - iarc - 1;
	if (depth) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || gama[i][j] == UNDEF)
		    Rast_set_f_null_value(cell6 + j, 1);
		else {
		    a1 = pow(gama[i][j], 3. / 5.);
		    cell6[j] = (FCELL) a1;	/* add conv? */
		    gmax = amax1(gmax, a1);
		}
	    }
	    Rast_put_f_row(fd6, cell6);
	}

	if (disch) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || gama[i][j] == UNDEF ||
		    cchez[i][j] == UNDEF)
		    Rast_set_f_null_value(cell7 + j, 1);
		else {
		    a2 = step * gama[i][j] * cchez[i][j];	/* cchez incl. sqrt(sinsl) */
		    cell7[j] = (FCELL) a2;	/* add conv? */
		    dismax = amax1(dismax, a2);
		}
	    }
	    Rast_put_f_row(fd7, cell7);
	}

	if (err) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || gammas[i][j] == UNDEF)
		    Rast_set_f_null_value(cell8 + j, 1);
		else {
		    cell8[j] = (FCELL) gammas[i][j];
		    gsmax = amax1(gsmax, gammas[i][j]);	/* add conv? */
		}
	    }
	    Rast_put_f_row(fd8, cell8);
	}


	if (conc) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || gama[i][j] == UNDEF)
		    Rast_set_f_null_value(cell14 + j, 1);
		else {
		    cell14[j] = (FCELL) gama[i][j];
		    /*      gsmax = amax1(gsmax, gama[i][j]); */
		}
	    }
	    Rast_put_f_row(fd14, cell14);
	}


	if (flux) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || gama[i][j] == UNDEF ||
		    slope[i][j] == UNDEF)
		    Rast_set_f_null_value(cell15 + j, 1);
		else {
		    a2 = gama[i][j] * slope[i][j];
		    cell15[j] = (FCELL) a2;
		    dismax = amax1(dismax, a2);
		}
	    }
	    Rast_put_f_row(fd15, cell15);
	}


	if (erdep) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || er[i][j] == UNDEF)
		    Rast_set_f_null_value(cell16 + j, 1);
		else {
		    cell16[j] = (FCELL) er[i][j];
		    ermax = amax1(ermax, er[i][j]);
		    ermin = amin1(ermin, er[i][j]);
		}
	    }
	    Rast_put_f_row(fd16, cell16);
	}

    }

    if (depth)
	Rast_close(fd6);
    if (disch)
	Rast_close(fd7);
    if (err)
	Rast_close(fd8);
    if (conc)
	Rast_close(fd14);
    if (flux)
	Rast_close(fd15);
    if (erdep)
	Rast_close(fd16);

    if (depth) {

	Rast_init_colors(&colors);

	dat1 = (FCELL) 0.;
	dat2 = (FCELL) 0.001;
	Rast_add_f_color_rule(&dat1, 255, 255, 255, &dat2, 255, 255, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.05;
	Rast_add_f_color_rule(&dat1, 255, 255, 0, &dat2, 0, 255, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.1;
	Rast_add_f_color_rule(&dat1, 0, 255, 255, &dat2, 0, 127, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.5;
	Rast_add_f_color_rule(&dat1, 0, 127, 255, &dat2, 0, 0, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) gmax;
	Rast_add_f_color_rule(&dat1, 0, 0, 255, &dat2, 0, 0, 0, &colors);


	if (ts == 1) {
	    if ((mapst = G_find_file("fcell", depth0, "")) == NULL)
		G_fatal_error("cannot find file %s", depth0);
	    Rast_write_colors(depth0, mapst, &colors);
	    Rast_quantize_fp_map_range(depth0, mapst, 0., (FCELL) gmax, 0,
				    (CELL) gmax);
	    Rast_free_colors(&colors);
	}
	else {
	    if ((mapst = G_find_file("fcell", depth, "")) == NULL)
		G_fatal_error("cannot find file %s", depth);
	    Rast_write_colors(depth, mapst, &colors);
	    Rast_quantize_fp_map_range(depth, mapst, 0., (FCELL) gmax, 0,
				    (CELL) gmax);
	    Rast_free_colors(&colors);
	}

    }

    if (disch) {

	Rast_init_colors(&colors);

	dat1 = (FCELL) 0.;
	dat2 = (FCELL) 0.0005;
	Rast_add_f_color_rule(&dat1, 255, 255, 255, &dat2, 255, 255, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.005;
	Rast_add_f_color_rule(&dat1, 255, 255, 0, &dat2, 0, 255, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.05;
	Rast_add_f_color_rule(&dat1, 0, 255, 255, &dat2, 0, 127, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.1;
	Rast_add_f_color_rule(&dat1, 0, 127, 255, &dat2, 0, 0, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) dismax;
	Rast_add_f_color_rule(&dat1, 0, 0, 255, &dat2, 0, 0, 0, &colors);

	if (ts == 1) {
	    if ((mapst = G_find_file("cell", disch0, "")) == NULL)
		G_fatal_error("cannot find file %s", disch0);
	    Rast_write_colors(disch0, mapst, &colors);
	    Rast_quantize_fp_map_range(disch0, mapst, 0., (FCELL) dismax, 0,
				    (CELL) dismax);
	    Rast_free_colors(&colors);
	}
	else {

	    if ((mapst = G_find_file("cell", disch, "")) == NULL)
		G_fatal_error("cannot find file %s", disch);
	    Rast_write_colors(disch, mapst, &colors);
	    Rast_quantize_fp_map_range(disch, mapst, 0., (FCELL) dismax, 0,
				    (CELL) dismax);
	    Rast_free_colors(&colors);
	}
    }

    if (flux) {

	Rast_init_colors(&colors);

	dat1 = (FCELL) 0.;
	dat2 = (FCELL) 0.001;
	Rast_add_f_color_rule(&dat1, 255, 255, 255, &dat2, 255, 255, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.1;
	Rast_add_f_color_rule(&dat1, 255, 255, 0, &dat2, 255, 127, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 1.;
	Rast_add_f_color_rule(&dat1, 255, 127, 0, &dat2, 191, 127, 63,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) dismax;
	Rast_add_f_color_rule(&dat1, 191, 127, 63, &dat2, 0, 0, 0,
				  &colors);

	if (ts == 1) {
	    if ((mapst = G_find_file("cell", flux0, "")) == NULL)
		G_fatal_error("cannot find file %s", flux0);
	    Rast_write_colors(flux0, mapst, &colors);
	    Rast_quantize_fp_map_range(flux0, mapst, 0., (FCELL) dismax, 0,
				    (CELL) dismax);
	    Rast_free_colors(&colors);
	}
	else {

	    if ((mapst = G_find_file("cell", flux, "")) == NULL)
		G_fatal_error("cannot find file %s", flux);
	    Rast_write_colors(flux, mapst, &colors);
	    Rast_quantize_fp_map_range(flux, mapst, 0., (FCELL) dismax, 0,
				    (CELL) dismax);
	    Rast_free_colors(&colors);
	}
    }


    if (erdep) {

	Rast_init_colors(&colors);

	dat1 = (FCELL) ermax;
	dat2 = (FCELL) 0.1;
	Rast_add_f_color_rule(&dat1, 0, 0, 0, &dat2, 0, 0, 255, &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.01;
	Rast_add_f_color_rule(&dat1, 0, 0, 255, &dat2, 0, 191, 191,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.0001;
	Rast_add_f_color_rule(&dat1, 0, 191, 191, &dat2, 170, 255, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.;
	Rast_add_f_color_rule(&dat1, 170, 255, 255, &dat2, 255, 255, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) - 0.0001;
	Rast_add_f_color_rule(&dat1, 255, 255, 255, &dat2, 255, 255, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) - 0.01;
	Rast_add_f_color_rule(&dat1, 255, 255, 0, &dat2, 255, 127, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) - 0.1;
	Rast_add_f_color_rule(&dat1, 255, 127, 0, &dat2, 255, 0, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) ermin;
	Rast_add_f_color_rule(&dat1, 255, 0, 0, &dat2, 255, 0, 255,
				  &colors);

	if (ts == 1) {
	    if ((mapst = G_find_file("cell", erdep0, "")) == NULL)
		G_fatal_error("cannot find file %s", erdep0);
	    Rast_write_colors(erdep0, mapst, &colors);
	    Rast_quantize_fp_map_range(erdep0, mapst, (FCELL) ermin,
				    (FCELL) ermax, (CELL) ermin,
				    (CELL) ermax);
	    Rast_free_colors(&colors);

	    type = "raster";
	    Rast_short_history(erdep0, type, &hist1);
	    sprintf(hist1.edhist[0], "The sediment flux file is %s", flux0);
	    hist1.edlinecnt = 1;
	    Rast_write_history(erdep0, &hist1);
	}
	else {

	    if ((mapst = G_find_file("cell", erdep, "")) == NULL)
		G_fatal_error("cannot find file %s", erdep);
	    Rast_write_colors(erdep, mapst, &colors);
	    Rast_quantize_fp_map_range(erdep, mapst, (FCELL) ermin,
				    (FCELL) ermax, (CELL) ermin,
				    (CELL) ermax);
	    Rast_free_colors(&colors);

	    type = "raster";
	    Rast_short_history(erdep, type, &hist1);
	    sprintf(hist1.edhist[0], "The sediment flux file is %s", flux);
	    hist1.edlinecnt = 1;
	    Rast_write_history(erdep, &hist1);
	}
    }

    /* history section */

    if (depth) {
	type = "raster";
	if (ts == 0) {
	    mapst = G_find_file("cell", depth, "");
	    if (mapst == NULL) {
		G_warning("File [%s] not found", depth);
		return -1;
	    }
	    Rast_short_history(depth, type, &hist);
	}
	else
	    Rast_short_history(depth0, type, &hist);

	/*    fprintf (stdout, "\n history initiated\n");
	   fflush(stdout); */

	sprintf(hist.edhist[0],
		"init.walk=%d, maxwalk=%d, remaining walkers=%d", nwalk,
		maxwa, nwalka);
	sprintf(hist.edhist[1], "duration (sec.)=%d, time-serie iteration=%d",
		timesec, tt);

	sprintf(hist.edhist[2], "written walkers=%d, deltap=%f, mean vel.=%f",
		lwwfin, deltap, vmean);

	sprintf(hist.edhist[3], "mean source (si)=%e, mean infil=%e", si0,
		infmean);

	sprintf(hist.datsrc_1, "input files: %s %s %s", elevin, dxin, dyin);
	sprintf(hist.datsrc_2, "input files: %s %s %s", rain, infil, manin);
	hist.edlinecnt = 4;

	Rast_command_history(&hist);

	if (ts == 1)
	    Rast_write_history(depth0, &hist);
	else
	    Rast_write_history(depth, &hist);
    }

    if (disch) {
	type = "raster";
	if (ts == 0) {
	    mapst = G_find_file("cell", disch, "");
	    if (mapst == NULL)
		G_fatal_error("file [%s] not found\n", disch);
	    Rast_short_history(disch, type, &hist);
	}
	else
	    Rast_short_history(disch0, type, &hist);

	/*    fprintf (stdout, "\n history initiated\n");
	   fflush(stdout); */

	sprintf(hist.edhist[0],
		"init.walkers=%d, maxwalk=%d, rem. walkers=%d", nwalk, maxwa,
		nwalka);
	sprintf(hist.edhist[1], "duration (sec.)=%d, time-serie iteration=%d",
		timesec, tt);

	sprintf(hist.edhist[2], "written walkers=%d, deltap=%f, mean vel.=%f",
		lwwfin, deltap, vmean);

	sprintf(hist.edhist[3], "mean source (si)=%e, mean infil=%e", si0,
		infmean);

	sprintf(hist.datsrc_1, "input files: %s %s %s", elevin, dxin, dyin);
	sprintf(hist.datsrc_2, "input files: %s %s %s", rain, infil, manin);
	hist.edlinecnt = 4;

	Rast_command_history(&hist);

	if (ts == 1)
	    Rast_write_history(disch0, &hist);
	else
	    Rast_write_history(disch, &hist);
    }

    if (flux) {
	type = "raster";
	if (ts == 0) {
	    mapst = G_find_file("cell", flux, "");
	    if (mapst == NULL)
		G_fatal_error("file [%s] not found\n", flux);
	    Rast_short_history(flux, type, &hist);
	}
	else
	    Rast_short_history(flux0, type, &hist);

	/*    fprintf (stdout, "\n history initiated\n");
	   fflush(stdout); */

	sprintf(hist.edhist[0],
		"init.walk=%d, maxwalk=%d, remaining walkers=%d", nwalk,
		maxwa, nwalka);
	sprintf(hist.edhist[1], "duration (sec.)=%d, time-serie iteration=%d",
		timesec, tt);

	sprintf(hist.edhist[2], "written walkers=%d, deltap=%f, mean vel.=%f",
		lwwfin, deltap, vmean);

	sprintf(hist.edhist[3], "mean source (si)=%f", si0);

	sprintf(hist.datsrc_1, "input files: %s %s %s", wdepth, dxin, dyin);
	sprintf(hist.datsrc_2, "input files: %s %s %s %s", manin, detin,
		tranin, tauin);

	hist.edlinecnt = 4;

	Rast_command_history(&hist);

	if (ts == 1)
	    Rast_write_history(flux0, &hist);
	else
	    Rast_write_history(flux, &hist);
    }

    return 1;
}


int output_et()
{

    FCELL *cell13, *cell17;
    int fd13, fd17;
    int i, iarc, j;
    float etmax = -1.e+12, etmin = 1.e+12;
    float trc;
    struct Colors colors;
    char *mapst = NULL;

    /*   char buf[256]; */
    FCELL dat1, dat2;

    /*   float a1,a2; */



    if (et) {
	cell17 = Rast_allocate_f_buf();
	/*      if (ts == 1) {
	   sprintf(buf,"%s.%.*d",et,ndigit,tt);
	   et0 = G_store(buf);
	   fd17 = Rast_open_fp_new (et0);
	   }
	   else */
	fd17 = Rast_open_fp_new(et);
    }

    if (tc) {
	cell13 = Rast_allocate_f_buf();
	/*   if (ts == 1) {
	   sprintf(buf,"%s.%.*d",tc,ndigit,tt);
	   tc0 = G_store(buf);
	   fd13 = Rast_open_fp_new (tc0);
	   }
	   else */
	fd13 = Rast_open_fp_new(tc);
    }


    Rast_set_window(&cellhd);

    if (my != G_window_rows())
	G_fatal_error("OOPS: rows changed from %d to %d\n", mx,
		      G_window_rows());
    if (mx != G_window_cols())
	G_fatal_error("OOPS: cols changed from %d to %d\n", my,
		      G_window_cols());

    for (iarc = 0; iarc < my; iarc++) {
	i = my - iarc - 1;
	if (et) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || er[i][j] == UNDEF)
		    Rast_set_f_null_value(cell17 + j, 1);
		else {
		    cell17[j] = (FCELL) er[i][j];	/* add conv? */
		    etmax = amax1(etmax, er[i][j]);
		    etmin = amin1(etmin, er[i][j]);
		}
	    }
	    Rast_put_f_row(fd17, cell17);
	}

	if (tc) {
	    for (j = 0; j < mx; j++) {
		if (zz[i][j] == UNDEF || sigma[i][j] == UNDEF ||
		    si[i][j] == UNDEF)
		    Rast_set_f_null_value(cell13 + j, 1);
		else {
		    if (sigma[i][j] == 0.)
			trc = 0.;
		    else
			trc = si[i][j] / sigma[i][j];
		    cell13[j] = (FCELL) trc;
		    /*  gsmax = amax1(gsmax, trc); */
		}
	    }
	    Rast_put_f_row(fd13, cell13);
	}
    }


    if (tc)
	Rast_close(fd13);

    if (et)
	Rast_close(fd17);

    if (et) {

	Rast_init_colors(&colors);

	dat1 = (FCELL) etmax;
	dat2 = (FCELL) 0.1;
	Rast_add_f_color_rule(&dat1, 0, 0, 0, &dat2, 0, 0, 255, &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.01;
	Rast_add_f_color_rule(&dat1, 0, 0, 255, &dat2, 0, 191, 191,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.0001;
	Rast_add_f_color_rule(&dat1, 0, 191, 191, &dat2, 170, 255, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) 0.;
	Rast_add_f_color_rule(&dat1, 170, 255, 255, &dat2, 255, 255, 255,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) - 0.0001;
	Rast_add_f_color_rule(&dat1, 255, 255, 255, &dat2, 255, 255, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) - 0.01;
	Rast_add_f_color_rule(&dat1, 255, 255, 0, &dat2, 255, 127, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) - 0.1;
	Rast_add_f_color_rule(&dat1, 255, 127, 0, &dat2, 255, 0, 0,
				  &colors);
	dat1 = dat2;
	dat2 = (FCELL) etmin;
	Rast_add_f_color_rule(&dat1, 255, 0, 0, &dat2, 255, 0, 255,
				  &colors);

	/*    if (ts == 1) {
	   if ((mapst = G_find_file("cell", et0, "")) == NULL)
	   G_fatal_error ("cannot find file %s", et0);
	   Rast_write_colors(et0, mapst, &colors);
	   Rast_quantize_fp_map_range(et0,mapst,(FCELL)etmin,(FCELL)etmax,(CELL)etmin,(CELL)etmax);
	   Rast_free_colors(&colors);
	   }
	   else { */

	if ((mapst = G_find_file("cell", et, "")) == NULL)
	    G_fatal_error("cannot find file %s", et);
	Rast_write_colors(et, mapst, &colors);
	Rast_quantize_fp_map_range(et, mapst, (FCELL) etmin, (FCELL) etmax,
				(CELL) etmin, (CELL) etmax);
	Rast_free_colors(&colors);
	/*  } */
    }

    return 1;
}
