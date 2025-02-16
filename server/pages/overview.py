import dash
from dash import html, dcc, callback, Input, Output
from chart_overview import generate_executive_overview_chart
from chart_dimension import generate_executive_dimension_chart
from chart_category import generate_executive_category_chart
from chart_metrics import generate_executive_metrics_chart
from library import read_config, load_summary, data_last_12_items
import pandas as pd

config = read_config()
filters = config['dimensions']
RAG = config['RAG']

dash.register_page(__name__, path='/')

dropdown_inputs = [Input(f"{column_name}-dropdown", "value") for column_name in filters.keys()]

def layout():
    return [
        html.Div([
            dcc.Link("About", href="/about", className="back-button"),
        ], className="back-button-container"),
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
    ]

@callback(
    [Output("overview-graph", "figure"),
        Output("dimension-graph", "figure"),
        Output("category-graph", "figure"),
        Output("metrics-table", "children")],
    dropdown_inputs
)
def update_charts(*selected_values):
    df_summary = load_summary()

    # Apply filtering dynamically based on selected values
    for selected_value, (column_name, _) in zip(selected_values, filters.items()):
        if selected_value:
            df_summary = df_summary[df_summary[column_name] == selected_value]

    df_summary['score'] = df_summary['totalok'] / df_summary['total'] * df_summary['weight']

    df_summary_latest = df_summary.merge(
        df_summary.groupby('metric_id', as_index=False).agg({'datestamp': 'max'}),
        on=['metric_id', 'datestamp'],
        how='inner'
    )

    fig_overview = generate_executive_overview_chart(RAG, data_last_12_items(df_summary))
    fig_dimension = generate_executive_dimension_chart(RAG, config['dimensions'], df_summary_latest)
    fig_category = generate_executive_category_chart(RAG, df_summary_latest)
    
    df_summary_latest = df_summary_latest[pd.to_datetime(df_summary_latest['datestamp']).dt.tz_localize('UTC') >= (pd.Timestamp.now(tz='UTC') - pd.DateOffset(days=config.get('stale_metric', 2)))]

    fig_metrics = generate_executive_metrics_chart(RAG, df_summary_latest)

    return fig_overview, fig_dimension, fig_category, fig_metrics
