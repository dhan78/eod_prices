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


import plotly.graph_objects as go

# Create some sample data
x = [1, 2, 3, 4, 5]
y = [2, 4, 1, 5, 3]

# Create a trace for the scatter plot
trace = go.Scatter(x=x, y=y, mode='markers')

# Create a list of annotations
annotations = [
    dict(
        x=3,  # X coordinate of the annotation
        y=1,  # Y coordinate of the annotation
        xref='x',
        yref='y',
        text='Annotation Text',
        showarrow=True,
        arrowhead=7,
        ax=0,
        ay=-40
    )
]

# Add the annotations to the trace
trace['text'] = [''] * len(x)  # Initialize empty text to avoid overlapping labels
for annotation in annotations:
    trace['text'][annotation['x']-1] = annotation['text']  # -1 because Python lists are 0-indexed

# Create the figure
fig = go.Figure(data=[trace])

# Update the layout to show annotations
fig.update_layout(annotations=annotations)

# Show the plot
fig.show()

