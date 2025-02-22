import math

import pandas as pd

MILE = 0.621371

class BadTimeFormatException(Exception):
    pass

def time_str_to_seconds(time_str: str) -> int:

    time_parts = time_str.split(':')
    if len(time_parts) > 3:
        raise BadTimeFormatException("More than 3 parts to result time")
    try:
        seconds = int(time_parts[-1])
        minutes = int(time_parts[-2])
        if len(time_parts) == 3:
            hours = int(time_parts[-3])
        else:
            hours = 0
        
        return seconds + 60 * minutes + 60 * 60 * hours

    except Exception as e:
        raise BadTimeFormatException(f"Unable to parse result time: {e}") from e

def seconds_to_hours_mins_seconds(seconds: int) -> tuple[int, int, int]:

    hours = math.floor(seconds / (60 * 60))
    remainder = seconds - (hours * 60 * 60)
    minutes = math.floor(remainder / 60)
    remainder = remainder - (minutes * 60)
    seconds = remainder

    return hours, minutes, seconds

class ParkrunMetrics:

    EXPECTED_COLS = (
        'Event',
        'Run Date',
        'Run Number',
        'Pos',
        'Time',
    )

    def __init__(self, results: pd.DataFrame):
        if any(col not in results for col in self.EXPECTED_COLS):
            raise KeyError(f"Parkrun results did not contain expected columns: {self.EXPECTED_COLS}")
        
        self.results = results.copy()
        self.results['Run Date'] = pd.to_datetime(self.results['Run Date'], dayfirst=True)
        self.results['Run Number'] = self.results['Run Number'].astype(int)
        self.results.sort_values('Run Date', inplace=True)
        self._create_seconds_col()
        self._create_gap_col()

    def _create_seconds_col(self) -> None:
        self.results['seconds'] = self.results['Time'].apply(time_str_to_seconds)

    def _create_gap_col(self) -> None:
        self.results['gaps'] = self.results['Run Date'].diff().dt.days
    
    def total_distance(self) -> float:
        return 5.0 * len(self.results)

    def total_time_seconds(self) -> int:
        return self.results['seconds'].sum()

    def total_time(self) -> tuple[int, int, int]:
        return seconds_to_hours_mins_seconds(self.total_time_seconds())

    def average_speed_km_per_hour(self) -> float:
        return (self.total_distance() / self.total_time_seconds()) * 60 * 60

    def average_speed_mins_per_km(self) -> tuple[int, int, int]:

        seconds_per_km = round(self.total_time_seconds() / self.total_distance())
        return seconds_to_hours_mins_seconds(seconds_per_km)

    def average_speed_mins_per_mile(self) -> tuple[int, int, int]:

        seconds_per_mile = round((self.total_time_seconds() / self.total_distance()) / MILE)
        return seconds_to_hours_mins_seconds(seconds_per_mile)

    def longest_gap_in_weeks(self) -> float:
        return self.results['gaps'].max() / 7

    def longest_streak(self) -> int:
        """Number of weeks without going more than 7 days without attending parkrun, +1

        Roughly best way of capturing longest consecutive parkrun streak, while not letting
        bonus holiday parkruns distort things too much.
        """

        longest_streak = -1
        current_streak = 0
        for gap in self.results['gaps'].iloc[1:].values:
            if gap <= 7:
                current_streak += gap
            else:
                longest_streak = max(longest_streak, math.floor(current_streak / 7))
                current_streak = 0

        return longest_streak + 1

    def parkruns_per_week(self) -> float:

        total_weeks = (self.results['Run Date'].max() - self.results['Run Date'].min()).days / 7
        return len(self.results) / total_weeks

    def average_gap_in_weeks(self) -> float:
        return self.results['gaps'].mean() / 7


    def different_event_count(self) -> int:
        return len(self.results['Event'].unique())

    def most_popular_parkrun(self) -> tuple[str, int]:
        event_counts = self.results['Event'].value_counts()
        assert event_counts.iloc[0] == event_counts.max()

        return event_counts.index[0], event_counts.iloc[0]

    def first_parkrun(self) -> str:
        return self.results['Event'].iloc[0]

    def youngest_event(self) -> tuple[str, int]:
        event_ages = self.results[['Event', 'Run Number']].sort_values('Run Number')
        youngest = event_ages.iloc[0]
        return youngest['Event'], youngest['Run Number']

    def oldest_event(self) -> tuple[str, int]:
        event_ages = self.results[['Event', 'Run Number']].sort_values('Run Number')
        oldest = event_ages.iloc[-1]
        return oldest['Event'], oldest['Run Number']