#!/bin/bash

./clear_mongo.sh
./geoloader osm --states ../data/states/states.txt osm 
./geoloader geojson ../data/geo/us_metro_areas.geojson metro
./geoloader geojson ../data/geo/us_states.geojson states
./geoloader geojson ../data/geo/us_counties.geojson counties
