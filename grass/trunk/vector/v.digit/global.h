#include <tcl.h>
#include <tk.h>
#include "Vect.h"

#ifdef MAIN
  #define Global
#else
  #define Global extern
#endif

/*      tool in c:         name in Tk */             
#define TOOL_NOTHING   0   /* */
#define TOOL_EXIT      1   /* exit */
#define TOOL_NEW_LINE  2   /* new_line */

Global struct Map_info Map;
Global struct Cell_head Region; /* Current region (synchronized with GRASS WIND) */ 
Global Tcl_Interp *Toolbox;
Global int Tool_next;           /* Next tool to be run */
Global double Xscale, Yscale;   /* Scale factors = size_in_map / size_on_screen */

