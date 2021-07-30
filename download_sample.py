import io
import dash
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_extensions import Download
import dash_table
from flask import Flask
import pandas as pd

server = Flask(__name__)
app = dash.Dash(server=server)

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')

app.layout = html.Div(
                [
                    Download(id="download"),
                    html.Button("Download",
                                id="save-button"),
                    html.Div("Press button to save data at your desktop",
                             id="output-1"),
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in df.columns],
                        data=df.to_dict('records'),
                    )
                ]
            )


@app.callback(
Output("download", "data"),
Input("save-button", "n_clicks"),
State("table", "data"))
def download_as_csv(n_clicks, table_data):
    df = pd.DataFrame.from_dict(table_data)
    if not n_clicks:
      raise PreventUpdate
    download_buffer = io.StringIO()
    df.to_csv(download_buffer, index=False)
    download_buffer.seek(0)
    return dict(content=download_buffer.getvalue(), filename="some_filename.csv")

if __name__ == '__main__':
    app.run_server(port='8099')
