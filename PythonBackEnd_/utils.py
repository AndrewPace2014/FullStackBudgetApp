import pandas as pd
import os
import warnings

def read_and_prepare_data(file_paths):
    data_frames = []
    date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']  # List of possible date formats

    for file_path in file_paths:
        print(f"Processing file: {file_path}")  # Debugging statement to check file paths
        if not os.path.exists(file_path):
            print(f"Error: File not found - {file_path}")
            continue
        try:
            df = pd.read_csv(file_path)
            print(f"Data read from {file_path}: {df.head()}")  # Debugging statement to check data read
            if 'Posting Date' in df.columns:
                # Process File Type 1
                df = df.rename(columns={
                    'Posting Date': 'Transaction Date',
                    'Description': 'Description',
                    'Amount': 'Amount',
                    'Type': 'Type',
                    'Balance': 'Balance',
                    'Check or Slip #': 'Check or Slip #'
                })
            elif 'Transaction Date' in df.columns:
                # Process File Type 2
                df = df.rename(columns={
                    'Transaction Date': 'Transaction Date',
                    'Post Date': 'Post Date',
                    'Description': 'Description',
                    'Category': 'Category',
                    'Type': 'Type',
                    'Amount': 'Amount',
                    'Memo': 'Memo'
                })
            else:
                print(f"Unknown file format: {file_path}")
                continue

            # Suppress warnings related to date parsing
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                for date_format in date_formats:
                    try:
                        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format=date_format, errors='raise')
                        break
                    except ValueError:
                        continue
                df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
            
            df = df.dropna(subset=['Transaction Date'])  # Drop rows with invalid dates

            # Ensure 'Amount' column is treated as numerical data
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

            data_frames.append(df)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    if data_frames:
        # Filter out empty DataFrames before concatenation
        data_frames = [df for df in data_frames if not df.empty]
        if data_frames:
            combined_data = pd.concat(data_frames, ignore_index=True)
            print(f"Combined data: {combined_data.head()}")  # Debugging statement to check combined data
            return combined_data
    return pd.DataFrame()  # Return an empty DataFrame instead of None

def filter_and_group_data(data, category):
    filtered_data = data[data['Category'] == category]
    grouped_data = filtered_data.groupby(['Transaction Date', 'Description'])['Amount'].sum().reset_index()
    return grouped_data

def extract_top_transactions(data, month, category, top_n=5):
    monthly_data = data[(data['Transaction Date'].dt.to_period('M') == month) & (data['Category'] == category)]
    top_transactions = monthly_data.nlargest(top_n, 'Amount')
    return top_transactions

def standardize_descriptions(data, description_mapping):
    data['Description'] = data['Description'].str.lower().str.strip()
    data['Description'] = data['Description'].replace(description_mapping)
    return data