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


def get_national_crime_rate_data():
    """Get US national violent crime rates per 100,000 population by year."""
    # Based on FBI UCR data - violent crime rate per 100,000 inhabitants
    return {
        2009: 429.4,  # Interpolated from trend
        2010: 403.6,  # FBI data
        2011: 387.1,  # Interpolated from trend  
        2012: 386.9,  # FBI data
        2013: 367.9,  # Interpolated from trend
        2014: 363.6,  # FBI data
        2015: 372.6,  # Interpolated from trend
        2016: 386.8,  # FBI data
        2017: 376.5,  # FBI data
        2018: 370.8,  # FBI data
        2019: 366.7,  # FBI data
        2020: 386.3,  # FBI data
        2021: 394.0,  # Estimated based on trend
        2022: 380.7,  # FBI data
        2023: 363.8,  # FBI data
        2024: 347.0,  # Estimated based on 4.5% decrease
        2025: 347.0   # Same as 2024 for projection
    }


def get_cambridge_population_data():
    """Get Cambridge population estimates by year."""
    # Based on US Census Bureau data and estimates
    return {
        2009: 105500,  # Estimated based on 2010 census and trends
        2010: 105162,  # US Census
        2011: 106000,  # Estimated
        2012: 107000,  # Estimated
        2013: 108500,  # Estimated  
        2014: 113041,  # Lowest recorded population
        2015: 115000,  # Estimated
        2016: 116500,  # Estimated
        2017: 118000,  # Estimated
        2018: 118500,  # Estimated
        2019: 118988,  # Peak population
        2020: 118403,  # US Census
        2021: 117275,  # Census estimate
        2022: 117420,  # Census estimate
        2023: 118214,  # Census estimate
        2024: 121186,  # Census estimate
        2025: 123086   # Projected
    }


def get_neighborhood_population_estimates():
    """Get neighborhood population estimates for Cambridge."""
    # Based on Cambridge official neighborhood data and census estimates
    # Using approximate proportions from city demographic profiles
    return {
        'Area 1/East Cambridge': 9500,
        'Area 2/MIT': 5900,  
        'Area 3/Wellington-Harrington': 7100,
        'Area 4/The Port': 10700,
        'Cambridgeport': 14200,
        'Area 6/Mid-Cambridge': 9500,
        'Area 7/Riverside': 8300,
        'Agassiz': 7100,
        'Peabody': 5900,
        'Brattle Street/West Cambridge': 11800,
        'North Cambridge': 14200,
        'Cambridge Highlands': 7100,
        'Strawberry Hill': 7100,
        # Alternative name mappings to match crime data neighborhood names
        'MIT': 5900,  
        'The Port': 10700,
        'Mid-Cambridge': 9500,
        'Riverside': 8300,
        'West Cambridge': 11800,
        'East Cambridge': 9500,  # Maps to Area 1/East Cambridge
        'Highlands': 7100,  # Maps to Cambridge Highlands
        'Inman/Harrington': 7100,  # Maps to Area 3/Wellington-Harrington
        'Baldwin': 7100,  # Assign to Agassiz neighborhood population
        'Unknown': 1200
    }


def calculate_national_average_crimes(year, population, national_rates, cambridge_population):
    """Calculate expected number of crimes based on national average rate."""
    if year not in national_rates or year not in cambridge_population:
        return None
    
    # National rate is per 100,000 population
    national_rate = national_rates[year]
    
    # Calculate expected crimes for given population
    expected_crimes = (national_rate / 100000) * population
    
    return round(expected_crimes, 1)


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
    
    # Add national average comparison data
    national_rates = get_national_crime_rate_data()
    cambridge_population = get_cambridge_population_data()
    neighborhood_populations = get_neighborhood_population_estimates()
    
    # Calculate national averages for Cambridge overall
    cambridge_national_avg = []
    for year in yearly_all['Year']:
        if year in cambridge_population:
            expected = calculate_national_average_crimes(year, cambridge_population[year], national_rates, cambridge_population)
            if expected is not None:
                cambridge_national_avg.append({
                    'Year': year,
                    'Crime_Count': expected,
                    'Neighborhood': 'National Average (Cambridge)',
                    'Type': 'National Average'
                })
    
    # Calculate national averages for each neighborhood
    neighborhood_national_avg = []
    neighborhoods = df['Neighborhood'].unique()
    
    for neighborhood in neighborhoods:
        if neighborhood in neighborhood_populations:
            pop = neighborhood_populations[neighborhood]
            for year in df['Year'].unique():
                expected = calculate_national_average_crimes(year, pop, national_rates, cambridge_population)
                if expected is not None:
                    neighborhood_national_avg.append({
                        'Year': year,
                        'Crime_Count': expected,
                        'Neighborhood': f'National Average ({neighborhood})',
                        'Type': 'National Average'
                    })
    
    # Convert to DataFrames and combine
    cambridge_avg_df = pd.DataFrame(cambridge_national_avg)
    neighborhood_avg_df = pd.DataFrame(neighborhood_national_avg)
    
    if not cambridge_avg_df.empty:
        all_data = pd.concat([all_data, cambridge_avg_df], ignore_index=True)
    if not neighborhood_avg_df.empty:
        all_data = pd.concat([all_data, neighborhood_avg_df], ignore_index=True)
    
    return all_data, has_2025_data


def create_crimes_by_year_chart(csv_path='./crimedata.csv'):
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
    
    # Add national average line for Cambridge (default visible)
    cambridge_national_data = yearly_data[yearly_data['Neighborhood'] == 'National Average (Cambridge)']
    if not cambridge_national_data.empty:
        cambridge_national_year_labels = create_year_labels(cambridge_national_data['Year'], has_2025_data)
        fig.add_trace(go.Scatter(
            x=cambridge_national_data['Year'],
            y=cambridge_national_data['Crime_Count'],
            mode='lines',
            name='US National Average',
            line=dict(color='#636e72', width=2, dash='dot'),
            visible=True,
            customdata=cambridge_national_year_labels,
            hovertemplate='<b>%{fullData.name}</b><br>Year: %{customdata}<br>Expected Crimes: %{y}<extra></extra>',
            showlegend=True  # Explicitly show in legend
        ))
    
    # Add traces for each neighborhood (initially hidden)  
    # Store trace mapping for dropdown logic
    neighborhood_trace_mapping = {}
    
    for i, neighborhood in enumerate(neighborhoods):
        if neighborhood != 'Unknown':  # Skip Unknown for cleaner display
            neighborhood_data = yearly_data[yearly_data['Neighborhood'] == neighborhood]
            if len(neighborhood_data) > 0:
                neighborhood_year_labels = create_year_labels(neighborhood_data['Year'], has_2025_data)
                
                # Record the trace index for this neighborhood
                neighborhood_trace_idx = len(fig.data)
                
                # Add actual neighborhood data - use consistent red color like Cambridge overall
                fig.add_trace(go.Scatter(
                    x=neighborhood_data['Year'],
                    y=neighborhood_data['Crime_Count'],
                    mode='lines+markers',
                    name=neighborhood,
                    line=dict(color='#d63031', width=3),  # Same color and width as Cambridge overall
                    marker=dict(size=8, color='#d63031'),  # Same size and color as Cambridge overall
                    visible=False,
                    customdata=neighborhood_year_labels,
                    hovertemplate='<b>%{fullData.name}</b><br>Year: %{customdata}<br>Crimes: %{y}<extra></extra>',
                    legendgroup=f'{neighborhood}_group'
                ))
                
                # Add national average for this specific neighborhood (hidden by default)
                neighborhood_national_data = yearly_data[yearly_data['Neighborhood'] == f'National Average ({neighborhood})']
                national_trace_idx = None
                if not neighborhood_national_data.empty:
                    national_trace_idx = len(fig.data)
                    neighborhood_national_year_labels = create_year_labels(neighborhood_national_data['Year'], has_2025_data)
                    fig.add_trace(go.Scatter(
                        x=neighborhood_national_data['Year'],
                        y=neighborhood_national_data['Crime_Count'],
                        mode='lines',
                        name=f'US National Average ({neighborhood})',  # Unique name per neighborhood
                        line=dict(color='#636e72', width=2, dash='dot'),
                        visible=False,
                        customdata=neighborhood_national_year_labels,
                        hovertemplate='<b>US National Average</b><br>Year: %{customdata}<br>Expected Crimes: %{y}<extra></extra>',
                        showlegend=False,  # Don't show in legend to avoid duplicates
                        legendgroup=f'{neighborhood}_group'  # Group traces together
                    ))
                
                # Store the mapping
                neighborhood_trace_mapping[neighborhood] = {
                    'data_trace': neighborhood_trace_idx,
                    'national_trace': national_trace_idx
                }
    
    # Create dropdown menu
    dropdown_buttons = []
    
    # Calculate total traces
    total_traces = len(fig.data)
    
    # All neighborhoods button (show Cambridge data + national average)
    all_visible = [True, True] + [False] * (total_traces - 2)  # Show first two traces (Cambridge + national avg)
    dropdown_buttons.append(dict(
        label="All Neighborhoods",
        method="update",
        args=[{"visible": all_visible}]
    ))
    
    # Individual neighborhood buttons
    for neighborhood in neighborhood_trace_mapping:
        visible_list = [False] * total_traces
        
        # Show the specific neighborhood data trace
        data_trace_idx = neighborhood_trace_mapping[neighborhood]['data_trace']
        visible_list[data_trace_idx] = True
        
        # Show the specific national average trace if it exists
        national_trace_idx = neighborhood_trace_mapping[neighborhood]['national_trace']
        if national_trace_idx is not None:
            visible_list[national_trace_idx] = True
        
        
        dropdown_buttons.append(dict(
            label=neighborhood,
            method="update",
            args=[{"visible": visible_list}]
        ))
    
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
            <h1>Crimes Over Time</h1>
            <p>Track violent crime trends year by year across Cambridge neighborhoods</p>
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
                <li><strong>Dotted lines show US national average</strong> - calculated using FBI national violent crime rates prorated to Cambridge/neighborhood population sizes</li>
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