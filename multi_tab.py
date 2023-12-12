import dash
import dash_html_components as html
import dash_core_components as dcc

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.Header(children='My Dash App'),
    html.Div(children=[
        dcc.Dropdown(
            id='dropdown-1',
            options=[
                {'label': 'Option 1', 'value': '1'},
                {'label': 'Option 2', 'value': '2'},
                {'label': 'Option 3', 'value': '3'},
            ],
            style={'width': '25%'},
        ),
        dcc.Dropdown(
            id='dropdown-2',
            options=[
                {'label': 'Option 1', 'value': '1'},
                {'label': 'Option 2', 'value': '2'},
                {'label': 'Option 3', 'value': '3'},
            ],
            style={'width': '25%'},
        ),
        dcc.Dropdown(
            id='dropdown-3',
            options=[
                {'label': 'Option 1', 'value': '1'},
                {'label': 'Option 2', 'value': '2'},
                {'label': 'Option 3', 'value': '3'},
            ],
            style={'width': '25%'},
        ),
    ]),
    html.Div(children=[
        dcc.Graph(
            id='graph-1',
            style={'width': '50%'},
        ),
        dcc.Graph(
            id='graph-2',
            style={'width': '50%'},
        ),
    ]),
    html.Div(children=[
        dcc.Graph(
            id='graph-3',
            style={'width': '50%'},
        ),
        dcc.Graph(
            id='graph-4',
            style={'width': '50%'},
        ),
    ]),
])

if __name__ == '__main__':
    app.run_server(debug=True)
