"""Mostly written by Google Gemini"""

import folium
import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic

def extract_truncated_route_from_gpx(gpx, target_distance_miles):
    """
    Extracts a truncated route from a GPX file up to a specified distance

    Args:
        gpx_file: GPX file of route.
        target_distance_miles: Distance in miles to truncate the route to.

    Returns:
        list: List of (latitude, longitude) points for the truncated route.
    """
    points = []
    cumulative_distance_miles = 0.0
    previous_point = None
    distance_reached = False

    # Get points in reverse order to start from John o' Groats
    all_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            all_points.extend(segment.points)


    for point in all_points:
        if previous_point:
            segment_distance_miles = geodesic(
                (previous_point.latitude, previous_point.longitude),
                (point.latitude, point.longitude)
            ).miles
            cumulative_distance_miles += segment_distance_miles

        if cumulative_distance_miles <= target_distance_miles:
            points.append((point.latitude, point.longitude))
            previous_point = point
        else:
            # Calculate how much further to go along this segment to reach the target distance
            overshot_distance = cumulative_distance_miles - target_distance_miles
            fraction_to_travel = 1 - (overshot_distance / segment_distance_miles)

            # Interpolate a point along the segment
            truncated_lat = previous_point.latitude + fraction_to_travel * (point.latitude - previous_point.latitude)
            truncated_lon = previous_point.longitude + fraction_to_travel * (point.longitude - previous_point.longitude)
            points.append((truncated_lat, truncated_lon)) # Insert truncated point
            distance_reached = True
            break # Stop once target distance is reached

    return points, distance_reached


def create_map(gpx_points, start_label: str, end_label: str):

    center_lat = sum(p[0] for p in gpx_points) / len(gpx_points)
    center_lon = sum(p[1] for p in gpx_points) / len(gpx_points)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6) # Adjusted zoom

    # Add the truncated route as a PolyLine
    folium.PolyLine(gpx_points, weight=2.5, color="red").add_to(m) # Route in red

    # Add markers
    if gpx_points:
        start_point = gpx_points[0]
        end_point = gpx_points[-1]

        folium.Marker(location=start_point, popup=start_label).add_to(m)

        folium.Marker(location=end_point, popup=end_label, icon=folium.Icon(color='green')).add_to(m) # Green marker for truncated end

    return m

