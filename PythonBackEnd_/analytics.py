# FILE: analytics.py

import pandas as pd
from utils import standardize_descriptions

def calculate_z_scores(data):
    data['Z-Score'] = data.groupby('Category')['Amount'].transform(lambda x: (x - x.mean()) / x.std())
    return data

def identify_unique_spend_patterns(data, z_score_threshold=3):
    data = calculate_z_scores(data)
    unique_spend_patterns = data[data['Z-Score'].abs() > z_score_threshold]
    unique_spend_patterns = unique_spend_patterns.sort_values(by='Z-Score', ascending=True)
    return unique_spend_patterns

# Add any other analytic functions here
