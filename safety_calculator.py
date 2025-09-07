#!/usr/bin/env python3
"""
Cambridge Neighborhood Safety Calculator
Interactive route-based safety analysis with time-of-day and transportation mode factors.
"""

import pandas as pd
import json
import math
from datetime import datetime, time


def categorize_crime_as_violent(crime_type):
    """Categorize crime type as violent or non-violent."""
    violent_crimes = {
        'Homicide', 'Aggravated Assault', 'Simple Assault', 'Street Robbery', 
        'Commercial Robbery', 'Kidnapping', 'Arson', 'Weapon Violations',
        'Stalking', 'Extortion/Blackmail', 'Threats', 'Domestic Dispute'
    }
    return crime_type in violent_crimes


def get_neighborhood_populations():
    """Get estimated population by neighborhood."""
    return {
        'Baldwin': 6500,
        'Cambridgeport': 12500,
        'East Cambridge': 8500,
        'Highlands': 4200,
        'Inman/Harrington': 7800,
        'MIT': 3000,
        'Mid-Cambridge': 15000,
        'North Cambridge': 14000,
        'Peabody': 5500,
        'Riverside': 11000,
        'Strawberry Hill': 2500,
        'The Port': 9500,
        'West Cambridge': 18000
    }


def load_and_process_crime_data(csv_path):
    """Load and process crime data for safety analysis."""
    print("Loading crime data for safety analysis...")
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
    df['Month'] = df['Crime_Date'].dt.month
    df['Year'] = df['Crime_Date'].dt.year
    
    # Clean neighborhood and location data
    df['Neighborhood'] = df['Neighborhood'].fillna('Unknown')
    df = df[df['Neighborhood'] != 'Unknown']
    df = df[df['Year'] >= 2020]  # Focus on recent years for current safety
    
    print(f"Processed {len(df)} recent violent crime incidents")
    return df


def calculate_neighborhood_safety_scores(df):
    """Calculate comprehensive safety scores for each neighborhood."""
    populations = get_neighborhood_populations()
    
    # Base crime rates per neighborhood
    neighborhood_stats = {}
    
    for neighborhood in populations.keys():
        neighborhood_data = df[df['Neighborhood'] == neighborhood].copy()
        
        if len(neighborhood_data) == 0:
            # No crime data - assign best possible score
            neighborhood_stats[neighborhood] = {
                'total_crimes': 0,
                'crime_rate': 0,
                'safety_score': 10.0,
                'time_patterns': {},
                'severity_breakdown': {}
            }
            continue
        
        total_crimes = len(neighborhood_data)
        population = populations[neighborhood]
        crime_rate = (total_crimes / population) * 1000
        
        # Calculate time-of-day patterns (crimes per hour)
        time_patterns = {}
        for hour in range(24):
            hour_crimes = len(neighborhood_data[neighborhood_data['Hour'] == hour])
            time_patterns[hour] = hour_crimes
        
        # Calculate severity breakdown
        severity_breakdown = neighborhood_data['Crime'].value_counts().to_dict()
        
        # Base safety score (10 = safest, 0 = least safe)
        # Invert crime rate: lower crime rate = higher safety score
        max_rate = 150  # Approximate maximum expected rate per 1000
        safety_score = max(0, 10 - (crime_rate / max_rate * 10))
        
        neighborhood_stats[neighborhood] = {
            'total_crimes': total_crimes,
            'crime_rate': crime_rate,
            'safety_score': safety_score,
            'time_patterns': time_patterns,
            'severity_breakdown': severity_breakdown
        }
    
    return neighborhood_stats


def calculate_time_multiplier(hour, day_of_week):
    """
    Calculate safety multiplier based on time of day and day of week.
    Returns multiplier where 1.0 = average, >1.0 = more dangerous, <1.0 = safer
    """
    # Time of day risk factors
    if 6 <= hour <= 17:  # Daytime (6am-5pm)
        time_factor = 0.7
    elif 18 <= hour <= 22:  # Evening (6pm-10pm)
        time_factor = 1.0
    else:  # Late night/early morning
        time_factor = 1.8
    
    # Day of week risk factors
    if day_of_week in [5, 6]:  # Weekend (Fri=4, Sat=5, Sun=6)
        day_factor = 1.2
    else:  # Weekday
        day_factor = 0.9
    
    return time_factor * day_factor


def calculate_transportation_multiplier(mode):
    """
    Calculate safety multiplier based on transportation mode.
    """
    multipliers = {
        'walking': 1.0,      # Baseline
        'biking': 0.8,       # Slightly safer (faster movement)
        'driving': 0.3,      # Much safer (enclosed vehicle)
        'public_transit': 0.6  # Generally safe, some exposure at stops
    }
    return multipliers.get(mode, 1.0)


def create_safety_calculator_page():
    """Generate the safety calculator HTML page."""
    print("Creating Safety Calculator page...")
    
    # Load and process data
    df = load_and_process_crime_data('../../crimedata.csv')
    neighborhood_stats = calculate_neighborhood_safety_scores(df)
    
    # Create complete HTML page
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cambridge Safety Calculator | Crime Data Analysis</title>
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
        
        .calculator-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        .input-panel {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .results-panel {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .form-group {{
            margin-bottom: 1.5rem;
        }}
        
        .form-group label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .form-group select, .form-group input {{
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e0e0e0;
            border-radius: 4px;
            font-size: 1rem;
        }}
        
        .form-group select:focus, .form-group input:focus {{
            outline: none;
            border-color: #d63031;
        }}
        
        .calculate-btn {{
            width: 100%;
            background: linear-gradient(45deg, #d63031, #e17055);
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .calculate-btn:hover {{
            background: linear-gradient(45deg, #b71c1c, #d63031);
            transform: translateY(-2px);
        }}
        
        .safety-score {{
            text-align: center;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }}
        
        .score-excellent {{
            background: linear-gradient(135deg, #4caf50, #8bc34a);
            color: white;
        }}
        
        .score-good {{
            background: linear-gradient(135deg, #8bc34a, #cddc39);
            color: white;
        }}
        
        .score-moderate {{
            background: linear-gradient(135deg, #ffc107, #ff9800);
            color: white;
        }}
        
        .score-poor {{
            background: linear-gradient(135deg, #ff5722, #f44336);
            color: white;
        }}
        
        .score-number {{
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        
        .score-label {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .breakdown {{
            margin-top: 1.5rem;
        }}
        
        .breakdown h3 {{
            color: #2c3e50;
            margin-bottom: 1rem;
        }}
        
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #eee;
        }}
        
        .breakdown-item:last-child {{
            border-bottom: none;
        }}
        
        .map-container {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
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
            .calculator-grid {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                padding: 1rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</head>
<body>
    <div class="header">
        <h1>🛡️ Cambridge Safety Calculator</h1>
        <p>Calculate safety scores for neighborhoods and commute routes</p>
    </div>
    
    <div class="nav">
        <a href="/cambridge-crime-map/">← Back to Analysis Home</a>
    </div>
    
    <div class="container">
        <div class="calculator-grid">
            <div class="input-panel">
                <h2 style="margin-bottom: 1.5rem; color: #2c3e50;">Calculate Your Safety Score</h2>
                
                <div class="form-group">
                    <label for="neighborhood">Neighborhood</label>
                    <select id="neighborhood">
                        <option value="">Select a neighborhood...</option>
                        {chr(10).join([f'<option value="{name}">{name}</option>' for name in sorted(neighborhood_stats.keys())])}
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="time">Time of Day</label>
                    <select id="time">
                        <option value="9">9:00 AM (Morning commute)</option>
                        <option value="12">12:00 PM (Lunch time)</option>
                        <option value="17">5:00 PM (Evening commute)</option>
                        <option value="20">8:00 PM (Evening)</option>
                        <option value="23">11:00 PM (Late night)</option>
                        <option value="2">2:00 AM (Very late)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="day">Day of Week</label>
                    <select id="day">
                        <option value="1">Monday</option>
                        <option value="2">Tuesday</option>
                        <option value="3">Wednesday</option>
                        <option value="4">Thursday</option>
                        <option value="5">Friday</option>
                        <option value="6">Saturday</option>
                        <option value="0">Sunday</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="transport">Transportation Mode</label>
                    <select id="transport">
                        <option value="walking">Walking</option>
                        <option value="biking">Biking</option>
                        <option value="driving">Driving</option>
                        <option value="public_transit">Public Transit</option>
                    </select>
                </div>
                
                <button class="calculate-btn" onclick="calculateSafety()">Calculate Safety Score</button>
            </div>
            
            <div class="results-panel">
                <h2 style="margin-bottom: 1.5rem; color: #2c3e50;">Safety Results</h2>
                
                <div id="safety-results" style="display: none;">
                    <div id="safety-score-display" class="safety-score">
                        <div class="score-number" id="score-number">-</div>
                        <div class="score-label" id="score-label">Safety Score</div>
                    </div>
                    
                    <div class="breakdown">
                        <h3>Score Breakdown</h3>
                        <div class="breakdown-item">
                            <span>Base Neighborhood Safety:</span>
                            <span id="base-score">-</span>
                        </div>
                        <div class="breakdown-item">
                            <span>Time of Day Factor:</span>
                            <span id="time-factor">-</span>
                        </div>
                        <div class="breakdown-item">
                            <span>Day of Week Factor:</span>
                            <span id="day-factor">-</span>
                        </div>
                        <div class="breakdown-item">
                            <span>Transportation Factor:</span>
                            <span id="transport-factor">-</span>
                        </div>
                    </div>
                    
                    <div class="breakdown">
                        <h3>Neighborhood Statistics</h3>
                        <div class="breakdown-item">
                            <span>Total Recent Crimes:</span>
                            <span id="total-crimes">-</span>
                        </div>
                        <div class="breakdown-item">
                            <span>Crime Rate (per 1,000):</span>
                            <span id="crime-rate">-</span>
                        </div>
                    </div>
                    
                    <div id="recommendations" class="info-box" style="margin-top: 1.5rem; background: #fff3cd; border-color: #ffeaa7;">
                        <h3 style="color: #856404;">Safety Recommendations</h3>
                        <div id="recommendation-text">Select a neighborhood to see personalized safety recommendations.</div>
                    </div>
                </div>
                
                <div id="no-results" style="text-align: center; color: #666; padding: 2rem;">
                    Select a neighborhood and click "Calculate Safety Score" to see results.
                </div>
            </div>
        </div>
        
        <div class="map-container">
            <h2 style="text-align: center; margin-bottom: 1.5rem; color: #2c3e50;">Cambridge Neighborhood Safety Map</h2>
            <div id="safety-map" style="height: 500px; width: 100%;"></div>
        </div>
        
        <div class="info-box">
            <h3>How the Safety Score Works</h3>
            <ul>
                <li><strong>Base Score (0-10):</strong> Calculated from recent violent crime rates in each neighborhood</li>
                <li><strong>Time Factors:</strong> Daytime hours are safer, late night hours increase risk</li>
                <li><strong>Day Factors:</strong> Weekdays are generally safer than weekends</li>
                <li><strong>Transportation:</strong> Driving is safest, walking has highest exposure</li>
                <li><strong>Final Score:</strong> Combines all factors for a personalized safety assessment</li>
                <li><strong>Data Source:</strong> Based on violent crimes (2020-present) from Cambridge Open Data</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>Data Source:</strong> <a href="https://data.cambridgema.gov/Public-Safety/Crime-Reports/xuad-73uj/about_data" target="_blank" style="color: #ecf0f1;">Cambridge Open Data Portal</a></p>
        <p>Safety scores are estimates based on historical crime data and should not be the sole factor in safety decisions</p>
    </div>
    
    <script>
        // Neighborhood safety data
        const neighborhoodStats = {json.dumps(neighborhood_stats, indent=8)};
        
        // Initialize map
        let map;
        let geojsonLayer;
        
        function initializeMap() {{
            map = L.map('safety-map').setView([42.3736, -71.1097], 12);
            
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }}).addTo(map);
            
            // Load neighborhood boundaries and color by safety score
            fetch('https://raw.githubusercontent.com/cambridgegis/cambridgegis_data/main/Boundary/CDD_Neighborhoods/BOUNDARY_CDDNeighborhoods.geojson')
                .then(response => response.json())
                .then(data => {{
                    geojsonLayer = L.geoJSON(data, {{
                        style: styleNeighborhoodBySafety,
                        onEachFeature: onEachFeature
                    }}).addTo(map);
                    
                    map.fitBounds(geojsonLayer.getBounds(), {{padding: [10, 10]}});
                }})
                .catch(error => {{
                    console.error('Error loading neighborhood data:', error);
                }});
        }}
        
        function styleNeighborhoodBySafety(feature) {{
            const name = mapNeighborhoodName(feature.properties.NAME);
            const stats = neighborhoodStats[name];
            
            if (!stats) {{
                return {{
                    fillColor: '#999999',
                    weight: 2,
                    opacity: 0.8,
                    color: '#2c3e50',
                    fillOpacity: 0.6
                }};
            }}
            
            const score = stats.safety_score;
            let color;
            
            if (score >= 8) color = '#4caf50';      // Excellent (green)
            else if (score >= 6) color = '#8bc34a'; // Good (light green)
            else if (score >= 4) color = '#ffc107'; // Moderate (yellow)
            else color = '#f44336';                  // Poor (red)
            
            return {{
                fillColor: color,
                weight: 2,
                opacity: 0.8,
                color: '#2c3e50',
                fillOpacity: 0.7
            }};
        }}
        
        function onEachFeature(feature, layer) {{
            const geojsonName = feature.properties.NAME;
            const ourName = mapNeighborhoodName(geojsonName);
            const stats = neighborhoodStats[ourName];
            
            let popupContent = `<h4>${{geojsonName}}</h4>`;
            
            if (stats) {{
                popupContent += `
                    <p><strong>Safety Score:</strong> ${{stats.safety_score.toFixed(1)}}/10</p>
                    <p><strong>Recent Crime Rate:</strong> ${{stats.crime_rate.toFixed(1)}} per 1,000</p>
                    <p><strong>Total Recent Crimes:</strong> ${{stats.total_crimes}}</p>
                    <p style="margin-top: 10px;"><em>Click neighborhood in calculator for detailed analysis</em></p>
                `;
            }} else {{
                popupContent += '<p>No safety data available</p>';
            }}
            
            layer.bindPopup(popupContent);
            
            // Click to select in calculator
            layer.on('click', function() {{
                document.getElementById('neighborhood').value = ourName;
                calculateSafety();
            }});
        }}
        
        function mapNeighborhoodName(geojsonName) {{
            const nameMapping = {{
                'The Port': 'The Port',
                'Neighborhood Nine': 'Baldwin',
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
                'Baldwin': 'Baldwin'
            }};
            return nameMapping[geojsonName] || geojsonName;
        }}
        
        function calculateSafety() {{
            const neighborhood = document.getElementById('neighborhood').value;
            const hour = parseInt(document.getElementById('time').value);
            const dayOfWeek = parseInt(document.getElementById('day').value);
            const transport = document.getElementById('transport').value;
            
            if (!neighborhood) {{
                alert('Please select a neighborhood');
                return;
            }}
            
            const stats = neighborhoodStats[neighborhood];
            if (!stats) {{
                alert('No data available for this neighborhood');
                return;
            }}
            
            // Calculate factors
            const baseScore = stats.safety_score;
            const timeMultiplier = calculateTimeMultiplier(hour, dayOfWeek);
            const transportMultiplier = calculateTransportMultiplier(transport);
            
            // Final score calculation
            let finalScore = baseScore;
            
            // Apply time factor (more dangerous times reduce score)
            if (timeMultiplier > 1.0) {{
                finalScore = finalScore * (2.0 - timeMultiplier); // Reduce score
            }} else {{
                finalScore = Math.min(10, finalScore * (1 + (1.0 - timeMultiplier) * 0.3)); // Slight boost
            }}
            
            // Apply transport factor (safer transport modes boost score)
            finalScore = Math.min(10, finalScore + (1.0 - transportMultiplier) * 2);
            
            // Ensure score stays in 0-10 range
            finalScore = Math.max(0, Math.min(10, finalScore));
            
            // Display results
            displayResults(finalScore, baseScore, timeMultiplier, transportMultiplier, stats, neighborhood);
        }}
        
        function calculateTimeMultiplier(hour, dayOfWeek) {{
            let timeFactor;
            if (hour >= 6 && hour <= 17) {{
                timeFactor = 0.7; // Daytime
            }} else if (hour >= 18 && hour <= 22) {{
                timeFactor = 1.0; // Evening
            }} else {{
                timeFactor = 1.8; // Late night
            }}
            
            const dayFactor = (dayOfWeek === 5 || dayOfWeek === 6) ? 1.2 : 0.9; // Weekend vs weekday
            return timeFactor * dayFactor;
        }}
        
        function calculateTransportMultiplier(mode) {{
            const multipliers = {{
                'walking': 1.0,
                'biking': 0.8,
                'driving': 0.3,
                'public_transit': 0.6
            }};
            return multipliers[mode] || 1.0;
        }}
        
        function displayResults(finalScore, baseScore, timeMultiplier, transportMultiplier, stats, neighborhood) {{
            // Show results panel
            document.getElementById('safety-results').style.display = 'block';
            document.getElementById('no-results').style.display = 'none';
            
            // Update score display
            const scoreElement = document.getElementById('score-number');
            const labelElement = document.getElementById('score-label');
            const containerElement = document.getElementById('safety-score-display');
            
            scoreElement.textContent = finalScore.toFixed(1);
            
            // Update score styling
            containerElement.className = 'safety-score';
            if (finalScore >= 8) {{
                containerElement.classList.add('score-excellent');
                labelElement.textContent = 'Excellent Safety';
            }} else if (finalScore >= 6) {{
                containerElement.classList.add('score-good');
                labelElement.textContent = 'Good Safety';
            }} else if (finalScore >= 4) {{
                containerElement.classList.add('score-moderate');
                labelElement.textContent = 'Moderate Safety';
            }} else {{
                containerElement.classList.add('score-poor');
                labelElement.textContent = 'Use Caution';
            }}
            
            // Update breakdown
            document.getElementById('base-score').textContent = baseScore.toFixed(1);
            document.getElementById('time-factor').textContent = timeMultiplier.toFixed(2) + 'x';
            document.getElementById('day-factor').textContent = '-';
            document.getElementById('transport-factor').textContent = transportMultiplier.toFixed(2) + 'x';
            document.getElementById('total-crimes').textContent = stats.total_crimes;
            document.getElementById('crime-rate').textContent = stats.crime_rate.toFixed(1);
            
            // Generate recommendations
            generateRecommendations(finalScore, timeMultiplier, transportMultiplier, neighborhood);
        }}
        
        function generateRecommendations(score, timeMultiplier, transportMultiplier, neighborhood) {{
            let recommendations = [];
            
            if (score >= 8) {{
                recommendations.push("This is a very safe area with low crime rates.");
            }} else if (score >= 6) {{
                recommendations.push("This area has good safety levels with moderate precautions needed.");
            }} else if (score >= 4) {{
                recommendations.push("Exercise normal safety precautions in this area.");
            }} else {{
                recommendations.push("Consider extra safety measures or alternative routes if possible.");
            }}
            
            if (timeMultiplier > 1.5) {{
                recommendations.push("Late night hours significantly increase risk. Consider traveling during daytime if possible.");
            }} else if (timeMultiplier > 1.2) {{
                recommendations.push("Evening and weekend hours have slightly higher risk levels.");
            }}
            
            if (transportMultiplier === 1.0) {{
                recommendations.push("Walking: Stay alert, stick to well-lit areas, and consider traveling with others.");
            }} else if (transportMultiplier === 0.8) {{
                recommendations.push("Biking: Use bike lanes when available and ensure good lighting/visibility.");
            }} else if (transportMultiplier === 0.6) {{
                recommendations.push("Public transit: Generally safe, but stay aware at stops and stations.");
            }} else if (transportMultiplier === 0.3) {{
                recommendations.push("Driving: Safest option with minimal exposure to street-level risks.");
            }}
            
            document.getElementById('recommendation-text').innerHTML = recommendations.map(r => `<p>• ${{r}}</p>`).join('');
        }}
        
        // Initialize map when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initializeMap();
        }});
    </script>
</body>
</html>
    '''
    
    # Save the HTML file
    with open('safety_calculator.html', 'w') as f:
        f.write(html_content)
    
    print("Safety Calculator saved as safety_calculator.html")
    print(f"\\nNeighborhood safety scores calculated:")
    for name, stats in neighborhood_stats.items():
        print(f"  {name}: {stats['safety_score']:.1f}/10 (Rate: {stats['crime_rate']:.1f}/1000)")


def main():
    """Generate the safety calculator page."""
    create_safety_calculator_page()


if __name__ == "__main__":
    main()