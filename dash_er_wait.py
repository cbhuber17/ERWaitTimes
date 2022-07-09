"""The main app to run the dash server to display the results of the ER wait times in Alberta with interactive
features."""

import dash
from dash import dcc
from dash import html
from dash import dash_table
import dash_daq as daq
import pandas as pd
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate  # TODO: May need removing
import dash_bootstrap_components as dbc
from plot_er_wait_stats import plot_line, plot_subplots_hour_violin, plot_hospital_hourly_violin, FONT_FAMILY, TIME_STAMP_HEADER
from capture_er_wait_data import URL

app = dash.Dash(__name__, assets_folder='assets', title='Alberta ER Wait Times', update_title='Please wait...',
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True  # Dynamic layout
server = app.server

# TODO: Live updating and adding to CSV/mongo
df_yyc = pd.read_csv('Calgary_hospital_stats.csv')
df_yeg = pd.read_csv('Edmonton_hospital_stats.csv')

yyc_hospitals = [x.replace(" ", "_") for x in list(df_yyc.columns)]
yeg_hospitals = [x.replace(" ", "_") for x in list(df_yeg.columns)]

# ------------------------------------------------------------------------

app.layout = html.Div([
    dcc.Location(id='url'), dcc.Store(id='viewport-container', data={}, storage_type='session'),
    html.Div(id='page-content')
])


# ------------------------------------------------------------------------
# TODO: Table dark mode callback
def get_table_stats_container(df):
    """Provides a HTML container for centering a statistics table for each city dataframe.
    :param: df (pandas.df) City data frame read from csv file
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
        stats[avg_header].append(df[hospital].mean() / 60.0)
        stats[std_header].append(df[hospital].std() / 60.0)

    df_stats[hospital_header] = stats[hospital_header]
    df_stats[avg_header] = stats[avg_header]
    df_stats[std_header] = stats[std_header]

    df_stats = df_stats.dropna(axis=0)
    df_stats = df_stats.round(decimals=1)

    stats_table = html.Div(
        [
            dash_table.DataTable(data=df_stats.to_dict('records'),
                                 style_cell={'textAlign': 'center',
                                             'height': 'auto',
                                             'padding-right': '10px',
                                             'padding-left': '10px',
                                             'whiteSpace': 'normal',
                                             },
                                 style_cell_conditional=[
                                     {'if': {'column_id': avg_header},
                                      'width': '150px'},
                                     {'if': {'column_id': std_header},
                                      'width': '150px'},
                                 ],
                                 fill_width=False,
                                 style_table={'overflowX': 'auto'},
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

def main_layout():
    """Returns the main/default (index) layout of the page.
    :param: None
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
                                 value=True,
                                 size=50,
                                 color='orange')
            ]
        ),
        html.Hr(),
        dcc.Graph(id="line-yyc", mathjax='cdn', responsive='auto', figure=plot_line("Calgary", False)),
        html.Hr(),
        get_table_stats_container(df_yyc),
        html.Hr(),
        dcc.Graph(id="line-yeg", mathjax='cdn', responsive='auto', figure=plot_line("Edmonton", False)),
        html.Hr(),
        get_table_stats_container(df_yeg),
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

def get_violin_layout(city, hospital):
    """Gets a single hospital violin plot to display on an entire page.
    :param: city (str) City containing the hospital
    :param: hospital (str) Hospital to be plotted
    :return: dash HTML layout of the violin plot of the hospital."""

    layout = html.Div([
        dcc.Graph(id=f'{city}-{hospital}', mathjax='cdn', responsive='auto',
                  figure=plot_hospital_hourly_violin(city, hospital, True, False, True))
    ])

    return layout


# ------------------------------------------------------------------------

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    """CALLBACK: Updates the page content based on the URL.
    TRIGGER: Upon page loading and when the URL changes
    :param: pathname (str) The URL in the browser
    :return: dash HTML layout based on the URL."""

    hospital_url = pathname.split('/')[-1]
    hospital_name = hospital_url.replace("_", " ")

    if pathname == '/':
        return main_layout()
    elif hospital_url in yyc_hospitals:
        return get_violin_layout("Calgary", hospital_name)  # TODO: Need to get dark_mode in here
    elif hospital_url in yeg_hospitals:
        return get_violin_layout("Edmonton", hospital_name)
    else:
        return main_layout()


# ------------------------------------------------------------------------

@app.callback([Output('url-link', 'style'), Output('h4', 'style')],
              [Input('dark-mode-switch', 'value'), Input('viewport-container', 'data')])
def update_source_link(dark_mode, screen_size):
    """CALLBACK: Updates the color of the source link based on the dark mode selected.
    TRIGGER: Upon page loading and when selecting the toggle for dark mode
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :param: screen_size (dict) Dictionary of 'height' and 'width' the screen size
    :return: A style dictionary of the color"""

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
    """CALLBACK: Updates the histogram based on the radio-button detail-size selected.
    TRIGGER: Upon page loading and when selecting the toggle for dark mode
    :param: dark_mode (bool) If dark mode plotting is done (True), light mode plotting (False)
    :return: Global style layout as dark or light theme"""

    color_mode = {'font_color': ('black', 'white'),
                  'bg_color': ('white', '#3a3f44')}

    return {'fontFamily': FONT_FAMILY, 'fontSize': 18, 'color': color_mode['font_color'][dark_mode],
            'border': '4px solid skyblue', 'background-color': color_mode['bg_color'][dark_mode]}


# ------------------------------------------------------------------------

@app.callback([Output('line-yyc', 'figure'), Output('line-yeg', 'figure')], [Input('dark-mode-switch', 'value')])
def update_line(dark_mode):
    """CALLBACK: Updates the line charts based on the dark mode selected.
    TRIGGER: Upon page load or toggling the dark mode switch.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return: (go.Figure), (go.Figure) objects that will be dynamically updated"""

    fig_yyc = plot_line("Calgary", False, dark_mode)
    fig_yeg = plot_line("Edmonton", False, dark_mode)

    fig_yyc.update_layout(transition_duration=500)
    fig_yeg.update_layout(transition_duration=500)

    return fig_yyc, fig_yeg


# ------------------------------------------------------------------------

@app.callback([Output('violin-yyc', 'figure'), Output('violin-yeg', 'figure')], [Input('dark-mode-switch', 'value')])
def update_violin(dark_mode):
    """CALLBACK: Updates the violin subplots based on the dark mode selected.
    TRIGGER: Upon page load or toggling the dark mode switch.
    :param: dark_mode (bool) Whether the plot is done in dark mode or not
    :return: (go.Figure) x 2 for Calgary and Edmonton."""
    fig_yyc = plot_subplots_hour_violin("Calgary", False, dark_mode)
    fig_yeg = plot_subplots_hour_violin("Edmonton", False, dark_mode)

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
