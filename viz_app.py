import streamlit as st
import pandas as pd

from parkrun_metrics import ParkrunMetrics, MILE

@st.cache_data
def fetch_data(parkrunner_id: str) -> pd.DataFrame:
    #Placeholder
    return pd.read_csv('my_data.csv')

@st.cache_data
def load_data(parkrunner_id: str) -> pd.DataFrame:
    return ParkrunMetrics(fetch_data(parkrunner_id))

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

if st.button("Submit"):
    try:

        metrics = load_data(parkrunner_select)

        agg_cols = st.columns(2)

        agg_cols[0].metric(
            "Total Distance",
            f"{round(distance_metric(metrics.total_distance()), 1)} {distance_unit()}",
            border = True,
        )

        hours, mins, seconds = metrics.total_time()
        agg_cols[1].metric(
            "Total Time",
            f"{hours}h {mins}m {seconds}s",
            border=True,
        )

    except Exception as e:
        st.write(f"An error has occurred: {e}")