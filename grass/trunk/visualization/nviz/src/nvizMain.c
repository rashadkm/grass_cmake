/*
 * This is basically tkAppInit.c from the tk4.0 distribution except
 * that we define Tcl_AppInit in tkAppInit.c.
 */

#include <stdlib.h>
#include <string.h>
#include <tk.h>
#include <grass/gis.h>
#include "interface.h"

extern int NVIZ_AppInit(Tcl_Interp *);


/*
 *----------------------------------------------------------------------
 *
 * main --
 *
 *	This is the main program for the application.
 *
 * Results:
 *	None: Tk_Main never returns here, so this procedure never
 *	returns either.
 *
 * Side effects:
 *	Whatever the application does.
 *
 *----------------------------------------------------------------------
 */

int main(int argc,		/* Number of command-line arguments. */
	 char **argv		/* Values of command-line arguments. */
    )
{
	int i;

	Tcl_FindExecutable(argv[0]);
	if (argc > 1) {
		if (strstr(argv[argc-1], "-h") != NULL) 
                        sprintf(argv[argc-1], "--h");
	}

    Tk_Main(argc, argv, NVIZ_AppInit);
    return 0;			/* Needed only to prevent compiler warning. */
}
