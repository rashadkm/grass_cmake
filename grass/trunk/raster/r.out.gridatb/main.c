#define	MAIN
#include "local_proto.h"
#undef	MAIN


int
main(argc,argv)
	int	argc;
	char	**argv;
{
	struct
	{
		struct	Option	*input;
		struct	Option	*output;
	} params;

	struct
	{
		struct	Flag	*overwr;
	} flags;


	params.input			= G_define_option();
	params.input->key		= "input";
	params.input->description	= "Input map";
	params.input->type		= TYPE_STRING;
	params.input->required		= YES;
	params.input->gisprompt		= "old,cell,raster";

	params.output			= G_define_option();
	params.output->key		= "output";
	params.output->description	= "GRIDATB i/o map file";
	params.output->type		= TYPE_STRING;
	params.output->required		= YES;

	flags.overwr			= G_define_flag();
	flags.overwr->key		= 'o';
	flags.overwr->description	= "Overwrite output map file";


	G_gisinit(argv[0]);

	if(G_parser(argc, argv)){
	        exit(-1);
	}

	iname  = params.input->answer;
	file   = params.output->answer;
	overwr = flags.overwr->answer;

	mapset = G_mapset();

	if(check_ready()){
		exit(-1);
	}

	rdwr_gridatb();

	exit(0);
}

