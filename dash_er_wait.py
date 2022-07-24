"""The main app to run the dash server to display the results of the ER wait times in Alberta with interactive
features."""

import datetime
import dash
from dash import dcc
from dash import html
from dash import dash_table
import dash_daq as daq
from dash.exceptions import PreventUpdate
import pandas as pd
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from plot_er_wait_stats import get_mongodb_df, plot_line, plot_subplots_hour_violin, plot_hospital_hourly_violin, \
    filter_df, get_wait_data_hour_dict, FONT_FAMILY, TIME_STAMP_HEADER
from capture_er_wait_data import URL, MINUTES_PER_HOUR, DATE_TIME_FORMAT

COLOR_MODE_DASH = {'font_color': ('black', 'white'),
                   'bg_color': ('#ffffd0', '#3a3f44')}

app = dash.Dash(__name__, assets_folder='assets', title='Alberta ER Wait Times', update_title='Please wait...',
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True  # Dynamic layout
server = app.server

# TODO: Sheldon M. Chumir not working violin
# df_yyc = pd.read_csv('Calgary_hospital_stats.csv')
# df_yeg = pd.read_csv('Edmonton_hospital_stats.csv')

df_yyc = get_mongodb_df("Calgary")
df_yeg = get_mongodb_df("Edmonton")

yyc_hospitals = [x.replace(" ", "_") for x in list(df_yyc.columns)]
yeg_hospitals = [x.replace(" ", "_") for x in list(df_yeg.columns)]

# ------------------------------------------------------------------------

app.layout = html.Div([
    dcc.Location(id='url'),
    dcc.Store(id='viewport-container', data={}, storage_type='session'),
    dcc.Store(id='dark-mode-value', data=True, storage_type='session'),
    html.Div(id='page-content')
])


# ------------------------------------------------------------------------

def get_max_date(df):
    """Returns the max date in the provided df.
    :param: df (pd.DataFrame) A dataframe containing hospital data for a particular city
    :return: (datetime.date) Max date of the df."""

    # Remove any N/A for now, out of town hospitals don't report their data
    df2 = df.copy()
    df2 = df2.dropna(axis=1, how='all')

    # Convert all string to datetime objects
    df2.loc[:, TIME_STAMP_HEADER] = pd.to_datetime(df2[TIME_STAMP_HEADER], format=DATE_TIME_FORMAT)

    return max(df2[TIME_STAMP_HEADER].dt.date)


# ------------------------------------------------------------------------


max_date_yyc = get_max_date(df_yyc)
max_date_yeg = get_max_date(df_yeg)


def get_table_container(df_stats, dark_mode, avg_header, std_header):
    """Provides an HTML container for centering a statistics table for each stats dataframe.
    :param: df_stats (pandas.df) Stats data frame
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :param: avg_header (str) String containing the average header
    :param: std_header (str) String containing the standard deviation header
    :return dbc.Container containing the HTML code for displaying the table."""

    stats_table = html.Div(
        [
            dash_table.DataTable(data=df_stats.to_dict('records'),
                                 style_header={
                                     'fontWeight': 'bold',
                                     'color': COLOR_MODE_DASH['font_color'][dark_mode]},
                                 style_cell={'textAlign': 'center',
                                             'height': 'auto',
                                             'padding-right': '10px',
                                             'padding-left': '10px',
                                             'whiteSpace': 'normal',
                                             'backgroundColor': COLOR_MODE_DASH['bg_color'][dark_mode],
                                             'color': COLOR_MODE_DASH['font_color'][dark_mode],
                                             },
                                 style_cell_conditional=[
                                     {'if': {'column_id': avg_header},
                                      'width': '150px'},
                                     {'if': {'column_id': std_header},
                                      'width': '150px'},
                                 ],
                                 fill_width=False,
                                 style_table={'overflowX': 'auto'},
                                 style_as_list_view=True,
                                 columns=[{"name": i, "id": i} for i in df_stats.columns]
                                 ),
        ],
    )

    container = dbc.Container([
        dbc.Row(
            [
                dbc.Col(
                    dcc.Markdown(""), xs=12, sm=12, md=3, lg=3, xl=3,
                ),
                dbc.Col(
                    stats_table, xs=12, sm=12, md=6, lg=6, xl=6
                ),
                dbc.Col(
                    dcc.Markdown(""), xs=12, sm=12, md=3, lg=3, xl=3,
                )
            ]
        )

    ])

    return container


# ------------------------------------------------------------------------

def get_table_stats_container(df, dark_mode):
    """Provides an HTML container for centering a statistics table for each city dataframe.
    :param: df (pandas.df) City data frame read from data
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return dbc.Container containing the HTML code for displaying the table."""

    hospital_header = 'Hospital'
    avg_header = 'Average Wait (hrs)'
    std_header = 'Standard Dev Wait (hrs)'

    df_stats = pd.DataFrame()
    stats = {hospital_header: [], avg_header: [], std_header: []}

    for hospital in df.columns:
        if hospital == TIME_STAMP_HEADER:
            continue

        stats[hospital_header].append(hospital)
        stats[avg_header].append(df[hospital].mean() / MINUTES_PER_HOUR)
        stats[std_header].append(df[hospital].std() / MINUTES_PER_HOUR)

    df_stats[hospital_header] = stats[hospital_header]
    df_stats[avg_header] = stats[avg_header]
    df_stats[std_header] = stats[std_header]

    df_stats = df_stats.dropna(axis=0)
    df_stats = df_stats.round(decimals=1)

    return get_table_container(df_stats, dark_mode, avg_header, std_header)


# ------------------------------------------------------------------------

def main_layout(dark_mode):
    """Returns the main/default (index) layout of the page.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return: dash HTML layout of the violin plot of the hospital."""

    layout = html.Div([
        html.Header(
            [
                html.A(
                    [
                        html.Img(id='ahs-logo', src='assets/ahs.jpg')
                    ], href='https://www.albertahealthservices.ca/'
                ),
                html.H1("Alberta ER Wait Times")
            ]
        ),
        html.H4(
            ["Source: ",
             html.A(
                 [f"{URL}"], id="url-link", href=f"{URL}")
             ], id="h4"),

        html.Div(
            [
                daq.ToggleSwitch(id='dark-mode-switch',
                                 label={'label': 'View Page in Dark Mode:', 'style': {'font-size': '20px'}},
                                 value=dark_mode,
                                 size=50,
                                 color='orange'),
                "Enter in number of hours for rolling average of line plots (1-48): ",
                dcc.Input(id='rolling-avg-hrs', type='number', value=1, min=1, max=48, step=1)
            ], id='page-settings'
        ),
        html.Hr(),
        dcc.Graph(id="line-yyc",
                  mathjax='cdn',
                  responsive='auto',
                  figure=plot_line("Calgary",
                                   max_date_yyc - datetime.timedelta(days=14),
                                   max_date_yyc,
                                   False)),
        html.Hr(),
        get_table_stats_container(df_yyc, dark_mode),
        html.Hr(),
        dcc.Graph(id="line-yeg",
                  mathjax='cdn',
                  responsive='auto',
                  figure=plot_line("Edmonton",
                                   max_date_yeg - datetime.timedelta(days=14),
                                   max_date_yeg,
                                   False)),
        html.Hr(),
        get_table_stats_container(df_yeg, dark_mode),
        html.Hr(),
        dcc.Graph(id='violin-yyc', mathjax='cdn', responsive='auto',
                  figure=plot_subplots_hour_violin("Calgary", False)),
        html.Hr(),
        dcc.Graph(id='violin-yeg', mathjax='cdn', responsive='auto',
                  figure=plot_subplots_hour_violin("Edmonton", False)),
        html.Footer(
            [
                html.Div(
                    ['This page was created using python apps: Plotly and Dash'],
                    id='footer-note'
                ),
                html.Div(
                    ['Contact:'],
                    id='footer-contact'
                ),
                html.A(
                    [
                        html.Img(src='assets/fb.png',
                                 id='fb-img')
                    ],
                    href='https://www.facebook.com/cbhuber/'
                ),
                html.A(
                    [
                        html.Img(src='assets/li.png',
                                 id='li-img')
                    ],
                    href='https://www.linkedin.com/in/cbhuber/'
                ),
                html.Div(
                    ['Ⓒ Colin Huber 2022, Distributed under the MIT License'],
                    id='copyright'
                )
            ]
        )
    ], id='main')

    return layout


# ------------------------------------------------------------------------

def get_violin_layout(df, city, hospital, dark_mode, y_arrow_vector):
    """Gets a single hospital violin plot to display on an entire page.
    :param: df (pandas.DataFrame) a df of the city
    :param: city (str) City containing the hospital
    :param: hospital (str) Hospital to be plotted
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :param: y_arrow_vector (int) Responsive distance of the y-arrow vector curve-fit annotation
    :return: dash HTML layout of the violin plot of the hospital."""

    df2 = filter_df(df)

    if df2 is None:
        raise PreventUpdate

    df3, hour_dict = get_wait_data_hour_dict(df2, hospital)

    hour_header = 'Hour'
    avg_header = 'Average Wait (hrs)'
    std_header = 'Standard Dev Wait (hrs)'

    df_stats = pd.DataFrame()
    stats = {hour_header: [], avg_header: [], std_header: []}

    for hour in df3.columns:
        stats[hour_header].append(hour_dict[hour])
        stats[avg_header].append(df3[hour].mean())
        stats[std_header].append(df3[hour].std())

    df_stats[hour_header] = stats[hour_header]
    df_stats[avg_header] = stats[avg_header]
    df_stats[std_header] = stats[std_header]

    df_stats = df_stats.round(decimals=1)

    table_container = get_table_container(df_stats, dark_mode, avg_header, std_header)

    layout = html.Div([
        dcc.Graph(id=f'{city}-{hospital}', mathjax='cdn', responsive='auto',
                  figure=plot_hospital_hourly_violin(city, hospital, True, False, dark_mode, y_arrow_vector)),
        html.Hr(),
        table_container,
    ], className='violin-page', style=update_layout(dark_mode))

    return layout


# ------------------------------------------------------------------------


@app.callback(Output('dark-mode-value', 'data'), [Input('dark-mode-switch', 'value')])
def dark_mode_setting(dark_mode):
    """CALLBACK: Updates the global value of dark mode based on changes in the switch.
    TRIGGER: Upon page loading and toggling the dark mode switch.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return: (bool) Whether the plot is done in dark mode or not """
    return dark_mode


# ------------------------------------------------------------------------

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname'), Input('dark-mode-value', 'data'), Input('viewport-container', 'data')])
def display_page(pathname, dark_mode, screen_size):
    """CALLBACK: Updates the page content based on the URL.
    TRIGGER: Upon page loading and when the URL changes
    :param: pathname (str) The URL in the browser
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return: dash HTML layout based on the URL."""

    mobile_small_height = 430
    y_arrow_vector = -500

    if screen_size['height'] < mobile_small_height:  # Landscape orientation
        y_arrow_vector = -150

    hospital_url = pathname.split('/')[-1]
    hospital_name = hospital_url.replace("_", " ")

    if pathname == '/':
        return main_layout(dark_mode)
    elif hospital_url in yyc_hospitals:
        return get_violin_layout(df_yyc, "Calgary", hospital_name, dark_mode, y_arrow_vector)
    elif hospital_url in yeg_hospitals:
        return get_violin_layout(df_yeg, "Edmonton", hospital_name, dark_mode, y_arrow_vector)
    else:
        return main_layout(dark_mode)


# ------------------------------------------------------------------------

@app.callback([Output('url-link', 'style'), Output('h4', 'style')],
              [Input('dark-mode-switch', 'value'), Input('viewport-container', 'data')])
def update_source_link(dark_mode, screen_size):
    """CALLBACK: Updates the color of the source link based on the dark mode selected.
    TRIGGER: Upon page loading and when selecting the toggle for dark mode
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :param: screen_size (dict) Dictionary of 'height' and 'width' the screen size
    :return: A style dictionary of the color and font size of the link"""

    mobile_small_length = 430

    if screen_size['width'] < mobile_small_length:  # Portrait orientation
        size = {'font-size': '10px'}
    else:
        size = {'font-size': '20px'}

    if dark_mode:
        color = {'color': 'orange'}
    else:
        color = {'color': 'blue'}

    return color, size


# ------------------------------------------------------------------------


@app.callback(Output('main', 'style'), [Input('dark-mode-switch', 'value')])
def update_layout(dark_mode):
    """CALLBACK: Updates layout based on the dark mode toggle switch selected.
    TRIGGER: Upon page loading and when selecting the toggle for dark mode
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: (dict) of styles to represent the main layout colors"""

    return {'fontFamily': FONT_FAMILY, 'fontSize': 18, 'color': COLOR_MODE_DASH['font_color'][dark_mode],
            'border': '4px solid skyblue', 'background-color': COLOR_MODE_DASH['bg_color'][dark_mode]}


# ------------------------------------------------------------------------

def get_min_max_date(relayout_data, df):
    """Returns the min and max dates from a df or the relayout data (based on x-axis selection or zoom)
    :param: relayout_data (dict) Data of the current x-axis relay.
    :param: df (pd.DataFrame) Dataframe of a particular city.
    :return: (str) The min and max dates."""

    date_format = '%Y-%m-%d'
    date_time_format1 = '%Y-%m-%dT%H:%M:%S'
    date_time_format2 = '%Y-%m-%d %H:%M:%S.%f'
    date_time_format3 = '%Y-%m-%dT%H:%M:%S.%f'
    date_time_format4 = '%Y-%m-%d %H:%M:%S'

    if relayout_data is None or 'autosize' in relayout_data:
        min_date_local = max_date_yyc - datetime.timedelta(days=14)  # Default show past 2 weeks
        max_date_local = max_date_yyc
    elif 'xaxis.autorange' in relayout_data:
        df2 = df.copy()
        df2 = df2.dropna(axis=1, how='all')

        # Convert all string to datetime objects
        df2.loc[:, TIME_STAMP_HEADER] = pd.to_datetime(df2[TIME_STAMP_HEADER], format=DATE_TIME_FORMAT)

        min_date_local = min(df2[TIME_STAMP_HEADER].dt.date)
        max_date_local = max(df2[TIME_STAMP_HEADER].dt.date)

    else:
        print(relayout_data)
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:

            if 'T' in relayout_data['xaxis.range[0]'] and '.' in relayout_data['xaxis.range[0]']:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[0]'], date_time_format3)
            elif ' ' in relayout_data['xaxis.range[0]'] and '.' not in relayout_data['xaxis.range[0]']:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[0]'], date_time_format4)
            elif 'T' in relayout_data['xaxis.range[0]']:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[0]'], date_time_format1)
            elif '.' in relayout_data['xaxis.range[0]']:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[0]'], date_time_format2)
            else:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[0]'], date_format)

            if 'T' in relayout_data['xaxis.range[1]'] and '.' in relayout_data['xaxis.range[1]']:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[1]'], date_time_format3)
            elif ' ' in relayout_data['xaxis.range[1]'] and '.' not in relayout_data['xaxis.range[1]']:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[1]'], date_time_format4)
            elif 'T' in relayout_data['xaxis.range[1]']:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[1]'], date_time_format1)
            elif '.' in relayout_data['xaxis.range[1]']:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[1]'], date_time_format2)
            else:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range[1]'], date_format)

        elif 'xaxis.range' in relayout_data:
            if 'T' in relayout_data['xaxis.range'][0]:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range'][0], date_time_format1)
            else:
                min_date_local = datetime.datetime.strptime(relayout_data['xaxis.range'][0], date_format)

            if 'T' in relayout_data['xaxis.range'][1]:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range'][1], date_time_format1)
            else:
                max_date_local = datetime.datetime.strptime(relayout_data['xaxis.range'][1], date_format)
        else:
            print(relayout_data)

    return min_date_local, max_date_local


# ------------------------------------------------------------------------

@app.callback(Output('line-yyc', 'figure'), [Input('dark-mode-switch', 'value'),
                                               Input('rolling-avg-hrs', 'value'),
                                               Input('line-yyc', 'relayoutData')])
def update_line_yyc(dark_mode, rolling_avg, relayout_data_yyc):
    """CALLBACK: Updates the line charts based on the dark mode selected.
    TRIGGER: Upon page load, toggling the dark mode switch, or changing x-axis timeline by button or zoom.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :param: rolling_avg (int) Number of hours to do rolling average on each hospital
    :return: (go.Figure), (go.Figure) objects that will be dynamically updated"""

    min_date_yyc_local, max_date_yyc_local = get_min_max_date(relayout_data_yyc, df_yyc)

    fig_yyc = plot_line("Calgary", min_date_yyc_local, max_date_yyc_local, False, dark_mode, rolling_avg)

    if fig_yyc is None:
        raise PreventUpdate

    fig_yyc.update_layout(transition_duration=500)

    return fig_yyc


# ------------------------------------------------------------------------

@app.callback(Output('line-yeg', 'figure'), [Input('dark-mode-switch', 'value'),
                                               Input('rolling-avg-hrs', 'value'),
                                               Input('line-yeg', 'relayoutData')])
def update_line_yeg(dark_mode, rolling_avg, relayout_data_yeg):
    """CALLBACK: Updates the line charts based on the dark mode selected.
    TRIGGER: Upon page load, toggling the dark mode switch, or changing x-axis timeline by button or zoom.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :param: rolling_avg (int) Number of hours to do rolling average on each hospital
    :return: (go.Figure), (go.Figure) objects that will be dynamically updated"""

    min_date_yeg_local, max_date_yeg_local = get_min_max_date(relayout_data_yeg, df_yeg)

    fig_yeg = plot_line("Edmonton", min_date_yeg_local, max_date_yeg_local, False, dark_mode, rolling_avg)

    if fig_yeg is None:
        raise PreventUpdate

    fig_yeg.update_layout(transition_duration=500)

    return fig_yeg


# ------------------------------------------------------------------------

@app.callback([Output('violin-yyc', 'figure'), Output('violin-yeg', 'figure')], [Input('dark-mode-switch', 'value')])
def update_violin(dark_mode):
    """CALLBACK: Updates the violin subplots based on the dark mode selected.
    TRIGGER: Upon page load or toggling the dark mode switch.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return: (go.Figure) x 2 for Calgary and Edmonton."""
    fig_yyc = plot_subplots_hour_violin("Calgary", False, dark_mode)
    fig_yeg = plot_subplots_hour_violin("Edmonton", False, dark_mode)

    if fig_yyc is None or fig_yeg is None:
        raise PreventUpdate

    fig_yyc.update_layout(transition_duration=500)
    fig_yeg.update_layout(transition_duration=500)

    return fig_yyc, fig_yeg


# ------------------------------------------------------------------------


"""CALLBACK: A client callback to execute JS in a browser session to get the screen width and height.
TRIGGER: Upon page loading.
Results are put in the Store() viewport-container data property."""
app.clientside_callback(
    """
    function(href) {
        var w = screen.width;
        var h = screen.height;
        return {'height': h, 'width': w};
    }
    """,
    Output('viewport-container', 'data'),
    Input('url', 'href')
)

# ------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server()
