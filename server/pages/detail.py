import dash
from dash import html, dcc, callback, Input, Output
from library import read_config, load_summary, load_detail, data_last_12_items
from chart_overview import generate_executive_overview_chart
from chart_detail import generate_detail_table
import pandas as pd
from chart_dimension import generate_executive_dimension_chart

config = read_config()
filters = config['dimensions']
RAG = config['RAG']

dash.register_page(__name__, path_template='/metric/<metric>')

dropdown_inputs = [Input(f"{column_name}-dropdown", "value") for column_name in filters.keys()]

def layout(metric = None):
    return html.Div([
        html.Div([
            dcc.Link("Home", href="/", className="button"),
            dcc.Link("About", href="/about", className="button"),
        ], className="button-container"),
        html.H1(f"Metric: {metric}"),
        dcc.Store(id="metric-id-store", data=metric),
        html.Div(className="graph-container", children=[
            html.Div(className="sub-graphs-container", children=[
                dcc.Graph(id="overview-detail-graph", className="graph sub-graph", config={"displayModeBar": False}),
                dcc.Graph(id="detail-dimension-graph", className="graph sub-graph", config={"displayModeBar": False}),
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
        Output("detail-dimension-graph", "figure"),
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
    
    latest_datestamp, indicator_value = df_summary.loc[df_summary['datestamp'].idxmax(), ['datestamp', 'indicator']]
    
    fig_overview = generate_executive_overview_chart(RAG, data_last_12_items(df_summary),"Metric Overview","An overview of the metric's score over time",indicator_value)

    df_metric = load_detail()
    
    # Apply filtering dynamically based on selected values
    for selected_value, (column_name, _) in zip(selected_values, filters.items()):
        if selected_value:
            df_metric = df_metric[df_metric[column_name] == selected_value]

    df_metric = df_metric[df_metric['metric_id'] == metric_id]  # filter df_summary by metric_id
    df_metric = df_metric.sort_values(by='compliance', ascending=True) # sort by compliance
    
    if config.get('privacy'):
        df_metric['detail'] = 'redacted - privacy enabled'
        df_metric['resource'] = 'redacted - privacy enabled'

    fig_table = generate_detail_table(RAG,df_metric)

    df_summary_latest = df_summary.merge(
        df_summary.groupby('metric_id', as_index=False).agg({'datestamp': 'max'}),
        on=['metric_id', 'datestamp'],
        how='inner'
    )

    fig_dimension = generate_executive_dimension_chart(RAG, config['dimensions'], df_summary_latest)
    
    return fig_overview,fig_dimension,fig_table
