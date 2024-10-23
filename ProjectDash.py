from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go # or plotly.express as px
import numpy as np


# Load the data
df = pd.read_csv('Small US Airline Flight Routes and Fares 1993-2024.csv')

# Split 'Geocoded_City1' into 'start_lat' and 'start_lon'
df[['start_lat', 'start_lon']] = df['Geocoded_City1'].str.split(', ', expand=True)

# Split 'Geocoded_City2' into 'end_lat' and 'end_lon'
df[['end_lat', 'end_lon']] = df['Geocoded_City2'].str.split(', ', expand=True)

# Convert the latitude and longitude columns to numeric
df['start_lat'] = pd.to_numeric(df['start_lat'])
df['start_lon'] = pd.to_numeric(df['start_lon'])
df['end_lat'] = pd.to_numeric(df['end_lat'])
df['end_lon'] = pd.to_numeric(df['end_lon'])

# Initialize the Dash app
app = Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1('Assignment 2: Exercise A'),
    html.Br(),
    
    html.H3('US Airline Flights Route', id='title'),
    
    dcc.Dropdown(
        id = 'year-dropdown',
        options = sorted([{'label': year, 'value': year} for year in df['Year'].unique()], key=lambda x: x['value']),
        placeholder = 'Select a year',
        multi=True
    ),
    html.Br(),
    
    dcc.Dropdown(
        id = 'source-city-dropdown',
        options = sorted([{'label': source, 'value': source} for source in df['city1'].unique()], key=lambda x: x['label']),
        placeholder = 'Select a source city',
        multi=True
    ),
    html.Br(),
    
    dcc.Graph(id='graph1'),
])

# Define the callback
@app.callback(
    Output('graph1', 'figure'),
    Input('year-dropdown', 'value'),
    Input('source-city-dropdown', 'value'),
)
def update_graph(year_selected, source_city_selected):
    # Create a route field for grouping (ensure consistent ordering for route pairs)
    df['route'] = df.apply(lambda row: tuple(sorted([row['city1'], row['city2']])), axis=1)

    # Count the number of flights per route
    route_counts = df.groupby(['route', 'start_lat', 'start_lon', 'airport_1']).size().reset_index(name='flight_count')
    
    
    if year_selected is None or len(year_selected) == 0:
        year_selected = df['Year'].unique()
    
    if source_city_selected is None or len(source_city_selected) == 0:
        source_city_selected = df['city1'].unique()
        
    # Filter the data
    df_year = df[df['Year'].isin(year_selected) & df['city1'].isin(source_city_selected)]
    
    # Group data by city and aggregate the necessary fields
    df_aggregated = df_year.groupby(['city1', 'start_lat', 'start_lon',]).agg({
        'passengers': 'sum',  # Sum the passengers
        'airport_1': 'first',  # Take the first airport name for hover text (you can change this)
        'end_lat': 'first',
        'end_lon': 'first',
    }).reset_index()

    # Count the number of flights (how many times each city occurs)
    flight_count = df_year['city1'].value_counts().reset_index()
    flight_count.columns = ['city1', 'flight_count']

    # Merge the flight count back to the aggregated data
    df_aggregated = df_aggregated.merge(flight_count, on='city1', how='left')

    # Add tooltips for hover information
    df_aggregated['hover_text'] = (
        'City: ' + df_aggregated['city1'] + '<br>' +
        'Total Flights: ' + df_aggregated['flight_count'].astype(str) + '<br>' +
        'Passengers: ' + df_aggregated['passengers'].astype(str) + '<br>' +
        'Airport: ' + df_aggregated['airport_1']
    )
    
    # Create a color scale (categorical color for each unique city)
    unique_cities = df_aggregated['city1'].unique()
    color_scale = px.colors.qualitative.Plotly  # Choose a Plotly qualitative color scale

    # Create a dictionary mapping each airport to a color
    city_colors = {city: color_scale[i % len(color_scale)] for i, city in enumerate(unique_cities)}
    
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scattergeo(
            locationmode = 'USA-states',
            lon = df_aggregated['start_lon'],
            lat = df_aggregated['start_lat'],
            hoverinfo = 'text',
            text= df_aggregated['hover_text'],
            mode = 'markers',
            marker = dict(
                size=route_counts['flight_count'],  # Marker size based on flight count
                sizemode='area',  # Optional: adjust size based on area
                sizeref=2.*max(route_counts['flight_count'])/(15.**2),  # Size scaling for better visualization
                color=[city_colors[city] for city in df_aggregated['city1']]  # Marker color based on city,
                )
            )
        )
    
    # line_hover_text = 'From: ' + df_year['city1'] + '<br>' + 'To: '+ df_year['city2'] + 'Flights: ' + df_year['passengers'].astype(str)
    
    for i, row in df_year.iterrows():
        fig.add_trace(
            go.Scattergeo(
                locationmode='USA-states',
                lon=[row['start_lon'], row['end_lon'], None],  # Longitude for the route
                lat=[row['start_lat'], row['end_lat'], None],  # Latitude for the route
                mode='lines',
                line=dict(
                    width=1,
                    color=city_colors[row['city1']],  # Color based on city1
                ),
                opacity=0.5
            )
        )
    
    fig.update_layout(
        title_text = 'American Airline flight paths<br>(Hover for airport names)',
        showlegend = False,
        geo = go.layout.Geo(
            scope = 'north america',
            projection_type = 'azimuthal equal area',
            showland = True,
            landcolor = 'rgb(30, 30, 30)',
            countrycolor = 'rgb(60, 60, 60)',
            lakecolor='rgb(40, 40, 40)',
            bgcolor='rgb(20, 20, 20)',
            lonaxis=dict(
                range=[-130, -60],  # Adjust longitude range (left-right)
            ),
            lataxis=dict(
                range=[20, 55],  # Adjust latitude range (up-down)
            ),
        ),
        paper_bgcolor='rgb(150, 150, 150)',
        font = dict(color='white'),
        height=700,
    )
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)