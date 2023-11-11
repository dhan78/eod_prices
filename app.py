import dash  # pip install dash
# import dash_labs as dl  # pip install dash-labs
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components

# Code from: https://github.com/plotly/dash-labs/tree/main/docs/demos/multi_page_example1
# test
app = dash.Dash(
    __name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP]
)
# server = app.server
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(page["name"], href=page["path"])) for page in dash.page_registry.values()
        if page["module"] != "pages.not_found_404"
    ],
    #     if page["module"] != "pages.not_found_404",
    #     dbc.DropdownMenu(
    #         [
    #             dbc.DropdownMenuItem(page["name"], href=page["path"])
    #             for page in dash.page_registry.values()
    #             if page["module"] != "pages.not_found_404"
    #         ],
    #         nav=True,
    #         label="Select Dashboard",
    #     )
    # ],

    brand="Options Analytics",
    color="primary",
    dark=True,
    className="mb-2",
)

app.layout = dbc.Container(
    [navbar, dash.page_container],
    fluid=True,
)

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port='8050' , threaded=True)
