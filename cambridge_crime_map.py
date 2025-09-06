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
from datetime import datetime, timedelta


def load_and_process_data(csv_path, time_filter='all'):
    """Load and process crime data from CSV file."""
    df = pd.read_csv(csv_path)
    
    # Clean data - remove rows without coordinates
    df = df.dropna(subset=['Reporting Area Lat', 'Reporting Area Lon'])
    
    # Convert coordinates to float
    df['lat'] = pd.to_numeric(df['Reporting Area Lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['Reporting Area Lon'], errors='coerce')
    
    # Remove invalid coordinates
    df = df.dropna(subset=['lat', 'lon'])
    
    # Parse dates
    df['Crime_Date'] = pd.to_datetime(df['Crime Date Time'], errors='coerce')
    df = df.dropna(subset=['Crime_Date'])
    
    # Apply time filter
    if time_filter == '1_year':
        cutoff_date = datetime.now() - timedelta(days=365)
        df = df[df['Crime_Date'] >= cutoff_date]
    elif time_filter == '5_years':
        cutoff_date = datetime.now() - timedelta(days=5*365)
        df = df[df['Crime_Date'] >= cutoff_date]
    
    # Filter to only violent crimes
    df['Violence_Category'] = df['Crime'].apply(categorize_crime_as_violent)
    df = df[df['Violence_Category'] == 'Violent']
    
    return df


def aggregate_by_location(df):
    """Aggregate violent crime incidents by location."""
    # Group by coordinates, count incidents
    grouped = df.groupby(['lat', 'lon']).size().reset_index(name='total_incidents')
    
    # Get detailed crime breakdown for tooltips
    crime_details = df.groupby(['lat', 'lon']).agg({
        'Crime': lambda x: ', '.join(x.value_counts().head(3).index.tolist()),
        'Crime_Date': ['min', 'max']
    }).reset_index()
    
    # Flatten column names
    crime_details.columns = ['lat', 'lon', 'top_crimes', 'earliest_date', 'latest_date']
    
    # Merge data
    result = grouped.merge(crime_details, on=['lat', 'lon'])
    
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
    """Define color palette for violent crimes."""
    return '#FF4444'  # Red for violent crimes


def create_cambridge_crime_map(csv_path='crimedata.csv'):
    """Create interactive Leaflet map of Cambridge violent crime incidents with time controls."""
    
    print("Creating map with time period controls...")
    
    # Load data for all time periods
    time_periods = {
        'all': {'label': 'All Time', 'data': None},
        '5_years': {'label': 'Past 5 Years', 'data': None}, 
        '1_year': {'label': 'Past Year', 'data': None}
    }
    
    # Load and process data for each time period
    for period in time_periods:
        print(f"Loading {time_periods[period]['label']} data...")
        df = load_and_process_data(csv_path, time_filter=period)
        if len(df) > 0:
            time_periods[period]['data'] = aggregate_by_location(df)
            print(f"  Found {len(df)} violent crime incidents")
        else:
            time_periods[period]['data'] = pd.DataFrame()
            print(f"  No data for {time_periods[period]['label']}")
    
    # Use all-time data to calculate map center
    all_time_df = load_and_process_data(csv_path, time_filter='all')
    center_lat = all_time_df['lat'].mean() if len(all_time_df) > 0 else 42.373
    center_lon = all_time_df['lon'].mean() if len(all_time_df) > 0 else -71.109
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Get color for violent crimes
    color = get_violence_color_palette()
    
    # Create feature groups for each time period
    def add_markers_to_group(fg, aggregated, color):
        """Helper function to add markers to a feature group."""
        # Calculate marker size range
        if len(aggregated) > 1:
            max_total = aggregated['total_incidents'].max()
            min_total = aggregated['total_incidents'].min()
        else:
            max_total = min_total = aggregated['total_incidents'].iloc[0] if len(aggregated) > 0 else 1
        
        for _, row in aggregated.iterrows():
            # Scale marker size based on total incidents at location
            if max_total > min_total:
                size = 8 + (row['total_incidents'] - min_total) / (max_total - min_total) * 20
            else:
                size = 12
            
            # Format dates for popup
            earliest = row['earliest_date'].strftime('%Y-%m-%d') if pd.notna(row['earliest_date']) else 'Unknown'
            latest = row['latest_date'].strftime('%Y-%m-%d') if pd.notna(row['latest_date']) else 'Unknown'
            
            # Create popup text
            popup_text = f"""
            <b>Location:</b> {row['Location'] if pd.notna(row['Location']) else 'Not specified'}<br>
            <b>Neighborhood:</b> {row['Neighborhood'] if pd.notna(row['Neighborhood']) else 'Not specified'}<br>
            <b>Violent Crime Types:</b> {row['top_crimes']}<br>
            <b>Total Incidents:</b> {row['total_incidents']}<br>
            <b>Date Range:</b> {earliest} to {latest}
            """
            
            # Add circle marker
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=size,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(fg)
    
    # Create feature groups and add markers - only All Time visible by default
    all_time_fg = folium.FeatureGroup(name='All Time', show=True)
    five_year_fg = folium.FeatureGroup(name='Past 5 Years', show=False)
    one_year_fg = folium.FeatureGroup(name='Past Year', show=False)
    
    if time_periods['all']['data'] is not None and len(time_periods['all']['data']) > 0:
        add_markers_to_group(all_time_fg, time_periods['all']['data'], color)
    
    if time_periods['5_years']['data'] is not None and len(time_periods['5_years']['data']) > 0:
        add_markers_to_group(five_year_fg, time_periods['5_years']['data'], color)
        
    if time_periods['1_year']['data'] is not None and len(time_periods['1_year']['data']) > 0:
        add_markers_to_group(one_year_fg, time_periods['1_year']['data'], color)
    
    # Add all feature groups to map
    all_time_fg.add_to(m)
    five_year_fg.add_to(m)
    one_year_fg.add_to(m)
    
    # Add additional base layers
    folium.TileLayer(
        tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        name='Stamen Terrain'
    ).add_to(m)
    folium.TileLayer('cartodb positron').add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topleft', collapsed=False).add_to(m)
    
    # Create custom legend with minimize/expand functionality
    legend_html = f'''
    <div id="legend" style="position: fixed; 
                top: 10px; right: 10px; width: 320px; height: 380px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 15px; overflow-y: auto;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1); transition: all 0.3s ease;
                ">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h4 style="margin: 0; color: #d63031;">Violent Crimes Only</h4>
        <button id="toggleLegend" onclick="toggleLegend()" style="
            background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;
            width: 30px; height: 30px; cursor: pointer; font-size: 16px;
            display: flex; align-items: center; justify-content: center;
            ">−</button>
    </div>
    <div id="legendContent">'
    
    <div style="margin: 10px 0;">
        <span style="display: inline-block; width: 15px; height: 15px; 
                     background-color: #FF4444; border: 1px solid black;"></span>
        <span style="margin-left: 8px; font-weight: bold;">Violent Crimes</span>
    </div>
    
    <div style="margin: 15px 0; font-size: 12px; color: #666;">
        <b>Includes:</b> Homicide, Assault, Robbery, Kidnapping, Arson, Weapon Violations, Threats, Stalking, Extortion
    </div>
    
    <hr style="margin: 15px 0;">
    
    <div style="font-size: 12px; color: #666;">
        <b>🔍 Time Period Controls:</b><br>
        Use the <b>layers icon</b> (📂) in the top-left corner to:<br>
        ✓ Check/uncheck time periods to show/hide<br>
        • All Time: {len(time_periods['all']['data']) if time_periods['all']['data'] is not None else 0} locations<br>
        • Past 5 Years: {len(time_periods['5_years']['data']) if time_periods['5_years']['data'] is not None else 0} locations<br>
        • Past Year: {len(time_periods['1_year']['data']) if time_periods['1_year']['data'] is not None else 0} locations
    </div>
    
    <hr style="margin: 15px 0;">
    
    <div style="font-size: 12px; color: #666;">
        <b>Marker Size:</b> Number of incidents at location
    </div>
    
    <hr style="margin: 15px 0;">
    
    <div style="font-size: 11px; color: #888; text-align: center;">
        <b>Data Source:</b><br>
        <a href="https://data.cambridgema.gov/Public-Safety/Crime-Reports/xuad-73uj/about_data" 
           target="_blank" style="color: #0066cc; text-decoration: none;">
           Cambridge Open Data Portal
        </a><br>
        <small>Crime Reports Dataset</small>
    </div>
    </div> <!-- end legendContent -->
    </div> <!-- end legend -->
    
    <script>
    function toggleLegend() {{
        const legend = document.getElementById('legend');
        const content = document.getElementById('legendContent');
        const button = document.getElementById('toggleLegend');
        
        if (content.style.display === 'none') {{
            // Expand
            content.style.display = 'block';
            legend.style.height = '380px';
            legend.style.width = '320px';
            button.innerHTML = '−';
            button.title = 'Minimize legend';
        }} else {{
            // Minimize
            content.style.display = 'none';
            legend.style.height = '50px';
            legend.style.width = '200px';
            button.innerHTML = '+';
            button.title = 'Expand legend';
        }}
    }}
    
    // Make legend responsive on mobile
    window.addEventListener('resize', function() {{
        const legend = document.getElementById('legend');
        const content = document.getElementById('legendContent');
        const button = document.getElementById('toggleLegend');
        
        if (window.innerWidth <= 768) {{
            // Mobile: start minimized
            if (content.style.display !== 'none') {{
                content.style.display = 'none';
                legend.style.height = '50px';
                legend.style.width = '200px';
                button.innerHTML = '+';
                button.title = 'Expand legend';
            }}
            legend.style.left = '10px';
            legend.style.right = 'auto';
        }} else {{
            // Desktop: restore position
            legend.style.left = 'auto';
            legend.style.right = '10px';
        }}
    }});
    
    // Auto-minimize on mobile on page load
    window.addEventListener('load', function() {{
        if (window.innerWidth <= 768) {{
            const legend = document.getElementById('legend');
            const content = document.getElementById('legendContent');
            const button = document.getElementById('toggleLegend');
            
            content.style.display = 'none';
            legend.style.height = '50px';
            legend.style.width = '200px';
            legend.style.left = '10px';
            legend.style.right = 'auto';
            button.innerHTML = '+';
            button.title = 'Expand legend';
        }}
    }});
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
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
    print(f"\nSummary:")
    
    # Load data for different time periods
    all_data = load_and_process_data('../../crimedata.csv', 'all')
    five_year_data = load_and_process_data('../../crimedata.csv', '5_years')
    one_year_data = load_and_process_data('../../crimedata.csv', '1_year')
    
    print(f"Violent crimes only:")
    print(f"All time: {len(all_data):,} incidents at {len(all_data.groupby(['lat', 'lon'])) if len(all_data) > 0 else 0} locations")
    print(f"Past 5 years: {len(five_year_data):,} incidents at {len(five_year_data.groupby(['lat', 'lon'])) if len(five_year_data) > 0 else 0} locations")
    print(f"Past year: {len(one_year_data):,} incidents at {len(one_year_data.groupby(['lat', 'lon'])) if len(one_year_data) > 0 else 0} locations")
    
    if len(all_data) > 0:
        print(f"Violent crime types: {len(all_data['Crime'].unique())}")
        print(f"Date range: {all_data['Crime_Date'].min().strftime('%Y-%m-%d')} to {all_data['Crime_Date'].max().strftime('%Y-%m-%d')}")
        
        # Show breakdown of violent crime types
        print(f"\nMost common violent crimes:")
        crime_counts = all_data['Crime'].value_counts().head(5)
        for crime, count in crime_counts.items():
            print(f"  {crime}: {count:,}")
    else:
        print("No violent crime data found")


if __name__ == "__main__":
    main()