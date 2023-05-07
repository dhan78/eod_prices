import random
import dash
import dash_html_components as html
import dash_leaflet as dl
from dash.dependencies import Input, Output, State

app = dash.Dash(__name__)

map_bounds = {
    'north': 52,
    'south': 51,
    'east': -0.05,
    'west': -0.15
}

app.layout = html.Div([
    dl.Map(
        [
            dl.TileLayer(),
            dl.Marker(position=(51.5, -0.1), children=[
                dl.Tooltip("Marker 1"),
                dl.CircleMarker(
                    center=(51.5, -0.1),
                    radius=100,
                    color='red',
                    fillColor='red',
                    children=[dl.Tooltip("Custom Tooltip")]
                ),
            ])
        ],
        id="map",
        style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"},
        center=[51.5, -0.1],
        zoom=10,
    ),
    html.Button('Add Marker', id='add-marker', n_clicks=0),
])

@app.callback(
    Output('map', 'children'),
    Input('add-marker', 'n_clicks'),
    State('map', 'children')
)
def add_marker(n_clicks, map_children):
    if n_clicks > 0:
        lat = random.uniform(map_bounds['south'], map_bounds['north'])
        lon = random.uniform(map_bounds['west'], map_bounds['east'])

        new_marker = dl.CircleMarker(
            center=(lat, lon),
            radius=10,
            color='red',
            children=[dl.Tooltip(f"Marker {n_clicks + 1}")]
        )
        map_children.append(new_marker)
    return map_children

if __name__ == '__main__':
    app.run_server(debug=True)
