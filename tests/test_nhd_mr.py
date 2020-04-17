# !/usr/bin/env python

"""Tests for `nhd_mr` package."""

import pytest
from hydrolink import nhd_mr


def test_input_buffer():
    """Tests to ensure buffer logic is working properly."""
    # Set needed variables
    ident, good_lat, good_lon = 2, 42.7284, -84.5026

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
    ident, good_lat, good_lon = 2, 42.7284, -84.5026
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
