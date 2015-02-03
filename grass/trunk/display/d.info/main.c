/*
 ****************************************************************************
 *
 * MODULE:       d.info
 * AUTHOR(S):    Glynn Clements
 * PURPOSE:      Display information about the active display monitor
 * COPYRIGHT:    (C) 2004-2015 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <dirent.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/display.h>
#include <grass/glocale.h>

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Flag *rflag, *dflag, *fflag, *bflag, *gflag, *sflag;
    double t, b, l, r;
    double n, s, e, w;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("display"));
    G_add_keyword(_("graphics"));
    G_add_keyword(_("monitors"));
    module->label =
	_("Displays information about the active display monitor.");
    module->description =
	_("Display monitors are maintained by d.mon.");

    rflag = G_define_flag();
    rflag->key = 'r';
    rflag->description =
	_("Display screen rectangle (left, right, top, bottom)");

    dflag = G_define_flag();
    dflag->key = 'd';
    dflag->description = _("Display screen dimensions (width, height)");

    fflag = G_define_flag();
    fflag->key = 'f';
    fflag->description = _("Display active frame rectangle");

    bflag = G_define_flag();
    bflag->key = 'b';
    bflag->description = _("Display screen rectangle of current region");

    gflag = G_define_flag();
    gflag->key = 'g';
    gflag->description =
	_("Display geographic coordinates and resolution of entire screen");

    sflag = G_define_flag();
    sflag->key = 's';
    sflag->description =
	_("Print path to support files of currently selected monitor");

    G_option_required(rflag, dflag, fflag, bflag, gflag, sflag, NULL);
    
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    D_open_driver();
    
    if (rflag->answer || dflag->answer || fflag->answer)
	D_get_frame(&t, &b, &l, &r);


    if (rflag->answer)
	fprintf(stdout, "rectangle: %f %f %f %f\n", l, r, t, b);

    if (dflag->answer)
	fprintf(stdout, "dimensions: %f %f\n", r - l, b - t);

    if (fflag->answer)
	fprintf(stdout, "frame: %f %f %f %f\n", l, r, t, b);

    if (bflag->answer) {
	D_setup(0);

	l = D_get_d_west();
	r = D_get_d_east();
	t = D_get_d_north();
	b = D_get_d_south();

	fprintf(stdout, "region: %f %f %f %f\n", l, r, t, b);
    }

    if (gflag->answer) {
	/* outer bounds of the screen (including margins) */
	D_setup(0);

	n = D_get_u_north();
	s = D_get_u_south();
	w = D_get_u_west();
	e = D_get_u_east();

	fprintf(stdout, "n=%f\n", n );
	fprintf(stdout, "s=%f\n", s );
	fprintf(stdout, "w=%f\n", w );
	fprintf(stdout, "e=%f\n", e );
	fprintf(stdout, "ewres=%.15g\n", (e-w)/(r-l) );
	fprintf(stdout, "nsres=%.15g\n", (n-s)/(b-t) );
    }

    if (sflag->answer) {
        const char *curr_mon;

        curr_mon = G_getenv_nofatal("MONITOR");
        if (!curr_mon) {
            G_warning(_("No monitor is currently selected"));
        }
        else {
            char *p;
            char tmpdir[GPATH_MAX], mon_path[GPATH_MAX];
            struct dirent *dp;
            DIR *dirp;

            G_temp_element(tmpdir);
            strcat(tmpdir, "/");
            strcat(tmpdir, "MONITORS");
            strcat(tmpdir, "/");
            strcat(tmpdir, curr_mon);

            G_file_name(mon_path, tmpdir, NULL, G_mapset());

            dirp = opendir(mon_path);
            if (!dirp) {
                G_warning(_("No support files found for monitor <%s>"), curr_mon);
            }
            else {
                 while ((dp = readdir(dirp)) != NULL) {
                     if (!dp->d_name || dp->d_type != DT_REG)
                         continue;

                     p = strrchr(dp->d_name, '.');
                     if (!p)
                         p = dp->d_name;
                     else
                         p++; /* skip '.' */
                     
                     fprintf(stdout, "%s=%s%c%s\n", p,
                             mon_path, HOST_DIRSEP, dp->d_name);
                 }
            }
        }
    }
    
    D_close_driver();

    exit(EXIT_SUCCESS);
}
