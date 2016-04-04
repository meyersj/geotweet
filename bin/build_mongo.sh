#!/bin/bash


function drop_db {
    mongo ${1} --eval "db.dropDatabase();"
}

db=geotweet

# clear geotweet database
drop_db ${db}

./geoloader osm --db ${db} --states ../data/states/states.txt osm 
./geoloader geojson --db ${db} ../data/geo/us_metro_areas.geojson metro
./geoloader geojson --db ${db} ../data/geo/us_states.geojson states
./geoloader geojson --db ${db} ../data/geo/us_counties.geojson counties
