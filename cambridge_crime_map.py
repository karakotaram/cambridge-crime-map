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
    
    # Add detailed crime list for each location
    detailed_crimes = df.groupby(['lat', 'lon'], include_groups=False).apply(
        lambda group: group[['Crime Date Time', 'Crime', 'File Number']].to_dict('records')
    ).reset_index(name='detailed_crimes')
    
    result = result.merge(detailed_crimes, on=['lat', 'lon'])
    
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
    
    # Create base map with higher zoom for better initial view
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles='OpenStreetMap'
    )
    
    # Get color for violent crimes
    color = get_violence_color_palette()
    
    # Create feature groups for each time period
    def add_markers_to_group(fg, aggregated, color, crime_data_store):
        """Helper function to add markers to a feature group."""
        # Calculate marker size range
        if len(aggregated) > 1:
            max_total = aggregated['total_incidents'].max()
            min_total = aggregated['total_incidents'].min()
        else:
            max_total = min_total = aggregated['total_incidents'].iloc[0] if len(aggregated) > 0 else 1
        
        for idx, row in aggregated.iterrows():
            # Scale marker size based on total incidents at location
            if max_total > min_total:
                size = 8 + (row['total_incidents'] - min_total) / (max_total - min_total) * 20
            else:
                size = 12
            
            # Format dates for popup
            earliest = row['earliest_date'].strftime('%Y-%m-%d') if pd.notna(row['earliest_date']) else 'Unknown'
            latest = row['latest_date'].strftime('%Y-%m-%d') if pd.notna(row['latest_date']) else 'Unknown'
            
            # Create unique ID for this marker
            marker_id = f"marker_{idx}_{hash(f'{row.lat}_{row.lon}')}"
            
            # Store crime details in the global store
            crime_data_store[marker_id] = row['detailed_crimes']
            
            # Create popup text with button to show detailed crimes
            popup_text = f"""
            <div style="min-width: 250px;">
                <b>Location:</b> {row['Location'] if pd.notna(row['Location']) else 'Not specified'}<br>
                <b>Neighborhood:</b> {row['Neighborhood'] if pd.notna(row['Neighborhood']) else 'Not specified'}<br>
                <b>Violent Crime Types:</b> {row['top_crimes']}<br>
                <b>Total Incidents:</b> {row['total_incidents']}<br>
                <b>Date Range:</b> {earliest} to {latest}<br><br>
                <button onclick="showCrimeDetails('{marker_id}')" 
                        style="background: #007bff; color: white; border: none; 
                               padding: 8px 12px; border-radius: 4px; cursor: pointer;">
                    View All {row['total_incidents']} Incidents
                </button>
            </div>
            """
            
            # Add circle marker
            marker = folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=size,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            )
            marker.add_to(fg)
    
    # Create feature groups - but implement radio button behavior by hiding/showing layers
    all_time_fg = folium.FeatureGroup(name='All Time')
    five_year_fg = folium.FeatureGroup(name='Past 5 Years') 
    one_year_fg = folium.FeatureGroup(name='Past Year')
    
    # Store for all crime details data that will be embedded in JavaScript
    crime_data_store = {}
    
    # Add markers to each group
    if time_periods['all']['data'] is not None and len(time_periods['all']['data']) > 0:
        add_markers_to_group(all_time_fg, time_periods['all']['data'], color, crime_data_store)
    
    if time_periods['5_years']['data'] is not None and len(time_periods['5_years']['data']) > 0:
        add_markers_to_group(five_year_fg, time_periods['5_years']['data'], color, crime_data_store)
        
    if time_periods['1_year']['data'] is not None and len(time_periods['1_year']['data']) > 0:
        add_markers_to_group(one_year_fg, time_periods['1_year']['data'], color, crime_data_store)
    
    # Add all feature groups to map 
    all_time_fg.add_to(m)
    five_year_fg.add_to(m) 
    one_year_fg.add_to(m)
    
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
        <h4 style="margin: 0; color: #d63031;">Cambridge Crime Map, 2009-Present</h4>
        <button id="toggleLegend" onclick="toggleLegend()" style="
            background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;
            width: 30px; height: 30px; cursor: pointer; font-size: 16px;
            display: flex; align-items: center; justify-content: center;
            ">−</button>
    </div>
    <div id="legendContent">
    
    <div style="margin: 15px 0; font-size: 13px; color: #333; line-height: 1.4;">
        Violent crimes reported in the City of Cambridge since 2009. Bubbles do not represent the actual location of the crime, but a near approximation within 100 block ranges.<br><br>
        Data can be filtered to only include incidents from the last five years or the last year. Link to data set below.
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
    
    # Add navigation header
    nav_html = '''
    <div id="navHeader" style="position: fixed; top: 0; left: 0; right: 0; 
                               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               color: white; padding: 15px; z-index: 10000;
                               box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                               font-family: 'Segoe UI', Arial, sans-serif;">
        <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin: 0; font-size: 1.8rem;">🗺️ Cambridge Crime Map</h1>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">Interactive map of violent crimes, 2009-Present</p>
            </div>
            <a href="/cambridge-crime-map/" style="background: rgba(255,255,255,0.2); color: white; 
                                          padding: 8px 16px; border-radius: 20px; text-decoration: none; 
                                          font-weight: bold; transition: all 0.3s ease;"
               onmouseover="this.style.background='rgba(255,255,255,0.3)'"
               onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                ← All Analyses
            </a>
        </div>
    </div>
    
    <style>
        body { margin-top: 80px !important; }
        
        @media (max-width: 768px) {
            #navHeader > div { flex-direction: column; text-align: center; gap: 10px; }
            #navHeader h1 { font-size: 1.5rem; }
            body { margin-top: 100px !important; }
        }
    </style>
    '''
    
    m.get_root().html.add_child(folium.Element(nav_html))
    
    # Add JavaScript to make layer control behave like radio buttons
    radio_behavior_js = '''
    <script>
    // Wait for the map and layer control to load
    window.addEventListener('load', function() {
        setTimeout(function() {
            makeLayerControlRadio();
        }, 1000);
    });
    
    function makeLayerControlRadio() {
        // Find all layer control checkboxes
        const layerControl = document.querySelector('.leaflet-control-layers');
        if (!layerControl) {
            setTimeout(makeLayerControlRadio, 500);
            return;
        }
        
        const checkboxes = layerControl.querySelectorAll('input[type="checkbox"]');
        const timePeriodsCheckboxes = [];
        
        // Identify time period checkboxes (they should be the overlay checkboxes)
        checkboxes.forEach(checkbox => {
            const label = checkbox.nextElementSibling;
            if (label && (label.textContent.includes('All Time') || 
                         label.textContent.includes('Past 5 Years') || 
                         label.textContent.includes('Past Year'))) {
                timePeriodsCheckboxes.push(checkbox);
            }
        });
        
        // Add event listeners to make them behave like radio buttons
        timePeriodsCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    // Uncheck all other time period checkboxes
                    timePeriodsCheckboxes.forEach(otherCheckbox => {
                        if (otherCheckbox !== this && otherCheckbox.checked) {
                            otherCheckbox.click(); // This will uncheck and hide the layer
                        }
                    });
                }
            });
        });
        
        // Ensure "All Time" is checked by default and others are unchecked
        timePeriodsCheckboxes.forEach(checkbox => {
            const label = checkbox.nextElementSibling;
            if (label && label.textContent.includes('All Time')) {
                if (!checkbox.checked) {
                    checkbox.click();
                }
            } else {
                if (checkbox.checked) {
                    checkbox.click();
                }
            }
        });
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(radio_behavior_js))
    
    # Add crime details functionality
    import json
    crime_details_js = f'''
    <script>
    // Store all crime details data
    window.crimeDetails = {json.dumps(crime_data_store, default=str)};
    
    function showCrimeDetails(markerId) {{
        const crimes = window.crimeDetails[markerId];
        if (!crimes || crimes.length === 0) {{
            alert('No detailed crime data available for this location.');
            return;
        }}
        
        // Create modal content
        let modalContent = `
            <div id="crimeModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                                      background: rgba(0,0,0,0.7); z-index: 10001; display: flex; 
                                      align-items: center; justify-content: center;">
                <div style="background: white; max-width: 800px; max-height: 80vh; width: 90%; 
                           border-radius: 8px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                    <div style="background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; 
                               display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: #333;">Crime Incidents at This Location</h3>
                        <button onclick="closeCrimeModal()" style="background: none; border: none; 
                                       font-size: 24px; cursor: pointer; color: #666;">&times;</button>
                    </div>
                    <div style="padding: 20px; max-height: 60vh; overflow-y: auto;">
                        <div style="margin-bottom: 15px; color: #666;">
                            <strong>${{crimes.length}}</strong> total incidents found
                        </div>
                        <div style="display: grid; gap: 10px;">
        `;
        
        // Sort crimes by date (most recent first)
        const sortedCrimes = crimes.sort((a, b) => new Date(b['Crime Date Time']) - new Date(a['Crime Date Time']));
        
        sortedCrimes.forEach((crime, index) => {{
            const date = new Date(crime['Crime Date Time']).toLocaleDateString();
            modalContent += `
                <div style="border: 1px solid #e9ecef; border-radius: 6px; padding: 12px; 
                           background: ${{index % 2 === 0 ? '#f8f9fa' : 'white'}};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <strong style="color: #d63031;">${{crime.Crime}}</strong>
                        <span style="background: #6c757d; color: white; padding: 2px 8px; 
                                   border-radius: 12px; font-size: 0.8em;">${{date}}</span>
                    </div>
                    <div style="font-size: 0.9em; color: #666;">
                        <strong>File Number:</strong> ${{crime['File Number'] || 'Not available'}}
                    </div>
                </div>
            `;
        }});
        
        modalContent += `
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalContent);
        
        // Close modal when clicking background
        document.getElementById('crimeModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeCrimeModal();
            }}
        }});
    }}
    
    function closeCrimeModal() {{
        const modal = document.getElementById('crimeModal');
        if (modal) {{
            modal.remove();
        }}
    }}
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape') {{
            closeCrimeModal();
        }}
    }});
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(crime_details_js))
    
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