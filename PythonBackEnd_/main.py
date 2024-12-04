from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import read_and_prepare_data
from data_processing import clean_data, determine_recurring_charges, analyze_recurring_charges
from analytics import identify_unique_spend_patterns
from mappings import COLOR_PALETTE
from dotenv import load_dotenv
import traceback

# Load environment variables from .env file
load_dotenv()
file_paths = [
    os.getenv('FILE_PATH_1'),
    os.getenv('FILE_PATH_2'),
    os.getenv('FILE_PATH_3'),
    os.getenv('FILE_PATH_4')
]

app = Flask(__name__)
CORS(app)

def main():
    print("File paths:", file_paths)  # Debugging statement to check file paths
    data = read_and_prepare_data(file_paths)
    
    if data is None or data.empty:
        print("Error: No data was read. Please check the file paths and the data files.")
        return None, None, None, None
    
    print("Data after reading and preparing:", data.head())  # Debugging statement to check data

    # Clean the data
    data = clean_data(data)
    print("Data after cleaning:", data.head())  # Debugging statement to check cleaned data

    # Ensure 'Amount' column is treated as numerical data
    data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce')
    print("Data with numerical Amount:", data.head())  # Debugging statement to check numerical Amount

    # Determine recurring charges
    recurring_charges = determine_recurring_charges(data)
    print("Recurring charges:", recurring_charges.head())  # Debugging statement to check recurring charges
    recurring_charges_summary = analyze_recurring_charges(recurring_charges, data)
    print("Recurring charges summary:", recurring_charges_summary)  # Debugging statement to check recurring charges summary

    # Identify unique spend patterns
    unique_spend_patterns = identify_unique_spend_patterns(data)
    print("Unique spend patterns:", unique_spend_patterns.head())  # Debugging statement to check unique spend patterns

    # Calculate monthly spending data
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    monthly_spending_data = data.groupby([data['date'].dt.to_period('M'), 'Category'])['Amount'].sum().unstack()
    monthly_spending_data.index = monthly_spending_data.index.astype(str)  # Convert Period to string

    if monthly_spending_data.empty:
        print("Error: No monthly spending data available.")
        return None, None, None, None

    print("Monthly spending data:", monthly_spending_data.head())  # Debugging statement to check monthly spending data

    # Ensure that the data is numerical
    monthly_spending_data = monthly_spending_data.apply(pd.to_numeric, errors='coerce')
    print("Monthly spending data with numerical values:", monthly_spending_data.head())  # Debugging statement to check numerical monthly spending data

    # Handle NaN values by filling them with None
    monthly_spending_data = monthly_spending_data.where(pd.notnull(monthly_spending_data), None).astype(object)

    # Calculate mean and standard deviation for each category manually
    category_stats = monthly_spending_data.agg(['mean', 'std']).T
    print("Category stats:", category_stats)  # Debugging statement to check category stats
    if 'mean' not in category_stats.columns or 'std' not in category_stats.columns:
        print("Error: Unable to calculate mean and standard deviation for categories.")
        return None, None, None, None

    category_stats['threshold'] = category_stats['mean'] - 1.5 * category_stats['std']

    # Set a minimum threshold value (15% of overall monthly volume)
    minimum_threshold_percentage = 0.15

    # Identify outlier months for each category
    outlier_months = []
    for month in monthly_spending_data.index:
        overall_monthly_volume = abs(monthly_spending_data.loc[month].sum())
        minimum_threshold_value = overall_monthly_volume * minimum_threshold_percentage
        for category in monthly_spending_data.columns:
            category_value = abs(monthly_spending_data.loc[month, category])
            if category_value >= minimum_threshold_value:
                category_threshold = category_stats.loc[category, 'threshold']
                if monthly_spending_data.loc[month, category] < category_threshold:
                    outlier_months.append((month, category))

    # High-level summary of spending
    total_spent = data['Amount'].sum()
    total_recurring = recurring_charges['Amount'].sum()
    total_unique_patterns = unique_spend_patterns['Amount'].sum()
    unique_patterns_summary = unique_spend_patterns[['date', 'Description', 'Category', 'Amount']].to_string(index=False)
    unique_patterns_by_category = unique_spend_patterns['Category'].value_counts().to_string()
    summary = (
        f"Total Spending: ${total_spent:.2f}\n"
        f"Total Recurring Charges: ${total_recurring:.2f}\n"
        f"{recurring_charges_summary}\n"
        f"Total Unique Spend Patterns: ${total_unique_patterns:.2f}\n"
        f"Unique Spend Patterns Details:\n{unique_patterns_summary}\n"
        f"\nNumber of Unique Patterns by Category:\n{unique_patterns_by_category}\n"
        f"Outlier Months: {len(outlier_months)}\n"
    )
    print(summary)

    return data, monthly_spending_data, outlier_months, summary

def plot_transactions(transactions, title, color, row, xaxis_title):
    if not transactions.empty:
        bar_trace = go.Bar(x=transactions['Description'], y=transactions['Amount'], name=title, marker_color=color)
        return bar_trace, row, xaxis_title
    else:
        return None, row, xaxis_title

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        data, monthly_spending_data, outlier_months, summary = main()
        if data is None or monthly_spending_data is None:
            return jsonify({'error': 'No data was read. Please check the file paths and the data files.'}), 400

        # Replace NaN values with None (null in JSON)
        data = data.where(pd.notnull(data), None).astype(object)
        monthly_spending_data = monthly_spending_data.where(pd.notnull(monthly_spending_data), None).astype(object)

        response = {
            'data': data.to_dict(orient='records'),
            'monthly_spending_data': monthly_spending_data.to_dict(orient='index'),
            'outlier_months': outlier_months,
            'summary': summary
        }

        print("Response:", response)  # Log the response

        return jsonify(response)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/plot', methods=['GET'])
def get_plot():
    try:
        data, monthly_spending_data, outlier_months, summary = main()
        total_plots = len(outlier_months) + 1
        vertical_spacing = min(0.024, 1 / (total_plots - 1))
        fig = make_subplots(rows=total_plots, cols=1, shared_xaxes=False, vertical_spacing=vertical_spacing)
        
        for category in monthly_spending_data.columns:
            fig.add_trace(go.Scatter(x=monthly_spending_data.index, y=monthly_spending_data[category], mode='lines+markers', name=category, line=dict(color=COLOR_PALETTE.get(category, 'grey'))), row=1, col=1)
        
        fig.update_layout(title='Monthly Spending Comparison', xaxis_title='Month', yaxis_title='Amount', legend_title='Category')

        current_row = 2
        for month, category in outlier_months:
            top_transactions = data[(data['date'].dt.to_period('M').astype(str) == month) & (data['Category'] == category)].nsmallest(10, 'Amount')
            color = COLOR_PALETTE.get(category, 'grey')
            xaxis_title = f"{month} - {category}"
            bar_trace, row, xaxis_title = plot_transactions(top_transactions, f'Top Transactions for {category} in {month}', color, current_row, xaxis_title)
            if bar_trace:
                fig.add_trace(bar_trace, row=row, col=1)
                fig.update_xaxes(title_text=xaxis_title, row=row, col=1)
                fig.update_yaxes(title_text='Amount', row=row, col=1)
                current_row += 1
        
        fig.update_layout(height=300 * total_plots, showlegend=True, title_text="Monthly Spending and Outlier Transactions")
        
        # Return the data and layout directly
        return jsonify({'data': fig.data, 'layout': fig.layout})
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)