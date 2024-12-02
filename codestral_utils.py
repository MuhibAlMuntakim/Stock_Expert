import importlib.util
import traceback
import re
import os
import ast
from mistralai import Mistral
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Mistral client
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def clean_codestral_output(script):
    """Cleans Codestral's output by removing markdown and redundant lines."""
    try:
        script_lines = script.splitlines()
        cleaned_lines = []
        inside_code_block = False

        for line in script_lines:
            if line.strip().startswith("```python"):
                inside_code_block = True
                continue
            if line.strip().startswith("```"):
                inside_code_block = False
                continue
            if inside_code_block or re.match(r"^\s*(import|from|#|class|def|\w+\s*=|if|for|while|plt\.)", line):
                cleaned_lines.append(line)

        cleaned_script = "\n".join([line for line in cleaned_lines if line.strip()])
        validate_script_syntax(cleaned_script)  # Validate the script syntax
        return cleaned_script
    except Exception as e:
        print("Error cleaning Codestral's output:", e)
        raise ValueError("Failed to clean and validate Codestral output.") from e


def validate_script_syntax(script):
    """Validates the syntax of a Python script."""
    try:
        ast.parse(script)  # Parse the script to check syntax
    except SyntaxError as e:
        print("Syntax error detected in script:", e)
        raise ValueError("Invalid syntax in Codestral's script.") from e


def sanitize_file_name(base_name):
    """Sanitize the file name by removing invalid characters."""
    if not isinstance(base_name, str):
        raise TypeError(f"Expected a string for the file name, but got {type(base_name).__name__}")
    return re.sub(r"[^a-zA-Z0-9_-]", "", base_name)


def filter_stock_data(stock_data, days=30):
    """Filter stock data to the last N days."""
    try:
        df = pd.DataFrame(stock_data)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by="Date", ascending=False)  # Sort by date descending
        filtered_df = df.head(days)  # Get the last N days
        filtered_df["Date"] = filtered_df["Date"].dt.strftime("%Y-%m-%d")  # Convert Timestamps to strings
        return filtered_df.to_dict(orient="list")
    except Exception as e:
        print("Error filtering stock data:", e)
        raise ValueError("Error occurred while filtering stock data.") from e



def generate_graph_with_codestral(stock_symbol, filtered_data):
    """Generate a stock graph using Codestral."""
    codestral_graph_prompt = (
        f"Write a Python script using matplotlib to generate a line graph for the stock '{stock_symbol}'. "
        f"The data is provided in the variable `filtered_data`. "
        f"The variable `filtered_data` is a dictionary with two keys:\n"
        f"- 'Date': A list of strings representing dates (e.g., ['2024-11-01', '2024-11-02']).\n"
        f"- 'Close': A list of numbers representing the corresponding closing prices (e.g., [150.5, 152.0]).\n\n"
        f"Your task:\n"
        f"- Convert the 'Date' values to datetime format using pandas.\n"
        f"- Plot 'Close' against 'Date'.\n"
        f"- The graph should have:\n"
        f"  - Title: 'Closing Prices for {stock_symbol}'\n"
        f"  - X-axis label: 'Date'\n"
        f"  - Y-axis label: 'Closing Price'\n"
        f"- Save the graph as 'graph.png'.\n\n"
        f"Here is the filtered data:\n\n"
        f"filtered_data = {filtered_data}\n\n"
        f"Write the Python script for this task. Ensure the script is error-free and executable as-is."
    )

    try:
        mistral_graph_response = mistral_client.chat.complete(
            model="codestral-latest",
            messages=[
                {"role": "user", "content": codestral_graph_prompt}
            ]
        )

        raw_script = mistral_graph_response.choices[0].message.content
        print("Raw Codestral Graph Script:", raw_script)  # Debugging
        cleaned_script = clean_codestral_output(raw_script)

        sanitized_file_name = sanitize_file_name(stock_symbol)
        script_path = f"{sanitized_file_name}_graph_script.py"
        with open(script_path, "w") as script_file:
            script_file.write(cleaned_script)

        # Validate and execute the script
        spec = importlib.util.spec_from_file_location("generated_graph", script_path)
        generated_graph = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generated_graph)

        graph_output_path = "graph.png"
        return graph_output_path

    except Exception as e:
        print("Error while executing Codestral's graph script. Check the generated code and logs.")
        print("Detailed Error Traceback:", traceback.format_exc())
        raise ValueError("Codestral failed to generate a valid graph script.") from e


def generate_pdf_with_codestral(stock_symbol, mistral_analysis, graph_path):
    """Generate a PDF report using the Codestral model."""
    codestral_pdf_prompt = (
        f"Write a Python script using the FPDF library to generate a PDF report. "
        f"The report must have the title 'Stock Analysis Report for {stock_symbol}', "
        f"include the following analysis text:\n\n{mistral_analysis}\n\n"
        f"and embed the graph located at '{graph_path}'. "
        f"The script should directly create and save the PDF as '{stock_symbol}_report.pdf'. "
        f"Do not include any markdown formatting, such as ```python or ```."
    )

    try:
        mistral_pdf_response = mistral_client.chat.complete(
            model="codestral-latest",
            messages=[
                {"role": "user", "content": codestral_pdf_prompt}
            ]
        )

        pdf_script = mistral_pdf_response.choices[0].message.content
        print("Raw Codestral PDF Script:", pdf_script)  # Debugging
        cleaned_script = clean_codestral_output(pdf_script)

        sanitized_file_name = sanitize_file_name(stock_symbol)
        script_path = f"{sanitized_file_name}_pdf_script.py"
        with open(script_path, "w") as script_file:
            script_file.write(cleaned_script)

        spec = importlib.util.spec_from_file_location("generated_pdf", script_path)
        generated_pdf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generated_pdf)

        pdf_output_path = f"{stock_symbol}_report.pdf"
        return pdf_output_path

    except Exception as e:
        print("Error while executing Codestral's PDF script. Check the generated code and logs.")
        print("Detailed Error Traceback:", traceback.format_exc())
        raise ValueError("Codestral failed to generate a valid PDF script.") from e
