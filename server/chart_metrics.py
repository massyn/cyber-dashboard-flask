from dash import dash_table,html

def generate_executive_metrics_chart(RAG, df):
    if df.empty:
        return html.Div("No data available for selected filters.", className="empty-message")

    if not 'indicator' in df:
        df['indicator'] = False

    q1 = (
        df.groupby(['metric_id', 'title'])
        .agg(
            score=('totalok', lambda x: x.sum() / df.loc[x.index, 'total'].sum()),
            slo_min=('slo_min', 'mean'),
            slo=('slo', 'mean'),
            total=('total','sum')
        )
        .reset_index()
    )
    # Merge the `indicator` column back
    q1 = q1.merge(df[['metric_id', 'title', 'indicator']].drop_duplicates(), on=['metric_id', 'title'], how='left')

    q1['Score'] = q1.apply(lambda row: f"{row['total']}" if row['indicator'] else f"{row['score'] * 100:.2f}%", axis=1)
    
    q1['rag'] = q1.apply(
        lambda row: (
            "red" if row['score'] < row['slo_min'] else 
            "amber" if row['slo_min'] <= row['score'] < row['slo'] else 
            "green"
        ) if row['slo'] > row['slo_min'] else (  # Normal logic when slo > slo_min
            "green" if row['score'] < row['slo_min'] else 
            "amber" if row['slo_min'] <= row['score'] < row['slo'] else 
            "red"
        ),  # Reversed logic when slo < slo_min
        axis=1
    )

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
            'textAlign': 'left',
            'whiteSpace': 'normal',
        },
        style_header={
            'textAlign': 'left',
            'fontWeight': 'bold',
        },
        style_data_conditional=[
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{rag} = "amber"',
                },
                'backgroundColor': RAG['amber'][0],
                'color': RAG['amber'][1]
            },
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{rag} = "red"',
                },
                'backgroundColor': RAG['red'][0],
                'color': RAG['red'][1]
            },
            {
                'if': {
                    'column_id': 'Score',
                    'filter_query': '{rag} = "green"',
                },
                'backgroundColor': RAG['green'][0],
                'color': RAG['green'][1]
            }
        ]
    )

    return fig
