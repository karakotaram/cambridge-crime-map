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


def aggregate_by_location_and_violence(df):
    """Aggregate incidents by location and violence category."""
    # Add violence category
    df['Violence_Category'] = df['Crime'].apply(categorize_crime_as_violent)
    
    # Group by coordinates and violence category, count incidents
    grouped = df.groupby(['lat', 'lon', 'Violence_Category']).size().reset_index(name='frequency')
    
    # Also get total incidents per location for sizing
    location_totals = df.groupby(['lat', 'lon']).size().reset_index(name='total_incidents')
    
    # Get detailed crime breakdown for tooltips
    crime_details = df.groupby(['lat', 'lon', 'Violence_Category']).agg({
        'Crime': lambda x: ', '.join(x.value_counts().head(3).index.tolist())
    }).reset_index()
    crime_details.columns = ['lat', 'lon', 'Violence_Category', 'top_crimes']
    
    # Merge all data
    result = grouped.merge(location_totals, on=['lat', 'lon'])
    result = result.merge(crime_details, on=['lat', 'lon', 'Violence_Category'])
    
    # Add additional info for tooltips
    location_info = df.groupby(['lat', 'lon']).agg({
        'Neighborhood': 'first',
        'Location': 'first',
        'Reporting Area': 'first'
    }).reset_index()
    
    result = result.merge(location_info, on=['lat', 'lon'])
    
    return result


def categorize_crime_as_violent(crime_type):
    """Categorize crime type as violent or non-violent."""
    violent_crimes = {
        'Homicide', 'Aggravated Assault', 'Simple Assault', 'Street Robbery', 
        'Commercial Robbery', 'Kidnapping', 'Arson', 'Weapon Violations',
        'Stalking', 'Extortion/Blackmail', 'Threats', 'Domestic Dispute'
    }
    
    return 'Violent' if crime_type in violent_crimes else 'Non-Violent'


def get_violence_color_palette():
    """Define color palette for violent vs non-violent crimes."""
    return {
        'Violent': '#FF4444',      # Red for violent crimes
        'Non-Violent': '#4444FF'   # Blue for non-violent crimes
    }


def create_cambridge_crime_map(csv_path='crimedata.csv'):
    """Create interactive Leaflet map of Cambridge crime incidents."""
    
    # Load and process data
    print("Loading crime data...")
    df = load_and_process_data(csv_path)
    print(f"Loaded {len(df)} incidents")
    
    # Aggregate data by violence category
    print("Aggregating incidents by location and violence category...")
    aggregated = aggregate_by_location_and_violence(df)
    
    # Get color palette for violence categories
    color_map = get_violence_color_palette()
    
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
        <b>Violence Category:</b> {row['Violence_Category']}<br>
        <b>Top Crime Types:</b> {row['top_crimes']}<br>
        <b>{row['Violence_Category']} incidents:</b> {row['frequency']}<br>
        <b>Total incidents at location:</b> {row['total_incidents']}
        """
        
        # Add circle marker
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=size,
            popup=folium.Popup(popup_text, max_width=300),
            color=color_map[row['Violence_Category']],
            fillColor=color_map[row['Violence_Category']],
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # Create legend
    print("Creating legend...")
    
    # Calculate statistics for legend
    violent_locations = len(aggregated[aggregated['Violence_Category'] == 'Violent'])
    nonviolent_locations = len(aggregated[aggregated['Violence_Category'] == 'Non-Violent'])
    
    # Get total counts by category
    df_with_categories = df.copy()
    df_with_categories['Violence_Category'] = df_with_categories['Crime'].apply(categorize_crime_as_violent)
    violent_total = len(df_with_categories[df_with_categories['Violence_Category'] == 'Violent'])
    nonviolent_total = len(df_with_categories[df_with_categories['Violence_Category'] == 'Non-Violent'])
    
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 280px; height: 300px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px;
                ">
    <h4 style="margin: 0 0 15px 0;">Crime Categories</h4>
    
    <div style="margin: 10px 0;">
        <span style="display: inline-block; width: 15px; height: 15px; 
                     background-color: #FF4444; border: 1px solid black;"></span>
        <span style="margin-left: 8px; font-weight: bold;">Violent Crimes</span><br>
        <span style="margin-left: 25px; font-size: 12px; color: #666;">
            {violent_total:,} incidents at {violent_locations} locations
        </span>
    </div>
    
    <div style="margin: 10px 0;">
        <span style="display: inline-block; width: 15px; height: 15px; 
                     background-color: #4444FF; border: 1px solid black;"></span>
        <span style="margin-left: 8px; font-weight: bold;">Non-Violent Crimes</span><br>
        <span style="margin-left: 25px; font-size: 12px; color: #666;">
            {nonviolent_total:,} incidents at {nonviolent_locations} locations
        </span>
    </div>
    
    <hr style="margin: 15px 0;">
    
    <div style="font-size: 12px; color: #666;">
        <b>Violent crimes include:</b><br>
        Homicide, Assault, Robbery, Kidnapping, Arson, Weapon Violations, Threats, etc.
    </div>
    
    <hr style="margin: 15px 0;">
    
    <div style="font-size: 12px; color: #666;">
        <b>Marker Size:</b> Total incidents at location<br>
        <small>Larger circles = more incidents</small>
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
    df['Violence_Category'] = df['Crime'].apply(categorize_crime_as_violent)
    
    violent_count = len(df[df['Violence_Category'] == 'Violent'])
    nonviolent_count = len(df[df['Violence_Category'] == 'Non-Violent'])
    
    print(f"\nSummary:")
    print(f"Total incidents: {len(df)}")
    print(f"Violent crimes: {violent_count:,} ({violent_count/len(df)*100:.1f}%)")
    print(f"Non-violent crimes: {nonviolent_count:,} ({nonviolent_count/len(df)*100:.1f}%)")
    print(f"Unique locations: {len(df.groupby(['lat', 'lon']))}")
    print(f"Original crime types: {len(df['Crime'].unique())}")
    print(f"Date range: {df['Date of Report'].min()} to {df['Date of Report'].max()}")


if __name__ == "__main__":
    main()