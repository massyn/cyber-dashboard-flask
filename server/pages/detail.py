import dash
from dash import html, dcc, callback, Input, Output
from library import read_config, load_summary, load_detail, data_last_12_items
from chart_overview import generate_executive_overview_chart
from chart_detail import generate_detail_table
import pandas as pd

config = read_config()
filters = config['dimensions']
RAG = config['RAG']

dash.register_page(__name__, path_template='/metric/<metric>')

dropdown_inputs = [Input(f"{column_name}-dropdown", "value") for column_name in filters.keys()]

def layout(metric = None):
    return html.Div([
        html.Div([
            dcc.Link("Back", href="/", className="back-button"),
        ], className="back-button-container"),
        html.H1(f"Metric: {metric}"),
        dcc.Store(id="metric-id-store", data=metric),
        html.Div([
            html.Div(className="graph-container", children=[
                dcc.Graph(id="overview-detail-graph", className="graph overview-graph", config={"displayModeBar": False}),
            ]),
            html.Div(className="table-container", children=[
            html.Div(className="metrics-header-container", children=[
                html.H2("Detail", className="metrics-header")
            ]),
            html.Div(id="detail-table", className="metrics-table")
        ])
        ])
    ])

@callback(
    [
        Output("overview-detail-graph", "figure"),
        Output("detail-table", "children")
    ],
    [Input("metric-id-store", "data")] + dropdown_inputs
)
def update_detail(metric_id,*selected_values):
    df_summary = load_summary()

    # Apply filtering dynamically based on selected values
    for selected_value, (column_name, _) in zip(selected_values, filters.items()):
        if selected_value:
            df_summary = df_summary[df_summary[column_name] == selected_value]

    # filter df_summary by metric_id
    df_summary = df_summary[df_summary['metric_id'] == metric_id]
    df_summary['score'] = df_summary['totalok'] / df_summary['total'] * df_summary['weight']
    fig_overview = generate_executive_overview_chart(RAG, data_last_12_items(df_summary),"Metric Overview")

    df_metric = load_detail()
    
    # Apply filtering dynamically based on selected values
    for selected_value, (column_name, _) in zip(selected_values, filters.items()):
        if selected_value:
            df_metric = df_metric[df_metric[column_name] == selected_value]

    # filter df_summary by metric_id
    df_metric = df_metric[df_metric['metric_id'] == metric_id]
    
    fig_table = generate_detail_table(RAG,df_metric)
    
    return fig_overview,fig_table
