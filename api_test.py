import requests
import os
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

def check_api_limit():
    # Test URL for Alpha Vantage
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()

        # Check for "Note" in the response
        if "Note" in data:
            print("API Limit Exceeded:")
            print(data["Note"])
        elif "Error Message" in data:
            print("Error:", data["Error Message"])
        else:
            print("API Call Successful. No rate limit issues detected.")
            print(data)  # Print the actual response if needed
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the check
check_api_limit()
