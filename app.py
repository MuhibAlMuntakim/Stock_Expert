import os
from dotenv import load_dotenv
import streamlit as st
from codestral_utils import generate_graph_with_codestral, generate_pdf_with_codestral, filter_stock_data
from mistral_agent import analyze_stock_with_mistral, fetch_alpha_vantage_data

# Load environment variables from .env
load_dotenv()

# Streamlit App
st.title("Stock Market Analyzer")

# Sidebar for Stock Symbol Input
st.sidebar.title("Stock Selection")
stock_symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., META, AAPL):")

# Initialize session state for completion tracking
if "completed" not in st.session_state:
    st.session_state.completed = False

# Main Section
if stock_symbol and not st.session_state.completed:
    st.subheader(f"Analyzing Stock: {stock_symbol}")

    try:
        # Step 1: Fetch stock data via Alpha Vantage through Mistral
        alpha_vantage_data = fetch_alpha_vantage_data(stock_symbol)

        if not alpha_vantage_data or "Time Series (Daily)" not in alpha_vantage_data:
            raise ValueError("Failed to fetch valid stock data from Alpha Vantage.")

        # Step 2: Filter stock data for the last 30 days
        time_series_data = alpha_vantage_data["Time Series (Daily)"]
        stock_data = {
            "Date": list(time_series_data.keys()),
            "Close": [float(data["4. close"]) for data in time_series_data.values()],
        }
        filtered_data = filter_stock_data(stock_data, days=30)

        # Step 3: Analyze stock data using Mistral
        mistral_analysis = analyze_stock_with_mistral(stock_symbol)

        if not mistral_analysis:
            raise ValueError("Mistral did not return a valid analysis.")

        # Display Mistral Analysis
        st.text_area("Mistral Investment Analysis", mistral_analysis, height=200)

        # Step 4: Generate graph using Codestral
        graph_path = generate_graph_with_codestral(stock_symbol, filtered_data)
        st.image(graph_path, caption=f"Closing Price Trend for {stock_symbol}")

        # Step 5: Generate PDF report using Codestral
        pdf_path = generate_pdf_with_codestral(stock_symbol, mistral_analysis, graph_path)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Analysis Report",
                data=pdf_file,
                file_name=f"{stock_symbol}_report.pdf",
                mime="application/pdf"
            )

        # Mark process as completed
        st.session_state.completed = True

    except Exception as e:
        st.error(f"Error: {e}")

elif st.session_state.completed:
    st.success("Analysis completed. You can enter a new stock symbol to start again.")
else:
    st.write("Please enter a stock symbol in the sidebar.")
