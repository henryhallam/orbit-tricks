#!/bin/bash
USER=edit_me
PASS=edit_me
CATID=39429,39512,39513,39514,39515,39518,39519,39520,39521,39525,39526,39527,39528,39529,39530,39531,39532,39555,39556,39557,39558,39559,39560,39561,39562,39563,39564

set -e
if [ "$PASS" == "edit_me" ]; then
 echo "Edit $0 with your Space Track username and password (and the catalog IDs you want)"
 exit 1
fi

if [ -z "$ORD" ]; then
    ORD=1
fi

QUERY="https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/$CATID/ORDINAL/$ORD/format/3le"
wget --post-data="identity=$USER&password=$PASS&query=$QUERY" https://www.space-track.org/ajaxauth/login -O norad$ORD.tle
cp norad$ORD.tle norad.tle

cat norad.tle

for C in ${CATID//,/ }; do
    QUERY="https://www.space-track.org/basicspacedata/query/class/tle/NORAD_CAT_ID/${C}/orderby/COMMENT%20asc/format/3le/metadata/false"
    wget --post-data="identity=$USER&password=$PASS&query=$QUERY" https://www.space-track.org/ajaxauth/login -O $C.tle
done
