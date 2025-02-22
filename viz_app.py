import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import gpxpy

from parkrun_metrics import ParkrunMetrics, MILE
from fetch_parkrun_data import fetch_parkrun_data
import map_viz

DEBUG = True
GPX_FILE = 'end_to_end_example_main_route.gpx'

@st.cache_data
def fetch_data(parkrunner_id: str) -> pd.DataFrame:
    if DEBUG:
        return pd.read_csv('my_data.csv')
    else:
        return fetch_parkrun_data(parkrunner_id)

@st.cache_data
def load_data(parkrunner_id: str) -> pd.DataFrame:
    return ParkrunMetrics(fetch_data(parkrunner_id))

@st.cache_data
def load_gpx():
    with open(GPX_FILE, 'rb') as f:
        return gpxpy.parse(f)

parkrunner_select = st.text_input("Parkrunner ID (Digits, don't need leading letter)")
miles_or_km = st.selectbox("Miles or Kilometers", ("Miles", "Kilometers"), index=1)
miles = miles_or_km == "Miles"

def distance_metric(dist: int | float) -> int | float:
    if miles:
        return dist * MILE
    else:
        return dist

def distance_unit() -> str:
    if miles:
        return "mi"
    else:
        return "km"

def rank_ending(n: int) -> str:
    n_str = str(n)
    if n_str.endswith('1'):
        return 'st'
    elif n_str.endswith('2'):
        return 'nd'
    elif n_str.endswith('3'):
        return 'rd'
    else:
        return 'th'

if st.button("Submit"):
    try:

        metrics = load_data(parkrunner_select)

        st.subheader("Totals")
        agg_cols = st.columns(3)

        agg_cols[0].metric(
            "Total parkruns",
            f"{len(metrics.results)}",
            border=True,
        )
        
        agg_cols[1].metric(
            "Total distance covered during parkruns",
            f"{round(distance_metric(metrics.total_distance()), 1)} {distance_unit()}",
            border = True,
        )

        hours, mins, seconds = metrics.total_time()
        agg_cols[2].metric(
            "Total time spent running parkruns",
            f"{hours}h {mins}m {seconds}s",
            border=True,
        )

        st.subheader("How far would you have run from Lands End to John O Groats?")
        points = map_viz.extract_truncated_route_from_gpx(load_gpx(), metrics.total_distance() * MILE)
        start_label = 'Lands End'
        end_label = f"How far you would be: ({round(distance_metric(metrics.total_distance()))} {distance_unit()} from Lands End)"
        m = map_viz.create_map(points, start_label, end_label)
        folium_static(m)

        st.subheader("Streaks")
        streak_cols = st.columns(3)

        streak_cols[0].metric(
            "Longest streak",
            f"{metrics.longest_streak()}",
            border=True,
        )

        streak_cols[1].metric(
            "Longest gap between parkruns",
            f"{round(metrics.longest_gap_in_weeks())} wks",
            border=True,
        )

        streak_cols[2].metric(
            "Avg gap between parkruns",
            f"{round(metrics.average_gap_in_weeks(), 1)} wks",
            border=True,
        )

        st.subheader("Speed")
        speed_cols = st.columns(2)

        speed_cols[0].metric(
            "Average speed",
            f"{round(distance_metric(metrics.average_speed_km_per_hour()), 1)} {distance_unit()} / h",
            border=True,
        )

        if miles:
            hours, mins, seconds = metrics.average_speed_mins_per_mile()
        else:
            hours, mins, seconds = metrics.average_speed_mins_per_km()
        if hours > 0:
            disp_str = f"{hours}h {mins}m {seconds}s"
        else:
            disp_str = f"{mins}:{seconds}"
        speed_cols[1].metric(
            "Average speed",
            f"{disp_str} / {distance_unit()}",
            border=True,
        )

        st.subheader("Events")

        st.metric(
            "Different events",
            f"{metrics.different_event_count()}",
            border=True,
        )

        fav_parkrun, visit_count = metrics.most_popular_parkrun()
        st.metric(
            "Favourite parkrun",
            f"{fav_parkrun} ({visit_count})",
            border=True
        )

        st.metric(
            "First parkrun",
            metrics.first_parkrun(),
            border=True,
        )

        youngest_parkrun, youngest_count = metrics.youngest_event()
        st.metric(
            "Youngest event attended",
            f"{youngest_parkrun} ({youngest_count}{rank_ending(youngest_count)} edition)",
            border=True,
        )

        oldest_parkrun, oldest_count = metrics.oldest_event()
        st.metric(
            "Oldest event attended",
            f"{oldest_parkrun} ({oldest_count}{rank_ending(oldest_count)} edition)",
            border=True,
        )

    except Exception as e:
        st.write(f"An error has occurred: {e}")