from dash import dash_table,html

def generate_executive_metrics_chart(RAG, df):
    if df.empty:
        return html.Div("No data available for selected filters.", className="empty-message")
    q1 = (
        df.groupby(['metric_id', 'title'])
        .agg(
            score=('totalok', lambda x: x.sum() / df.loc[x.index, 'total'].sum()),
            slo_min=('slo_min', 'mean'),
            slo=('slo', 'mean'),
        )
        .reset_index()
    )

    q1['Score'] = (q1['score'] * 100).round(2).astype(str) + '%'

    # Create hyperlink for the 'title' column
    q1['title'] = q1.apply(
        lambda row: f"[{row['title']}](/metric/{row['metric_id']})",
        axis=1
    )

    fig = dash_table.DataTable(
        id='table',
        columns=[
            {"name": "Id" , "id" : "metric_id"},
            {"name": "Title", "id": "title", "presentation": "markdown"},
            {"name": "Score", "id": "Score"},
        ],
        data=q1.sort_values(by="score", ascending=True).to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_data={
            'textAlign': 'left',  # Align text to the left
            'whiteSpace': 'normal',  # Enable text wrapping
        },
        style_header={
            'textAlign': 'left',  # Align header text to the left
            'fontWeight': 'bold',  # Make header text bold
        },
        style_data_conditional=[
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{score} < {slo} && {score} >= {slo_min}',
                },
                'backgroundColor': RAG['amber'][0],
                'color': RAG['amber'][1]
            },
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{score} < {slo_min}',
                },
                'backgroundColor': RAG['red'][0],
                'color': RAG['red'][1]
            },
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{score} >= {slo}',
                },
                'backgroundColor': RAG['green'][0],
                'color': RAG['green'][1]
            }
        ]
    )

    return fig
