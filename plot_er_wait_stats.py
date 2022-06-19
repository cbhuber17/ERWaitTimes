"""TBD."""

import plotly.offline as pyo
import plotly.graph_objs as go
import pandas as pd
from capture_er_wait_data import DATE_TIME_FORMAT

FONT_FAMILY = "Helvetica"


def plot_line(city, plot_offline=True):
    """TBD."""

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
            color="Black"
        ),
        paper_bgcolor='#F5F5F5',
        plot_bgcolor='#D6D6D6',

        # TODO: At some point with too much time data, limit the x-axis range
        # xaxis={'range': [0, len(df2.index)]},
        yaxis={'range': [0, 20]},
        spikedistance=1000,
        hoverdistance=100,
        hoverlabel=dict(
            font=dict(
                size=16,
                family=FONT_FAMILY,
                color="white"
            )
        )
    )

    fig = go.Figure(data=traces, layout=layout)
    fig.update_xaxes(showgrid=False, gridwidth=5, gridcolor='White', showspikes=True, spikecolor="black",
                     spikesnap="cursor", spikemode="across", spikethickness=2)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='White', showspikes=True, spikecolor="black",
                     spikethickness=2)
    fig.update_traces(hovertemplate='Wait: %{y:.1f} hrs at %{x}<extra></extra>')

    if plot_offline:
        pyo.plot(fig, filename=html_file)

    return fig


if __name__ == "__main__":
    plot_line("Calgary")
    plot_line("Edmonton")
