"""Contains routines/functions for plotting the ER wait time data."""

import plotly.offline as pyo
import plotly.graph_objs as go
import pandas as pd
from capture_er_wait_data import DATE_TIME_FORMAT

FONT_FAMILY = "Helvetica"


# -------------------------------------------------------------------------------------------------

def plot_line(city, plot_offline=True, dark_mode=True):
    """Plots the line plot of the ER wait times.
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object"""

    color_mode = {'title': ('black', 'white'),
                  'hover': ('white', 'black'),
                  'spikecolor': ('black', 'white'),
                  'paper_bgcolor': ('white', 'black'),
                  'plot_bgcolor': ('#D6D6D6', '#3A3F44')}

    html_file = city + "_er_wait_times.html"

    # Capture data
    df = pd.read_csv(city + "_hospital_stats.csv")

    # Remove any N/A for now, out of town hospitals don't report their data
    df2 = df.copy()
    df2 = df2.dropna(axis=1, how='all')

    # Convert all string to datetime objects
    df2.loc[:, 'time_stamp'] = pd.to_datetime(df2['time_stamp'], format=DATE_TIME_FORMAT)

    # Convert to hours for better readability
    for hospital in df2.columns:
        if hospital == 'time_stamp':
            continue

        df2[hospital] = df2[hospital].astype("float64")
        df2[hospital] /= 60.0

    traces = [go.Scatter(
        x=df2['time_stamp'],
        y=df2[hospital_name],
        mode='lines',
        name=hospital_name,
        connectgaps=True,
    ) for hospital_name in df2.columns if hospital_name != 'time_stamp']

    layout = go.Layout(
        title={'text': city + ' ER Wait Times',
               'x': 0.5,
               'y': 0.95,
               'xanchor': 'center',
               'yanchor': 'top'},
        xaxis_title={'text': "Date/Time"},
        yaxis_title={'text': "Wait Time in Hours"},
        legend_title={'text': city + " Hospitals"},
        font=dict(
            family=FONT_FAMILY,
            size=20,
            color=color_mode['title'][dark_mode]
        ),
        paper_bgcolor=color_mode['paper_bgcolor'][dark_mode],
        plot_bgcolor=color_mode['plot_bgcolor'][dark_mode],

        # TODO: At some point with too much time data, limit the x-axis range, this will be additional function input
        # xaxis={'range': [0, len(df2.index)]},
        yaxis={'range': [0, 20]},
        spikedistance=1000,
        hoverdistance=100,
        hoverlabel=dict(
            font=dict(
                size=16,
                family=FONT_FAMILY,
                color=color_mode['hover'][dark_mode]
            )
        )
    )

    fig = go.Figure(data=traces, layout=layout)

    fig.update_xaxes(showgrid=False, gridwidth=5, gridcolor='White', showspikes=True,
                     spikecolor=color_mode['spikecolor'][dark_mode], spikesnap="cursor", spikemode="across",
                     spikethickness=2)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='White', showspikes=True,
                     spikecolor=color_mode['spikecolor'][dark_mode], spikethickness=2)

    # Trace label automatically displayed as <extra>
    fig.update_traces(hovertemplate='Wait: %{y:.1f} hrs on %{x} at: ')

    if plot_offline:
        pyo.plot(fig, filename=html_file)

    return fig

# -------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    plot_line("Calgary")
    plot_line("Edmonton")
