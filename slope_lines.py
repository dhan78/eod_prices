import plotly.graph_objects as go

# Create x and y data for the slope line
x = [1, 10000000000]  # Range of x values from 1 to 10 billion
y = [1.4 * val for val in x]  # Calculate corresponding y values

# Create a trace for the slope line
slope_trace = go.Scatter(
    x=x,
    y=y,
    mode='lines',
    name='Slope Line',
    line=dict(color='blue', width=1)
)

# Create a layout for the chart
layout = go.Layout(
    title='Slope Line: y = 1.4x',
    xaxis=dict(title='EBITDA'),
    yaxis=dict(title='DEBT'),
)

# Create a figure and add the slope trace and layout
fig = go.Figure(data=[slope_trace], layout=layout)

# Display the chart
fig.show()
