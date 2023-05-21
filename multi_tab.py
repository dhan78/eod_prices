import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

app = dash.Dash(__name__)

# Bar chart data
bar_data = {'Category': ['A', 'B', 'C', 'D'],
            'Value': [10, 15, 7, 12]}

# Heatmap data
heatmap_data = [[1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12],
                [13, 14, 15, 16]]

app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Bar Chart', value='tab-1', children=[
            dcc.Graph(id='bar-chart')
        ]),
        dcc.Tab(label='Heatmap', value='tab-2', children=[
            html.Div([
                dcc.Dropdown(
                    id='dropdown',
                    options=[
                        {'label': 'Option 1', 'value': 'option1'},
                        {'label': 'Option 2', 'value': 'option2'},
                        {'label': 'Option 3', 'value': 'option3'}
                    ],
                    multi=True,
                    placeholder='Select values...'
                    ,style={'width': '50%'}
                )
            ]),
            dcc.Graph(id='heatmap')

        ])
    ])
])

@app.callback(
    Output('bar-chart', 'figure'),
    [Input('tabs', 'value')]
)
def update_bar_chart(selected_tab):
    if selected_tab == 'tab-1':
        fig = go.Figure(data=[go.Bar(x=bar_data['Category'], y=bar_data['Value'])])
        fig.update_layout(title='Bar Chart')
        return fig

# @app.callback(
#     Output('heatmap', 'figure'),
#     [Input('dropdown', 'value')]
# )
# def update_heatmap(selected_values):
#     if selected_values:
#         filtered_data = [[heatmap_data[i][j] for j in range(len(heatmap_data[i])) if heatmap_data[i][j] % 2 == 0] for i in range(len(heatmap_data)) if i % 2 == 0]
#         fig = go.Figure(data=[go.Heatmap(z=filtered_data)])
#         fig.update_layout(title='Heatmap')
#         return fig

if __name__ == '__main__':
    app.run_server(debug=True)
