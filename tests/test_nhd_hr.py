#!/usr/bin/env python

"""Tests for `utils` package."""

import pytest
from hydrolink import nhd_hr

def test_init_buffer_coordinates():
    '''
    Description
    -----------
    Tests to ensure buffer logic and coordinate bound logic is working properly.
    '''
    good_buffers = [0,10,2000]
    for buffer in good_buffers:
        ident, good_lat, good_lon, stream_name = 2, 42.7284, -84.5026, 'Red Cedar River'
        bad_lat = 17.4
        bad_lon = -63.9
        #Good buffer, good lat, lon should have status=1 
        buffer_test = nhd_hr.HighResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        assert buffer_test.status == 1 and buffer_test.message == ''
        #bad_lat should set status to 0 (fail) 
        m = f'Coordinates for id: {ident} are outside of the bounding box of the United States.'
        us_bounds_test = nhd_hr.HighResPoint(ident, bad_lat, good_lon, buffer_m=buffer)
        assert us_bounds_test.status == 0 and us_bounds_test.message == m
        #bad lon should set status to 0 (fail) 
        us_bounds_test = nhd_hr.HighResPoint(ident, good_lat, bad_lon, buffer_m=buffer)
        assert us_bounds_test.status == 0 and us_bounds_test.message == m

    #buffer greater than 2000 should set status to 0 (fail) 
    bad_buffers = [2001, 3000]
    for buffer in bad_buffers:
        buffer_test = nhd_hr.HighResPoint(ident, good_lat, good_lon, buffer_m=buffer)
        m = 'Maximum buffer is 2000 meters.'
        assert buffer_test.status == 0 and buffer_test.message == m





