 /*
 * \brief calculates shape index
 *
 *   Author: Claudio Porta and Lucio Davide Spano students of Computer Science University of Pisa (Italy)
 *			Commission from Faunalia Pontedera (PI) www.faunalia.it
 *
 *   This program is free software under the GPL (>=v2)
 *   Read the COPYING file that comes with GRASS for details.
 * 
 *  BUGS: please send bugs reports to  spano@cli.di.unipi.it, porta@cli.di.unipi.it
 */

#include <stdlib.h>
#include <fcntl.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "../r.li.daemon/daemon.h"

int main(int argc, char *argv[]){
	struct Option *raster, *conf, *output;
	struct GModule *module;
	
	G_gisinit(argv[0]);
	module = G_define_module();
	module->description =_("Calculates shape index on a raster file");
	
	/* define options */
	
	raster = G_define_standard_option(G_OPT_R_MAP);
	
	conf = G_define_option();
	conf->key = "conf";
	conf->description = "configuration file in ~/.r.li/history/ folder \
	(i.e conf=my_configuration";
	conf->gisprompt = "file,file,file";
	conf->type = TYPE_STRING;
	conf->required = YES;
	
	output = G_define_standard_option(G_OPT_R_OUTPUT);
	
	/** add other options for index parameters here */
	
	if (G_parser(argc, argv))
	   exit(EXIT_FAILURE);

	return calculateIndex(conf->answer,shape_index, NULL, raster->answer, output->answer);
	
}

int shape_index(int fd, char ** par, area_des ad, double *result){


	double area;
	char *mapset;
	struct Cell_head hd;
	CELL complete_value;
	double EW_DIST1,EW_DIST2,NS_DIST1,NS_DIST2;
	int mask_fd=-1, null_count=0;
	int i=0, k=0;
	int *mask_buf;
	
	G_set_c_null_value(&complete_value, 1);
	mapset = G_find_cell(ad->raster, "");
	if (G_get_cellhd(ad->raster, mapset, &hd) == - 1)
		return 0;

	
	/* open mask if needed */
	if (ad->mask == 1){
		if ((mask_fd = open(ad->mask_name, O_RDONLY, 0755)) < 0)
				return 0;
		mask_buf = malloc(ad->cl * sizeof(int));
		for (i=0;i<ad->rl;i++)			
		{
			if (read(mask_fd, mask_buf, (ad->cl * sizeof(int))) < 0)
				return 0;
			for (k=0; k<ad->cl; k++)
			{
				if (mask_buf[k] == 0){
					null_count++;
				}
			}
		}
	}

	
	
	/*calculate distance*/
	G_begin_distance_calculations();
		/* EW Dist at North edge */
    EW_DIST1 =
	G_distance(hd.east, hd.north, hd.west, hd.north);
    /* EW Dist at South Edge */
    EW_DIST2 =
	G_distance(hd.east, hd.south, hd.west, hd.south);
    /* NS Dist at East edge */
    NS_DIST1 =
	G_distance(hd.east, hd.north, hd.east, hd.south);
    /* NS Dist at West edge */
    NS_DIST2 =
	G_distance(hd.west, hd.north, hd.west, hd.south);
	
	
	
	
	area = (((EW_DIST1 + EW_DIST2) / 2) / hd.cols)* \
			(((NS_DIST1 + NS_DIST2) / 2) / hd.rows)* \
			(ad->rl * ad->cl - null_count);
	
	*result= area ;
	return 1;
}
