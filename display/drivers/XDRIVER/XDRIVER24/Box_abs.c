#include <stdio.h>
#include "includes.h"
#include "../lib/driver.h"

extern Display *dpy;
extern Window grwin;
extern GC gc;
extern Pixmap bkupmap;
extern int backing_store;

int Box_abs (int x1, int y1, int x2, int y2)
{
    int tmp;

    if (x1 > x2) {
        tmp = x1;
        x1 = x2;
        x2 = tmp;
    }
    if (y1 > y2) {
        tmp = y1;
        y1 = y2;
        y2 = tmp;
    }
    XFillRectangle(dpy, grwin, gc, x1, y1, (unsigned) x2 - x1 + 1,
            (unsigned) y2 - y1);
    if (!backing_store)
        XFillRectangle(dpy, bkupmap, gc, x1, y1, (unsigned) x2 - x1 + 1,
                (unsigned) y2 - y1);

    return 0;
}

/* Why I need to add 1 to the widths and heights below is a mystery.
 * Otherwise errors appear mainly when zoomed-in on cell data !? - PRT */
int Box_abs2 (int x1, int y1, int width, int height)
{
    XFillRectangle(dpy, grwin, gc, x1, y1, (unsigned) width + 1,
            (unsigned) height);
    if (!backing_store)
        XFillRectangle(dpy, bkupmap, gc, x1, y1, (unsigned) width + 1,
                (unsigned) height);

    return 0;
}

int Box_rel (int width, int height)
{
    XFillRectangle(dpy, grwin, gc, cur_x, cur_y, (unsigned) width + 1,
            (unsigned) height);
    if (!backing_store)
        XFillRectangle(dpy, bkupmap, gc, cur_x, cur_y,
                (unsigned) width + 1, (unsigned) height);

    return 0;
}
