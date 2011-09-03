#!/usr/bin/env python

# written by Markus Neteler 18. August 1998 / 20. Jan. 1999
#            neteler geog.uni-hannover.de
# mosaic code from Felix Gershunov (Felix spsl.nsc.ru)
# updated for GRASS 5.7 by Michael Barton 2004/04/05
# converted to Python by Glynn Clements
#
# COPYRIGHT:    (C) 1999,2007,2008 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# TODO: - implement g.findfile for 3 and 4 maps (currently only current mapset supported)
#            [done for 2 maps]
#       - fix isnull() in r.mapcalc for 3 and 4 maps composites
#            [done for 2 maps]
#       - fix color table length (currently only 256 cols supported, make
#         flexible)
#            [done for 2 maps]
#--------------------------------------------------


#%module
#% description: Mosaics several images and extends colormap.
#% keywords: raster
#% keywords: imagery
#% keywords: mosaicking
#%end
#%option G_OPT_R_INPUTS
#%end
#%option G_OPT_R_OUTPUT
#%end

import sys
import os
import grass.script as grass

def copy_colors(fh, map, offset):
    p = grass.pipe_command('r.colors.out', map = map)
    for line in p.stdout:
	f = line.rstrip('\r\n').split(' ')
	if offset:
	    if f[0] in ['nv', 'default']:
		continue
	    f[0] = str(float(f[0]) + offset)
	fh.write(' '.join(f) + '\n')
    p.wait()

def get_limit(map):
    return grass.raster_info(map)['max']

def make_expression(i, count):
    if i > count:
	return "null()"
    else:
	e = make_expression(i + 1, count)
	return "if(isnull($image%d),%s,$image%d+$offset%d)" % (i, e, i, i)

def main():
    images = options['input'].split(',')
    output = options['output']

    count = len(images)

    grass.warning(_('Do not forget to set region properly to cover all images.'))

    offset = 0
    offsets = []
    parms = {}
    for n, img in enumerate(images):
	offsets.append(offset)
	parms['image%d' % (n + 1)] = img
	parms['offset%d' % (n + 1)] = offset
	offset += get_limit(img) + 1

    grass.message(_("Mosaicing %d images...") % count)

    grass.mapcalc("$output = " + make_expression(1, count),
		  output = output, **parms)

    #modify the color table:
    p = grass.feed_command('r.colors', map = output, rules='-')
    for img, offset in zip(images, offsets):
	print img, offset
	copy_colors(p.stdin, img, offset)
    p.stdin.close()
    p.wait()

    grass.message(_("Done. Raster map <%s> created.") % output)

    # write cmd history:
    grass.raster_history(output)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
