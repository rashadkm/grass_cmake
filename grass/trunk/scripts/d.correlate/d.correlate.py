#!/usr/bin/env python
#
############################################################################
#
# MODULE:       d.correlate for GRASS 6; based on dcorrelate.sh for GRASS 4,5
# AUTHOR(S):    CERL - Michael Shapiro; updated to GRASS 6 by Markus Neteler 5/2005
#               Converted to Python by Glynn Clements
# PURPOSE:      prints a graph of the correlation between data layers (in pairs)
#               derived from <grass5>/src.local/d.correlate.sh
# COPYRIGHT:    (C) 2005, 2008 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# TODO GRASS 7: rename parameters to map1, map2 or better multiple map=map1[,map2[...]]
#############################################################################

#%Module
#%  description: Prints a graph of the correlation between data layers (in pairs).
#%  keywords: display, diagram
#%End
#%option
#% key: layers
#% type: string
#% gisprompt: old,cell,raster
#% description: raster input map
#% required: yes
#% multiple: yes
#%end

import sys
import os
import grass

def main():
    layers = options['layers'].split(',')

    if len(layers) < 2:
	grass.error("At least 2 layers are required")

    tmpfile = grass.tempfile()

    for map in layers:
	if not grass.find_file(map, element = 'cell')['file']:
	    grass.fatal("Input map <%s> not found" % map)

    grass.write_command('d.text', color = 'black', size = 4, line = 1, stdin = "CORRELATION")

    colors = "red black blue green gray violet".split()
    line = 2
    iloop = 0
    jloop = 0
    for iloop, i in enumerate(layers):
	for jloop, j in enumerate(layers):
	    if i != j and iloop <= jloop:
		color = colors[0]
		colors = colors[1:]
		colors.append(color)
		grass.write_command('d.text', color = color, size = 4, line = line, stdin = "%s %s" % (i, j))
		line += 1

		ofile = file(tmpfile, 'w')
		grass.run_command('r.stats', flags = 'cnA', input = (i, j), stdout = ofile)
		ofile.close()

		ifile = file(tmpfile, 'r')
		first = True
		for l in ifile:
		    f = l.rstrip('\r\n').split(' ')
		    x = float(f[0])
		    y = float(f[1])
		    if first:
			minx = maxx = x
			miny = maxy = y
			first = False
		    if minx > x: minx = x
		    if maxx < x: maxx = x
		    if miny > y: miny = y
		    if maxy < y: maxy = y
		ifile.close()

		kx = 100.0/(maxx-minx+1)
		ky = 100.0/(maxy-miny+1)

		p = grass.feed_command('d.graph', color = color)
		ofile = p.stdin

		ifile = file(tmpfile, 'r')
		for l in ifile:
		    f = l.rstrip('\r\n').split(' ')
		    x = float(f[0])
		    y = float(f[1])
		    ofile.write("icon + 0.1 %f %f\n" % ((x-minx+1) * kx, (y-miny+1) * ky))
		ifile.close()

		ofile.close()
		p.wait()

    grass.try_remove(tmpfile)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
