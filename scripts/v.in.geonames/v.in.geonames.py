#!/usr/bin/env python

############################################################################
#
# MODULE:       v.in.geonames
#
# AUTHOR(S):    Markus Neteler, neteler cealp it
#               Converted to Python by Glynn Clements
#
# PURPOSE:      Import geonames.org dumps
#               http://download.geonames.org/export/dump/
#
#               Feature Codes: http://www.geonames.org/export/codes.html
#
# COPYRIGHT:    (c) 2008 Markus Neteler, GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# TODO: fix encoding issues for Asian fonts in 'alternatename' column (v.in.ascii)
#       fix spurious char stuff in elevation column
#############################################################################

#%Module
#%  description: Imports geonames.org country files into a GRASS vector points map.
#%  keywords: vector, import, gazetteer
#%End
#%option
#% key: input
#% type: string
#% key_desc: name
#% description: Uncompressed geonames file from (with .txt extension)
#% gisprompt: old_file,file,input
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% key_desc: name
#% gisprompt: new,vector,vector
#% description: Name for output vector map
#% required : yes
#%end

import sys
import os
import grass

def main():
    infile  = options['input']
    outfile = options['output']
    
    # save command line
    cmdline = os.path.basename(sys.argv[0])
    if infile:
	cmdline += ' input=' + infile
    if outfile:
	cmdline += ' output=' + outfile

    #### setup temporary file
    tmpfile = grass.tempfile()

    #are we in LatLong location?
    s = grass.read_command("g.proj", flags='j')
    kv = grass.parse_key_val(s)
    if kv['+proj'] != 'longlat':
	grass.fatal("This module only operates in LatLong/WGS84 locations")

    # input test
    if not os.access(infile, os.R_OK):
	grass.fatal("File <%s> not found" % infile)

    # DBF doesn't support lengthy text fields
    s = grass.read_command('db.connect', flags = 'p')
    kv = grass.parse_key_val(s, ':')
    dbfdriver = kv['driver'] == 'dbf'
    if dbfdriver:
	grass.warning("Since DBF driver is used, the content of the 'alternatenames' column might be cut with respect to the original Geonames.org column content")

    #let's go
    #change TAB to vertical bar
    num_places = 0
    inf = file(infile)
    outf = file(tmpfile, 'wb')
    for line in inf:
	fields = line.rstrip('\r\n').split('\t')
	line2 = '|'.join(fields) + '\n'
	outf.write(line2)
	num_places += 1
    outf.close()
    inf.close()

    grass.message("Converted %d place names." % num_places)

    # pump data into GRASS:
    #  http://download.geonames.org/export/dump/readme.txt
    #  The main 'geoname' table has the following fields :
    #  ---------------------------------------------------
    #  geonameid         : integer id of record in geonames database
    #  name              : name of geographical point (utf8) varchar(200)
    #  asciiname         : name of geographical point in plain ascii characters, varchar(200)
    #  alternatenames    : alternatenames, comma separated varchar(4000)
    #  latitude          : latitude in decimal degrees (wgs84)
    #  longitude         : longitude in decimal degrees (wgs84)
    #  feature class     : see http://www.geonames.org/export/codes.html, char(1)
    #  feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
    #  country code      : ISO-3166 2-letter country code, 2 characters
    #  cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 60 characters
    #  admin1 code       : fipscode (subject to change to iso code), isocode for the us and ch, see file admin1Codes.txt for display names of this code; varchar(20)
    #  admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80)
    #  admin3 code       : code for third level administrative division, varchar(20)
    #  admin4 code       : code for fourth level administrative division, varchar(20)
    #  population        : integer
    #  elevation         : in meters, integer
    #  gtopo30           : average elevation of 30'x30' (ca 900mx900m) area in meters, integer
    #  timezone          : the timezone id (see file http://download.geonames.org/export/dump/timeZones.txt)
    #  modification date : date of last modification in yyyy-MM-dd format

    # geonameid|name|asciiname|alternatenames|latitude|longitude|featureclass|featurecode|countrycode|cc2|admin1code|admin2code|admin3code|admin4code|population|elevation|gtopo30|timezone|modificationdate

    # TODO: elevation seems to contain spurious char stuff :(

    # debug:
    # head -n 3 ${TMPFILE}.csv

    columns = ['geonameid integer',
	       'name varchar(200)',
	       'asciiname varchar(200)',
	       'alternatename varchar(4000)',
	       'latitude double precision',
	       'longitude double precision',
	       'featureclass varchar(1)',
	       'featurecode varchar(10)',
	       'countrycode varchar(2)',
	       'cc2 varchar(60)',
	       'admin1code varchar(20)',
	       'admin2code varchar(20)',
	       'admin3code varchar(20)',
	       'admin4code varchar(20)',
	       'population integer',
	       'elevation varchar(5)',
	       'gtopo30 integer',
	       'timezone varchar(50)',
	       'modification date']

    grass.run_command('v.in.ascii', cat = 0, x = 6, y = 5, fs = '|',
		      input = tmpfile, output = outfile,
		      columns = columns)

    os.remove(tmpfile)

    # write cmd history:
    grass.run_command('v.support', map = outfile, cmdhist = cmdline)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()

