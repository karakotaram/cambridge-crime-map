#!/usr/bin/env python3
"""
Cambridge Violent Crimes by Year Analysis
Interactive line graph showing crime trends over time with neighborhood filtering.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def load_and_process_data(csv_path):
    """Load and process crime data for yearly analysis."""
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
    
    print(f"Processed {len(df)} violent crime incidents")
    return df


def create_yearly_analysis(df):
    """Create yearly crime analysis data."""
    # Check if we have 2025 data and calculate pro-rating factor
    current_year = datetime.now().year
    prorate_factor = 1.0
    has_2025_data = False
    
    if 2025 in df['Year'].values:
        has_2025_data = True
        # Find the most recent incident in 2025
        df_2025 = df[df['Year'] == 2025]
        latest_date_2025 = df_2025['Crime_Date'].max()
        
        # Calculate what day of year this represents
        day_of_year = latest_date_2025.timetuple().tm_yday
        days_in_2025 = 365  # 2025 is not a leap year
        
        # Calculate pro-rating factor (how much to multiply by to get full year estimate)
        prorate_factor = days_in_2025 / day_of_year
        
        print(f"Latest 2025 crime: {latest_date_2025.strftime('%m/%d/%Y')} (day {day_of_year})")
        print(f"Pro-rating factor for 2025: {prorate_factor:.2f}x")
    
    # Overall yearly counts
    yearly_all = df.groupby('Year').size().reset_index(name='Crime_Count')
    yearly_all['Neighborhood'] = 'All Neighborhoods'
    
    # By neighborhood yearly counts
    yearly_by_neighborhood = df.groupby(['Year', 'Neighborhood']).size().reset_index(name='Crime_Count')
    
    # Apply pro-rating to 2025 data
    if has_2025_data:
        yearly_all.loc[yearly_all['Year'] == 2025, 'Crime_Count'] = (yearly_all.loc[yearly_all['Year'] == 2025, 'Crime_Count'] * prorate_factor).astype(int)
        yearly_by_neighborhood.loc[yearly_by_neighborhood['Year'] == 2025, 'Crime_Count'] = (yearly_by_neighborhood.loc[yearly_by_neighborhood['Year'] == 2025, 'Crime_Count'] * prorate_factor).astype(int)
    
    # Combine data
    all_data = pd.concat([yearly_all, yearly_by_neighborhood], ignore_index=True)
    
    return all_data, has_2025_data


def create_crimes_by_year_chart(csv_path='../../crimedata.csv'):
    """Create interactive Plotly chart for crimes by year with neighborhood filtering."""
    
    # Load and process data
    df = load_and_process_data(csv_path)
    yearly_data, has_2025_data = create_yearly_analysis(df)
    
    # Get neighborhood list for dropdown
    neighborhoods = sorted(df['Neighborhood'].unique())
    
    # Create custom labels for years (2025 -> 2025E if pro-rated)
    def create_year_labels(years, has_2025_data):
        return [f"{year}E" if year == 2025 and has_2025_data else str(year) for year in years]
    
    # Create the main figure
    fig = go.Figure()
    
    # Add trace for all neighborhoods (default visible)
    all_neighborhoods_data = yearly_data[yearly_data['Neighborhood'] == 'All Neighborhoods']
    year_labels = create_year_labels(all_neighborhoods_data['Year'], has_2025_data)
    
    fig.add_trace(go.Scatter(
        x=all_neighborhoods_data['Year'],
        y=all_neighborhoods_data['Crime_Count'],
        mode='lines+markers',
        name='All Neighborhoods',
        line=dict(color='#d63031', width=3),
        marker=dict(size=8, color='#d63031'),
        visible=True,
        customdata=year_labels,
        hovertemplate='<b>%{fullData.name}</b><br>Year: %{customdata}<br>Crimes: %{y}<extra></extra>'
    ))
    
    # Add traces for each neighborhood (initially hidden)
    colors = px.colors.qualitative.Set3
    for i, neighborhood in enumerate(neighborhoods):
        if neighborhood != 'Unknown':  # Skip Unknown for cleaner display
            neighborhood_data = yearly_data[yearly_data['Neighborhood'] == neighborhood]
            if len(neighborhood_data) > 0:
                neighborhood_year_labels = create_year_labels(neighborhood_data['Year'], has_2025_data)
                fig.add_trace(go.Scatter(
                    x=neighborhood_data['Year'],
                    y=neighborhood_data['Crime_Count'],
                    mode='lines+markers',
                    name=neighborhood,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6),
                    visible=False,
                    customdata=neighborhood_year_labels,
                    hovertemplate='<b>%{fullData.name}</b><br>Year: %{customdata}<br>Crimes: %{y}<extra></extra>'
                ))
    
    # Create dropdown menu
    dropdown_buttons = []
    
    # All neighborhoods button
    non_unknown_neighborhoods = [n for n in neighborhoods if n != 'Unknown']
    all_visible = [True] + [False] * len(non_unknown_neighborhoods)
    dropdown_buttons.append(dict(
        label="All Neighborhoods",
        method="update",
        args=[{"visible": all_visible}]
    ))
    
    # Individual neighborhood buttons
    trace_index = 1  # Start after 'All Neighborhoods' trace
    for neighborhood in neighborhoods:
        if neighborhood != 'Unknown':
            visible_list = [False] * (1 + len([n for n in neighborhoods if n != 'Unknown']))
            visible_list[trace_index] = True
            dropdown_buttons.append(dict(
                label=neighborhood,
                method="update",
                args=[{"visible": visible_list}]
            ))
            trace_index += 1
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Violent Crimes in Cambridge by Year',
            x=0.5,
            font=dict(size=24, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='Year', font=dict(size=16)),
            tickfont=dict(size=14),
            gridcolor='#ecf0f1',
            tickmode='array',
            tickvals=list(yearly_data[yearly_data['Neighborhood'] == 'All Neighborhoods']['Year'].unique()),
            ticktext=create_year_labels(yearly_data[yearly_data['Neighborhood'] == 'All Neighborhoods']['Year'].unique(), has_2025_data)
        ),
        yaxis=dict(
            title=dict(text='Number of Violent Crimes', font=dict(size=16)),
            tickfont=dict(size=14),
            gridcolor='#ecf0f1'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Arial"),
        hovermode='x unified',
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
            text="Filter by Neighborhood:",
            showarrow=False,
            x=0.02,
            y=1.05,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            font=dict(size=14, color='#2c3e50')
        )]
    )
    
    return fig, df, has_2025_data


def create_summary_stats(df):
    """Create summary statistics for the page."""
    current_year = datetime.now().year
    total_crimes = len(df)
    years_span = df['Year'].max() - df['Year'].min() + 1
    neighborhoods_count = len(df['Neighborhood'].unique())
    
    # Year-over-year change
    recent_years = df[df['Year'].isin([current_year-2, current_year-1])]
    if len(recent_years) > 0:
        recent_by_year = recent_years.groupby('Year').size()
        if len(recent_by_year) == 2:
            yoy_change = ((recent_by_year.iloc[1] - recent_by_year.iloc[0]) / recent_by_year.iloc[0] * 100)
            yoy_change = round(yoy_change, 1)
        else:
            yoy_change = 0
    else:
        yoy_change = 0
    
    return {
        'total_crimes': total_crimes,
        'years_span': years_span,
        'neighborhoods_count': neighborhoods_count,
        'yoy_change': yoy_change
    }


def main():
    """Generate the crimes by year HTML page."""
    print("Creating Crimes by Year analysis...")
    
    # Create the chart
    fig, df, has_2025_data = create_crimes_by_year_chart()
    
    # Get summary stats
    stats = create_summary_stats(df)
    
    # Convert to HTML
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='crimes-chart',
        config={'displayModeBar': True, 'displaylogo': False}
    )
    
    # Create complete HTML page
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cambridge Crimes by Year | Crime Data Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .nav {{
            background: white;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .nav a {{
            color: #d63031;
            text-decoration: none;
            font-weight: bold;
            font-size: 1rem;
        }}
        
        .nav a:hover {{
            text-decoration: underline;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #d63031;
            display: block;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 2rem 0;
        }}
        
        .info-box {{
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
        }}
        
        .info-box h3 {{
            color: #0c5460;
            margin-bottom: 1rem;
        }}
        
        .info-box ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .info-box li {{
            margin: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }}
        
        .info-box li::before {{
            content: "ℹ️";
            position: absolute;
            left: 0;
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
        <h1>📈 Crimes Over Time</h1>
        <p>Track violent crime trends year by year across Cambridge neighborhoods</p>
    </div>
    
    <div class="nav">
        <a href="../../index.html">← Back to Analysis Home</a>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{stats['total_crimes']:,}</span>
                <div class="stat-label">Total Violent Crimes</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['years_span']}</span>
                <div class="stat-label">Years of Data</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['neighborhoods_count']}</span>
                <div class="stat-label">Neighborhoods</div>
            </div>
            <div class="stat-card">
                <span class="stat-number" style="color: {'#e74c3c' if stats['yoy_change'] > 0 else '#27ae60'}">{stats['yoy_change']:+.1f}%</span>
                <div class="stat-label">Recent Change</div>
            </div>
        </div>
        
        <div class="chart-container">
            {chart_html}
        </div>
        
        <div class="info-box">
            <h3>How to Use This Analysis</h3>
            <ul>
                <li>Use the dropdown menu to filter by specific neighborhoods or view all data</li>
                <li>Hover over data points to see exact crime counts for each year</li>
                <li>The default view shows trends across all Cambridge neighborhoods</li>
                <li>Data includes only violent crimes: homicide, assault, robbery, kidnapping, arson, weapons violations, threats, stalking, and extortion</li>
                <li>Years with no data points indicate zero violent crimes reported for that neighborhood</li>
                {'<li><strong>*2025E data:</strong> 2025 crime counts have been pro-rated to estimate a full year based on the most recent incident date</li>' if has_2025_data else ''}
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>Data Source:</strong> <a href="https://data.cambridgema.gov/Public-Safety/Crime-Reports/xuad-73uj/about_data" target="_blank" style="color: #ecf0f1;">Cambridge Open Data Portal</a></p>
        <p>Crime Reports Dataset | Violent crimes from 2009 to present</p>
    </div>
</body>
</html>
    '''
    
    # Save the HTML file
    with open('crimes_by_year.html', 'w') as f:
        f.write(html_content)
    
    print("Crimes by Year analysis saved as crimes_by_year.html")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total violent crimes: {stats['total_crimes']:,}")
    print(f"Years analyzed: {stats['years_span']}")
    print(f"Neighborhoods: {stats['neighborhoods_count']}")
    print(f"Recent year-over-year change: {stats['yoy_change']:+.1f}%")


if __name__ == "__main__":
    main()