/*
 ****************************************************************************
 *
 * MODULE:     v.out.ascii
 * AUTHOR(S):  Michael Higgins, U.S. Army Construction Engineering Research Laboratory
 *             James Westervelt, U.S. Army Construction Engineering Research Laboratory
 *             Radim Blazek, ITC-Irst, Trento, Italy
 *             Martin Landa, CTU in Prague, Czech Republic (v.out.ascii.db merged & update for GRASS7)
 *
 * PURPOSE:    Writes GRASS vector data as ASCII files
 * COPYRIGHT:  (C) 2000-2009 by the GRASS Development Team
 *
 *             This program is free software under the GNU General
 *             Public License (>=v2). Read the file COPYING that comes
 *             with GRASS for details.
 *
 ****************************************************************************
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>

#include "local_proto.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Map_info Map;

    FILE *ascii, *att;
    char *input, *output, *delim, **columns, *where;
    int format, dp, field, ret, region, old_format;
    int ver, pnt;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("export"));
    G_add_keyword(_("ascii"));
    module->description =
	_("Converts a GRASS binary vector map to a GRASS ASCII vector map.");

    parse_args(argc, argv, &input, &output, &format, &dp, &delim,
	       &field, &columns, &where, &region, &old_format);

    if (format == GV_ASCII_FORMAT_ALL && columns) {
	G_warning(_("Parameter 'column' ignored in standard mode"));
    }

    ver = 5;
    pnt = 0;
    if (old_format)
	ver = 4;
    
    if (ver == 4 && format == GV_ASCII_FORMAT_POINT) {
	G_fatal_error(_("Format 'point' is not supported for old version"));
    }
    
    if (ver == 4 && strcmp(output, "-") == 0) {
	G_fatal_error(_("'output' must be given for old version"));
    }

    Vect_set_open_level(1);	/* only need level I */
    if (Vect_open_old(&Map, input, "") < 0)
	G_fatal_error(_("Unable to open vector map <%s>"),
		      input);
    
    if (strcmp(output, "-") != 0) {
	if (ver == 4) {
	    ascii = G_fopen_new("dig_ascii", output);
	}
	else if (strcmp(output, "-") == 0) {
	    ascii = stdout;
	}
	else {
	    ascii = fopen(output, "w");
	}

	if (ascii == NULL) {
	    G_fatal_error(_("Unable to open file <%s>"), output);
	}
    }
    else {
	ascii = stdout;
    }

    if (format == GV_ASCII_FORMAT_ALL) {
	Vect_write_ascii_head(ascii, &Map);
	fprintf(ascii, "VERTI:\n");
    }

    /* Open dig_att */
    att = NULL;
    if (ver == 4 && !pnt) {
	if (G_find_file("dig_att", output, G_mapset()) != NULL)
	    G_fatal_error(_("dig_att file already exist"));

	if ((att = G_fopen_new("dig_att", output)) == NULL)
	    G_fatal_error(_("Unable to open dig_att file <%s>"),
			  output);
    }

    if (where || columns)
	G_message(_("Fetching data..."));
    ret = Vect_write_ascii(ascii, att, &Map, ver, format, dp, delim,
			   region, field, where,
			   columns);

    if (ret < 1) {
	if (format == GV_ASCII_FORMAT_POINT) {
	    G_warning(_("No points found, nothing to be exported"));
	}
	else {
	    G_warning(_("No features found, nothing to be exported"));
	}
    }
    
    if (ascii != NULL)
	fclose(ascii);
    if (att != NULL)
	fclose(att);

    Vect_close(&Map);

    exit(EXIT_SUCCESS);
}
