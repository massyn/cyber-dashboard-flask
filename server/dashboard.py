from flask import flash, redirect, session, url_for, request, render_template, send_from_directory
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import yaml
import os
from chart_overview import generate_executive_overview_chart
from chart_dimension import generate_executive_dimension_chart
from chart_category import generate_executive_category_chart
from chart_metrics import generate_executive_metrics_chart
import hashlib
from library import read_config

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

# Function to load the dataset
def load_summary():
    return pd.read_parquet(config['data']['summary'])

# Function to create Dash app
def create_dashboard(server):
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=["/static/style.css"]
    )

    # Load data
    data = load_summary()
    data_latest = data[data['datestamp'] == data['datestamp'].max()]

    # Dash layout
    app.layout = html.Div(className="app-container", children=[
        html.Div(className="sidebar", children=[
            html.H2("Filters", className="sidebar-header"),
            html.Div(className="filters-container", children=[
                html.Div([
                    html.Label(f"Select a {label}:", className="dropdown-label"),
                    dcc.Dropdown(
                        id=f"{column_name}-dropdown",
                        options=[{"label": value, "value": value} for value in sorted(data_latest.get(column_name, pd.Series()).unique())],
                        value=None,
                        placeholder=f"Select a {label}",
                        className="dropdown"
                    )
                ], className="filter-item") for column_name, label in filters.items()
            ])
        ]),
        html.Div(className="main-content", children=[
            html.Div(className="header", children=[
                html.H1("Continuous Assurance", className="header-title"),
                html.P("Visualize data interactively with customizable filters.", className="header-description"),
                html.A("Logout", href="/logout", className="logout-link")  # Add a logout link
            ]),
            html.Div(className="graph-container", children=[
                dcc.Graph(id="overview-graph", className="graph overview-graph", config={"displayModeBar": False}),
                html.Div(className="sub-graphs-container", children=[
                    dcc.Graph(id="dimension-graph", className="graph sub-graph", config={"displayModeBar": False}),
                    dcc.Graph(id="category-graph", className="graph sub-graph", config={"displayModeBar": False})
                ])
            ]),
            html.Div(className="table-container", children=[
                html.Div(className="metrics-header-container", children=[
                    html.H2("Metrics", className="metrics-header")
                ]),
                html.Div(id="metrics-table", className="metrics-table")
            ])
        ])
    ])

    # Generate callback inputs dynamically
    dropdown_inputs = [Input(f"{column_name}-dropdown", "value") for column_name in filters.keys()]

    @server.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @server.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # check if the username and password matches
            if username in config['users'] and hashlib.sha256(password.encode()).hexdigest().lower() == config['users'].get(username,'').lower():
                session['logged_in'] = True
                return redirect(url_for('/'))
            else:
                flash('Invalid username or password.', 'error')

        return render_template('login.html')

    @server.route('/logout')
    def logout():
        session.pop('logged_in', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @server.before_request
    def require_login():
        # Skip login check for static files and the login endpoint
        if request.endpoint not in ('login', 'static','/favicon.ico') and not session.get('logged_in'):
            return redirect(url_for('login'))

    # Callback to update the bar chart based on selected filters
    @app.callback(
        [Output("overview-graph", "figure"),
         Output("dimension-graph", "figure"),
         Output("category-graph", "figure"),
         Output("metrics-table", "children")],
        dropdown_inputs
    )
    def update_charts(*selected_values):
        """Update bar charts based on selected filter values."""
        df_summary = load_summary()

        # Apply filtering dynamically based on selected values
        for selected_value, (column_name, _) in zip(selected_values, filters.items()):
            if selected_value:
                df_summary = df_summary[df_summary[column_name] == selected_value]

        df_summary['score'] = df_summary['totalok'] / df_summary['total'] * df_summary['weight']

        df_summary_latest = df_summary[df_summary['datestamp'] == df_summary['datestamp'].max()]

        fig_overview = generate_executive_overview_chart(RAG, df_summary)
        fig_dimension = generate_executive_dimension_chart(RAG, config['dimensions'], df_summary_latest)
        fig_category = generate_executive_category_chart(RAG, df_summary_latest)
        fig_metrics = generate_executive_metrics_chart(RAG, df_summary_latest)

        return fig_overview, fig_dimension, fig_category, fig_metrics

    return app