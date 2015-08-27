#!/usr/bin/env python
# -*- coding: utf-8 -*-

# generates topics.html and topic_*.html
# (c) 2012 by the GRASS Development Team, Markus Neteler, Luca Delucchi

import os
import sys
import glob
from build_html import *

path = sys.argv[1]
year = os.getenv("VERSION_DATE")

min_num_modules_for_topic = 3

keywords = {}

htmlfiles = glob.glob1(path, '*.html')

for fname in htmlfiles:
    fil = open(os.path.join(path, fname))
    # TODO maybe move to Python re (regex)
    lines = fil.readlines()
    try:
        index_keys = lines.index('<h2>KEYWORDS</h2>\n')+1
        index_desc = lines.index('<h2>NAME</h2>\n')+1
    except:
        continue
    try:
        key = lines[index_keys].split(',')[1].strip().capitalize().replace(' ', '_')
        key = key.split('>')[1].split('<')[0]
    except:
        continue
    try:
        desc = lines[index_desc].split('-', 1)[1].strip()
    except:
        desc.strip()
    if key not in keywords.keys():
        keywords[key] = {}
        keywords[key][fname] = desc
    elif fname not in keywords[key]:
        keywords[key][fname] = desc

topicsfile = open(os.path.join(path, 'topics.html'), 'w')
topicsfile.write(header1_tmpl.substitute(title = "GRASS GIS " \
                        "%s Reference Manual: Topics index" % grass_version))
topicsfile.write(headertopics_tmpl)

for key, values in sorted(keywords.iteritems()):
    keyfile = open(os.path.join(path, 'topic_%s.html' % key.lower()), 'w')
    keyfile.write(header1_tmpl.substitute(title = "GRASS GIS " \
                        "%s Reference Manual: Topic %s" % (grass_version,
                                                    key.replace('_', ' '))))
    keyfile.write(headerkey_tmpl.substitute(keyword=key.replace('_', ' ')))
    num_modules = 0
    for mod, desc in sorted(values.iteritems()):
        num_modules += 1
        keyfile.write(desc1_tmpl.substitute(cmd=mod, desc=desc,
                                            basename=mod.replace('.html', '')))
    if num_modules >= min_num_modules_for_topic:
        topicsfile.writelines([moduletopics_tmpl.substitute(
            key=key.lower(), name=key.replace('_', ' '))])
    keyfile.write("</table>\n")
    write_html_footer(keyfile, "index.html", year)
topicsfile.write("</ul>\n")
write_html_footer(topicsfile, "index.html", year)
topicsfile.close()
