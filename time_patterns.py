#!/usr/bin/env python3
"""
Cambridge Crime Time Pattern Analysis
Interactive heatmaps showing when violent crimes occur by hour and day of week.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    """Load and process crime data for time pattern analysis."""
    print("Loading crime data for time pattern analysis...")
    df = pd.read_csv(csv_path)
    
    # Parse crime date and time
    df['Crime_Date'] = pd.to_datetime(df['Crime Date Time'], errors='coerce')
    df = df.dropna(subset=['Crime_Date'])
    
    # Filter to violent crimes only
    df['Is_Violent'] = df['Crime'].apply(categorize_crime_as_violent)
    df = df[df['Is_Violent']]
    
    # Extract time components
    df['Hour'] = df['Crime_Date'].dt.hour
    df['DayOfWeek'] = df['Crime_Date'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['DayName'] = df['Crime_Date'].dt.day_name()
    df['Year'] = df['Crime_Date'].dt.year
    
    # Clean neighborhood data
    df['Neighborhood'] = df['Neighborhood'].fillna('Unknown')
    df = df[df['Neighborhood'] != 'Unknown']
    df = df[df['Year'] == 2024]  # Focus on 2024 data
    
    print(f"Processed {len(df)} violent crime incidents for time analysis")
    return df


def create_time_heatmap_data(df, neighborhood=None):
    """Create heatmap data for time patterns."""
    if neighborhood and neighborhood != 'All Neighborhoods':
        df_filtered = df[df['Neighborhood'] == neighborhood].copy()
    else:
        df_filtered = df.copy()
    
    # Create hour-by-day matrix
    heatmap_data = df_filtered.groupby(['DayOfWeek', 'Hour']).size().reset_index(name='Count')
    
    # Create full matrix (all hours and days, even if no crimes)
    all_hours = list(range(24))
    all_days = list(range(7))
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Create pivot table
    pivot_data = heatmap_data.pivot(index='DayOfWeek', columns='Hour', values='Count').fillna(0)
    
    # Ensure all hours and days are represented
    for hour in all_hours:
        if hour not in pivot_data.columns:
            pivot_data[hour] = 0
    
    for day in all_days:
        if day not in pivot_data.index:
            new_row = pd.Series([0] * 24, index=pivot_data.columns, name=day)
            pivot_data = pd.concat([pivot_data, new_row.to_frame().T])
    
    # Sort by day and hour
    pivot_data = pivot_data.sort_index().sort_index(axis=1)
    
    return pivot_data, day_names


def create_time_patterns_chart(csv_path='../../crimedata.csv'):
    """Create interactive time pattern heatmaps."""
    
    # Load and process data
    df = load_and_process_data(csv_path)
    
    # Get available neighborhoods
    neighborhoods = ['All Neighborhoods'] + sorted(df['Neighborhood'].unique())
    
    # Create heatmaps for each neighborhood
    heatmap_data = {}
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hour_labels = [f"{h:02d}:00" for h in range(24)]
    
    for neighborhood in neighborhoods:
        pivot_data, _ = create_time_heatmap_data(df, neighborhood)
        heatmap_data[neighborhood] = {
            'z': pivot_data.values.tolist(),
            'max_value': pivot_data.values.max()
        }
    
    # Create the main figure with subplots
    fig = go.Figure()
    
    # Add heatmap traces for each neighborhood
    for i, neighborhood in enumerate(neighborhoods):
        data = heatmap_data[neighborhood]
        
        fig.add_trace(go.Heatmap(
            z=data['z'],
            x=hour_labels,
            y=day_names,
            colorscale='Reds',
            showscale=True,
            name=neighborhood,
            visible=(i == 0),  # Only show "All Neighborhoods" initially
            hoverongaps=False,
            hovertemplate='<b>%{y}</b><br>Time: %{x}<br>Incidents: %{z}<extra></extra>',
            colorbar=dict(
                title=dict(text="Number of<br>Incidents")
            )
        ))
    
    # Create dropdown menu
    dropdown_buttons = []
    for i, neighborhood in enumerate(neighborhoods):
        visible_list = [False] * len(neighborhoods)
        visible_list[i] = True
        dropdown_buttons.append(dict(
            label=neighborhood,
            method="update",
            args=[{"visible": visible_list}]
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Cambridge Violent Crime Patterns by Time and Day',
            x=0.5,
            font=dict(size=24, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='Hour of Day', font=dict(size=16)),
            tickfont=dict(size=12),
            side='bottom'
        ),
        yaxis=dict(
            title=dict(text='Day of Week', font=dict(size=16)),
            tickfont=dict(size=12),
            autorange='reversed'  # Monday at top
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Arial"),
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
            text="Select Neighborhood:",
            showarrow=False,
            x=0.02,
            y=1.05,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            font=dict(size=14, color='#2c3e50')
        )],
        height=600
    )
    
    return fig, df, heatmap_data


def create_summary_stats(df, heatmap_data):
    """Create summary statistics for time patterns."""
    total_crimes = len(df)
    
    # Find peak times across all neighborhoods
    all_neighborhoods_data = heatmap_data['All Neighborhoods']['z']
    max_crimes = 0
    peak_day = peak_hour = 0
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_idx, day_data in enumerate(all_neighborhoods_data):
        for hour_idx, count in enumerate(day_data):
            if count > max_crimes:
                max_crimes = count
                peak_day = day_idx
                peak_hour = hour_idx
    
    peak_day_name = day_names[peak_day]
    peak_hour_str = f"{peak_hour:02d}:00"
    
    # Calculate totals by day and hour
    df_copy = df.copy()
    crimes_by_day = df_copy.groupby('DayOfWeek').size()
    crimes_by_hour = df_copy.groupby('Hour').size()
    
    busiest_day = day_names[crimes_by_day.idxmax()]
    busiest_hour = f"{crimes_by_hour.idxmax():02d}:00"
    
    # Weekend vs weekday comparison
    weekend_crimes = df_copy[df_copy['DayOfWeek'].isin([5, 6])].shape[0]  # Sat, Sun
    weekday_crimes = df_copy[~df_copy['DayOfWeek'].isin([5, 6])].shape[0]
    
    return {
        'total_crimes': total_crimes,
        'peak_day': peak_day_name,
        'peak_hour': peak_hour_str,
        'peak_crimes': int(max_crimes),
        'busiest_day': busiest_day,
        'busiest_hour': busiest_hour,
        'weekend_crimes': weekend_crimes,
        'weekday_crimes': weekday_crimes,
        'weekend_avg': round(weekend_crimes / 2, 1),  # 2 weekend days
        'weekday_avg': round(weekday_crimes / 5, 1)   # 5 weekday days
    }


def main():
    """Generate the time patterns HTML page."""
    print("Creating Time Pattern Analysis...")
    
    # Create the chart
    fig, df, heatmap_data = create_time_patterns_chart()
    
    # Get summary stats
    stats = create_summary_stats(df, heatmap_data)
    
    # Convert to HTML
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='time-patterns-chart',
        config={'displayModeBar': True, 'displaylogo': False}
    )
    
    # Create complete HTML page
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cambridge Time Pattern Analysis | Crime Data Analysis</title>
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
        
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        .insight-card {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .insight-card h3 {{
            color: #2c3e50;
            margin-bottom: 1rem;
        }}
        
        .insight-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #eee;
        }}
        
        .insight-item:last-child {{
            border-bottom: none;
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
            content: "⏰";
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
            
            .insights-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⏰ Time Pattern Analysis</h1>
        <p>Discover when violent crimes occur throughout the day and week</p>
    </div>
    
    <div class="nav">
        <a href="/cambridge-crime-map/">← Back to Analysis Home</a>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{stats['total_crimes']:,}</span>
                <div class="stat-label">Total 2024 Crimes</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['peak_crimes']}</span>
                <div class="stat-label">Peak Hour Incidents</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['busiest_day']}</span>
                <div class="stat-label">Busiest Day</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['busiest_hour']}</span>
                <div class="stat-label">Busiest Hour</div>
            </div>
        </div>
        
        <div class="chart-container">
            {chart_html}
        </div>
        
        <div class="insights-grid">
            <div class="insight-card">
                <h3>Peak Crime Times</h3>
                <div class="insight-item">
                    <span>Highest Single Hour:</span>
                    <span>{stats['peak_day']} at {stats['peak_hour']}</span>
                </div>
                <div class="insight-item">
                    <span>Peak Incidents:</span>
                    <span>{stats['peak_crimes']} crimes</span>
                </div>
                <div class="insight-item">
                    <span>Busiest Overall Day:</span>
                    <span>{stats['busiest_day']}</span>
                </div>
                <div class="insight-item">
                    <span>Busiest Overall Hour:</span>
                    <span>{stats['busiest_hour']}</span>
                </div>
            </div>
            
            <div class="insight-card">
                <h3>Weekend vs Weekday</h3>
                <div class="insight-item">
                    <span>Weekend Crimes (Sat-Sun):</span>
                    <span>{stats['weekend_crimes']:,} total</span>
                </div>
                <div class="insight-item">
                    <span>Weekday Crimes (Mon-Fri):</span>
                    <span>{stats['weekday_crimes']:,} total</span>
                </div>
                <div class="insight-item">
                    <span>Average Weekend Day:</span>
                    <span>{stats['weekend_avg']} crimes/day</span>
                </div>
                <div class="insight-item">
                    <span>Average Weekday:</span>
                    <span>{stats['weekday_avg']} crimes/day</span>
                </div>
            </div>
        </div>
        
        <div class="info-box">
            <h3>How to Use This Analysis</h3>
            <ul>
                <li>Use the dropdown to view patterns for all neighborhoods or specific areas</li>
                <li>Darker red colors indicate more frequent crime incidents</li>
                <li>Hover over cells to see exact incident counts for each time period</li>
                <li>Look for patterns: Are certain days or hours consistently more dangerous?</li>
                <li>Data covers violent crimes from 2024 for current relevance</li>
                <li>Each cell represents one hour on one day of the week</li>
                <li>Use patterns to inform personal safety decisions about timing activities</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>Data Source:</strong> <a href="https://data.cambridgema.gov/Public-Safety/Crime-Reports/xuad-73uj/about_data" target="_blank" style="color: #ecf0f1;">Cambridge Open Data Portal</a></p>
        <p>Time pattern analysis based on violent crimes from 2024</p>
    </div>
</body>
</html>
    '''
    
    # Save the HTML file
    with open('time_patterns.html', 'w') as f:
        f.write(html_content)
    
    print("Time Pattern Analysis saved as time_patterns.html")
    
    # Print summary
    print(f"\\nSummary:")
    print(f"Total crimes analyzed: {stats['total_crimes']:,}")
    print(f"Peak single hour: {stats['peak_day']} at {stats['peak_hour']} ({stats['peak_crimes']} incidents)")
    print(f"Busiest day overall: {stats['busiest_day']}")
    print(f"Busiest hour overall: {stats['busiest_hour']}")
    print(f"Weekend vs weekday daily average: {stats['weekend_avg']} vs {stats['weekday_avg']}")


if __name__ == "__main__":
    main()