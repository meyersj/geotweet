#!/bin/bash


function drop_db {
    mongo ${1} --eval "db.dropDatabase();"
}

db=geotweet

# clear geotweet database
drop_db ${db}

./geoloader osm --mongo ${db} --states ../data/states/states.txt osm 
./geoloader geojson --mongo ${db} ../data/geo/us_metro_areas.geojson metro
./geoloader geojson --mongo ${db} ../data/geo/us_states.geojson states
./geoloader geojson --mongo ${db} ../data/geo/us_counties.geojson counties
