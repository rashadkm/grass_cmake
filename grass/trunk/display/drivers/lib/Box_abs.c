#include "driverlib.h"
int 
Box_abs (int x1, int y1, int x2, int y2)
{
	static int x[4], y[4] ;

	x[0] = x1 ; y[0] = y1 ;
	x[1] = x1 ; y[1] = y2 ;
	x[2] = x2 ; y[2] = y2 ;
	x[3] = x2 ; y[3] = y1 ;

	Polygon_abs(x, y, 4) ;

	return 0;
}
