#!/usr/bin/env python

"""Tests for `utils` package."""

import pytest
from shapely.geometry import Point
from hydrolink import utils
import json


def test_crs_to_nad83():
    """Placeholder for test if conversions are occuring correctly.

    test if conversions are occuring correctly
    4326 to 4269
    3857 to 4269
    5070 to 4269
    """
    pass


def test_clean_water_name():
    """Test function utils.clean_water_name.  Ensure abbreviations are being correctly addressed."""
    assert utils.clean_water_name('Grand stream (north)') == 'grand stream'
    assert utils.clean_water_name('(north)Grand stream ') == 'grand stream'
    assert utils.clean_water_name('Grand st.') == 'grand stream'
    assert utils.clean_water_name('Grand St') == 'grand stream'
    assert utils.clean_water_name('grand str ') == 'grand stream'
    assert utils.clean_water_name('grand str.') == 'grand stream'
    assert utils.clean_water_name('trib. Grand Rv.') == 'tributary grand river'
    assert utils.clean_water_name('trib Grand Rv ') == 'tributary grand river'
    assert utils.clean_water_name('Grand Rv. unt') == 'grand river unnamed tributary'
    assert utils.clean_water_name('Grand River trib)') == 'grand river tributary'
    assert utils.clean_water_name('trib. Grand River') == 'tributary grand river'
    assert utils.clean_water_name('Grand River') == 'grand river'
    assert utils.clean_water_name('br. Grand River') == 'branch grand river'
    assert utils.clean_water_name('Grand River br ') == 'grand river branch'
    assert utils.clean_water_name('Grand Ck.') == 'grand creek'
    assert utils.clean_water_name('Grand ck') == 'grand creek'
    assert utils.clean_water_name('unt Grand Rv.') == 'unnamed tributary grand river'


def test_gnis_name_similarity():
    """Test function utils.gnis_name_similarity.  Ensure logic and match ratio correctly assigned."""
    gnis_name = 'Red Cedar River'
    test_scenarios = [{'source_water_name': 'red cedar river',
                       'flowline name similarity message': 'exact water name match',
                       'match_ratio': 1.0
                       },
                      {'source_water_name': 'Red Cedar River',
                       'flowline name similarity message': 'exact water name match',
                       'match_ratio': 1.0
                       },
                      {'source_water_name': '   ',
                       'flowline name similarity message': 'no source water name provided',
                       'match_ratio': 0
                       },
                      {'source_water_name': 'red cedar rv.',
                       'flowline name similarity message': 'most likely match, based on fuzzy match',
                       'match_ratio': 1.0
                       },
                      {'source_water_name': 'red Cedar',
                       'flowline name similarity message': 'most likely match, based on fuzzy match',
                       'match_ratio': 0.75
                       }]
    for test in test_scenarios:
        name = test['source_water_name']
        message = test['flowline name similarity message']
        ratio = test['match_ratio']
        name_similarity = utils.gnis_name_similarity(gnis_name, name)
        assert message == name_similarity['flowline name similarity message']
        if test['match_ratio'] is not None:
            assert ratio == name_similarity['flowline name similarity']
        else:
            assert 'flowline name similarity' not in name_similarity


def test_build_distance_line():
    """Test build_distance_line function.

    Verify build_distance_line function.
    Ensure distance between two points is being measured correctly.
    Line lengths were measured in arcmap.  Accounts for 1% rounding error.
    """
    # Input CRS which all data are transformed too
    crs = {'init': 'epsg:4269'}

    # using shapely create 2 points to allow for measuring of connecting line
    point1 = Point(-72.522365, 41.485054)
    point2 = Point(-72.529494, 41.464437)

    # test if the build_distance_line measurement is within 1% rounding error of arcmap measurement
    arcmap_length_m = 2381.955938
    arcmap_length_m_lt1 = arcmap_length_m - (arcmap_length_m * 0.01)
    arcmap_length_m_gt1 = arcmap_length_m + (arcmap_length_m * 0.01)
    len = utils.build_distance_line(point1, point2, crs=crs)
    assert arcmap_length_m_lt1 <= len <= arcmap_length_m_gt1


def test_build_flowline_details():
    """Test build flowline details.

    Currently tests closest_confluence.
    Use known data in JSON format to test function. JSON was built with 1500m buffer
    and verified using services in ArcGIS Pro.
    Could build this out a bit more.
    """
    lon = -84.5026
    lat = 42.7284
    input_point = Point(lon, lat)

    # imports flowlines json stored from live test. this is the input
    with open('tests/flowlines_json.json') as f:
        flowlines_json = json.load(f)

    flowlines_data = []
    all_flowline_terminal_node_points = []
    for flowline_data in flowlines_json['features']:
        source_water_name = flowline_data['attributes']['gnis_name']
        flowline_attributes, terminal_node_points, flowline_geo = utils.build_flowline_details(flowline_data, input_point, 'nhdhr', source_water_name)
        flowlines_data.append(flowline_attributes)
        all_flowline_terminal_node_points = all_flowline_terminal_node_points + terminal_node_points

    closest_confluence_meters = utils.closest_confluence(all_flowline_terminal_node_points, input_point, flowline_geo)
    assert closest_confluence_meters == 595.535732278204
    # assert flowlines_data == flowlines_data_test
