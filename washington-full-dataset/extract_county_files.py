import geopandas as gpd
from shapely.geometry import Polygon, Point, shape
from shapely.ops import transform
'''
This script takes a GeoDataFrame with state and county boundaries and splits it into separate GeoJSON files for each county.
It also reduces the area of the counties by 10% to avoid issues with OSM.
'''


input_file = 'state_county_boundaries_with_area_reduced.geojson'
dows_unified_file = 'simplified_washington_complete_area.geojson'
dows_gdf = gpd.read_file(dows_unified_file)
# Get the shape from the first file
dows_shape = dows_gdf.geometry[0]

input_gdf = gpd.read_file(input_file)
# For each row in the GeoDataFrame, create a new GeoDataFrame with the geometry of that row
for index, row in input_gdf.iterrows():
    # Create a new GeoDataFrame with the geometry of the current row
    gdf = gpd.GeoDataFrame(index=[0], crs=input_gdf.crs, geometry=[row['geometry']])
    
    # Create a new file name based on the county name
    county_name = row['JURISDICT_LABEL_NM']
    file_name = f"dow-{county_name.replace(' ', '_').replace('/', '_')}.geojson"
    counties_folder = 'counties'
    file_name = f"{counties_folder}/{file_name}"
    # Check if the directory exists, if not create it
    import os
    if not os.path.exists(counties_folder):
        os.makedirs(counties_folder)
    
    # Save the new GeoDataFrame to a GeoJSON file
    intersection = gdf.geometry.intersection(dows_shape)
    intersection.to_file(file_name, driver='GeoJSON')
    # gdf.to_file(file_name, driver='GeoJSON')