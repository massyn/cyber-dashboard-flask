import dash
from dash import html,dcc

dash.register_page(__name__, path_template='/about')

def layout():
    with open("about.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    return html.Div([
        html.Div([
            dcc.Link("Home", href="/", className="back-button"),
        ], className="back-button-container"),
        dcc.Markdown(md_content)
    ])
