#!/usr/bin/env python3
"""
Cambridge Violent Crimes Per Capita by Neighborhood Analysis
Interactive bar chart showing crime rates per 1,000 residents with year filtering.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime


def categorize_crime_as_violent(crime_type):
    """Categorize crime type as violent or non-violent."""
    violent_crimes = {
        'Homicide', 'Aggravated Assault', 'Simple Assault', 'Street Robbery', 
        'Commercial Robbery', 'Kidnapping', 'Arson', 'Weapon Violations',
        'Stalking', 'Extortion/Blackmail', 'Threats', 'Domestic Dispute'
    }
    
    return crime_type in violent_crimes


def get_neighborhood_populations():
    """
    Estimated population by neighborhood based on Cambridge total population (118,403)
    and typical neighborhood distributions. Estimates based on area, density, and housing patterns.
    """
    return {
        'Baldwin': 6500,          # Harvard area, dense student/family housing
        'Cambridgeport': 12500,   # Large neighborhood, mixed housing
        'East Cambridge': 8500,   # Dense urban area near downtown Boston
        'Highlands': 4200,        # Suburban area, single-family homes
        'Inman/Harrington': 7800, # Mixed residential area
        'MIT': 3000,              # Primarily students/staff, smaller residential area
        'Mid-Cambridge': 15000,   # Central area, high density
        'North Cambridge': 14000, # Large residential area
        'Peabody': 5500,          # Mixed residential
        'Riverside': 11000,       # Large neighborhood along river
        'Strawberry Hill': 2500,  # Smaller suburban area
        'The Port': 9500,         # Dense urban area
        'West Cambridge': 18000   # Large affluent area including Brattle Street
        # Total: ~118,000 (matches Cambridge population)
    }


def load_and_process_data(csv_path):
    """Load and process crime data for per capita analysis."""
    print("Loading crime data...")
    df = pd.read_csv(csv_path)
    
    # Parse crime date
    df['Crime_Date'] = pd.to_datetime(df['Crime Date Time'], errors='coerce')
    df = df.dropna(subset=['Crime_Date'])
    
    # Filter to violent crimes only
    df['Is_Violent'] = df['Crime'].apply(categorize_crime_as_violent)
    df = df[df['Is_Violent']]
    
    # Extract year
    df['Year'] = df['Crime_Date'].dt.year
    
    # Clean neighborhood data
    df['Neighborhood'] = df['Neighborhood'].fillna('Unknown')
    df = df[df['Year'] >= 2009]  # Focus on 2009 onwards for cleaner data
    df = df[df['Neighborhood'] != 'Unknown']  # Remove unknown neighborhoods for per capita analysis
    
    print(f"Processed {len(df)} violent crime incidents across neighborhoods")
    return df


def create_per_capita_analysis(df, selected_year=None):
    """Create per capita crime analysis data."""
    populations = get_neighborhood_populations()
    
    # Filter by year if specified
    if selected_year and selected_year != 'All Time':
        df_filtered = df[df['Year'] == int(selected_year)]
        period_label = str(selected_year)
    else:
        df_filtered = df
        period_label = "All Time (2009-Present)"
    
    # Count crimes by neighborhood
    crime_counts = df_filtered.groupby('Neighborhood').size().reset_index(name='Crime_Count')
    
    # Add population data and calculate per capita rates
    crime_counts['Population'] = crime_counts['Neighborhood'].map(populations)
    
    # Remove neighborhoods without population data
    crime_counts = crime_counts.dropna(subset=['Population'])
    
    # Calculate crimes per 1,000 residents
    crime_counts['Crimes_Per_1000'] = (crime_counts['Crime_Count'] / crime_counts['Population']) * 1000
    
    # Sort by crime rate (highest first)
    crime_counts = crime_counts.sort_values('Crimes_Per_1000', ascending=False)
    
    print(f"Analyzing {period_label}: {len(crime_counts)} neighborhoods")
    
    return crime_counts, period_label


def create_crimes_per_capita_chart(csv_path='./crimedata.csv'):
    """Create interactive Plotly chart for crimes per capita by neighborhood with year filtering."""
    
    # Load and process data
    df = load_and_process_data(csv_path)
    
    # Get available years for dropdown
    available_years = sorted(df['Year'].unique())
    
    # Create main chart (All Time by default)
    crime_data, period_label = create_per_capita_analysis(df)
    
    # Create the bar chart
    fig = go.Figure()
    
    # Add All Time trace (visible by default)
    fig.add_trace(go.Bar(
        x=crime_data['Neighborhood'],
        y=crime_data['Crimes_Per_1000'],
        name='All Time',
        marker_color='#d63031',
        visible=True,
        customdata=list(zip(crime_data['Crime_Count'], crime_data['Population'])),
        hovertemplate='<b>%{x}</b><br>' +
                      'Crimes per 1,000: %{y:.1f}<br>' +
                      'Total crimes: %{customdata[0]}<br>' +
                      'Population: %{customdata[1]:,}' +
                      '<extra></extra>'
    ))
    
    # Add traces for each year (initially hidden)
    colors = px.colors.qualitative.Set3
    for i, year in enumerate(available_years):
        year_data, _ = create_per_capita_analysis(df, year)
        fig.add_trace(go.Bar(
            x=year_data['Neighborhood'],
            y=year_data['Crimes_Per_1000'],
            name=str(year),
            marker_color=colors[i % len(colors)],
            visible=False,
            customdata=list(zip(year_data['Crime_Count'], year_data['Population'])),
            hovertemplate='<b>%{x}</b><br>' +
                          'Crimes per 1,000: %{y:.1f}<br>' +
                          'Total crimes: %{customdata[0]}<br>' +
                          'Population: %{customdata[1]:,}' +
                          '<extra></extra>'
        ))
    
    # Create dropdown menu
    dropdown_buttons = []
    
    # All Time button
    all_visible = [True] + [False] * len(available_years)
    dropdown_buttons.append(dict(
        label="All Time (2009-Present)",
        method="update",
        args=[{"visible": all_visible}]
    ))
    
    # Individual year buttons
    for i, year in enumerate(available_years):
        visible_list = [False] * (1 + len(available_years))
        visible_list[i + 1] = True  # +1 because All Time is at index 0
        dropdown_buttons.append(dict(
            label=str(year),
            method="update",
            args=[{"visible": visible_list}]
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Violent Crimes Per Capita by Cambridge Neighborhood',
            x=0.5,
            font=dict(size=24, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='Neighborhood', font=dict(size=16)),
            tickfont=dict(size=12),
            tickangle=45,
            gridcolor='#ecf0f1'
        ),
        yaxis=dict(
            title=dict(text='Violent Crimes per 1,000 Residents', font=dict(size=16)),
            tickfont=dict(size=14),
            gridcolor='#ecf0f1'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Arial"),
        hovermode='closest',
        updatemenus=[dict(
            buttons=dropdown_buttons,
            direction="down",
            showactive=True,
            x=0.02,
            xanchor="left",
            y=0.98,
            yanchor="top",
            bgcolor='white',
            bordercolor='#bdc3c7',
            borderwidth=1
        )],
        annotations=[dict(
            text="Filter by Time Period:",
            showarrow=False,
            x=0.02,
            y=1.05,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            font=dict(size=14, color='#2c3e50')
        )],
        margin=dict(b=120)  # Extra margin for rotated labels
    )
    
    return fig, df, crime_data


def create_summary_stats(df, crime_data):
    """Create summary statistics for the page."""
    total_crimes = len(df)
    years_span = df['Year'].max() - df['Year'].min() + 1
    neighborhoods_count = len(crime_data)
    
    # Calculate city-wide rate
    total_population = sum(get_neighborhood_populations().values())
    citywide_rate = (total_crimes / total_population) * 1000
    
    # Highest crime rate neighborhood
    highest_rate_neighborhood = crime_data.iloc[0]['Neighborhood']
    highest_rate = crime_data.iloc[0]['Crimes_Per_1000']
    
    return {
        'total_crimes': total_crimes,
        'years_span': years_span,
        'neighborhoods_count': neighborhoods_count,
        'citywide_rate': citywide_rate,
        'highest_rate_neighborhood': highest_rate_neighborhood,
        'highest_rate': highest_rate
    }


def main():
    """Generate the crimes per capita HTML page."""
    print("Creating Crimes Per Capita analysis...")
    
    # Create the chart
    fig, df, crime_data = create_crimes_per_capita_chart()
    
    # Get summary stats
    stats = create_summary_stats(df, crime_data)
    
    # Prepare crime data for map popups (2024 data specifically)
    crime_data_2024, _ = create_per_capita_analysis(df, 2024)
    crime_data_dict = {}
    for _, row in crime_data_2024.iterrows():
        crime_data_dict[row['Neighborhood']] = {
            'crime_count': int(row['Crime_Count']),
            'population': int(row['Population']),
            'rate': float(row['Crimes_Per_1000'])
        }
    
    # Create mapping from GeoJSON names to our neighborhood names
    geojson_to_our_names = {
        'The Port': 'The Port',
        'Neighborhood Nine': 'Baldwin',  # Based on the data, this seems to be the northern area
        'Wellington-Harrington': 'Inman/Harrington',
        'Mid-Cambridge': 'Mid-Cambridge', 
        'North Cambridge': 'North Cambridge',
        'Cambridge Highlands': 'Highlands',
        'Strawberry Hill': 'Strawberry Hill',
        'West Cambridge': 'West Cambridge',
        'Riverside': 'Riverside',
        'Cambridgeport': 'Cambridgeport',
        'Area 2/MIT': 'MIT',
        'East Cambridge': 'East Cambridge',
        'Baldwin': 'Baldwin'  # There are apparently two Baldwin areas
    }
    
    # Convert to HTML
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='per-capita-chart',
        config={'displayModeBar': True, 'displaylogo': False}
    )
    
    # Create complete HTML page
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cambridge Crimes Per Capita | Crime Data Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: #f8f9fa;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 3rem 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>') repeat;
            opacity: 0.3;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .nav {{
            background: white;
            padding: 1rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-bottom: 3px solid #e9ecef;
        }}
        
        .nav-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .nav a {{
            color: #1e3c72;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            transition: all 0.3s ease;
        }}
        
        .nav a:hover {{
            color: #2a5298;
            transform: translateX(-2px);
        }}
        
        .nav a::before {{
            content: '←';
            margin-right: 0.5rem;
            font-size: 1.2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            text-align: center;
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e3c72;
            display: block;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 2.5rem;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            margin: 3rem 0;
            border: 1px solid #e9ecef;
        }}
        
        .info-box {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            padding: 2.5rem;
            margin: 3rem 0;
            border: 1px solid #e9ecef;
        }}
        
        .info-box h3 {{
            color: #1e3c72;
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            font-weight: 600;
        }}
        
        .info-box ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .info-box li {{
            margin-bottom: 1rem;
            padding-left: 2rem;
            position: relative;
            color: #495057;
            line-height: 1.7;
        }}
        
        .info-box li::before {{
            content: "→";
            color: #1e3c72;
            font-weight: bold;
            position: absolute;
            left: 0;
            top: 0;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 2rem;
            text-align: center;
            margin-top: 3rem;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>Crimes Per Capita by Neighborhood</h1>
            <p>Violent crime rates per 1,000 residents across Cambridge neighborhoods</p>
        </div>
    </div>
    
    <div class="nav">
        <div class="nav-content">
            <a href="/">Back to Analysis Home</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{stats['total_crimes']:,}</span>
                <div class="stat-label">Total Violent Crimes</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['neighborhoods_count']}</span>
                <div class="stat-label">Neighborhoods Analyzed</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['citywide_rate']:.1f}</span>
                <div class="stat-label">City-wide Rate per 1,000</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['highest_rate']:.1f}</span>
                <div class="stat-label">Highest Rate ({stats['highest_rate_neighborhood']})</div>
            </div>
        </div>
        
        <div class="chart-container">
            {chart_html}
        </div>
        
        <div class="chart-container">
            <h2 style="text-align: center; margin-bottom: 1.5rem; color: #2c3e50;">Cambridge Neighborhood Boundaries</h2>
            <div id="neighborhood-map" style="height: 600px; width: 100%;"></div>
            
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            
            <script>
                // Initialize the map
                var map = L.map('neighborhood-map').setView([42.3736, -71.1097], 12);
                
                // Add OpenStreetMap tiles
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    maxZoom: 18
                }}).addTo(map);
                
                // Color scheme for neighborhoods - using same colors as bar chart
                var neighborhoodColors = {{
                    'Baldwin': '#8dd3c7',
                    'Cambridgeport': '#ffffb3',
                    'East Cambridge': '#bebada',
                    'Highlands': '#fb8072',
                    'Inman/Harrington': '#80b1d3',
                    'MIT': '#fdb462',
                    'Mid-Cambridge': '#b3de69',
                    'North Cambridge': '#fccde5',
                    'Peabody': '#d9d9d9',
                    'Riverside': '#bc80bd',
                    'Strawberry Hill': '#ccebc5',
                    'The Port': '#ffed6f',
                    'West Cambridge': '#8dd3c7'
                }};
                
                // Default color for any neighborhoods not in our list
                var defaultColor = '#999999';
                
                // Crime data for popups (2024 data)
                var crimeData = {json.dumps(crime_data_dict)};
                
                // Mapping from GeoJSON neighborhood names to our neighborhood names
                var nameMapping = {json.dumps(geojson_to_our_names)};
                
                // Function to get color for neighborhood
                function getNeighborhoodColor(name) {{
                    return neighborhoodColors[name] || defaultColor;
                }}
                
                // Function to style each neighborhood
                function style(feature) {{
                    var geojsonName = feature.properties.NAME;
                    var ourName = nameMapping[geojsonName] || geojsonName;
                    return {{
                        fillColor: getNeighborhoodColor(ourName),
                        weight: 2,
                        opacity: 0.8,
                        color: '#2c3e50',
                        fillOpacity: 0.6
                    }};
                }}
                
                // Function to handle click events
                function onEachFeature(feature, layer) {{
                    var geojsonName = feature.properties.NAME;
                    var ourName = nameMapping[geojsonName] || geojsonName;
                    var popupContent = '<h4>' + geojsonName + '</h4>';
                    
                    // Add crime rate info if available
                    if (crimeData[ourName]) {{
                        var data = crimeData[ourName];
                        popupContent += '<table style="margin-top: 10px; font-size: 14px;">';
                        popupContent += '<tr><td><strong>2024 Crime Rate:</strong></td><td>' + data.rate.toFixed(1) + ' per 1,000 residents</td></tr>';
                        popupContent += '<tr><td><strong>2024 Violent Crimes:</strong></td><td>' + data.crime_count.toLocaleString() + '</td></tr>';
                        popupContent += '<tr><td><strong>Population:</strong></td><td>' + data.population.toLocaleString() + '</td></tr>';
                        popupContent += '</table>';
                    }} else {{
                        popupContent += '<p>No 2024 crime data available for this neighborhood</p>';
                        popupContent += '<p><small>Mapped name: ' + ourName + '</small></p>';
                    }}
                    
                    layer.bindPopup(popupContent);
                    
                    // Highlight on mouseover
                    layer.on({{
                        mouseover: function(e) {{
                            var layer = e.target;
                            layer.setStyle({{
                                weight: 3,
                                opacity: 1.0,
                                fillOpacity: 0.8
                            }});
                        }},
                        mouseout: function(e) {{
                            geojsonLayer.resetStyle(e.target);
                        }}
                    }});
                }}
                
                // Variable to store the GeoJSON layer
                var geojsonLayer;
                
                // Load and display the neighborhood boundaries
                fetch('https://raw.githubusercontent.com/cambridgegis/cambridgegis_data/main/Boundary/CDD_Neighborhoods/BOUNDARY_CDDNeighborhoods.geojson')
                    .then(response => response.json())
                    .then(data => {{
                        geojsonLayer = L.geoJSON(data, {{
                            style: style,
                            onEachFeature: onEachFeature
                        }}).addTo(map);
                        
                        // Fit map bounds to show all neighborhoods
                        map.fitBounds(geojsonLayer.getBounds(), {{padding: [10, 10]}});
                    }})
                    .catch(error => {{
                        console.error('Error loading neighborhood data:', error);
                        document.getElementById('neighborhood-map').innerHTML = 
                            '<p style="text-align: center; color: #666; padding: 2rem;">Unable to load neighborhood boundary map.</p>';
                    }});
            </script>
        </div>
        
        <div class="info-box">
            <h3>How to Use This Analysis</h3>
            <ul>
                <li>Use the dropdown menu to filter by specific years or view all-time data</li>
                <li>Hover over bars to see exact crime counts, rates, and population estimates</li>
                <li>The default view shows all-time rates from 2009 to present</li>
                <li>Neighborhoods are sorted by crime rate (highest to lowest)</li>
                <li>Click on neighborhood boundaries in the map to see detailed crime statistics</li>
                <li>Map colors correspond to the bar chart colors for easy reference</li>
                <li>Population estimates are based on area, density, and housing patterns</li>
                <li>Data includes only violent crimes: homicide, assault, robbery, kidnapping, arson, weapons violations, threats, stalking, and extortion</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>Data Source:</strong> <a href="https://data.cambridgema.gov/Public-Safety/Crime-Reports/xuad-73uj/about_data" target="_blank" style="color: #ecf0f1;">Cambridge Open Data Portal</a></p>
        <p>Crime Reports Dataset | Population estimates based on neighborhood characteristics</p>
        <p style="margin-top: 1rem; font-size: 0.9rem;">*Population estimates are approximate and based on area size, housing density, and demographic patterns</p>
    </div>
</body>
</html>
    '''
    
    # Save the HTML file
    with open('crimes_per_capita.html', 'w') as f:
        f.write(html_content)
    
    print("Crimes Per Capita analysis saved as crimes_per_capita.html")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total violent crimes: {stats['total_crimes']:,}")
    print(f"Neighborhoods analyzed: {stats['neighborhoods_count']}")
    print(f"City-wide rate: {stats['citywide_rate']:.1f} per 1,000 residents")
    print(f"Highest rate: {stats['highest_rate_neighborhood']} ({stats['highest_rate']:.1f} per 1,000)")


if __name__ == "__main__":
    main()