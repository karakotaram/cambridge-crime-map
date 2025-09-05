#!/usr/bin/env python3
"""
Interactive Leaflet map of Cambridge crime incidents with circle markers.
Markers are colored by incident type and sized by frequency.
"""

import pandas as pd
import folium
from collections import Counter
import numpy as np
from math import sqrt


def load_and_process_data(csv_path):
    """Load and process crime data from CSV file."""
    df = pd.read_csv(csv_path)
    
    # Clean data - remove rows without coordinates
    df = df.dropna(subset=['Reporting Area Lat', 'Reporting Area Lon'])
    
    # Convert coordinates to float
    df['lat'] = pd.to_numeric(df['Reporting Area Lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['Reporting Area Lon'], errors='coerce')
    
    # Remove invalid coordinates
    df = df.dropna(subset=['lat', 'lon'])
    
    return df


def aggregate_by_location_and_crime(df):
    """Aggregate incidents by location and crime type to calculate frequencies."""
    # Group by coordinates and crime type, count incidents
    grouped = df.groupby(['lat', 'lon', 'Crime']).size().reset_index(name='frequency')
    
    # Also get total incidents per location for sizing
    location_totals = df.groupby(['lat', 'lon']).size().reset_index(name='total_incidents')
    
    # Merge to get both crime-specific and total counts
    result = grouped.merge(location_totals, on=['lat', 'lon'])
    
    # Add additional info for tooltips
    location_info = df.groupby(['lat', 'lon']).agg({
        'Neighborhood': 'first',
        'Location': 'first',
        'Reporting Area': 'first'
    }).reset_index()
    
    result = result.merge(location_info, on=['lat', 'lon'])
    
    return result


def get_color_palette():
    """Define color palette for different crime types."""
    colors = [
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Blue
        '#96CEB4',  # Green
        '#FCEA4B',  # Yellow
        '#FF8A80',  # Light Red
        '#9C27B0',  # Purple
        '#FF5722',  # Deep Orange
        '#795548',  # Brown
        '#607D8B',  # Blue Grey
        '#E91E63',  # Pink
        '#00BCD4',  # Cyan
        '#8BC34A',  # Light Green
        '#FFC107',  # Amber
        '#FF9800',  # Orange
        '#673AB7',  # Deep Purple
        '#3F51B5',  # Indigo
        '#2196F3',  # Blue
        '#009688',  # Teal
        '#4CAF50'   # Green
    ]
    return colors


def create_cambridge_crime_map(csv_path='crimedata.csv'):
    """Create interactive Leaflet map of Cambridge crime incidents."""
    
    # Load and process data
    print("Loading crime data...")
    df = load_and_process_data(csv_path)
    print(f"Loaded {len(df)} incidents")
    
    # Aggregate data
    print("Aggregating incidents by location and type...")
    aggregated = aggregate_by_location_and_crime(df)
    
    # Get unique crime types and assign colors
    crime_types = aggregated['Crime'].unique()
    colors = get_color_palette()
    color_map = {crime: colors[i % len(colors)] for i, crime in enumerate(crime_types)}
    
    # Calculate center of Cambridge (approximate)
    center_lat = df['lat'].mean()
    center_lon = df['lon'].mean()
    
    # Create base map
    print("Creating map...")
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add markers for each location-crime combination
    print("Adding markers...")
    
    # Calculate marker size range
    max_total = aggregated['total_incidents'].max()
    min_total = aggregated['total_incidents'].min()
    
    for _, row in aggregated.iterrows():
        # Scale marker size based on total incidents at location (5-25 pixel radius)
        size = 5 + (row['total_incidents'] - min_total) / (max_total - min_total) * 20
        
        # Create popup text
        popup_text = f"""
        <b>Location:</b> {row['Location'] if pd.notna(row['Location']) else 'Not specified'}<br>
        <b>Neighborhood:</b> {row['Neighborhood'] if pd.notna(row['Neighborhood']) else 'Not specified'}<br>
        <b>Crime Type:</b> {row['Crime']}<br>
        <b>Incidents of this type:</b> {row['frequency']}<br>
        <b>Total incidents at location:</b> {row['total_incidents']}
        """
        
        # Add circle marker
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=size,
            popup=folium.Popup(popup_text, max_width=300),
            color=color_map[row['Crime']],
            fillColor=color_map[row['Crime']],
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # Create legend
    print("Creating legend...")
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 250px; height: 400px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; overflow-y: scroll;
                ">
    <h4 style="margin: 10px;">Crime Types</h4>
    '''
    
    # Add color legend for crime types
    for crime_type in sorted(crime_types):
        color = color_map[crime_type]
        count = len(aggregated[aggregated['Crime'] == crime_type])
        legend_html += f'''
        <div style="margin: 5px 10px;">
            <span style="display: inline-block; width: 12px; height: 12px; 
                         background-color: {color}; border: 1px solid black;"></span>
            <span style="margin-left: 5px; font-size: 10px;">{crime_type} ({count} locations)</span>
        </div>
        '''
    
    legend_html += '''
    <hr style="margin: 10px;">
    <div style="margin: 10px; font-size: 10px;">
        <b>Marker Size:</b> Total incidents at location<br>
        <small>Larger circles = more total incidents</small>
    </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add additional map layers
    folium.TileLayer(
        tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        name='Stamen Terrain'
    ).add_to(m)
    folium.TileLayer('cartodb positron').add_to(m)
    folium.LayerControl().add_to(m)
    
    return m


def main():
    """Main function to create and save the map."""
    # Create map
    crime_map = create_cambridge_crime_map('../../crimedata.csv')
    
    # Save map
    output_file = 'cambridge_crime_map.html'
    crime_map.save(output_file)
    print(f"\nMap saved as {output_file}")
    print("Open this file in a web browser to view the interactive map.")
    
    # Print summary statistics
    df = load_and_process_data('../../crimedata.csv')
    print(f"\nSummary:")
    print(f"Total incidents: {len(df)}")
    print(f"Unique locations: {len(df.groupby(['lat', 'lon']))}")
    print(f"Crime types: {len(df['Crime'].unique())}")
    print(f"Date range: {df['Date of Report'].min()} to {df['Date of Report'].max()}")


if __name__ == "__main__":
    main()