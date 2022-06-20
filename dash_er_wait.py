"""The main app to run the dash server to display the results of the ER wait times in Alberta with interactive
features."""

import dash
from dash import dcc
from dash import html
import dash_daq as daq
import pandas as pd
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from plot_er_wait_stats import plot_line, FONT_FAMILY

app = dash.Dash(__name__, assets_folder='assets')

server = app.server

df_yyc = pd.read_csv('Calgary_hospital_stats.csv')
df_yeg = pd.read_csv('Edmonton_hospital_stats.csv')

# Dash HTML layout
app.layout = html.Div([
    dcc.Location(id='url'), dcc.Store(id='viewport-container', data={}, storage_type='session'),
    html.Header([html.H1("Alberta ER Wait Times")], style={'text-align': 'center', 'text-decoration': 'underline'}),

    html.Div([daq.ToggleSwitch(id='dark-mode-switch', label=dict(label='View Page in Dark Mode:',
                                                                 style={'font-size': '20px'}), value=True, size=50,
                               color='skyblue')]),

    dcc.Graph(id="line-yyc", mathjax='cdn', responsive='auto', figure=plot_line("Calgary", False)),
    html.Hr(),
    dcc.Graph(id="line-yeg", mathjax='cdn', responsive='auto', figure=plot_line("Edmonton", False)),
    html.Hr(),
    html.Footer(
        [html.Div(['This page was created using python apps: Plotly and Dash - Content developed by Colin Huber'],
                  style={'font-size': '30px'}),
         html.Div(['Contact:'], style={'text-decoration': 'underline', 'color': 'skyblue', 'font-size': '30px'}),
         html.A([html.Img(src='assets/fb.png')], href='https://www.facebook.com/cbhuber/'),
         html.A([html.Img(src='assets/li.png', style={'margin-left': '10px'})],
                href='https://www.linkedin.com/in/cbhuber/')],
        style={'text-align': 'center'},
    ),
    html.Div(['Ⓒ Colin Huber 2022, Distributed under the MIT License'], style={'text-align': 'center'})
], id='main')


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
