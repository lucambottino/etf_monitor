'''
# Initialize Dash application
app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.Button("Generate Data", id="generate-button", n_clicks=0),
        dcc.Interval(
            id='interval-component',
            interval=1*60*1000, # in milliseconds
            n_intervals=0
        ),
        dash_table.DataTable(
            id='table',
            style_data={
                'whiteSpace': 'normal',
                'width': '10px',
                'lineWidth': '15px',
                'max-width': '30px'
            }, style_cell={'width': '10%'}
        ),
    ]
)

@app.callback(
    Output("table", "data"),
    [Input("generate-button", "n_clicks"), Input('interval-component', 'n_intervals')],
)
def update_table(n, intervals):
    data = generate_data()
    return data

if __name__ == '__main__':
    app.run_server(debug=True)
'''