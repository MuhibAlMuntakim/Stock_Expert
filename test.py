import os
import time
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Constants
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")  # Fetch API key from .env
BASE_URL = "https://www.alphavantage.co/query"
CACHE_FILE = "stock_cache.json"
CACHE_EXPIRY = timedelta(hours=1)  # Cache expiry time (1 hour)

def load_cache():
    """Load the cache from a JSON file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save the cache to a JSON file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def fetch_stock_data(symbol):
    """Fetch stock data from Alpha Vantage API with caching and rate limit handling."""
    if not API_KEY:
        raise ValueError("API key is missing. Make sure ALPHA_VANTAGE_API_KEY is set in the .env file.")

    cache = load_cache()
    current_time = datetime.now()

    # Check if data is in cache and not expired
    if symbol in cache:
        cached_time = datetime.strptime(cache[symbol]["timestamp"], "%Y-%m-%d %H:%M:%S")
        if current_time - cached_time < CACHE_EXPIRY:
            print(f"Using cached data for {symbol}")
            return cache[symbol]["data"]

    # API parameters
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY,
    }

    # Retry logic for handling rate limits
    retries = 3
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1}: Fetching stock data for {symbol}...")
            response = requests.get(BASE_URL, params=params)
            data = response.json()

            # Debug: Print the full API response
            print(f"Full API Response (Attempt {attempt + 1}):\n{json.dumps(data, indent=2)}")

            # Check for rate limit message
            if "Note" in data and "API call frequency" in data["Note"]:
                raise Exception("Rate limit exceeded. Retrying...")

            # Handle Alpha Vantage error messages
            if "Error Message" in data:
                raise Exception(f"Error from API: {data['Error Message']}")
            if "Information" in data:
                raise Exception(f"API Information: {data['Information']}")

            # Check for valid data
            if "Time Series (Daily)" in data:
                # Cache the data
                cache[symbol] = {
                    "data": data,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                save_cache(cache)
                return data
            else:
                raise Exception("Invalid response received from API.")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(60)  # Wait before retrying
            else:
                raise

if __name__ == "__main__":
    stock_symbol = "AAPL"  # Replace with your desired stock symbol

    try:
        # Fetch stock data and display the result
        stock_data = fetch_stock_data(stock_symbol)
        print("\nStock Data Retrieved:")
        print(json.dumps(stock_data, indent=2))

        # Extract key metrics for display (e.g., latest closing price)
        time_series = stock_data.get("Time Series (Daily)", {})
        if time_series:
            latest_date = max(time_series.keys())
            latest_data = time_series[latest_date]
            print(f"\nLatest Data for {stock_symbol} on {latest_date}:")
            print(json.dumps(latest_data, indent=2))
        else:
            print("No time series data found.")

    except Exception as e:
        print(f"Failed to fetch stock data: {e}")
