import pandas as pd
from geopy.geocoders import Nominatim
import dash
import dash_leaflet as dl
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

# Initialize the Nominatim geocoder
geolocator = Nominatim(user_agent="airport_locator")

# icon = {
    # "iconUrl": "https://leafletjs.com/examples/custom-icons/leaf-green.png",
    # "shadowUrl": "https://leafletjs.com/examples/custom-icons/leaf-shadow.png",
    # "iconSize": [38, 95],  # size of the icon
    # "shadowSize": [50, 64],  # size of the shadow
    # "iconAnchor": [
    #     22,
    #     94,
    # ],  # point of the icon which will correspond to marker's location
    # "shadowAnchor": [4, 62],  # the same for the shadow
    # "popupAnchor": [
    #     -3,
    #     -76,
    # ],  # point from which the popup should open relative to the iconAnchor
# }



# Define the state name
state_list = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]
state_list_dropdown_values = [{'label':st,'value':st} for st in state_list]

# Use geopy to get the latitude and longitude of the state
# location = geolocator.geocode(state, exactly_one=True)
def get_airports_for_state(state):
    # Define the search query to find airports in the state
    query = f"airports in {state}"

    # Use geopy to get the latitude and longitude of the airports in the state
    airports = geolocator.geocode(query, exactly_one=False)

    # Print the latitude and longitude of each airport
    if not airports: return None
    airport_list=[]
    for airport in airports:
        try:
            if airport: airport_list.append(f"{state}| {airport.latitude}| {airport.longitude}| {airport.address}")
        except:
            pass

    df_airport = pd.DataFrame.from_dict(airport_list)
    df_airport.columns=['all_cols']
    df_airport = df_airport.all_cols.str.split('|',expand=True)
    df_airport.columns=['state','latitude','longitude','address']
    df_airport.latitude =df_airport.latitude.astype(float)
    df_airport.longitude =df_airport.longitude.astype(float)

    return df_airport

def get_airport_markers(p_df_airport):
    markers = []
    for airport in p_df_airport.itertuples():
        markers.append(
            dl.Marker(
                title=airport.address,
                position=(airport.latitude, airport.longitude),
                # icon=dl.(color='red'),
                children=[
                    dl.Tooltip(airport.address),
                    dl.Popup(airport.address),
                ],
            )
        )
    cluster = dl.MarkerClusterGroup(id="markers", children=markers)
    return cluster


# print (get_airports_for_state('New Jersey'))



app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(
        id='state_selector',
        options=state_list_dropdown_values,
        value='New Jersey'
    ),
    html.Div(dl.Map(id='map', style={'height': '100vh'}))
])


@app.callback(
    Output('map', 'children'),
    [Input('state_selector', 'value')]
)
def update_map(state):
    # df_airport = pd.read_pickle('alabama.pickle') # get_airports_for_state(state)
    df_airport = get_airports_for_state(state)
    if df_airport.shape[0]<1 :
        return [dash.no_update]

    return [
        dl.Map(
            [
                dl.TileLayer(),
                get_airport_markers(df_airport),
            ],
            zoom=7,
            center=(df_airport.latitude.mean(), df_airport.longitude.mean()),
        )
    ]

if __name__ == '__main__':
    app.run_server(port=8050, debug=True, host='0.0.0.0')
