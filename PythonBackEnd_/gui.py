import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinterhtml import HtmlFrame  # Import HtmlFrame
from main import main, plot_transactions, COLOR_PALETTE

def run_gui():
    print("Running GUI...")
    try:
        data, monthly_spending_data, outlier_months, summary = main()
        print("Data loaded from main function.")
    except Exception as e:
        print(f"Error loading data from main function: {e}")
        return

    if data is None:
        print("No data returned from main function.")
        return

    try:
        # Create subplots with adjusted height for better readability
        total_plots = len(outlier_months) + 1
        vertical_spacing = min(0.024, 1 / (total_plots - 1))
        fig = make_subplots(rows=total_plots, cols=1, shared_xaxes=False, vertical_spacing=vertical_spacing)
        
        # Line chart for monthly spending comparison
        for category in monthly_spending_data.columns:
            fig.add_trace(go.Scatter(x=monthly_spending_data.index, y=monthly_spending_data[category], mode='lines+markers', name=category, line=dict(color=COLOR_PALETTE.get(category, 'grey'))), row=1, col=1)
        
        fig.update_layout(title='Monthly Spending Comparison', xaxis_title='Month', yaxis_title='Amount', legend_title='Category')

        # Bar charts for outlier months with more space for readability
        current_row = 2
        for month, category in outlier_months:
            # Extract the most negative transactions for the outlier month and category
            top_transactions = data[(data['Transaction Date'].dt.to_period('M').astype(str) == month) & (data['Category'] == category)].nsmallest(10, 'Amount')
            color = COLOR_PALETTE.get(category, 'grey')  # Use default color if category not found
            xaxis_title = f"{month} - {category}"
            bar_trace, row, xaxis_title = plot_transactions(top_transactions, f'Top Transactions for {category} in {month}', color, current_row, xaxis_title)
            if bar_trace:
                fig.add_trace(bar_trace, row=row, col=1)
                fig.update_xaxes(title_text=xaxis_title, row=row, col=1)
                fig.update_yaxes(title_text='Amount', row=row, col=1)
                current_row += 1
        
        # Adjusting layout for better readability
        fig.update_layout(height=300 * total_plots, showlegend=True, title_text="Monthly Spending and Outlier Transactions")

        # Save the plot as an HTML file
        plot_div = plot(fig, output_type='div', include_plotlyjs=True)
        print("Plot created.")
        print(f"Plot div content length: {len(plot_div)}")
    except Exception as e:
        print(f"Error creating plot: {e}")
        return

    try:
        # Create the GUI
        root = tk.Tk()
        root.title("Spending Analysis")
        print("GUI window created.")

        # Create a frame for the summary
        summary_frame = ttk.LabelFrame(root, text="Summary")
        summary_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create a scrolled text widget for the summary
        summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, width=80, height=20)
        summary_text.grid(row=0, column=0, padx=10, pady=10)
        summary_text.insert(tk.END, format_summary(summary))
        summary_text.config(state=tk.DISABLED)
        print("Summary section created.")

        # Create a frame for the plot
        plot_frame = ttk.LabelFrame(root, text="Plot")
        plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        try:
            # Reintroduce the HtmlFrame widget
            print("Creating HtmlFrame...")
            plot_html = HtmlFrame(plot_frame, horizontal_scrollbar="auto")
            print("HtmlFrame created.")
            print("Setting content for HtmlFrame...")
            plot_html.set_content(plot_div)
            print("Content set for HtmlFrame.")
            plot_html.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            print("Plot section created.")
        except Exception as e:
            print(f"Error creating HtmlFrame: {e}")
            messagebox.showerror("Error", f"Failed to create plot section: {e}")

        root.mainloop()
        print("GUI loop started.")
    except Exception as e:
        print(f"Error creating GUI: {e}")

def format_summary(summary):
    # Format the summary string to be more readable
    formatted_summary = ""
    lines = summary.split('\n')
    for line in lines:
        if line.startswith("Total") or line.startswith("Outlier Months"):
            formatted_summary += f"\n{line}\n"
        elif line:
            formatted_summary += f"  {line}\n"
    return formatted_summary

if __name__ == "__main__":
    run_gui()
