#!/bin/sh

#fetch the description stuff from HTML pages for 5.7

GRASS57=$HOME/grass57

########################
PATHGRASS50=`grep GRASS50 $GRASS57/include/Make/Platform.make | sed 's+ ++g' |cut -d '=' -f2`

if [ $# -ne 1 ] ; then
 echo g51.extract_description.sh htmlfile
 exit
fi

FILE=$PATHGRASS50/html/html/$1.html

CUTLINE="`grep -ni '<H2>DESCRIPTION' $FILE | cut -d':' -f1`"
if [ "$CUTLINE" == "" ] ; then
  echo "ERROR: no <H2>DESCRIPTION</H2> present in html file"
  exit
fi

TOTALLINES=`wc -l $FILE  | awk '{print $1}'`
FROMBOTTOM=$(( $TOTALLINES - $CUTLINE ))

echo "<H2>DESCRIPTION</H2>" > description.html
echo "" >> description.html
tail -$FROMBOTTOM $FILE | grep -vi '</body>' | grep -vi '</html>' >> description.html
