from flask import flash, redirect, url_for, render_template, send_from_directory, jsonify
from dash import Dash, html, dcc, Input, Output, page_container
import pandas as pd
#import plotly.express as px
#import datetime
import os
from library import read_config, load_summary

config = read_config()

filters = config['dimensions']
RAG = config['RAG']

if not os.path.exists(config['data']['summary']):
    initial_data = pd.DataFrame({
        "datestamp": pd.Series(dtype="datetime64[ns]"),
        "metric_id": pd.Series(dtype="str"),
        "total": pd.Series(dtype="float64"),
        "totalok": pd.Series(dtype="float64"),
        "slo": pd.Series(dtype="float64"),
        "slo_min": pd.Series(dtype="float64"),
        "weight": pd.Series(dtype="float64"),
        "title": pd.Series(dtype="str"),
        "category": pd.Series(dtype="str")
    })
    for d in config['dimensions']:
        initial_data[d] = pd.Series(dtype="str")

    initial_data.to_parquet(config['data']['summary'], index=False)

# Function to create Dash app
def create_dashboard(server):
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=["/static/style.css"],
        use_pages=True
    )

    # Load data
    data = load_summary()

    initial_options = get_dropdown_options()

    # Dash layout
    app.layout = html.Div(className="app-container", children=[
        html.Div(className="sidebar", children=[
            html.H2("Filters", className="sidebar-header"),
            html.Div(className="filters-container", children=[
                html.Div([
                    html.Label(f"Select a {label}:", className="dropdown-label"),
                    dcc.Dropdown(
                        id=f"{column_name}-dropdown",
                        options=initial_options.get(column_name, []),
                        value=None,
                        placeholder=f"Select a {label}",
                        className="dropdown"
                    )
                ], className="filter-item") for column_name, label in filters.items()],
            )
        ]),
        html.Div(className="main-content", children=[
            html.Div(className="header", children=[
                html.H1("Continuous Assurance", className="header-title"),
                html.P(config.get('title','Set the "title" field in config.yml'), className="header-description"),
                # html.P("Build 1.2.3", className="footer-text")
            ]),
            page_container
        ])
    ])

    @server.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
    @app.callback(
        [Output(f"{column_name}-dropdown", "options") for column_name in filters.keys()],
        [
            Input("overview-graph", "id")
            #,Input("overview-detail-graph", "id")
        ]
    )
    def update_dropdown_options(_):
        return list(get_dropdown_options().values())

def get_dropdown_options():
    df_summary = load_summary()
    
    if df_summary.empty:
        return {col: [] for col in filters.keys()}  # Return empty lists if no data

    data_latest = df_summary[df_summary['datestamp'] == df_summary['datestamp'].max()]
    dropdown_options = {
        column_name: [{"label": value, "value": value} for value in sorted(data_latest[column_name].dropna().unique())]
        for column_name in filters.keys()
    }
    
    return dropdown_options