#include <stdlib.h>
#include "distance.h"

static int cmp ( struct Distance *, struct Distance *);
static int scan_dist (char *, double *);

int parse_distances (char **zone_list, double to_meters)
{
    double dist;
    double ew2 = 0.0;
    int i;
    int count;

    for (count = 0; zone_list[count]; count++)
	;
    if (count <= 0) return 0;

	/* create an array to hold the distances */

    distances = (struct Distance *) G_calloc (count, sizeof(struct Distance));

	/* scan the command line for the distances */

    if (window.proj != PROJECTION_LL)
    {
	ew2 = window.ew_res * window.ew_res;
	ns_to_ew_squared = window.ns_res * window.ns_res / ew2;
    }

    for (i = 0; i < count; i++)
    {
	if (!scan_dist(zone_list[i], &dist))
	{
	    fprintf (stderr, "%s: %s - illegal distance specification\n",
		pgm_name, zone_list[i]);
	    return 0;
	}
	else
	{
	    dist *= (to_meters * meters_to_grid);
	    if (window.proj != PROJECTION_LL)
		dist = dist*dist/ew2;
	    distances[i].dist = dist;
	}
	distances[i].label = zone_list[i];
    }

	/* sort the distances in increasing order */

    qsort (distances, count, sizeof(struct Distance), cmp);

    return count;
}

static int cmp ( struct Distance *a, struct Distance *b)
{
    if (a->dist < b->dist) return -1;
    return a->dist > b->dist;
}

static int scan_dist (char *s, double *dist)
{
    char dummy[2];

    *dummy = 0;
    if (sscanf (s, "%lf%1s", dist, dummy) != 1) return 0;
    if (*dummy) return 0;
    if (*dist <= 0.0) return 0;
    return 1;
}
