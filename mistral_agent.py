import os
import json
import requests
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Mistral client
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def fetch_alpha_vantage_data(symbol):
    """Fetch stock data from Alpha Vantage API."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("Alpha Vantage API key is missing. Please check your .env file.")

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Alpha Vantage API call failed: {response.status_code}, {response.text}")

def analyze_stock_with_mistral(stock_symbol):
    """Analyze stock data using Mistral AI function calling."""
    # Define tools for Mistral
    tools = [
        {
            "type": "function",
            "function": {
                "name": "fetch_alpha_vantage_data",
                "description": "Fetch stock market data for a given stock symbol using the Alpha Vantage API.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol to retrieve data for (e.g., AAPL, MSFT)."
                        }
                    },
                    "required": ["symbol"]
                },
            },
        }
    ]

    # Define the initial prompt
    prompt = (
    f"Provide an investment analysis for the stock {stock_symbol}. "
    "Use the provided tool to fetch stock market data, including daily closing prices, and follow these steps to deliver actionable insights: "
    "\n\n"
    "1. Retrieve stock data for the past 30 days using the 'fetch_alpha_vantage_data' tool. "
    "\n\n"
    "2. Analyze the data to classify the stock based on the following risk categories: "
    "- 'Low Risk': Minimal price fluctuations, stable trend, and low volatility. "
    "- 'Moderate Risk': Moderate price changes and trend variations. "
    "- 'High Risk': High volatility, frequent trend reversals, or sharp price movements."
    "\n\n"
    "3. Begin your response with a clear statement of the classification (e.g., 'NVDA is classified as High Risk'). "
    "Then, provide a detailed explanation of the classification by referencing key metrics and observations from your analysis: "
    "- Calculate price volatility as the percentage difference between the highest and lowest closing prices over the period. "
    "- Highlight the overall trend (e.g., uptrend, downtrend, or flat) and note significant turning points. "
    "- If trading volume data is available, analyze its relationship with price changes and note key observations."
    "\n\n"
    "4. Offer investment recommendations based on your findings: "
    "- Suggest whether to 'Buy,' 'Hold,' or 'Sell' the stock and explain the reasoning behind your advice."
    "\n\n"
    "Structure your response professionally, starting with the classification, followed by a summary of the analysis, and concluding with actionable recommendations."
)



    # Send the initial request to Mistral
    response = mistral_client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice="any"
    )

    # Log the response for debugging
    print("Full Response from Mistral:", response)

    # Extract the tool call from the response
    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        # Get the first tool call
        tool_call = tool_calls[0]
        print("Tool Call Made by Mistral:", tool_call)  # Debugging

        if tool_call.function.name == "fetch_alpha_vantage_data":
            arguments = json.loads(tool_call.function.arguments)
            # Execute the function to fetch stock data
            stock_data = fetch_alpha_vantage_data(arguments["symbol"])

            # Respond to Mistral with the tool result
            follow_up_response = mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "tool",
                        "name": "fetch_alpha_vantage_data",
                        "content": json.dumps(stock_data),
                        "tool_call_id": tool_call.id  # Use tool_call.id instead of tool_call.tool_call_id
                    },
                    {
                        "role": "assistant",
                        "content": "The tool has returned the stock data. Please analyze the result and classify the stock as Low Risk, Moderate Risk, or High Risk with reasoning.",
                        "prefix": True
                    }
                ]
            )

            # Return the analysis result from Mistral
            return follow_up_response.choices[0].message.content.strip()

    raise ValueError("Mistral did not make a valid tool call for fetching stock data.")

