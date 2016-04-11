from pyproj import Proj, transform


# Convert between geographic and projected coordinate systems
# Geographic: EPSG Projection 4326 - WGS 84
proj4326 = Proj(init='epsg:4326')
# Projected: ESRI Projection 102005 - USA Contiguous Equidistant Conic
ESRI102005 = '+proj=eqdc +lat_0=39 +lon_0=-96 ' + \
    '+lat_1=33 +lat_2=45 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
proj102005 = Proj(ESRI102005)


def project(lonlat):
    return transform(proj4326, proj102005, *lonlat)


def rproject(lonlat):
    return transform(proj102005, proj4326, *lonlat)
