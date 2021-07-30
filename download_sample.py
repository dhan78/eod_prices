import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    html.Label("Show?"),
    dcc.Dropdown(
        id="my-input",
        options = [
            {'label':'Yes', 'value':1},
            {'label':'No', 'value':0}
        ]
    ),
    html.Div(
        id="graph-container",
        children = [

        dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    )
    ])


])

@app.callback(Output('graph-container', 'style'), [Input('my-input', 'value')],prevent_initial_call=True)
def hide_graph(my_input):
    if my_input:
        return {'display':'block'}
    return {'display':'none'}



if __name__ == '__main__':
    app.run_server(port=8125, debug = True)
