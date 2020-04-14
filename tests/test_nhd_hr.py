# !/usr/bin/env python

"""Tests for `utils` package."""

import pytest
from hydrolink import nhd_hr
import requests


def test_input_buffer():
    """Tests to ensure buffer logic is working properly."""
    # Set needed variables
    ident, good_lat, good_lon = 2, 42.7284, -84.5026

    good_buffers = [0, 10, 2000]
    for buffer in good_buffers:
        # Good buffer, good lat, lon should have status=1
        buffer_test = nhd_hr.HighResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        assert buffer_test.status == 1 and buffer_test.message == ''

    # buffer greater than 2000 should set status to 0 (fail)
    bad_buffers = [2001, 3000]
    for buffer in bad_buffers:
        buffer_test = nhd_hr.HighResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        m = 'Maximum buffer is 2000 meters, reduce buffer.'
        assert buffer_test.status == 0 and buffer_test.message == m


def test_input_coordinates():
    """Make sure code handles lat or lon falling outside U.S. bounds."""
    ident, good_lat, good_lon = 2, 42.7284, -84.5026
    bad_lat = 17.4
    bad_lon = -63.9

    good_buffers = [0, 10, 2000]
    for buffer in good_buffers:
        # Good buffer, good lat, lon should have status=1
        us_bounds_test = nhd_hr.HighResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        assert us_bounds_test.status == 1 and us_bounds_test.message == ''
        m = f'Coordinates for id: {ident} are outside of the bounding box of the United States.'
        us_bounds_test = nhd_hr.HighResPoint(ident, bad_lat, good_lon, buffer_m=buffer)
        assert us_bounds_test.status == 0 and us_bounds_test.message == m
        # bad lon should set status to 0 (fail)
        us_bounds_test = nhd_hr.HighResPoint(ident, good_lat, bad_lon, buffer_m=buffer)
        assert us_bounds_test.status == 0 and us_bounds_test.message == m


@pytest.mark.skip(reason="this tests similarities of addressing to NDH services, not always required")
def test_addressing():
    """Test against hem point events SOE.

    Use HEM SOE extension HEMPointEvents to pass the snap location on best reach to return reach measure.
    Assert that returned measure is the same as what I am getting when not using this service.
    Documentation of HEMPointEvents is found https://edits.nationalmap.gov/hem-soe-docs/soe-reference/hem-point-events.html

    """
    list_reachcodes = [{'gnis_name': None,
                        'lengthkm': 0.035,
                        'permanent_identifier': '152093660',
                        'reachcode': '04050004002359',
                        'meters from flowline': 559.1053858081182,
                        'nhdhr measure': 20.54223
                        },
                       {'gnis_name': 'Red Cedar River',
                        'lengthkm': 7.032,
                        'permanent_identifier': '152093413',
                        'reachcode': '04050004000126',
                        'meters from flowline': 52.94060499992746,
                        'nhdhr measure': 90.32618961126374
                        }]

    lon = -84.5026
    lat = 42.7284

    # find closest flowline for each reachcode, only test those
    for reach in list_reachcodes:
        reachcode = reach['reachcode']
        # min_meters = reach['meters from flowline']
        nhdhr_meas = reach['nhdhr measure']

        hem_get_hr_xy = 'https://edits.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/exts/Vwe_HEM_Soe/HEMPointEvents'
        xy = '{"x":' + str(lon) + ',"y":' + str(lat) + ', "spatialReference": {"wkid":4269}}'

        payload = {"point": xy,
                   "reachcode": reachcode,
                   "searchToleranceMeters": 1500,
                   "outWKID": 4269,
                   "f": "json"
                   }

        hr_xy = requests.post(hem_get_hr_xy, params=payload, verify=False).json()

        if hr_xy['resultStatus'] == 'success' and hr_xy['features']:
            # hl_reach_meas = hr_xy['features'][0]['attributes']
            meas = hr_xy['features'][0]['attributes']['MEASURE']
        assert nhdhr_meas == meas
