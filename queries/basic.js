// Metro Mongo Word Count Results

// List metro areas
db.metro_word.distinct("metro_area")

// Get top word occurences for Portland
db.metro_word.find({
    metro_area: "Portland, OR--WA"
}).sort({count:-1})



// POI Nearby Tweets (local)

// List metro areas
db.metro_osm.distinct("metro_area")

// Most frequent POI locations
db.metro_osm.find({
    metro_area: "Portland, OR--WA"
}).sort({count:-1})



// POI Nearby Tweets (emr)

// List metro areas
db.metro_osm_emr.distinct("metro_area")

// Most frequent POI locations
db.metro_osm_emr.find({
    metro_area: "Portland, OR--WA"
}).sort({count:-1})

