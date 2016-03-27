#!/bin/bash

function drop_db {
    mongo ${1} --eval "db.dropDatabase();"
}

drop_db osm
drop_db boundary
