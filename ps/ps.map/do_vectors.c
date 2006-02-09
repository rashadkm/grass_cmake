/* Function: do_vectors
**
** Author: Paul W. Carlson	March 1992
** Modified by: Janne Soimasuo August 1994 line_cat added
** Modified by: Radim Blazek Jan 2000 areas added
** Modified by: Hamish Bowman Jun 2005 points moved to do_vpoints()
*/

#include <string.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/symbol.h>
#include "clr.h"
#include "vector.h"
#include "ps_info.h"
#include "local_proto.h"

int do_vectors (int after_masking)
{
    int n, z, lz, dig;
    struct Map_info Map;
    char dashes[100], buf[20], *ptr;
    extern int verbose;

    n = vector.count;
    while (n-- > 0) {
	if( vector.layer[n].type == VPOINTS  ) continue;
	if ( after_masking &&  vector.layer[n].masked) continue;
	if (!after_masking && !vector.layer[n].masked) continue;

	if (verbose > 1) {
	    fprintf (stdout,"PS-PAINT: reading vector file <%s in %s> ...",
		vector.layer[n].name, vector.layer[n].mapset);
	    fflush(stdout);
	}

	Vect_set_open_level(2); 
	Vect_set_fatal_error ( GV_FATAL_PRINT );
	if (2 >  Vect_open_old(&Map, vector.layer[n].name, vector.layer[n].mapset)) {
	    char name[100];

	    sprintf(name, "%s in %s", vector.layer[n].name, vector.layer[n].mapset);
	    error("vector file", name, "can't open");
	    continue;
	}

	if ( vector.layer[n].type == VAREAS ) {
    	    PS_vareas_plot(&Map, n);
	} else if ( vector.layer[n].type == VLINES ) {
	    fprintf(PS.fp, "[] 0 setdash\n");
	    if (vector.layer[n].hwidth && vector.layer[n].ref == LINE_REF_CENTER) {
		set_ps_color( &(vector.layer[n].hcolor) );
		fprintf(PS.fp, "%.8f W\n",  
		   vector.layer[n].width + 2. * vector.layer[n].hwidth);
		PS_vlines_plot(&Map, n, LINE_DRAW_HIGHLITE);
		Vect_rewind(&Map); 
	    }

	    fprintf(PS.fp, "%.8f W\n", vector.layer[n].width );
	    set_ps_color( &(vector.layer[n].color) );
	    dashes[0] = '[';
	    dashes[1] = 0;
	    lz = 0;
	    if (vector.layer[n].linestyle != NULL) {
		G_strip(vector.layer[n].linestyle);
 		ptr = vector.layer[n].linestyle;
		while (*ptr && (*ptr < '1' || *ptr > '9')) {
		    lz++;
		    ptr++;
		}
		if (lz) {
	    	    sprintf(buf, "%d ", lz);
		    strcat(dashes, buf);
		}
		while (*ptr) {
		    dig = 0;
		    while (*ptr >= '1' && *ptr <= '9') {
			dig++;
			ptr++;
		    }
		    if (dig) {
			sprintf(buf, "%d ", dig);
			strcat(dashes, buf);
		    }
		    z = 0;
	    	    while (*ptr && (*ptr < '1' || *ptr > '9')) {
			z++;
			ptr++;
	    	    }
	    	    if (z) 
		    {
			sprintf(buf, "%d ", z);
			strcat(dashes, buf);
		    }
		}
	    }
	    sprintf(buf, "] %d", lz);
	    strcat(dashes, buf);
	    fprintf(PS.fp, "%s setdash\n", dashes);
	    vector.layer[n].setdash = G_store(dashes);
	    PS_vlines_plot(&Map, n, LINE_DRAW_LINE);
	}

	Vect_close(&Map);
	fprintf(PS.fp, "[] 0 setdash\n");
	if (verbose > 1) fprintf (stdout,"\n");
    }

    return 0;
}


int do_vpoints (int after_masking)
{
    int n;
    struct Map_info Map;
    extern int verbose;

    n = vector.count;
    while (n-- > 0) {
    	if( vector.layer[n].type != VPOINTS ) continue;
	if ( after_masking &&  vector.layer[n].masked) continue;
	if (!after_masking && !vector.layer[n].masked) continue;

	if (verbose > 1) {
	    fprintf (stdout,"PS-PAINT: reading vector points file <%s in %s> ...",
		vector.layer[n].name, vector.layer[n].mapset);
	    fflush(stdout);
	}

	Vect_set_open_level(2); 
	Vect_set_fatal_error ( GV_FATAL_PRINT );
	if (2 >  Vect_open_old(&Map, vector.layer[n].name, vector.layer[n].mapset)) {
	    char name[100];

	    sprintf(name, "%s in %s", vector.layer[n].name, vector.layer[n].mapset);
	    error("vector file", name, "can't open");
	    continue;
	}

	PS_vpoints_plot(&Map, n, LINE_DRAW_LINE);
	
	Vect_close(&Map);
	fprintf(PS.fp, "[] 0 setdash\n");
	if (verbose > 1) fprintf (stdout,"\n");
    }

    return 0;
}
