/****************************************************************************
 *
 * MODULE:       r.colors
 *
 * AUTHOR(S):    Michael Shapiro - CERL
 *               David Johnson
 *
 * PURPOSE:      Allows creation and/or modification of the color table
 *               for a raster map layer.
 *
 * COPYRIGHT:    (C) 2006 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ***************************************************************************/

#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/gis.h>

/* stats.c */
int get_stats(char *, char *, struct Cell_stats *);
/* main.c */
int main(int, char *[]);
int more_usage(void);
/* rules.c */
int read_color_rules(FILE *, struct Colors *, DCELL, DCELL, int);

#endif /* __LOCAL_PROTO_H__ */
