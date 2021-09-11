import functools

from utils.pc_utils import *

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State






app = dash.Dash('Foo', external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash()
tickr = Ticker('TSLA')
# current_price = tickr.get_lastSalePrice()
fig = tickr.get_charts()
oc = OptionChart(None,None)
figOption = None
# {'display':'none'}
# {'display':'block'}
content_first_row = dbc.Row(
    [
        dbc.Col(
            [dcc.Input(id="target_close", type="number",debounce=True, placeholder="0",),
            html.Div(id='slider-output-container',
                     style={'font-family':'Arial',
                               'font-size': '15px'}),
             ], md=2
        ),
        dbc.Col(
            html.Button('Reset Targets', id='reset-val', n_clicks=0), md=2
        ),
        dbc.Col(
            dbc.Checklist(
                options=[
                    {"label": "ShowOptionHistory", "value": "showOptionHistory"},
                    {"label": "Replay History", "value": "ReplayHistory", },
                ],
                value=[""],
                id="switches-input",
                switch=True,
            ), md=2
        )
    ]
)

app.layout = html.Div([content_first_row,
    html.Div(id='option-chart-output-id',children=[dcc.Loading(dcc.Graph(id='option-chart-output', figure ={}),type='default')],style={'display': 'none'}),
    html.Div(id='replay-history-output-id',children=[
                                                    dcc.DatePickerRange( id='date_picker',
                                                        minimum_nights=4,
                                                        clearable=True,
                                                        with_portal=True,
                                                        start_date=prev_monday,
                                                        end_date=prev_friday
                                                    ),
                                                    html.Button('Build History', id='replay-history', n_clicks=0),
                                                    dcc.Loading(dcc.Graph(id='replay-history-output', figure ={}),type='default')
                                                    ],style={'display': 'none'}),
    html.Div(dcc.Graph(id='graph', figure=fig),),
    dcc.Interval(
        id='interval-component',
        interval= 30 * 1000,  # in milliseconds
        n_intervals=0
    )

])

def get_option_chart_display(p_switch_value,p_DivName):
    if p_DivName in p_switch_value:
        return {'display':'block'}
    else:
        return {'display': 'none'}

@app.callback(
    [Output('graph', 'figure'),
     Output('option-chart-output', 'figure'),
     Output('slider-output-container', 'children'),
     Output('option-chart-output-id','style'),
     Output('replay-history-output-id','style'),
     Output('replay-history-output','figure')
     ],
    [Input('target_close', 'value'),
     Input('graph', 'clickData'),
     Input('interval-component', 'n_intervals'),Input('reset-val', 'n_clicks'),
     Input('switches-input','value'),
     Input('replay-history','n_clicks')
     ],
    [State('graph','figure'),State('target_close','value'),
     State('date_picker','start_date'),State('date_picker','end_date'),
     ],
    prevent_initial_call=True
)
def display_click_data(target_closing_price, clickData,n_intervals, n_clicks,switch_value, replay_history, figure,target_close,
                       start_date,end_date):
    tickr.target_close_lst.append(target_close)
    target_close_text = 'Target Closing Price (Modeled) : "{}"'.format(', '.join([str(i) for i in list(set(tickr.target_close_lst)) if i]))
    toggle_display=functools.partial(get_option_chart_display,switch_value)
    try:
        ctx = dash.callback_context

        if ctx.triggered[0]['prop_id'] == 'graph.clickData': # just clicking chart
            if 'showOptionHistory' not in switch_value : raise dash.exceptions.PreventUpdate # option Toggle is OFF
            curveNum = clickData['points'][0]['curveNumber']
            curveName = figure['data'][curveNum]['name']
            if curveName.split()[0] not in ['C','P']: raise dash.exceptions.PreventUpdate # Clicked on Ratio chart
            clickData['points'][0]['curveName'] = figure['data'][curveNum]['name']
            df_click = pd.DataFrame(clickData['points']).dropna(subset=['curveName'])
            df_click['expiry_dt'] = df_click.curveName.apply(lambda x: pd.to_datetime(x.split()[1]).strftime('%b %d'))
            oc = OptionChart(df_click.expiry_dt,df_click.x)
            return dash.no_update,oc.generate_fig(),target_close_text, toggle_display('showOptionHistory'),toggle_display('ReplayHistory'),dash.no_update
        elif ctx.triggered[0]['prop_id'] == 'interval-component.n_intervals': # triggered by timer
            tickr.get_lastSalePrice()
            # if tickr.state == OIC_State.RUNNING:
            print (f'Previous call status: {tickr.state}')
            if tickr.marketStatus == 'Market Closed': raise dash.exceptions.PreventUpdate()

            return tickr.get_charts(),dash.no_update,target_close_text,toggle_display('showOptionHistory'),toggle_display('ReplayHistory'),dash.no_update
        elif ctx.triggered[0]['prop_id'] == 'target_close.value': # triggered by changing target_close
            tickr.target_close = target_close
            tickr.get_lastSalePrice()
            tickr.predict()
            return tickr.get_charts(), dash.no_update,target_close_text, toggle_display('showOptionHistory'),toggle_display('ReplayHistory'),dash.no_update
        elif ctx.triggered[0]['prop_id'] == 'reset-val.n_clicks': # triggered by clicking reset button
            tickr.target_close_lst , tickr.target_close = [], None
            tickr.dict_target = {}
            target_close_text = 'Target Closing Price : "{}"'.format(
                ', '.join([str(i) for i in list(set(tickr.target_close_lst))]))
            return tickr.get_charts(), dash.no_update, target_close_text, toggle_display('showOptionHistory'),toggle_display('ReplayHistory'),dash.no_update
        elif ctx.triggered[0]['prop_id'] == 'switches-input.value':  # triggered by option toggle buttn
            return dash.no_update, dash.no_update, dash.no_update, toggle_display('showOptionHistory'),toggle_display('ReplayHistory'),dash.no_update
        elif ctx.triggered[0]['prop_id'] == 'replay-history.n_clicks':  # triggered by clicking Build History
            fig = tickr.create_history_fig(start_date,end_date)
            return dash.no_update, dash.no_update, dash.no_update, toggle_display('showOptionHistory'), toggle_display( 'ReplayHistory'),fig
    except:
        e = sys.exc_info()[1]
        print (traceback.print_exc())
        raise dash.exceptions.PreventUpdate
        # return fig, dash.no_update,target_close_text, dash





app.run_server(debug=True, host='0.0.0.0',threaded=True)  # Turn off reloader if inside Jupyter
