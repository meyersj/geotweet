// return Documents from 'metro' collection that
//  have a geojson object stored at key=geometry
//  be within 30000 meters from Portland
db.metro.find({
    geometry:{
        $near:{
            $geometry: {type:"Point", coordinates:[-122.5, 45.5]},
            $maxDistance: 30000  // meters
        }
    }
})


// Collection wide command
db.runCommand({
    geoNear:"metro",
    near: {type:"Point", coordinates:[-122.5, 45.5]},
    spherical: true,
    limit: 2
})


// List out all Metro Areas
db.geotweet.distinct("metro_area")


// Get top word occurences for Portland
db.geotweet.find({
    metro_area: "Portland, OR--WA"
}).sort({count:-1})


// Top occurences
db.geotweet.aggregate({
    $sort: { count:-1 }
})

