import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import gpxpy

from parkrun_metrics import ParkrunMetrics, MILE
from fetch_parkrun_data import fetch_parkrun_data
import map_viz

DEBUG = True
GPX_FILE = 'end_to_end_example_main_route.gpx'
MISSING_METRIC = '--'

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
number_of_parkruns = st.number_input("Or just enter the number of parkruns completed", min_value=1, value=1)
miles_or_km = st.selectbox("Miles or Kilometers", ("Miles", "Kilometers"), index=1)
miles = miles_or_km == "Miles"

st.markdown("Parkrunner ID lookup only works when running locally, due to robot detection. Code can be found [here](%s)." % "https://github.com/tobycrisford/parkrun_viz")

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

        if (parkrunner_select is None) or (parkrunner_select == ''):
            metrics = None
        else:
            try:
                metrics = load_data(parkrunner_select)
            except Exception as e:
                st.warning(f"Unable to fetch data for parkrunner ID: {e}.\nIf this looks like robot detection, try cloning repo and running app locally instead, or just enter a number of parkruns.")
                metrics = None

        st.subheader("Totals")
        agg_cols = st.columns(3)

        metric = str(number_of_parkruns) if metrics is None else str(len(metrics.results))
        agg_cols[0].metric(
            "Total parkruns",
            metric,
            border=True,
        )
        
        if metrics is not None:
            dist = metrics.total_distance()
        else:
            dist = 5 * number_of_parkruns
        metric = f"{round(distance_metric(dist), 1)} {distance_unit()}"
        agg_cols[1].metric(
            "Total distance covered during parkruns",
            metric,
            border = True,
        )

        if metrics is not None:
            hours, mins, seconds = metrics.total_time()
            metric = f"{hours}h {mins}m {seconds}s"
        else:
            metric = MISSING_METRIC
        agg_cols[2].metric(
            "Total time spent running parkruns",
            metric,
            border=True,
        )

        st.subheader("How far would you have run from Lands End to John O Groats?")
        points, distance_reached = map_viz.extract_truncated_route_from_gpx(load_gpx(), dist * MILE)
        start_label = 'Lands End'
        if distance_reached:
            end_label = f"How far you would be: ({round(distance_metric(dist))} {distance_unit()} from Lands End)"
        else:
            end_label = "You've made it all the way to John O Groats and some!"
        m = map_viz.create_map(points, start_label, end_label)
        folium_static(m)

        st.subheader("Streaks")
        streak_cols = st.columns(3)

        metric = MISSING_METRIC if metrics is None else f"{metrics.longest_streak()}"
        streak_cols[0].metric(
            "Longest streak",
            metric,
            border=True,
        )

        metric = MISSING_METRIC if metrics is None else f"{round(metrics.longest_gap_in_weeks())} wks"
        streak_cols[1].metric(
            "Longest gap between parkruns",
            metric,
            border=True,
        )

        metric = MISSING_METRIC if metrics is None else f"{round(metrics.average_gap_in_weeks(), 1)} wks"
        streak_cols[2].metric(
            "Avg gap between parkruns",
            metric,
            border=True,
        )

        st.subheader("Speed")
        speed_cols = st.columns(2)

        metric = MISSING_METRIC if metrics is None else f"{round(distance_metric(metrics.average_speed_km_per_hour()), 1)} {distance_unit()} / h"
        speed_cols[0].metric(
            "Average speed",
            metric,
            border=True,
        )

        if metrics is not None:
            if miles:
                hours, mins, seconds = metrics.average_speed_mins_per_mile()
            else:
                hours, mins, seconds = metrics.average_speed_mins_per_km()
            if hours > 0:
                disp_str = f"{hours}h {mins}m {seconds}s"
            else:
                disp_str = f"{mins}:{seconds}"
            metric = f"{disp_str} / {distance_unit()}"
        else:
            metric = MISSING_METRIC
        speed_cols[1].metric(
            "Average speed",
            metric,
            border=True,
        )

        st.subheader("Events")

        metric = MISSING_METRIC if metrics is None else f"{metrics.different_event_count()}"
        st.metric(
            "Different events",
            metric,
            border=True,
        )

        if metrics is not None:
            fav_parkrun, visit_count = metrics.most_popular_parkrun()
            metric = f"{fav_parkrun} ({visit_count})"
        else:
            metric = MISSING_METRIC
        st.metric(
            "Favourite parkrun",
            metric,
            border=True
        )

        metric = MISSING_METRIC if metrics is None else metrics.first_parkrun()
        st.metric(
            "First parkrun",
            metric,
            border=True,
        )

        if metrics is not None:
            youngest_parkrun, youngest_count = metrics.youngest_event()
            metric = f"{youngest_parkrun} ({youngest_count}{rank_ending(youngest_count)} edition)"
        else:
            metric = MISSING_METRIC
        st.metric(
            "Youngest event attended",
            metric,
            border=True,
        )

        if metrics is not None:
            oldest_parkrun, oldest_count = metrics.oldest_event()
            metric = f"{oldest_parkrun} ({oldest_count}{rank_ending(oldest_count)} edition)"
        else:
            metric = MISSING_METRIC
        st.metric(
            "Oldest event attended",
            metric,
            border=True,
        )

    except Exception as e:
        st.write(f"An error has occurred: {e}")