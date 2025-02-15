from dash import dash_table, html

def generate_detail_table(RAG, df):
    if df.empty:
        return html.Div("No data available for selected filters.", className="empty-message")

    df['rag'] = df.apply(lambda row: "red" if row['compliance'] == 0 else "green" if row['compliance'] == 1 else "amber", axis = 1)

    table = dash_table.DataTable(
        data=df.to_dict(orient="records"),
        columns=[
            {"name": "datestamp" , "id" : "datestamp"},
            {"name": "resource" , "id" : "resource"},
            {"name": "detail" , "id" : "detail"},
            {"name": "compliance" , "id" : "compliance"},
        ],
        page_size=20,
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
                    'column_id': 'compliance',
                },
                'textAlign': 'center'
            },
            {
                'if': {
                    'column_id': 'compliance',
                    'filter_query': 'rag = "amber"',
                },
                'backgroundColor': RAG['amber'][0],
                'color': RAG['amber'][1]
            },
            {
                'if': {
                    'column_id': 'compliance',
                    'filter_query': '{rag} = "red"',
                },
                'backgroundColor': RAG['red'][0],
                'color': RAG['red'][1]
            },
            {
                'if': {
                    'column_id': 'compliance',
                    'filter_query': '{rag} = "green"',
                },
                'backgroundColor': RAG['green'][0],
                'color': RAG['green'][1]
            }
        ]
    )

    return table
