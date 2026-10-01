from pyproj import Proj
p = Proj(proj='utm', zone=50, ellps='WGS84', preserve_units=False)
lon, lat = 114.04269993055507, 22.41609264758215
x, y = p(lon, lat)
print(f"UTM 50N: {x}, {y}")

p2 = Proj("epsg:2326") # Hong Kong 1980 Grid
x2, y2 = p2(lon, lat)
print(f"HK 1980 Grid: {x2}, {y2}")
