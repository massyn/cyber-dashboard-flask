from dash import dash_table, html

def generate_detail_table(RAG, df):
    if df.empty:
        return html.Div("No data available for selected filters.", className="empty-message")

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
        # style_data_conditional=[
        #     {
        #         'if': {
        #             'column_id': 'compliance',
        #             'filter_query': '{compliance} < 1 & {compliance} >= 0',
        #         },
        #         'backgroundColor': RAG['amber'][0],
        #         'color': 'white'
        #     },
        #     {
        #         'if': {
        #             'column_id': 'compliance',
        #             'filter_query': '{compliance} == 0',
        #         },
        #         'backgroundColor': RAG['red'][0],
        #         'color': 'white'
        #     },
        #     {
        #         'if': {
        #             'column_id': 'compliance',
        #             'filter_query': '{compliance} == 1',
        #         },
        #         'backgroundColor': RAG['green'][0],
        #         'color': 'white'
        #     }
        # ]
    )

    return table
