#include "glob.h"

int 
store_reclass (CELL result, int primary, CELL *cat)
{
    int i;
    CELL *rcats;


    reclass = (RECLASS *) G_realloc (reclass, (result+1) * sizeof (RECLASS));
    reclass[result].result = result;
    reclass[result].cat = rcats = (CELL *) G_malloc (nfiles * sizeof(CELL));

/*
 * the primary file may not have been the first on the command line
 * enforce the results in the order that the files were specified
 */
    for (i = 0; i < primary; i++)
	rcats[i] = cat[i+1];
    rcats[i] = cat[0];
    for (i = primary+1; i < nfiles; i++)
	rcats[i] = cat[i];
    return (0) ;
}
