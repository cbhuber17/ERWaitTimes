import plotly.offline as pyo
import plotly.graph_objs as go
import pandas as pd
from capture_er_wait_data import stats_file_name
from capture_er_wait_data import date_time_format

# Capture data
df = pd.read_csv(stats_file_name)

# Remove any N/A for now, out of town hospitals don't report their data
df2 = df.copy()
df2 = df2.dropna(axis=1, how='all')

# Convert all string to datetime objects
df2.loc[:, 'time_stamp'] = pd.to_datetime(df2['time_stamp'], format=date_time_format)

# Convert to hours for better readability
for hospital in df2.columns:
    if hospital == 'time_stamp':
        continue

    df2[hospital] = df2[hospital].astype("float64")
    df2[hospital] /= 60.0


traces = [go.Scatter(
    x=df2['time_stamp'],
    y=df2[hospital_name],
    mode='markers+lines',
    name=hospital_name,
    connectgaps=True,
) for hospital_name in df2.columns if hospital_name != 'time_stamp']

layout = go.Layout(
    title={'text': 'Calgary ER Wait Times',
           'x': 0.5,
           'y': 0.95,
           'xanchor': 'center',
           'yanchor': 'top'},
    xaxis_title={'text': "Date/Time"},
    yaxis_title={'text': "Wait Time in Hours"},
    legend_title={'text': "Calgary Hospitals"},
    font=dict(
        family="Verdana",
        size=20,
        color="Black"
    ),
    paper_bgcolor='#F5F5F5',
    plot_bgcolor='#D6D6D6',

    # TODO: At some point with too much time data, limit the x-axis range
    # xaxis={'range': [0, len(df2.index)]},
    yaxis={'range': [0, 10]},

)

fig = go.Figure(data=traces, layout=layout)
fig.update_xaxes(showgrid=False, gridwidth=5, gridcolor='White')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='White')
pyo.plot(fig, filename='testing.html')
