import time
import random

import requests
from bs4 import BeautifulSoup
import pandas as pd

PARKRUN_URL = 'https://www.parkrun.org.uk/parkrunner/{id}/all/'
RESULTS_SELECTOR = 'results'

class DataFetchError(Exception):
    pass

def get_browser_headers():
    """
    Claude generated function
    Returns headers that make the request look like it's coming from a real browser
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',  # Do Not Track
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def fetch_table_data(url: str, table_id: str, which_table: int, sleep_time=None) -> tuple[pd.DataFrame | None, str | None]:
    """
    Claude-generated function - with modifications

    Fetches table data from a webpage with optional delay and rotating user agents
    
    Args:
        url: The webpage URL
        table_id: id for the target table
        which_table: index of table to select if multiple found with this ID
        sleep_time: Optional delay between requests (in seconds)
    """
    try:
        # Optional delay to avoid hitting rate limits
        if sleep_time:
            time.sleep(random.uniform(1, sleep_time))
        
        # Make the request with browser-like headers
        response = requests.get(url, headers=get_browser_headers(), timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table
        tables = soup.find_all('table', id=table_id)
        if not tables:
            return None, f"Results table not found in {response.text}"

        table = tables[which_table]
        
        # Extract headers
        headers = []
        for th in table.find_all('th'):
            headers.append(th.text.strip())
        
        # If no headers found, create numbered columns
        if not headers:
            # Try to get the number of columns from the first row
            first_row = table.find('tr')
            if first_row:
                num_cols = len(first_row.find_all(['td', 'th']))
                headers = [f'Column {i+1}' for i in range(num_cols)]
        
        # Extract rows
        rows = []
        for tr in table.find_all('tr'):
            row = [td.text.strip() for td in tr.find_all('td')]
            if row:  # Only append non-empty rows
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers if len(headers) == len(rows[0]) else None)
        return df, None

    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"
    except Exception as e:
        return None, f"Error processing data: {str(e)}"


def fetch_parkrun_data(parkrunner_id: str, sleep_time = None) -> pd.DataFrame:
    """Fetch all results for this parkrunner as pandas dataframe."""

    results_df, msg = fetch_table_data(
        PARKRUN_URL.format(id=parkrunner_id),
        table_id = RESULTS_SELECTOR,
        which_table = -1,
        sleep_time = sleep_time,
    )

    if results_df is None:
        raise DataFetchError(msg)

    return results_df

