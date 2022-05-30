import plotly.offline as pyo
import plotly.graph_objs as go
import pandas as pd
from capture_er_wait_data import stats_file_name

# Capture data
df = pd.read_csv(stats_file_name)

# Remove any N/A for now, out of town hospitals don't report their data
df2 = df.dropna(axis=1, how='all')

traces = [go.Scatter(
    x=df2.index,
    y=df2[hospital_name],
    mode='markers+lines',
    name=hospital_name,
) for hospital_name in df2.columns if hospital_name != 'time_stamp']

layout = go.Layout(
    title={'text': 'Calgary ER Wait Times',
           'x': 0.5,
           'y': 0.95,
           'xanchor': 'center',
           'yanchor': 'top'},
    xaxis_title={'text': "Date/Time"},
    yaxis_title={'text': "Wait Time in Minutes"},
    legend_title={'text': "Calgary Hospitals"},
    font=dict(
        family="Arial",
        size=20,
        color="Black"
    ),
    paper_bgcolor='#F5F5F5',
    plot_bgcolor='#F0F0F0'
)

fig = go.Figure(data=traces, layout=layout)
fig.update_xaxes(showgrid=False, gridwidth=5, gridcolor='White')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='White')
pyo.plot(fig, filename='testing.html')
