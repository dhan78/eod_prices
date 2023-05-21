import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(
        id='heatmap',
        figure={
            'data': [{
                'type': 'heatmap',
                'z': [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                'colorscale': 'Viridis'
            }],
            'layout': {
                'height': 400,
                'width': 400
            }
        }
    ),
    html.Div(id='selected-color')
])


@app.callback(
    Output('selected-color', 'children'),
    Input('heatmap', 'clickData')
)
def display_selected_color(selected_data):
    if selected_data:
        points = selected_data['points']
        if points:
            # Retrieve the color of the first selected cell
            color = points[0]['data']['z'][points[0]['y']][points[0]['x']]
            return f'Selected cell color: {color}'

    return 'No cell selected'


if __name__ == '__main__':
    app.run_server(debug=True)
