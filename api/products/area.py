from __future__ import division

from math import sin, radians

WGS84_RADIUS = 6378137


def ring_area(coordinates):
    """
    Translated from Mapbox's geojson-area library:
    https://github.com/mapbox/geojson-area/blob/master/index.js

    :returns the approximate area in square meters
    """

    assert isinstance(coordinates, (list, tuple))

    _area = 0
    coordinates_length = len(coordinates)

    if coordinates_length > 2:
        for i in range(0, coordinates_length):
            if i == (coordinates_length - 2):
                lower_index = coordinates_length - 2
                middle_index = coordinates_length - 1
                upper_index = 0
            elif i == (coordinates_length - 1):
                lower_index = coordinates_length - 1
                middle_index = 0
                upper_index = 1
            else:
                lower_index = i
                middle_index = i + 1
                upper_index = i + 2

            p1 = coordinates[lower_index]
            p2 = coordinates[middle_index]
            p3 = coordinates[upper_index]

            _area += (radians(p3[0]) - radians(p1[0])) * sin(radians(p2[1]))

        _area = _area * WGS84_RADIUS * WGS84_RADIUS / 2

    return _area


def from_bounding_box_to_polygon(location):
    """
    Pick a minLon,minLat,maxLon,maxLat bounding box and return
    the corresponding (squared) polygon
    """
    return (
        (location.mapbox_bounding_box[0], location.mapbox_bounding_box[1]),
        (location.mapbox_bounding_box[0], location.mapbox_bounding_box[3]),
        (location.mapbox_bounding_box[2], location.mapbox_bounding_box[3]),
        (location.mapbox_bounding_box[2], location.mapbox_bounding_box[1]),
    )


def bounding_box_area(location):
    """
    :return: bounding box area in square kilometers
    """
    return round(ring_area(from_bounding_box_to_polygon(location)) / 1000000, 0)
