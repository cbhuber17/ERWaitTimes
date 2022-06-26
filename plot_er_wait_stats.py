"""Contains routines/functions for plotting the ER wait time data."""

import plotly.offline as pyo
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from capture_er_wait_data import DATE_TIME_FORMAT

FONT_FAMILY = "Helvetica"
HOURS_IN_DAY = 24
HALF_DAY_HOURS = 12
Y_AXIS_RANGE = [0, 20]  # Hours

# Dark/light mode colors
COLOR_MODE = {'title': ('black', 'white'),
              'hover': ('white', 'black'),
              'spikecolor': ('black', 'white'),
              'paper_bgcolor': ('white', 'black'),
              'plot_bgcolor': ('#D6D6D6', '#3A3F44'),
              'range_bgcolor': ('lawngreen', 'navy'),
              'range_border_color': ('black', 'orange'),
              'an_bgcolor': ('#FFFFE0', 'white'),
              'an_text_color': ('black', 'navy')}


# -------------------------------------------------------------------------------------------------

def plot_line(city, plot_offline=True, dark_mode=True):
    """Plots the line plot of the ER wait times.
    :param: city (str) City to be plotted
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object"""

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
            color=COLOR_MODE['title'][dark_mode]
        ),
        paper_bgcolor=COLOR_MODE['paper_bgcolor'][dark_mode],
        plot_bgcolor=COLOR_MODE['plot_bgcolor'][dark_mode],
        yaxis={'range': Y_AXIS_RANGE},
        spikedistance=1000,
        hoverdistance=100,
        hoverlabel=dict(
            font=dict(
                size=16,
                family=FONT_FAMILY,
                color=COLOR_MODE['hover'][dark_mode]
            )
        )
    )

    fig = go.Figure(data=traces, layout=layout)

    fig.update_xaxes(showgrid=False, gridwidth=5, gridcolor='White', showspikes=True,
                     spikecolor=COLOR_MODE['spikecolor'][dark_mode], spikesnap="cursor", spikemode="across",
                     spikethickness=2,
                     rangeselector=dict(
                         bgcolor=COLOR_MODE['range_bgcolor'][dark_mode],
                         bordercolor=COLOR_MODE['range_border_color'][dark_mode],
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
                     spikecolor=COLOR_MODE['spikecolor'][dark_mode], spikethickness=2)

    # Trace label automatically displayed as <extra>
    fig.update_traces(hovertemplate='Wait: %{y:.1f} hrs on %{x} at: ')

    if plot_offline:
        pyo.plot(fig, filename=html_file)

    return fig


# -------------------------------------------------------------------------------------------------

def create_hour_dict(hour, hour_dict):
    """Creates a standard 12-hour format dictionary based on integer input.
    :param: hour (int) hour between 0-23 inclusive
    :param: hour_dict (dict) the dictionary to construct (e.g. 0 will be "12 AM")
     :return: None"""

    if hour < HALF_DAY_HOURS:
        hour_dict[hour] = f'{hour} AM'
        if hour % HALF_DAY_HOURS == 0:
            hour_dict[hour] = f'{hour + HALF_DAY_HOURS} AM'
    else:
        hour_dict[hour] = f'{hour - HALF_DAY_HOURS} PM'
        if hour % HALF_DAY_HOURS == 0:
            hour_dict[hour] = f'{hour} PM'


# -------------------------------------------------------------------------------------------------

def my_24h_cosine(x, amplitude, phase, offset):
    """Typical Cosine function for a 24h period: amplitude * cos(x*(π/12) + phase) + offset
    :param: x (int or float) x-coordinate in hours
    :param: amplitude (int or float) amplitude of wave (hours)
    :param: phase (int or float) phase offset, must be in radians
    :param: offset (int or float) vertical offset (hours)
    :return: amplitude * cos(x*(π/12) + phase) + offset"""

    # 24h day in radians (omega is the angular rate)
    radians_per_hour = float(np.pi / 12)

    return np.cos(x * radians_per_hour + phase) * amplitude + offset


# -------------------------------------------------------------------------------------------------

def get_cos_fit(df):
    """Uses least-squares to get a best-fit curve cosine model.
    :param: df (pd.DataFrame) Data frame containing the 24 hr data
    :return: (list) and (list) Cosine curve params and y values representing the cosine curve."""

    # Get sinusoid best-fit as the median/mean avg of each hour
    x_values = []
    y_values = []

    for hour in range(0, HOURS_IN_DAY):
        x_values.append(hour)
        y_values.append(float((df[hour].mean() + df[hour].median()) / 2.0))

    x_values = np.array(x_values)
    y_values = np.array(y_values)

    guess_amplitude = 3 * np.std(y_values) / (2 ** 0.5)
    guess_phase = 0
    guess_offset = np.mean(y_values)

    p0 = [guess_amplitude, guess_phase, guess_offset]

    curve_param, curve_covariance = curve_fit(my_24h_cosine, x_values, y_values, p0=p0)

    cosine_curve_fit = my_24h_cosine(x_values, *curve_param)

    return curve_param, cosine_curve_fit


# -------------------------------------------------------------------------------------------------

def filter_df(df):
    """Does initial filter of data frame:
    - Drops any columns/hospitals that have NaN data
    - Converts all time_stamp column elements to datetime objects
    - Converts the wait time from minutes to hours
    :param: df (pd.DataFrame) The dataframe from a csv file
    :return: (pd.DataFrame) filtered df."""

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

    return df2


# -------------------------------------------------------------------------------------------------

def get_wait_data_hour_dict(df, hospital):
    """Provides a new data frame to hold wait times at every hour (cols) for every day (rows).
    :param: df (pd.DataFrame) Filtered dataframe containing time_stamp and hospital columns
    :param: hospital (str) The hospital to filter data
    :return: (pd.DataFrame) and (dict) of a hours x wait times df and hour_dictionary (e.g hour_dict[0] = '12 AM')
    """

    data = {}
    hour_dict = {}

    # Create new df to hold wait times at every hour (cols) for every day (rows)
    for hour in range(0, HOURS_IN_DAY):
        hour_filter = df.time_stamp.dt.hour == hour
        data[hour] = df[hour_filter][hospital].tolist()
        create_hour_dict(hour, hour_dict)

    # Not all hours will have equal amount of data, create by day (cols) for every hour (rows) then transpose
    df2 = pd.DataFrame.from_dict(data, orient='index')
    df2 = df2.transpose()

    return df2, hour_dict


# -------------------------------------------------------------------------------------------------

def get_violin_layout(title_text, x_axis_label, dark_mode):
    """Gets the layout that is common among violin plots.
    :param: title_text (str) The title of the plot
    :param: x_axis_label (str) The label of the x-axis
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Layout)"""

    layout = go.Layout(
        title={'text': title_text,
               'x': 0.5,
               'y': 0.95,
               'xanchor': 'center',
               'yanchor': 'top'},
        xaxis_title={'text': x_axis_label},
        yaxis_title={'text': "Wait Time in Hours"},
        legend_title={'text': "Time (Hour)"},
        showlegend=False,
        font=dict(
            family=FONT_FAMILY,
            size=20,
            color=COLOR_MODE['title'][dark_mode]
        ),
        paper_bgcolor=COLOR_MODE['paper_bgcolor'][dark_mode],
        plot_bgcolor=COLOR_MODE['plot_bgcolor'][dark_mode],
        yaxis={'range': Y_AXIS_RANGE},
        hoverdistance=50,
        hoverlabel=dict(
            font=dict(
                size=16,
                family=FONT_FAMILY,
                color=COLOR_MODE['hover'][dark_mode]
            )
        )
    )

    return layout


# -------------------------------------------------------------------------------------------------


def plot_hospital_hourly_violin(city, hospital, plot_best_fit=True, plot_offline=True, dark_mode=True):
    """Plots as violin data for each hour of the ER wait times.
    :param: city (str) City to be plotted
    :param: hospital (str) Hospital in city to be plotted
    :param: plot_best_fit (bool) If a best-fit curve is to be generated (default: True)
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object"""

    html_file = city + '_' + hospital + "_violin.html"

    # Capture data
    df = pd.read_csv(city + "_hospital_stats.csv")

    # Filter data
    df2 = filter_df(df)

    # Filter data by hospital
    df2 = df2[['time_stamp', hospital]].copy()

    # Span of data for sub-title
    min_date = min(df2['time_stamp'].dt.date)
    max_date = max(df2['time_stamp'].dt.date)

    df3, hour_dict = get_wait_data_hour_dict(df2, hospital)

    # Don't plot best fit curve if midnight column is entirely NaN
    plot_best_curve = df3[0].isna().sum() != len(df3[0]) and plot_best_fit

    if plot_best_curve:
        curve_param, cosine_curve_fit = get_cos_fit(df3)

        # Cosine best-fit curve
        plot_cosine = go.Scatter(x=list(hour_dict.values()), y=cosine_curve_fit, name="Average",
                                 line=dict(width=4, color='red'))

    layout = get_violin_layout(hospital + f' ER Wait Times<br><sup>Date range: {min_date} to {max_date}</sup>', 'Time',
                               dark_mode)

    fig = go.Figure(layout=layout)

    for hour in range(0, HOURS_IN_DAY):
        fig.add_trace(go.Violin(x0=hour_dict[hour], y=df3[hour],
                                box_visible=True,
                                meanline_visible=True,
                                name=hour_dict[hour],
                                opacity=0.9))

    if plot_best_curve:
        fig.add_trace(plot_cosine)

        # LaTeX/MathJax format to show the model equation and stat values
        model_equation = r"$\normalsize{a\cos(\omega t + \phi) + k}$"
        model_results = r"$a={:.1f} hrs\\\omega=24hrs/day\\\phi={:.1f} hrs\\k={:.1f} hrs$".format(curve_param[0],
                                                                                                  curve_param[1]
                                                                                                  * 2 * np.pi,
                                                                                                  curve_param[2])
        equation_to_show = r"$\displaylines{" + model_equation[1:-1] + r"\\" + model_results[1:-1] + r"}$"

        # Arrow annotation properties
        arrowhead = 2
        arrowsize = 2
        arrowwidth = 2
        arrowcolor = "red"
        x_arrow_vector = 50
        y_arrow_vector = -500  # TODO: This needs to be responsive

        # Annotation variables
        x_annotation_point = 13.5
        y_annotation_point = my_24h_cosine(x_annotation_point, *curve_param)

        # Border of annotation properties
        bordercolor = "red"
        borderwidth = 3
        borderpad = 35
        bgcolor = COLOR_MODE['an_bgcolor'][dark_mode]

        # Arrow annotation of the equation of the curve
        fig.add_annotation(x=x_annotation_point, y=y_annotation_point, text=equation_to_show, showarrow=True,
                           arrowhead=arrowhead, arrowsize=arrowsize, arrowwidth=arrowwidth, arrowcolor=arrowcolor,
                           bordercolor=bordercolor, borderpad=borderpad, borderwidth=borderwidth, bgcolor=bgcolor,
                           ax=x_arrow_vector, ay=y_arrow_vector,
                           font=dict(color=COLOR_MODE['an_text_color'][dark_mode]))

    if plot_offline:
        pyo.plot(fig, filename=html_file, include_mathjax='cdn', config={'responsive': True})

    return fig


# -------------------------------------------------------------------------------------------------

def plot_all_hospitals_violin(city, plot_offline=True, dark_mode=True):
    """Plots all hospitals (all timestamps) violin data.
    :param: city (str) City to be plotted
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object"""

    html_file = city + "_hospitals_violin.html"

    # Capture data
    df = pd.read_csv(city + "_hospital_stats.csv")

    # Filter
    df = filter_df(df)

    # Span of data for sub-title
    min_date = min(df['time_stamp'].dt.date)
    max_date = max(df['time_stamp'].dt.date)

    layout = get_violin_layout(city + f' ER Wait Times<br><sup>Date range: {min_date} to {max_date}</sup>', 'Hospital',
                               dark_mode)

    fig = go.Figure(layout=layout)

    for hospital in df:
        if hospital == 'time_stamp':
            continue

        fig.add_trace(go.Violin(x0=hospital, y=df[hospital],
                                box_visible=True,
                                meanline_visible=True,
                                name=hospital,
                                opacity=0.9))

    if plot_offline:
        pyo.plot(fig, filename=html_file, config={'responsive': True})

    return fig


# -------------------------------------------------------------------------------------------------

def set_subplot_yaxes(fig, num_hospitals):
    """Sets the range of all subplot y-axes values.
    :param: fig (go.Figure) object
    :param: num_hospitals (int) number of hospitals in the city
    :return: None"""

    set_yaxes = {}

    for i in range(1, num_hospitals + 1):
        if i == 1:
            set_yaxes['yaxis'] = dict(range=Y_AXIS_RANGE)
        else:
            set_yaxes[f'yaxis{i}'] = dict(range=Y_AXIS_RANGE)

    fig.update_layout(**set_yaxes)


# -------------------------------------------------------------------------------------------------


def set_subplot_xaxes(fig, num_hospitals):
    """Sets the tick labels on the last 2 plots at the bottom.
    :param: fig (go.Figure) object
    :param: num_hospitals (int) number of hospitals in the city
    :return: None"""

    set_xaxes = {f'xaxis{num_hospitals - 1}_showticklabels': True,
                 f'xaxis{num_hospitals}_showticklabels': True}

    fig.update_layout(**set_xaxes)


# -------------------------------------------------------------------------------------------------

def get_subplot_dict():
    """Gets 2 dictionaries containing layout for subplots that involve a max of 2 columns.
    :param: None
    :return: (dict) subplot_dimensions - Dimensions of the subplot based on the input int size
    :return: (dict) subplot_locations - The order of the subplot locations, starting top left and going right then down
    """

    subplot_dimensions = {}
    subplot_locations = {}

    # Theoretical max # of hospitals per city
    max_hospitals = 20

    for i in range(max_hospitals):

        if i % 2 == 0:
            subplot_dimensions[i] = (int(i / 2), 2)
            subplot_locations[i] = (int(i / 2), 2)
        else:
            subplot_dimensions[i] = (int(i / 2) + 1, 2)
            subplot_locations[i] = (int(i / 2) + 1, 1)

    subplot_dimensions[0] = (0, 0)
    subplot_locations[0] = (0, 0)
    subplot_dimensions[1] = (1, 0)
    subplot_dimensions[2] = (1, 2)

    return subplot_dimensions, subplot_locations


# -------------------------------------------------------------------------------------------------

def plot_subplots_hour_violin(city, plot_offline=True, dark_mode=True):
    """Plots all the hourly violin charts as subplots for a particular city.
    :param: city (str) City to be plotted
    :param: plot_offline (bool) If an offline plot is to be generated (default: True)
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (go.Figure) object
    """

    html_file = city + '_subplots.html'

    subplot_dimensions, subplot_locations = get_subplot_dict()

    df = pd.read_csv(city + "_hospital_stats.csv")

    # Filter data
    df2 = filter_df(df)

    hospitals = list(df2.columns)
    hospitals.remove('time_stamp')

    # Span of data for sub-title
    min_date = min(df2['time_stamp'].dt.date)
    max_date = max(df2['time_stamp'].dt.date)

    num_hospitals = len(df2.columns) - 1
    rows, cols = subplot_dimensions[num_hospitals]

    fig = make_subplots(rows=rows, cols=cols, shared_xaxes=True, subplot_titles=hospitals, vertical_spacing=0.03,
                        y_title="Wait time in Hours")

    # y_title font size, it is an annotation that is at the end of the layout list
    fig.layout.annotations[-1]["font"] = {'size': 30}

    figures_dict = {}
    counter = 0

    for hospital in df2:

        if hospital == 'time_stamp':
            continue

        counter += 1
        figures_dict[hospital] = plot_hospital_hourly_violin(city, hospital, False, False, dark_mode)
        row, col = subplot_locations[counter]

        for trace in figures_dict[hospital].data:
            fig.add_trace(trace, row=row, col=col)

    fig.update_layout(
        title={'text': f"{city} Hospitals ER Wait Times<br><sup>Date range: {min_date} to {max_date}</sup>",
               'x': 0.5,
               'y': 0.985,
               'xanchor': 'center',
               'yanchor': 'top'},
        font=dict(
            family=FONT_FAMILY,
            size=20,
            color=COLOR_MODE['title'][dark_mode]
        ),
        showlegend=False, height=2000,
        paper_bgcolor=COLOR_MODE['paper_bgcolor'][dark_mode],
        plot_bgcolor=COLOR_MODE['plot_bgcolor'][dark_mode],
        hoverdistance=50,
        hoverlabel=dict(
            font=dict(
                size=16,
                family=FONT_FAMILY,
                color=COLOR_MODE['hover'][dark_mode]
            )
        )
    )

    # Set x-axis tick mark labels
    set_subplot_xaxes(fig, num_hospitals)

    # Make all subplot y-axes consistent
    set_subplot_yaxes(fig, num_hospitals)

    if plot_offline:
        pyo.plot(fig, filename=html_file, config={'responsive': True})

    return fig


# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # plot_line("Calgary")
    # plot_line("Edmonton")

    # plot_hospital_hourly_violin("Calgary", "South Health Campus")
    # plot_hospital_hourly_violin("Calgary", "Alberta Children's Hospital")
    # plot_hospital_hourly_violin("Calgary", "Foothills Medical Centre")
    # plot_hospital_hourly_violin("Calgary", "Peter Lougheed Centre")
    # plot_hospital_hourly_violin("Calgary", "Rockyview General Hospital")
    # plot_hospital_hourly_violin("Calgary", "Sheldon M. Chumir Centre")
    # plot_hospital_hourly_violin("Calgary", "South Calgary Health Centre")

    # plot_all_hospitals_violin("Calgary")
    # plot_all_hospitals_violin("Edmonton")

    # TODO: Height needs ot be increased for Edm and max y reduced
    # plot_subplots_hour_violin("Calgary")
    plot_subplots_hour_violin("Edmonton")
