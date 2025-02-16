import plotly.express as px
import plotly.graph_objects as go
from dash import html

def generate_executive_overview_chart(RAG,df,title = "Executive Summary"):
    if df.empty:
        return html.Div("No data available for selected filters.", className="empty-message")
    df = df[df['indicator'] != True]
    q1 = (
        df.groupby(['metric_id', 'datestamp', 'weight'])
        .agg(
            weighted_score   = ('totalok', lambda x: x.sum() / df.loc[x.index, 'total'].sum() * df.loc[x.index, 'weight'].iloc[0]),
            weighted_slo     = ('slo'    , lambda x: x.mean() * df.loc[x.index, 'weight'].iloc[0]),
            weighted_slo_min = ('slo_min', lambda x: x.mean() * df.loc[x.index, 'weight'].iloc[0]),
        )
        .reset_index()
    )

    result = (
        q1.groupby('datestamp')
        .agg(
            score   = ('weighted_score'   , lambda x: x.sum() / q1.loc[x.index, 'weight'].sum()),
            slo_min = ('weighted_slo_min' , lambda x: x.sum() / q1.loc[x.index, 'weight'].sum()),
            slo     = ('weighted_slo'     , lambda x: x.sum() / q1.loc[x.index, 'weight'].sum()),
        )
        .reset_index()
    )

    result['rag'] = result.apply(lambda row: "red" if row['score'] < row['slo_min'] else "amber" if row['slo_min'] <= row['score'] < row['slo'] else "green", axis = 1)

    fig = px.bar(
        result, x="datestamp", y="score",
        color="rag",
        color_discrete_map={
            "red"  : RAG['red'][0],
            "amber": RAG['amber'][0],
            "green": RAG['green'][0]
        },
        title=title,
        text_auto=True
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%", title=None)
    fig.update_xaxes(title=None)
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_type="category")

    # Add SLO lines
    fig.add_trace(
        go.Scatter(
            x=result["datestamp"],
            y=result["slo"],
            mode="lines",
            name="SLO",
            line=dict(color=RAG['green'][0])
        )
    )
    # Add SLO_min lines
    fig.add_trace(
        go.Scatter(
            x=result["datestamp"],
            y=result["slo_min"],
            mode="lines",
            name="SLO_Min",
            line=dict(color=RAG['amber'][0])
        )
    )
    return fig
