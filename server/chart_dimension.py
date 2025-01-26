import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash import html

def generate_executive_dimension_chart(RAG,dimensions,df):
    if df.empty:
        return html.Div("No data available for selected filters.", className="empty-message")
    q1 = (
        df.groupby(['metric_id', next(iter(dimensions.keys())), 'weight'], as_index=False).apply(
            lambda group: pd.Series({
                'score': group['totalok'].sum() / group['total'].sum(),
                'slo_min': group['slo_min'].mean(),
                'slo': group['slo'].mean(),
            })
        ).reset_index()
    )
    result = (
        q1.groupby(next(iter(dimensions.keys())))
        .agg(
            score=('score', lambda x: (x * q1.loc[x.index, 'weight']).sum() / q1.loc[x.index, 'weight'].sum()),
            slo_min=('slo_min', 'mean'),
            slo=('slo', 'mean'),
        )
        .reset_index()
    )
    result['rag'] = result.apply(lambda row: "red" if row['score'] < row['slo_min'] else "amber" if row['slo_min'] <= row['score'] < row['slo'] else "green", axis = 1)

    fig = px.bar(
        result.sort_values(by="score", ascending=False),
        y=next(iter(dimensions.keys())),
        x="score",
        orientation='h',
        title=f"By {next(iter(dimensions.values()))}",
        text_auto=True,
        color="rag",
        color_discrete_map={
            "red": RAG['red'][0],
            "amber": RAG['amber'][0],
            "green": RAG['green'][0]
        },
    )
    fig.update_yaxes(title=None)
    fig.update_xaxes(range=[0, 1],tickformat=".0%", title=None)
    fig.update_layout(showlegend=False)

    slo_value = result["slo"].mean()
    fig.add_vline(
        x=slo_value,
        line_color=RAG['green'][0]
    )
    slo_value = result["slo_min"].mean()
    fig.add_vline(
        x=slo_value,
        line_color=RAG['amber'][0]
    )

    return fig