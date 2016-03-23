#!/bin/bash

db=osm
mongo ${db} --eval "db.dropDatabase();"
