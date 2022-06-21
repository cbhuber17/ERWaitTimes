"""Contains routines/functions for plotting the ER wait time data."""

import plotly.offline as pyo
import plotly.graph_objs as go
import pandas as pd
from capture_er_wait_data import DATE_TIME_FORMAT

FONT_FAMILY = "Helvetica"
HOURS_IN_DAY = 24
HALF_DAY_HOURS = 12


# -------------------------------------------------------------------------------------------------

def plot_line(city, plot_offline=True, dark_mode=True):
    """Plots the line plot of the ER wait times.
    :param: city (str) City to be plotted
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object"""

    color_mode = {'title': ('black', 'white'),
                  'hover': ('white', 'black'),
                  'spikecolor': ('black', 'white'),
                  'paper_bgcolor': ('white', 'black'),
                  'plot_bgcolor': ('#D6D6D6', '#3A3F44'),
                  'range_bgcolor': ('lawngreen', 'navy'),
                  'range_border_color': ('black', 'orange')}

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
                     spikethickness=2,
                     rangeselector=dict(
                         bgcolor=color_mode['range_bgcolor'][dark_mode],
                         bordercolor=color_mode['range_border_color'][dark_mode],
                         borderwidth=1,
                         buttons=list([
                             dict(count=1, label="1d", step="day", stepmode="backward"),
                             dict(count=7, label="1w", step="day", stepmode="backward"),
                             dict(count=14, label="2w", step="day", stepmode="backward"),
                             dict(count=1, label="1m", step="month", stepmode="backward"),
                             dict(count=1, label="YTD", step="year", stepmode="todate"),
                             dict(step="all", label="All")
                         ])
                     )
                     )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='White', showspikes=True,
                     spikecolor=color_mode['spikecolor'][dark_mode], spikethickness=2)

    # Trace label automatically displayed as <extra>
    fig.update_traces(hovertemplate='Wait: %{y:.1f} hrs on %{x} at: ')

    if plot_offline:
        pyo.plot(fig, filename=html_file)

    return fig


# -------------------------------------------------------------------------------------------------

def plot_violin(city, hospital, plot_offline=True, dark_mode=True):
    """Plots as violin data for each hour of the ER wait times.
    :param: city (str) City to be plotted
    :param: hospital (str) Hospital in city to be plotted
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object"""

    color_mode = {'title': ('black', 'white'),
                  'hover': ('white', 'black'),
                  'spikecolor': ('black', 'white'),
                  'paper_bgcolor': ('white', 'black'),
                  'plot_bgcolor': ('#D6D6D6', '#3A3F44'),
                  'range_bgcolor': ('lawngreen', 'navy'),
                  'range_border_color': ('black', 'orange')}

    html_file = city + '_' + hospital + "_violin.html"

    # Capture data
    df = pd.read_csv(city + "_hospital_stats.csv")

    # Remove any N/A for now, out of town hospitals don't report their data
    df2 = df.copy()
    df2 = df2.dropna(axis=1, how='all')

    # Convert all string to datetime objects
    df2.loc[:, 'time_stamp'] = pd.to_datetime(df2['time_stamp'], format=DATE_TIME_FORMAT)

    # Convert to hours for better readability
    for wait_time in df2.columns:
        if wait_time == 'time_stamp':
            continue

        df2[wait_time] = df2[wait_time].astype("float64")
        df2[wait_time] /= 60.0

    # Filter by specific hospital
    df3 = df2[['time_stamp', hospital]].copy()

    data = {}
    hour_dict = {}

    # Create new df to hold wait times at every hour (cols) for every day (rows)
    for hour in range(0, HOURS_IN_DAY):
        hour_filter = df3.time_stamp.dt.hour == hour
        data[hour] = df3[hour_filter][hospital].tolist()

        # TODO: Put in a function
        if hour < HALF_DAY_HOURS:
            hour_dict[hour] = f'{hour} AM'
            if hour % HALF_DAY_HOURS == 0:
                hour_dict[hour] = f'{hour + HALF_DAY_HOURS} AM'
        else:
            hour_dict[hour] = f'{hour - HALF_DAY_HOURS} PM'
            if hour % HALF_DAY_HOURS == 0:
                hour_dict[hour] = f'{hour} PM'

    # Not all hours will have equal amount of data, create by day (cols) for every hour (rows) then transpose
    df4 = pd.DataFrame.from_dict(data, orient='index')
    df4 = df4.transpose()

    layout = go.Layout(
        title={'text': hospital + ' ER Wait Times',  # TODO: Put subtitle "Data spans from date X to date Y"
               'x': 0.5,
               'y': 0.95,
               'xanchor': 'center',
               'yanchor': 'top'},
        xaxis_title={'text': "Time"},
        yaxis_title={'text': "Wait Time in Hours"},
        legend_title={'text': "Time (Hour)"},
        showlegend=False,
        font=dict(
            family=FONT_FAMILY,
            size=20,
            color=color_mode['title'][dark_mode]
        ),
        paper_bgcolor=color_mode['paper_bgcolor'][dark_mode],
        plot_bgcolor=color_mode['plot_bgcolor'][dark_mode],
        yaxis={'range': [0, 15]},
        hoverdistance=100,
        hoverlabel=dict(
            font=dict(
                size=16,
                family=FONT_FAMILY,
                color=color_mode['hover'][dark_mode]
            )
        )
    )

    fig = go.Figure(layout=layout)

    for hour in range(0, HOURS_IN_DAY):
        fig.add_trace(go.Violin(x0=hour_dict[hour], y=df4[hour],
                                box_visible=True,
                                meanline_visible=True,
                                name=hour_dict[hour],
                                opacity=0.9))

    if plot_offline:
        pyo.plot(fig, filename=html_file)

    return fig


# -------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    plot_line("Calgary", False)
    plot_line("Edmonton", False)

    plot_violin("Calgary", "South Health Campus")
