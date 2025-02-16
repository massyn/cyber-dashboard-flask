from flask import flash, redirect, url_for, render_template, send_from_directory, jsonify
from dash import Dash, html, dcc, Input, Output, page_container
import pandas as pd
import os
from library import read_config, load_summary

config = read_config()

filters = config['dimensions']
RAG = config['RAG']

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
        html.Header(className="header", children=[
            html.P("Continuous Assurance", className="header-title"),
            html.P(config.get('title', 'Set the "title" field in config.yml'), className="header-description"),
        ]),
        
        html.Div(className="main-container", children=[  
            html.Aside(className="sidebar", children=[
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
                    ], className="filter-item") for column_name, label in filters.items()
                ])
            ]),
            
            html.Main(className="content", children=[
                html.Div(className="page-content", children=[page_container])
            ])
        ]),
        
        # html.Footer(className="footer", children=[
        #     html.P("Footer text here")
        # ])
    ])
    
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