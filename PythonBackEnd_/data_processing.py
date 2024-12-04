import pandas as pd
import re
from utils import standardize_descriptions
from mappings import CATEGORY_MAPPING, DESCRIPTION_MAPPING

def clean_data(data):
    # Check if 'date' column exists, otherwise use 'Transaction Date'
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'], errors='coerce')  # Ensure 'date' column is in datetime format
    elif 'Transaction Date' in data.columns:
        data['date'] = pd.to_datetime(data['Transaction Date'], errors='coerce')  # Ensure 'Transaction Date' column is in datetime format
    else:
        raise KeyError("The input file must contain a 'date' or 'Transaction Date' column.")

    # Ensure 'description' column exists
    if 'description' in data.columns:
        data.rename(columns={'description': 'Description'}, inplace=True)
    elif 'Description' not in data.columns:
        raise KeyError("The input file must contain a 'description' or 'Description' column.")
    
    # Clean the Description field
    data['Description'] = data['Description'].apply(clean_description)
    # Convert Description and Category fields to lowercase
    data['Description'] = data['Description'].str.lower()
    if 'Category' in data.columns:
        data['Category'] = data['Category'].str.lower()
    else:
        data['Category'] = 'uncategorized'  # Assign a default category if not present

    # Map categories
    data['Category'] = data['Category'].map(CATEGORY_MAPPING).fillna(data['Category'])
    data['Month'] = data['date'].dt.to_period('M').astype(str)

    # Filter out positive amounts (assuming negative amounts are expenses)
    data = data[data['Amount'] < 0]

    # Replace NaN values with None
    data = data.where(pd.notnull(data), None).astype(object)
    
    return data

def clean_description(description):
    # Use regular expression to remove any invoice IDs or extraneous information
    cleaned_description = re.sub(r'\s*[\*#]\S+|\d+', '', description)  # Remove any * or # followed by non-whitespace characters and digits
    return cleaned_description.strip()

def determine_recurring_charges(data):
    # Ensure 'date' column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])
    
    # Ensure 'Description' column exists
    if 'Description' not in data.columns:
        raise KeyError("The data must contain a 'Description' column.")
    
    # Group by Description to identify potential recurring charges
    data['Amount'] = data['Amount'].round(2)  # Round amounts to 2 decimal places for consistency
    grouped = data.groupby('Description')

    recurring_charges = []

    for description, group in grouped:
        group = group.sort_values(by='date')
        dates = group['date'].dt.to_period('M')
        amounts = group['Amount'].values

        # Check for monthly recurrence
        if len(dates) >= 3 and all((dates.iloc[i] + 1 == dates.iloc[i + 1]) and abs(amounts[i] - amounts[i + 1]) <= 1 for i in range(len(dates) - 1)):
            total_amount = group['Amount'].sum()
            recurring_charges.append((description, total_amount, 'monthly'))
            continue

        # Check for quarterly recurrence (every 3 months)
        if len(dates) >= 3 and all((dates.iloc[i] + 3 == dates.iloc[i + 1]) and abs(amounts[i] - amounts[i + 1]) <= 5 for i in range(len(dates) - 1)):
            total_amount = group['Amount'].sum()
            recurring_charges.append((description, total_amount, 'quarterly'))
            continue

        # Check for semi-annual recurrence (every 6 months)
        if len(dates) >= 2 and all((dates.iloc[i] + 6 == dates.iloc[i + 1]) and abs(amounts[i] - amounts[i + 1]) == 0 for i in range(len(dates) - 1)):
            total_amount = group['Amount'].sum()
            recurring_charges.append((description, total_amount, 'semi-annual'))
            continue

        # Check for annual recurrence (every year)
        if len(dates) >= 2 and all((dates.iloc[i] + 12 == dates.iloc[i + 1]) and abs(amounts[i] - amounts[i + 1]) == 0 for i in range(len(dates) - 1)):
            total_amount = group['Amount'].sum()
            recurring_charges.append((description, total_amount, 'annual'))
            continue

    return pd.DataFrame(recurring_charges, columns=['Description', 'Amount', 'Frequency'])

def identify_unique_spend_patterns(data):
    # Implement your logic to identify unique spend patterns here
    return data

def analyze_recurring_charges(recurring_charges, data):
    recurring_charges = standardize_descriptions(recurring_charges, DESCRIPTION_MAPPING)
    
    # Group by frequency and calculate total amount and count for each type
    analysis = recurring_charges.groupby('Frequency').agg(
        Total_Amount=('Amount', 'sum'),
        Count=('Amount', 'size')
    ).reset_index()
    
    # Extract summaries for each frequency type
    monthly_summary = analysis[analysis['Frequency'] == 'monthly']
    quarterly_summary = analysis[analysis['Frequency'] == 'quarterly']
    semi_annual_summary = analysis[analysis['Frequency'] == 'semi-annual']
    
    # Format the summaries
    summary = "Recurring Charges Summary:\n"
    
    if not monthly_summary.empty:
        summary += f"Monthly Charges: {monthly_summary['Count'].values[0]} charges, Total Amount: ${monthly_summary['Total_Amount'].values[0]:.2f}\n"
    
    if not quarterly_summary.empty:
        summary += f"Quarterly Charges: {quarterly_summary['Count'].values[0]} charges, Total Amount: ${quarterly_summary['Total_Amount'].values[0]:.2f}\n"
    
    if not semi_annual_summary.empty:
        summary += f"Semi-Annual Charges: {semi_annual_summary['Count'].values[0]} charges, Total Amount: ${semi_annual_summary['Total_Amount'].values[0]:.2f}\n"
    
    # Extract unique descriptions with frequency types
    unique_descriptions = recurring_charges[['Description', 'Frequency']].drop_duplicates()
    summary += "\nUnique Recurring Charge Descriptions:\n"
    for _, row in unique_descriptions.iterrows():
        summary += f"{row['Description']} ({row['Frequency']})\n"
    
    return summary