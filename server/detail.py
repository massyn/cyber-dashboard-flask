from dash import Dash, html, dcc

def create_detail(server):
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/',
        external_stylesheets=["/static/style.css"]
    )

    # Dash layout
    app.layout = html.Div(className="app-container", children=[
        html.Div(className="main-content", children=[
            html.Div(className="header", children=[
                html.H1("Continuous Assurance", className="header-title"),
                html.P("Detail", className="header-description"),
                html.A("Logout", href="/logout", className="logout-link")  # Add a logout link
            ])
        ])
    ])