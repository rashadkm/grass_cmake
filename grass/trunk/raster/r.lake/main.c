/****************************************************************************
 *
 * MODULE:       r.lake
 *
 * AUTHOR(S):    Maris Nartiss - maris.nartiss gmail.com
 *               with hints from friendly GRASS dev team
 *
 * PURPOSE:      Fills lake with water at given height above DEM.
 *               As seed You can use already existing map or
 *               X,Y coordinates.
 *
 * COPYRIGHT:    (C) 2005-2006 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *  TODO:        - Option to create 3D output;
 *               - Test with lat/lon location, feets and other crap;
 *               - In progress: Add different debug level messages;
 *               - In progress: Option to output resulting lake area and volume.
 *
 *  BUGS:        - Lake (seed) map cannot be negative!
 *               - Negative output (-n) maps cannot be used as input.
 *               - Code is not large file safe (i.e. array with whole map).
 *
 *****************************************************************************/

/* You are not allowed to remove this comment block. /M. Nartiss/
 *
 *  Kaarliit, shii programma ir veltiita Tev.
 *
 */
#include <stdio.h>
#include <stdlib.h>

#include <grass/gis.h>
#include <grass/glocale.h>

/* Saves map file from 2d array. NULL must be 0. Also meanwhile calculates area and volume. */
void save_map (FCELL **out, int out_fd, int rows, int cols, int flag, FCELL *min_depth, FCELL *max_depth, double *area, double *volume)
{
    int row, col;
    double cellsize = -1;

    G_debug(1,_("Saving new map"));

    if (G_begin_cell_area_calculations() == 0 || G_begin_cell_area_calculations() == 1) /* All cells have constant size... */
    {
      cellsize = G_area_of_cell_at_row(0);
    }
    G_debug(1,_("Cell area: %f"),cellsize);

    for (row = 0; row < rows; row++)
    {
      if (cellsize == -1) /* Get LatLon current rows cell size */
          cellsize = G_area_of_cell_at_row(row);
        for (col = 0; col < cols; col++)
        {
            if (flag == 1)  /* Create negative map */
              out[row][col] = 0 - out[row][col];
            if (out[row][col] == 0)
            {
              G_set_f_null_value(&out[row][col],1);
            }
            if (out[row][col] > 0 || out[row][col] < 0)
            {
              G_debug(5,"volume %f += cellsize %f  * value %f [%d,%d]",*volume, cellsize, out[row][col],row,col);
              *area += cellsize;
              *volume += cellsize * out[row][col];
            }

            /* Get min/max depth. Can be usefull ;) */
            if (out[row][col] > *max_depth)
              *max_depth = out[row][col];
            if (out[row][col] < *min_depth)
              *min_depth = out[row][col];
        }
        if (G_put_f_raster_row(out_fd, out[row])==-1)
          G_fatal_error(_("Error writing result map file!"));
        G_percent(row+1,rows,5);
    }
}

/* Check water presence in sliding window */
short is_near_water (FCELL window[][3])
{
    int i,j;

    /* If center is under water */
    if (window[1][1] > 0 )
        return 1;

    for (i = 0; i < 3; i++)
    {
        for (j = 0; j < 3; j++)
        {
            if (window[i][j] > 0)
                return 1;
        }
    }
    return 0;
}

/* Loads values into window around central cell */
void load_window_values (FCELL **in_rows, FCELL window[][3],
           int rows, int cols, int row, int col)
{
    int i,j;
    rows -= 1; /* Row'n'Col count starts from 0! */
    cols -= 1;

    for (i = -1; i < 2; i++)
    {
        if (row + i < 0 || row + i > rows)
        { /* First or last line... */
            window[i+1][0] = 0;
            window[i+1][1] = 0;
            window[i+1][2] = 0;
            continue;
        }
        else
        {
            for (j = -1; j < 2; j++)
            {
                if (col + j < 0 || col + j > cols - 1)
                { /* First or last column... */
                    window[i+1][j+1] = 0;
                    continue;
                }
                else
                { /* All normal cases... */
                    window[i+1][j+1] = in_rows[row+i][col+j];
                }
            }
        }
    }
}

int main(int argc, char *argv[])
{
    char *terrainmap, *seedmap, *lakemap, *mapset;
    int rows, cols, in_terran_fd, out_fd, lake_fd, row, col, pases, pass;
    int lastcount, curcount, start_col, start_row;
    double east, north, area = 0, volume = 0;
    FCELL **in_terran, **out_water, water_level, max_depth = 0, min_depth = 0;
    FCELL water_window[3][3];
    struct Option *tmap_opt, *smap_opt, *wlvl_opt, *lake_opt, *sdxy_opt;
    struct Flag *negative_flag, *overwrite_flag;
    struct GModule *module;
    struct Colors colr;
    struct Cell_head window;
    struct History history;

    module = G_define_module();
    module->description =
        _("Fills lake from seed at given level");

    tmap_opt = G_define_option() ;
    tmap_opt->key         = "dem";
    tmap_opt->key_desc    = "name";
    tmap_opt->description = _("Terrain raster map (DEM)");
    tmap_opt->type        = TYPE_STRING;
    tmap_opt->gisprompt   = "old,fcell,raster";
    tmap_opt->required    = YES;

    wlvl_opt = G_define_option() ;
    wlvl_opt->key         = "wl";
    wlvl_opt->description = _("Water level");
    wlvl_opt->type        = TYPE_DOUBLE;
    wlvl_opt->required    = YES;

    lake_opt = G_define_option() ;
    lake_opt->key         = "lake";
    lake_opt->key_desc    = "name";
    lake_opt->description = _("Output raster map with lake");
    lake_opt->type        = TYPE_STRING;
    lake_opt->gisprompt   = "new,fcell,raster";
    lake_opt->required    = NO;

    sdxy_opt = G_define_option() ;
    sdxy_opt->key         = "xy";
    sdxy_opt->description = _("Seed point coordinates");
    sdxy_opt->type        = TYPE_DOUBLE;
    sdxy_opt->key_desc    = "east,north";
    sdxy_opt->required    = NO;
    sdxy_opt->multiple    = NO;

    smap_opt = G_define_option() ;
    smap_opt->key         = "seed";
    smap_opt->key_desc    = "name";
    smap_opt->description = _("Raster map with seed (at least 1 cell > 0)");
    smap_opt->type        = TYPE_STRING;
    smap_opt->gisprompt   = "old,cell,raster";
    smap_opt->required    = NO;

    negative_flag = G_define_flag();
    negative_flag->key = 'n';
    negative_flag->description = _("Use negative depth values for lake raster map");

    overwrite_flag = G_define_flag();
    overwrite_flag->key = 'o';
    overwrite_flag->description = _("Overwrite seed map with result (lake) map");

    if (G_parser(argc, argv))  /* Returns 0 if successful, non-zero otherwise */
        exit(EXIT_FAILURE);

    G_gisinit(argv[0]);

    if (smap_opt->answer && sdxy_opt->answer)
      G_fatal_error(_("Both seed map and coordinates cannot be specifed"));

    if (!smap_opt->answer && !sdxy_opt->answer)
      G_fatal_error(_("Seed map or seed coordinates must be set!"));

    if (sdxy_opt->answer && !lake_opt->answer)
      G_fatal_error(_("Seed coordinates and output map lake= must be set!"));

    if (lake_opt->answer && overwrite_flag->answer)
      G_fatal_error(_("Both lake and overwrite cannot be specifed"));

    if (!lake_opt->answer && !overwrite_flag->answer)
      G_fatal_error(_("Output lake map or overwrite flag must be set!"));

    terrainmap = tmap_opt->answer;
    seedmap   = smap_opt->answer;
    sscanf(wlvl_opt->answer,"%f",&water_level);
    lakemap   = lake_opt->answer;

    /* If lakemap is set, write to it, else is set overwrite flag and we should write to seedmap. */
    if (lakemap)
    {
      lake_fd = G_open_raster_new(lakemap, 1);
      if (lake_fd < 0)
        G_fatal_error(_("Cannot write lake raster map <%s>!"), lakemap);
    }

    rows = G_window_rows();
    cols = G_window_cols();

    /* If we use x,y as seed... */
    if (sdxy_opt->answer)
    {
      G_get_window (&window);
      east = window.east;
      north= window.north;

      G_scan_easting  (sdxy_opt->answers[0], &east, G_projection());
      G_scan_northing (sdxy_opt->answers[1], &north, G_projection());
      start_col = (int)G_easting_to_col(east, &window);
      start_row = (int)G_northing_to_row(north, &window );

      if (start_row < 0 || start_row > rows ||
          start_col < 0 || start_col > cols)
          G_fatal_error(_("Seed point outside the current region."));
    }

    /* Open terran map */
    mapset = G_find_cell(terrainmap,"");
    if (mapset == NULL)
        G_fatal_error(_("Terrain raster map <%s> not found!"), terrainmap);

    in_terran_fd = G_open_cell_old(terrainmap,mapset);
    if (in_terran_fd < 0) G_fatal_error(_("Cannot open terrain raster map <%s@%s>!"), terrainmap,mapset);

    /* Open seed map */
    if (smap_opt->answer)
    {
      mapset = G_find_cell(seedmap,"");
      if (mapset == NULL)
          G_fatal_error(_("Seed map <%s> not found!"), seedmap);

      out_fd = G_open_cell_old(seedmap,mapset);
      if (out_fd < 0) G_fatal_error(_("Cannot open seed map <%s@%s>!"), seedmap, mapset);
    }

    /* Pointers to rows. Row = ptr to 'col' size array. */
    in_terran = G_malloc(rows * sizeof(FCELL *));
    out_water = G_malloc(rows * sizeof(FCELL *));
    if (in_terran == NULL || out_water == NULL)
         G_fatal_error(_("Failure to allocate memory for row pointers"));


    G_debug(1,_("Loading maps: "));
    /* foo_rows[row] == array with data (2d array). */
    for (row = 0; row < rows; row++)
    {
        in_terran[row] = G_malloc(cols * sizeof(FCELL *));
        out_water[row] = G_calloc(sizeof(FCELL *), cols);

        /* In newly created space load data from file.*/
        if (G_get_f_raster_row(in_terran_fd, in_terran[row], row)!=1)
          G_fatal_error(_("Error reading terrain raster map. Probably broken file."));

        if (smap_opt->answer)
          if (G_get_f_raster_row(out_fd, out_water[row], row)!=1)
            G_fatal_error(_("Error reading seed raster map. Probably broken file."));

        G_percent(row+1,rows,5);
    }

    /* Set seed point */
    if (sdxy_opt->answer)
      /* Check is water level higher than seed point */
      if (in_terran[start_row][start_col] >= water_level)
        G_fatal_error(_("Given water level at seed point is below earth surface. \n Increase water level or move seed point."));
      out_water[start_row][start_col] = 1;

    /* Close seed map for reading. */
    if (smap_opt->answer)
      G_close_cell(out_fd);

    /* Open output map for writing. */
    if (lakemap)
    {
      out_fd = lake_fd;
    }
    else
    {
      out_fd = G_open_raster_new(seedmap, 1);
      if (out_fd < 0) G_fatal_error(_("Cannot write lake raster map <%s@%s>!"), seedmap, mapset);
    }

    /* More pases are renudant. Real pases count is controled by altered cell count. */
    pases = (int) (rows*cols)/2;

    G_debug(1,_("Starting lake filling at level of %8.4f in %d passes. \nPercent done:"),water_level,pases);

    lastcount = 0;

    for (pass = 0; pass < pases; pass++)
    {
    G_debug(3,_("Pass: %d\n"),pass);
    curcount  = 0;
        /* Move from left upper corner to right lower corner. */
        for (row = 0; row < rows; row++)
        {
            for (col = 0; col < cols; col++)
            {
                /* Loading water data into window. */
                load_window_values (out_water, water_window, rows, cols, row, col);

                /* Cheking presence of water. */
                if (is_near_water(water_window)==1)
                {
                    if (in_terran[row][col] < water_level)
                    {
                        out_water[row][col] = water_level - in_terran[row][col];
                        curcount++;
                    }
                    else
                    {
                        out_water[row][col] = 0; /* Cell is higher than water level -> NULL. */
                    }
                }
            }
        }
        if (curcount == lastcount) break; /* We done. */
        lastcount = curcount;
        curcount  = 0;
        /* Move backwards - from lower right corner to upper left corner. */
        for (row = rows - 1; row >= 0; row--)
        {
            for (col = cols - 1; col >= 0; col--)
            {
                load_window_values (out_water, water_window, rows, cols, row, col);

                if (is_near_water(water_window)==1)
                {
                    if (in_terran[row][col] < water_level)
                    {
                        out_water[row][col] = water_level - in_terran[row][col];
                        curcount++;
                    }
                    else
                    {
                        out_water[row][col] = 0;
                    }
                }
            }
        }
        G_percent (pass+1,pases,10);
        if (curcount == lastcount) break; /* We done. */
        lastcount = curcount;
    } /*pases*/

    G_percent (pases,pases,10); /* Show 100%. */

    save_map(out_water, out_fd, rows, cols, negative_flag->answer, &min_depth, &max_depth, &area, &volume);

    G_message(_("Lake depth from %f to %f"),min_depth,max_depth);
    G_message(_("Lake area %f square meters"),area);
    G_message(_("Lake volume %f cubic meters"),volume);
    G_warning(_("Volume is correct only if lake depth (terrain raster map) is in meters"));

    /* Close all files. Lake map gets written only now. */
    G_close_cell(in_terran_fd);
    G_close_cell(out_fd);

    /* Add blue color gradient from light bank to dark depth */
    G_init_colors (&colr);
    if (negative_flag->answer == 1)
    {
      G_add_f_raster_color_rule (&max_depth, 0, 240, 255,
                                 &min_depth, 0, 50, 170, &colr);
    }
    else
    {
      G_add_f_raster_color_rule (&min_depth, 0, 240, 255,
                                 &max_depth, 0, 50, 170, &colr);
    }

    if (G_write_colors(lakemap, G_mapset(), &colr) != 1)
      G_fatal_error(_("Error writing color file for <%s@%s>!"),lakemap,G_mapset());

    G_short_history(lakemap, "raster", &history);
    G_command_history(&history);
    G_write_history(lakemap, &history);
    G_message(_("All done."));

    return EXIT_SUCCESS;
}

