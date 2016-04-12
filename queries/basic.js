// List out all Metro Areas
db.metro_word.distinct("metro_area")

// Get top word occurences for Portland
db.metro_word.find({
    metro_area: "Portland, OR--WA"
}).sort({count:-1})

db.metro_word.aggregate({
    $sort: { count:-1 }
})

// metro_nearby_osm_tag_count
db.metro_osm.distinct("metro_area")

db.metro_osm.find({
    metro_area: "Portland, OR--WA"
}).sort({count:-1})

db.metro_osm.aggregate({
    $sort: { count:-1 }
})
