"""Utility functions used across hydrolink modules.

Author
----------
Daniel Wieferich: dwieferich@usgs.gov
"""

# Import packages
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
import shapely.wkt
import re
import difflib

############################################################################################
############################################################################################


def crs_to_nad83(input_point, crs):
    """Reproject point data to NAD83, aka crs 4269.

    Parameters
    ----------
    input_point: shapely point
        See shapely.geometry Point method
    input_crs: int
        EPSG defined coordinate reference system, default is 4269 which is NAD83

    Returns
    ----------
    lon_nad83: float
        longitude in crs 4269 (NAD83)
    lat_nad83: float
        latitude in crs 4269 (NAD83)

    """
    # create geoseries of shapely point
    pt_gdf = gpd.GeoSeries(input_point)
    # set crs of geoseries, using user provided crs
    epsg_crs = f'epsg:{str(int(crs))}'
    pt_gdf.crs = epsg_crs
    # reproject point
    pt_gdf = pt_gdf.to_crs('epsg:4269')

    lon_nad83 = float(pt_gdf[0].x)
    lat_nad83 = float(pt_gdf[0].y)

    return lon_nad83, lat_nad83


def build_flowline_details(flowline_data, input_point, nhd_version='nhdhr', source_water_name=''):
    """Brings together functions to get hydrolink details for a flowline.

    Parameters
    ----------
    flowline_data: dictionary
        Contains information about a flowline, built in nhd_hr.hydrolink_flowlines or nhd_mr.hydrolink_flowlines
    input_point: shapely point
        Input location for hydrolinking. For formatting see shapely.geometry Point method
    nhd_version: {'nhdhr', 'nhdplusv2'}, default 'nhdhr'
        Version of National Hydrography Dataset. Supported versions include

        - ``'nhdhr'``: National Hydrography Dataset High Resolution
        - ``'nhdplusv2'``: National Hydrography Dataset Plus Version 2.1 Medium Resolution

    source_water_name: str, optional, default ''
        If available name of water body (e.g. name of lake, river, estuary...)

    Returns
    ----------
    flowline_attributes: dictionary
        Hydrolink calculated attributes updated to input flowline_data
    terminal_node_points: list
        List of shapely points expressed in wkt representing terminal nodes of flowline
        Example [POINT (-70.63598606746581 41.7689812018329)', 'POINT (-70.63435706746833 41.77051200183053)']
    flowline_geo: list
        List of shapely points representing shapely linestring of the flowline

    """
    flowline_attributes = flowline_data['attributes']
    # get all keys lower case hr lower, mr was upper
    flowline_attributes = {key.lower(): v for key, v in flowline_attributes.items()}
    flowline_geo = flowline_data['geometry']['paths'][0]

    # measure distance from point to flowline, return point location on flowline (flowline_point)
    flowline_snap_point, snap_distance_meters = point_to_line_meters(flowline_geo, input_point)
    # list of nhd measures within flowline_geo (m values)
    node_measures = [x[2] for x in flowline_geo]

    # check to see if there are more than 2 occurences of a terminal node (this indicates a confluence)
    terminal_node_points = list(set([Point(x[0], x[1]).wkt for x in flowline_geo if x[2] == max(node_measures) or x[2] == min(node_measures)]))

    nhd_measure = nhd_flowline_measure(flowline_geo, node_measures, flowline_snap_point)

    name_similarity = gnis_name_similarity(flowline_attributes['gnis_name'], source_water_name)
    flowline_attributes.update(name_similarity)

    label_nhd_version = f'{nhd_version} flowline measure'
    flowline_attributes.update({'meters from flowline': snap_distance_meters,
                                label_nhd_version: nhd_measure
                                })

    return flowline_attributes, terminal_node_points, flowline_geo


def nhd_flowline_measure(flowline_geo, node_measures, flowline_snap_point):
    """Measure along flowline where the flowline_snap_point is located (the address).

    Parameters
    ----------
    flowline_geo: list
        List of shapely points representing shapely linestring of the flowline, see build_flowline_details
    node_measures: list
        nhd measures within flowline_geo (m values)
    flowline_snap_point: shapely point
        shapely point that marks snap location (closest location on line to a coordinate), see point_to_line_meters

    Returns
    ----------
    nhd_measure:
        Measure along NHD flowline where 0 is most downstream node and 100 is most upstream node within the reachcode
        Note a reachcode can span multiple flowlines

    """
    flowline_line = LineString(flowline_geo)

    # Below calculates measure along nhd flowline
    # Make sure the max node value is actually the max measure for the flowline
    max_node_point = [Point(x[0], x[1]) for x in flowline_geo if x[2] == max(node_measures)][0]
    min_node_point = [Point(x[0], x[1]) for x in flowline_geo if x[2] == min(node_measures)][0]

    length_line_to_point = flowline_line.project(flowline_snap_point)
    length_line_total = max(flowline_line.project(min_node_point), flowline_line.project(max_node_point))
    # total span of flowline measures
    flowline_total_meas = float(max(node_measures)) - float(min(node_measures))

    if flowline_line.project(min_node_point) > flowline_line.project(max_node_point):
        nhd_measure = (float(max(node_measures)) - ((float(flowline_total_meas) * float(length_line_to_point)) / float(length_line_total)))
    elif length_line_total != 0:
        nhd_measure = (((float(flowline_total_meas) * float(length_line_to_point)) / float(length_line_total)) + float(min(node_measures)))
    else:
        nhd_measure = None

    return nhd_measure


def closest_confluence(terminal_node_points, input_point, flowline_geo):
    """Calculate distance from input point coordinates to closest confluence.

    This function accepts a list of terminal nodes.  A confluence is considered where
    a terminal node is shared in three or more flowlines.  The smaller this number
    the less certain a hydrolink will be.

    Parameters
    ----------
    terminal_node_points: list
        complete list of terminal node points from a subset of flowlines including duplicate values
    input_point: shapely point
        location from which distance calculations are made. For formatting see shapely.geometry Point method
    flowline_geo: list
        List of shapely points representing shapely linestring of the flowline, see build_flowline_details

    Returns
    ----------
    closest_confluence_meters: float
        distance from input point to closest confluence in meters

    """
    confluence_points = sorted(set([i for i in terminal_node_points if terminal_node_points.count(i) > 2]))
    closest_confluence_meters = None
    if len(confluence_points) > 0:
        for point_wkt in confluence_points:
            p = shapely.wkt.loads(point_wkt)
            confluence_snap_distance_meters = build_distance_line(p, input_point, crs='epsg:4269')
            if closest_confluence_meters is None or closest_confluence_meters > confluence_snap_distance_meters:
                closest_confluence_meters = confluence_snap_distance_meters

    return closest_confluence_meters


def point_to_line_meters(flowline_geo, input_point):
    """Calculate distance in meters from input point coordinates to closest point along a line.

    Parameters
    ----------
    input_point: shapely point
        Location from which distance calculations are made. For formatting see shapely.geometry Point method
    flowline_geo: list
        List of shapely points representing shapely linestring of the flowline, see build_flowline_details

    Returns
    ----------
    flowline_snap_point: shapely point
        Location along flowline that is closest in distance to input_point.

    """
    flowline_geo_line = LineString(flowline_geo)
    snap_meas = flowline_geo_line.project(input_point)
    # for flowline find x,y on line closest to input x,y
    snap_xy = flowline_geo_line.interpolate(snap_meas)
    # shapely point that marks snap location (closest location on line to a coordinate)
    flowline_snap_point = Point(snap_xy.x, snap_xy.y)
    snap_distance_meters = build_distance_line(flowline_snap_point, input_point, crs='epsg:4269')

    return flowline_snap_point, snap_distance_meters


def build_distance_line(point_1, point_2, crs='epsg:4269'):
    """Build line from point1 to point2 an measure distance in meters.

    Parameters
    ----------
    point_1: shapely point
        Location from which distance calculations are made
    point_2: shapely point
        Location to which distance calculations are made
    crs: str, default = 'epsg:4269'
        The value can be anything accepted by pyproj.CRS.from_user_input(), such as an
        authority string (eg “EPSG:4326”) or a WKT string.

    Returns
    ----------
    line_length_meters: float
        Distance in meters

    """
    line_geom = LineString([point_1, point_2])
    line_geoseries = gpd.GeoSeries(line_geom)
    line_geoseries.crs = crs
    line_geoseries = line_geoseries.to_crs('epsg:5070')
    line_length_meters = line_geoseries.length[0]
    return line_length_meters


def gnis_name_similarity(gnis_name, source_water_name):
    """Similarity comparison of two names using difflib.

    Measures similarity between two names using difflib
    Returned dictionary has a measure of similarity called 'flowline name similarity'

    Parameters
    ----------
    gnis_name: str
        name of water feature as defined by USGS Geographic Names Information System
    source_water_name: str
        name of water feature as defined by user

    Returns
    ----------
    name_similarity: dictionary
        dictionary capturing measures of similarity
        'flowline name similarity' is a float and values range from 0 (no match) to 1 (exact match)
        'flowline name similarity message' is a text representation of the similarity measure

    """
    name_similarity = {}
    if gnis_name is None and (source_water_name is None or source_water_name.isspace() or source_water_name.lower() == 'none'):
        name_similarity.update({'flowline name similarity message': 'no source water name provided and no GNIS_NAME',
                                'flowline name similarity': 0
                                })
    elif source_water_name is None or source_water_name.isspace() or source_water_name.lower() == 'none':
        name_similarity.update({'flowline name similarity message': 'no source water name provided',
                                'flowline name similarity': 0
                                })
    elif gnis_name is None:
        name_similarity.update({'flowline name similarity message': 'no GNIS name',
                                'cleaned source water name': source_water_name.lower(),
                                'flowline name similarity': 0
                                })
    elif gnis_name.lower() == source_water_name.lower():
        name_similarity.update({'flowline name similarity message': 'exact water name match',
                                'cleaned source water name': source_water_name.lower(),
                                'flowline name similarity': 1.0
                                })
    else:
        cleaned_water_name = clean_water_name(source_water_name)
        gnis = gnis_name.lower()
        if 'tributary' not in cleaned_water_name and 'branch' not in cleaned_water_name:
            match_ratio = difflib.SequenceMatcher(lambda x: x == " ", gnis, cleaned_water_name).ratio()
            name_similarity.update({'cleaned source water name': cleaned_water_name,
                                    'flowline name similarity': match_ratio
                                    })
            if match_ratio >= 0.75:
                name_similarity.update({'flowline name similarity message': 'most likely match, based on fuzzy match'})
            elif 0.75 > match_ratio >= 0.6:
                name_similarity.update({'flowline name similarity message': 'likely match, based on fuzzy match'})
            elif match_ratio < 0.6:
                name_similarity.update({'flowline name similarity message': 'likely not a match, based on fuzzy match'})
        else:
            name_similarity.update({'cleaned source water name': cleaned_water_name,
                                    'flowline name similarity message': 'tributary or branch in source water name, fuzzy match not conducted.',
                                    'flowline name similarity': 0
                                    })

    return name_similarity


def clean_water_name(name):
    """Quick and dirty approach to clean up unstandardized water names.

    Replaces common abbreviations, and deals with unnneeded spaces.
    This needs improvement but need to be careful not to replace unwanted strings.
    This step is implemented with the assumption that GNIS_NAME never contains abbreviations... something to verify.
    If you have a better way to do this let me know!!!!

    Parameters
    ----------
    name: str
        name of water feature as defined by user

    Returns
    ----------
    water_name_cleaned: str
        resulting waterbody name with common abbreviations (hopefully) spelled out

    """
    name_lower = f' {name.lower()} '
    name_lower = re.sub(r"[\(\[].*?[\)\]]", "", name_lower)
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


def df_for_selection(flowlines_data):
    """Organizes flowline data into pandas dataframe for ease in selection of information.

    Parameters
    ----------
    flowlines_data: dictionary
        data for all flowlines

    Returns
    ----------
    df: pandas dataframe

    """
    df = (pd.DataFrame(flowlines_data)).sort_values(by=['meters from flowline'])
    df = df.reset_index(drop=True)
    df['closest flowline order'] = df.index + 1

    return df
