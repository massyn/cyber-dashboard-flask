from dash import dash_table

def generate_executive_metrics_chart(RAG,df):

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

    fig = dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in q1.columns],
        data=q1.sort_values(by="score", ascending=True).to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_data_conditional=[
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{score} < {slo} && {score} >= {slo_min}',
                },
                'backgroundColor': RAG['amber'][0],
                'color': 'white'
            },
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{score} < {slo_min}',
                },
                'backgroundColor': RAG['red'][0],
                'color': 'white'
            },
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{score} >= {slo}',
                },
                'backgroundColor': RAG['green'][0],
                'color': 'white'
            },
            {
                'if': {
                    'column_id': 'score',
                },
                'display': 'none'
            },
            {
                'if': {
                    'column_id': 'slo',
                },
                'display': 'none'
            },
            {
                'if': {
                    'column_id': 'slo_min',
                },
                'display': 'none'
            }
        ],
        style_header_conditional=[
            {
                'if': {
                    'column_id': 'score',
                },
                'display': 'none'
            },
            {
                'if': {
                    'column_id': 'slo',
                },
                'display': 'none'
            },
            {
                'if': {
                    'column_id': 'slo_min',
                },
                'display': 'none'
            }
        ]
    )

    return fig