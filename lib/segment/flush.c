#include "segment.h"

int segment_flush (SEGMENT *SEG)
{
    int i;

    for (i = 0; i < SEG->nseg; i++)
	if (SEG->scb[i].n >= 0 && SEG->scb[i].dirty)
	    segment_pageout (SEG, i);

	return 0;
}
