#Import packages
import geopandas as gpd
from shapely.geometry import Point, LineString
import re

############################################################################################
############################################################################################
'''
Author
------------
Daniel Wieferich: dwieferich@usgs.gov

Description
------------
Module that holds common methods for multiple hydrolink modules
'''

        
def crs_to_nad83(lon, lat, crs):
    '''
    Description
    ------------
    Reproject point data to NAD83, aka crs 4269

    Parameters
    ------------
    input_lat: float, latitude of the point to be hydrolinked
    input_lon: float, longitude of the point to be hydrolinked
    input_crs: int, coordinate reference system, default is 4269 which is NAD83

    Output
    ------------
    lon_nad83 = longitude in crs 4269
    lat_nad83 = latitude in crs 4269
    '''
    init_point = Point(float(lon), float(lat))
    #create geoseries of shapely point  
    pt_gdf = gpd.GeoSeries(init_point)
    #set crs of geoseries, using user provided crs
    epsg = f'epsg:{str(int(crs))}'
    crs={'init':epsg}
    pt_gdf.crs = crs
    #reproject point
    pt_gdf = pt_gdf.to_crs({'init':'epsg:4269'})
    
    lon_nad83 = float(pt_gdf[0].x)
    lat_nad83 = float(pt_gdf[0].y)
    
    return lon_nad83, lat_nad83

def build_meas_line(point1, point2, crs={'init':'epsg:4269'}):
    '''
    Description: where point1 and 2 are shapely points
    '''
    line_geom = LineString([point1, point2]) 
    line_geoseries = gpd.GeoSeries(line_geom)           
    line_geoseries.crs = crs
    line_geoseries=line_geoseries.to_crs({'init':'epsg:5070'})
    line_length_meters = line_geoseries.length[0]
    return line_length_meters

def clean_water_name(name):
    '''
    Description: replace common abbreviations, this needs improvement but be careful not to replace 
    strings we dont want to this code currently assumes GNIS_NAME never contains abbreviations... 
    something to verify. If you have a better way to do this let me know!!!!
    '''
    name_lower = f' {name.lower()} '
    name_lower = re.sub("[\(\[].*?[\)\]]", "", name_lower)
    name_lower = name_lower.replace(' st. ', ' stream ')
    name_lower = name_lower.replace(' st ', ' stream ')
    name_lower = name_lower.replace(' str ', ' stream ')
    name_lower = name_lower.replace(' str. ', ' stream ')
    name_lower = name_lower.replace(' rv. ', ' river ')
    name_lower = name_lower.replace(' rv ', ' river ')
    name_lower = name_lower.replace(' unt ', ' unnamed tributary ')
    name_lower = name_lower.replace(' trib. ', ' tributary ')
    name_lower = name_lower.replace(' trib) ', ' tributary ')
    name_lower = name_lower.replace(' trib ', ' tributary ')
    name_lower = name_lower.replace(' ck ', ' creek ')
    name_lower = name_lower.replace(' ck. ', ' creek ')
    name_lower = name_lower.replace(' br ', ' branch ')
    name_lower = name_lower.replace(' br. ', ' branch ')
    water_name_cleaned = name_lower.strip()
    return water_name_cleaned  

############################################################################################
############################################################################################