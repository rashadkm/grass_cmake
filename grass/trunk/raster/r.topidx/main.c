/*
 * r.topidx: creates topographic index map from elevation map.
 * 	     Based on GRIDATB.FOR.
 *
 * GRIDATB.FOR Author: Keith Beven <k.beven@lancaster.ac.uk>
 *
 * $Id$
 *
 *	Copyright (C) 2000 by the GRASS Development Team
 *	Author: Huidae Cho <hdcho@geni.knu.ac.kr>
 *		Hydro Laboratory, Kyungpook National University
 *		South Korea
 *
 *	This program is free software under the GPL (>=v2)
 *	Read the file COPYING coming with GRASS for details.
 *
 *
 * $Log$
 * Revision 1.4  2002-01-22 04:51:31  glynn
 * Merge releasebranch_11_april_2001_5_0_0 with HEAD
 *
 * Revision 1.3.4.1  2001/06/15 18:37:36  glynn
 * Call G_gisinit(argv[0]) before anything else
 *
 * Revision 1.3  2000/11/22 09:34:40  jan
 * added module description
 *
 * Revision 1.2  2000/11/01 17:26:35  cho
 * updated copyleft
 *
 * Revision 1.1  2000/08/20 05:57:16  cho
 * Huidae Cho <hdcho@geni.knu.ac.kr>: TOPMODEL simulation and other stuff
 *
 *
 */

#define	MAIN
#include "local_proto.h"
#undef	MAIN


int
main(argc,argv)
	int	argc;
	char	**argv;
{
	struct GModule *module;
	struct
	{
		struct	Option	*input;
		struct	Option	*output;
	} params;

	struct
	{
		struct	Flag	*overwr;
		struct	Flag	*verbose;
	} flags;

	G_gisinit(argv[0]);

	module = G_define_module();
    module->description =
		"Creates topographic index, ln(a/tan(beta)), map from elevation map.";

	params.input			= G_define_option();
	params.input->key		= "input";
	params.input->description	= "Elevation map";
	params.input->type		= TYPE_STRING;
	params.input->required		= YES;
	params.input->gisprompt		= "old,cell,raster";

	params.output			= G_define_option();
	params.output->key		= "output";
	params.output->description	= "Topographic index ln(a/tanB) map";
	params.output->type		= TYPE_STRING;
	params.output->required		= YES;
	params.output->gisprompt	= "new,cell,raster";

	flags.overwr			= G_define_flag();
	flags.overwr->key		= 'o';
	flags.overwr->description	= "Overwrite output map";

	flags.verbose			= G_define_flag();
	flags.verbose->key		= 'v';
	flags.verbose->description	= "Output verbosely";

	if(G_parser(argc, argv)){
	        exit(-1);
	}

	mapset  = G_mapset();
	iname   = params.input->answer;
	oname   = params.output->answer;
	overwr  = flags.overwr->answer;
	verbose = flags.verbose->answer;

	if(check_ready())
		exit(-1);

	G_get_cellhd(iname,mapset,&cellhd);
	if(adjcellhd(&cellhd))
		exit(-1);

	getcells();
	initialize();
	atanb();
	putcells();

	exit(0);
}

