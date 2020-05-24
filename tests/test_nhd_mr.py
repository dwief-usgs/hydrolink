# !/usr/bin/env python

"""Tests for `nhd_mr` package."""

import pytest
from hydrolink import nhd_mr
import validators

# Create test point that can be used for tests
ident, good_lat, good_lon = 2, 42.7284, -84.5026
test_point = nhd_mr.MedResPoint(ident, good_lat, good_lon)


def test_build_nhd_query():
    """Validate structure of url."""
    # test hem_flowline and waterbody
    test_point.build_nhd_query(query=['network_flow', 'waterbody','nonnetwork_flow'])
    assert validators.url(test_point.flowline_query)
    assert validators.url(test_point.nonnetwork_flowline_query)
    assert validators.url(test_point.waterbody_query)

    # test hem_waterbody_flowline
    test_point.hydrolink_waterbody = {}
    test_point.hydrolink_waterbody['nhdplusv2 waterbody permanent identifier'] = '88894713'
    test_point.build_nhd_query(query=['waterbody_flowline'])
    assert validators.url(test_point.flowline_query)


def test_input_buffer():
    """Tests to ensure buffer logic is working properly."""

    good_buffers = [0, 10, 2000]
    for buffer in good_buffers:
        # Good buffer, good lat, lon should have status=1
        buffer_test = nhd_mr.MedResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        assert buffer_test.status == 1 and buffer_test.message == ''

    # buffer greater than 2000 should set status to 0 (fail)
    bad_buffers = [2001, 3000]
    for buffer in bad_buffers:
        buffer_test = nhd_mr.MedResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        m = 'Maximum buffer is 2000 meters, reduce buffer.'
        assert buffer_test.status == 0 and buffer_test.message == m


def test_input_coordinates():
    """Make sure code handles lat or lon falling outside U.S. bounds."""
    bad_lat = 17.4
    bad_lon = -63.9

    good_buffers = [0, 10, 2000]
    for buffer in good_buffers:
        # Good buffer, good lat, lon should have status=1
        us_bounds_test = nhd_mr.MedResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        assert us_bounds_test.status == 1 and us_bounds_test.message == ''
        m = f'Coordinates for id: {ident} are outside of the bounding box of the United States.'
        us_bounds_test = nhd_mr.MedResPoint(ident, bad_lat, good_lon, buffer_m=buffer)
        assert us_bounds_test.status == 0 and us_bounds_test.message == m
        # bad lon should set status to 0 (fail)
        us_bounds_test = nhd_mr.MedResPoint(ident, good_lat, bad_lon, buffer_m=buffer)
        assert us_bounds_test.status == 0 and us_bounds_test.message == m
