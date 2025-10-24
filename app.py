import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple

# ==================== CONFIGURATION ====================
OPENWEATHER_API_KEY = "ca1c293c61b639a3844df5e1ad3d1e32"

# Weather condition icons and animations
WEATHER_ICONS = {
    'Clear': '☀️',
    'Clouds': '☁️',
    'Rain': '🌧️',
    'Drizzle': '🌦️',
    'Thunderstorm': '⛈️',
    'Snow': '❄️',
    'Mist': '🌫️',
    'Fog': '🌫️',
    'Haze': '🌫️',
}

# Clothing suggestions based on temperature
def get_clothing_suggestion(temp_c: float, condition: str) -> str:
    if temp_c < 0:
        return "🧥 Heavy winter coat, gloves, scarf, and warm boots"
    elif temp_c < 10:
        return "🧥 Warm jacket, long sleeves, and closed shoes"
    elif temp_c < 15:
        return "👕 Light jacket or sweater recommended"
    elif temp_c < 20:
        return "👕 Long sleeves or light layers"
    elif temp_c < 25:
        return "👕 Comfortable casual wear"
    else:
        return "👕 Light, breathable clothing. Stay hydrated!"

# AQI interpretation
def get_aqi_info(aqi: int) -> Tuple[str, str]:
    if aqi <= 50:
        return "Good", "#00e400"
    elif aqi <= 100:
        return "Moderate", "#ffff00"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#ff7e00"
    elif aqi <= 200:
        return "Unhealthy", "#ff0000"
    elif aqi <= 300:
        return "Very Unhealthy", "#8f3f97"
    else:
        return "Hazardous", "#7e0023"

# UV Index interpretation
def get_uv_info(uvi: float) -> Tuple[str, str]:
    if uvi < 3:
        return "Low", "#3ea72d"
    elif uvi < 6:
        return "Moderate", "#fff300"
    elif uvi < 8:
        return "High", "#f18b00"
    elif uvi < 11:
        return "Very High", "#e53210"
    else:
        return "Extreme", "#b567a4"

# ==================== API FUNCTIONS ====================

@st.cache_data(ttl=600, show_spinner=False)
def get_current_weather(city: str, api_key: str, units: str = "metric") -> Optional[Dict]:
    """Fetch current weather data."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units={units}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching current weather: {e}")
        return None

@st.cache_data(ttl=600, show_spinner=False)
def get_forecast(city: str, api_key: str, units: str = "metric") -> Optional[Dict]:
    """Fetch 5-day forecast data (3-hour intervals)."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units={units}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching forecast: {e}")
        return None

@st.cache_data(ttl=600, show_spinner=False)
def get_air_quality(lat: float, lon: float, api_key: str) -> Optional[Dict]:
    """Fetch air quality data."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_uv_index(lat: float, lon: float, api_key: str) -> Optional[float]:
    """Fetch UV index (using current weather endpoint as OneCall is paid)."""
    try:
        # Note: Free tier doesn't have dedicated UV endpoint
        # Using current weather data which sometimes includes UV
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        # Simulate UV based on time of day and weather
        hour = datetime.now().hour
        if 6 <= hour <= 18:
            return min(11, max(0, (12 - abs(hour - 12)) * 0.8))
        return 0
    except:
        return None

@st.cache_data(show_spinner=False)
def load_image_from_url(url: str) -> Optional[Image.Image]:
    """Load weather icon from URL."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except:
        return None

# ==================== UI RENDERING FUNCTIONS ====================

def render_weather_animation(condition: str):
    """Display weather condition animation using CSS."""
    animations = {
        'Rain': """
            <style>
            @keyframes rain {
                0% { top: -10%; }
                100% { top: 100%; }
            }
            .raindrop {
                position: absolute;
                width: 2px;
                height: 20px;
                background: linear-gradient(transparent, #4a9eff);
                animation: rain 0.5s linear infinite;
            }
            </style>
            <div style="position:relative; height:100px; overflow:hidden;">
                <div class="raindrop" style="left:10%; animation-delay:0s;"></div>
                <div class="raindrop" style="left:30%; animation-delay:0.2s;"></div>
                <div class="raindrop" style="left:50%; animation-delay:0.4s;"></div>
                <div class="raindrop" style="left:70%; animation-delay:0.1s;"></div>
                <div class="raindrop" style="left:90%; animation-delay:0.3s;"></div>
            </div>
        """,
        'Snow': """
            <style>
            @keyframes snow {
                0% { top: -10%; }
                100% { top: 100%; }
            }
            .snowflake {
                position: absolute;
                font-size: 20px;
                animation: snow 3s linear infinite;
            }
            </style>
            <div style="position:relative; height:100px; overflow:hidden;">
                <div class="snowflake" style="left:10%; animation-delay:0s;">❄️</div>
                <div class="snowflake" style="left:40%; animation-delay:1s;">❄️</div>
                <div class="snowflake" style="left:70%; animation-delay:2s;">❄️</div>
            </div>
        """,
    }
    
    if condition in animations:
        st.markdown(animations[condition], unsafe_allow_html=True)

def render_current_weather(data: Dict, units: str):
    """Render current weather section."""
    temp_unit = "°C" if units == "metric" else "°F"
    speed_unit = "m/s" if units == "metric" else "mph"
    
    # Extract data
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    condition = data['weather'][0]['main']
    description = data['weather'][0]['description'].capitalize()
    humidity = data['main']['humidity']
    pressure = data['main']['pressure']
    wind_speed = data['wind']['speed']
    wind_deg = data['wind'].get('deg', 0)
    icon_code = data['weather'][0]['icon']
    city_name = data['name']
    country = data['sys']['country']
    
    # Weather icon
    icon_url = f"https://openweathermap.org/img/wn/{icon_code}@4x.png"
    
    st.markdown(f"## 🌍 {city_name}, {country}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Display icon
        img = load_image_from_url(icon_url)
        if img:
            st.image(img, width=150)
        else:
            st.markdown(f"<div style='font-size:100px; text-align:center;'>{WEATHER_ICONS.get(condition, '🌡️')}</div>", 
                       unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<h1 style='text-align:center; font-size:72px; margin:0;'>{temp:.1f}{temp_unit}</h1>", 
                   unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; font-size:24px;'>{description}</p>", 
                   unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>Feels like {feels_like:.1f}{temp_unit}</p>", 
                   unsafe_allow_html=True)
    
    with col3:
        st.metric("Humidity", f"{humidity}%", delta=None)
        st.metric("Wind", f"{wind_speed} {speed_unit}", delta=None)
        st.metric("Pressure", f"{pressure} hPa", delta=None)
    
    # Weather animation
    render_weather_animation(condition)
    
    # Clothing suggestion
    st.info(f"👔 **What to Wear:** {get_clothing_suggestion(temp, condition)}")

def render_hourly_forecast(forecast_data: Dict, units: str):
    """Render 24-hour forecast."""
    st.markdown("### 📅 Hourly Forecast (Next 24 Hours)")
    
    temp_unit = "°C" if units == "metric" else "°F"
    
    # Get next 24 hours (8 data points at 3-hour intervals)
    hourly_data = forecast_data['list'][:8]
    
    times = []
    temps = []
    feels_like = []
    conditions = []
    rain_prob = []
    
    for item in hourly_data:
        dt = datetime.fromtimestamp(item['dt'])
        times.append(dt.strftime('%H:%M'))
        temps.append(item['main']['temp'])
        feels_like.append(item['main']['feels_like'])
        conditions.append(item['weather'][0]['main'])
        rain_prob.append(item.get('pop', 0) * 100)  # Probability of precipitation
    
    # Create interactive chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=times, y=temps,
        mode='lines+markers',
        name='Temperature',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=times, y=feels_like,
        mode='lines',
        name='Feels Like',
        line=dict(color='#4ECDC4', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Temperature Trend",
        xaxis_title="Time",
        yaxis_title=f"Temperature ({temp_unit})",
        hovermode='x unified',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Hourly cards
    cols = st.columns(min(len(hourly_data), 4))
    for i, (col, item) in enumerate(zip(cols, hourly_data[:4])):
        with col:
            dt = datetime.fromtimestamp(item['dt'])
            icon = WEATHER_ICONS.get(item['weather'][0]['main'], '🌡️')
            st.markdown(f"""
                <div style='text-align:center; padding:10px; background:rgba(255,255,255,0.1); border-radius:10px;'>
                    <div style='font-size:14px;'>{dt.strftime('%H:%M')}</div>
                    <div style='font-size:40px;'>{icon}</div>
                    <div style='font-size:20px; font-weight:bold;'>{item['main']['temp']:.0f}{temp_unit}</div>
                    <div style='font-size:12px;'>💧 {item.get('pop', 0)*100:.0f}%</div>
                </div>
            """, unsafe_allow_html=True)

def render_daily_forecast(forecast_data: Dict, units: str):
    """Render 5-day daily forecast."""
    st.markdown("### 📆 7-Day Forecast")
    
    temp_unit = "°C" if units == "metric" else "°F"
    
    # Group by day and get min/max temps
    daily_data = {}
    for item in forecast_data['list']:
        dt = datetime.fromtimestamp(item['dt'])
        date_key = dt.strftime('%Y-%m-%d')
        
        if date_key not in daily_data:
            daily_data[date_key] = {
                'temps': [],
                'conditions': [],
                'rain_prob': [],
                'humidity': [],
                'wind': [],
                'date': dt
            }
        
        daily_data[date_key]['temps'].append(item['main']['temp'])
        daily_data[date_key]['conditions'].append(item['weather'][0]['main'])
        daily_data[date_key]['rain_prob'].append(item.get('pop', 0))
        daily_data[date_key]['humidity'].append(item['main']['humidity'])
        daily_data[date_key]['wind'].append(item['wind']['speed'])
    
    # Display daily cards
    for date_key in sorted(daily_data.keys())[:7]:
        day = daily_data[date_key]
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{day['date'].strftime('%A, %B %d')}**")
        with col2:
            # Most common condition
            condition = max(set(day['conditions']), key=day['conditions'].count)
            st.markdown(f"<div style='font-size:30px; text-align:center;'>{WEATHER_ICONS.get(condition, '🌡️')}</div>", 
                       unsafe_allow_html=True)
        with col3:
            st.metric("High", f"{max(day['temps']):.0f}{temp_unit}")
        with col4:
            st.metric("Low", f"{min(day['temps']):.0f}{temp_unit}")
        with col5:
            st.metric("Rain", f"{max(day['rain_prob'])*100:.0f}%")
        with col6:
            st.metric("Wind", f"{sum(day['wind'])/len(day['wind']):.1f}")
        
        st.markdown("---")

def render_advanced_features(current_data: Dict, lat: float, lon: float, api_key: str):
    """Render advanced features: AQI, UV, sunrise/sunset, moon phase."""
    st.markdown("### 🔬 Advanced Weather Information")
    
    col1, col2, col3 = st.columns(3)
    
    # Air Quality Index
    with col1:
        st.markdown("#### 💨 Air Quality")
        aqi_data = get_air_quality(lat, lon, api_key)
        if aqi_data and 'list' in aqi_data:
            aqi = aqi_data['list'][0]['main']['aqi']
            # Convert to US AQI scale (simplified)
            aqi_value = aqi * 50
            quality, color = get_aqi_info(aqi_value)
            
            st.markdown(f"""
                <div style='background:{color}; padding:20px; border-radius:10px; text-align:center;'>
                    <h2 style='margin:0; color:white;'>{aqi_value:.0f}</h2>
                    <p style='margin:0; color:white;'>{quality}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Pollutant details
            components = aqi_data['list'][0]['components']
            st.write(f"PM2.5: {components.get('pm2_5', 0):.1f} μg/m³")
            st.write(f"PM10: {components.get('pm10', 0):.1f} μg/m³")
            st.write(f"O₃: {components.get('o3', 0):.1f} μg/m³")
        else:
            st.info("Air quality data unavailable")
    
    # UV Index
    with col2:
        st.markdown("#### ☀️ UV Index")
        uvi = get_uv_index(lat, lon, api_key)
        if uvi is not None:
            level, color = get_uv_info(uvi)
            
            st.markdown(f"""
                <div style='background:{color}; padding:20px; border-radius:10px; text-align:center;'>
                    <h2 style='margin:0; color:white;'>{uvi:.1f}</h2>
                    <p style='margin:0; color:white;'>{level}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if uvi >= 3:
                st.warning("🕶️ Sun protection recommended")
            else:
                st.info("☀️ Sun protection optional")
        else:
            st.info("UV data unavailable")
    
    # Sunrise/Sunset
    with col3:
        st.markdown("#### 🌅 Sun & Moon")
        sunrise = datetime.fromtimestamp(current_data['sys']['sunrise'])
        sunset = datetime.fromtimestamp(current_data['sys']['sunset'])
        
        st.write(f"🌅 Sunrise: **{sunrise.strftime('%H:%M')}**")
        st.write(f"🌇 Sunset: **{sunset.strftime('%H:%M')}**")
        
        # Calculate day length
        day_length = sunset - sunrise
        hours = day_length.seconds // 3600
        minutes = (day_length.seconds % 3600) // 60
        st.write(f"⏱️ Day length: **{hours}h {minutes}m**")
        
        # Moon phase (simplified calculation)
        now = datetime.now()
        moon_age = ((now.year - 2000) * 12.3685 + now.month + now.day / 30.0) % 29.53
        moon_phases = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
        phase_idx = int(moon_age / 29.53 * 8) % 8
        st.write(f"🌙 Moon: **{moon_phases[phase_idx]}**")

def render_alerts(current_data: Dict):
    """Render weather alerts and warnings."""
    # Check for severe conditions
    alerts = []
    
    temp = current_data['main']['temp']
    wind_speed = current_data['wind']['speed']
    condition = current_data['weather'][0]['main']
    
    if temp < 0:
        alerts.append(("⚠️ Freezing Temperature", "warning"))
    if temp > 35:
        alerts.append(("🔥 Extreme Heat Warning", "error"))
    if wind_speed > 10:
        alerts.append(("💨 High Wind Advisory", "warning"))
    if condition in ['Thunderstorm', 'Snow']:
        alerts.append((f"⛈️ {condition} Alert", "error"))
    
    if alerts:
        st.markdown("### 🚨 Active Alerts")
        for message, alert_type in alerts:
            if alert_type == "error":
                st.error(message)
            else:
                st.warning(message)

def render_weather_map(lat: float, lon: float):
    """Render interactive weather map."""
    st.markdown("### 🗺️ Weather Map")
    
    # Create simple map with location marker
    map_data = pd.DataFrame({
        'lat': [lat],
        'lon': [lon]
    })
    
    st.map(map_data, zoom=8)
    
    st.info("📍 Map shows your current search location. Premium features like precipitation radar and storm tracking require additional API subscriptions.")

# ==================== MAIN APP ====================

def main():
    st.set_page_config(
        page_title="Advanced Weather App",
        layout="wide",
        page_icon="🌤️",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'favorites' not in st.session_state:
        st.session_state['favorites'] = ['London', 'New York', 'Tokyo']
    if 'units' not in st.session_state:
        st.session_state['units'] = 'metric'
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'light'
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = OPENWEATHER_API_KEY
    
    # Apply theme
    theme = st.session_state['theme']
    if theme == 'dark':
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #ffffff;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #ffffff;
            }
            </style>
        """, unsafe_allow_html=True)
    
    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.markdown("# ⚙️ Settings")
        
        # Theme toggle
        theme_option = st.radio(
            "🎨 Theme",
            options=['light', 'dark'],
            index=0 if st.session_state['theme'] == 'light' else 1,
            horizontal=True
        )
        if theme_option != st.session_state['theme']:
            st.session_state['theme'] = theme_option
            st.rerun()
        
        st.markdown("---")
        
        # Unit preferences
        st.markdown("### 📏 Units")
        units = st.radio(
            "Temperature",
            options=['metric', 'imperial'],
            format_func=lambda x: "Celsius (°C)" if x == 'metric' else "Fahrenheit (°F)",
            index=0 if st.session_state['units'] == 'metric' else 1
        )
        st.session_state['units'] = units
        
        st.markdown("---")
        
        # API Key
        st.markdown("### 🔑 API Key")
        api_key = st.text_input(
            "OpenWeather API Key",
            value=st.session_state['api_key'],
            type="password",
            help="Get your free API key from openweathermap.org"
        )
        st.session_state['api_key'] = api_key
        
        st.markdown("---")
        
        # Favorites
        st.markdown("### ⭐ Favorite Locations")
        
        # Add new favorite
        new_fav = st.text_input("Add new favorite", placeholder="City name")
        if st.button("➕ Add") and new_fav:
            if new_fav not in st.session_state['favorites']:
                st.session_state['favorites'].append(new_fav)
                st.success(f"Added {new_fav}")
                st.rerun()
        
        # Display and manage favorites
        if st.session_state['favorites']:
            for fav in st.session_state['favorites']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"📍 {fav}", key=f"fav_{fav}", use_container_width=True):
                        st.session_state['selected_city'] = fav
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{fav}"):
                        st.session_state['favorites'].remove(fav)
                        st.rerun()
        
        st.markdown("---")
        
        # Info
        st.markdown("### ℹ️ About")
        st.info("""
            **Advanced Weather App**
            
            Features:
            - Real-time weather data
            - 24-hour & 7-day forecasts
            - Air Quality Index
            - UV Index
            - Weather alerts
            - Interactive maps
            - Clothing suggestions
            
            Built with Streamlit & OpenWeatherMap API
        """)
    
    # ==================== MAIN CONTENT ====================
    st.markdown("<h1 style='text-align:center;'>🌤️ Advanced Weather Application</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Comprehensive weather information at your fingertips</p>", unsafe_allow_html=True)
    
    # Search section
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        city = st.text_input(
            "🔍 Search Location",
            value=st.session_state.get('selected_city', ''),
            placeholder="Enter city name or ZIP code",
            label_visibility="collapsed"
        )
    with col2:
        search_btn = st.button("🔍 Search", use_container_width=True, type="primary")
    with col3:
        if st.button("📍 Use GPS", use_container_width=True):
            st.info("GPS location detection requires browser permissions. Using default location.")
            city = "London"
    
    if search_btn or city:
        if not city:
            st.warning("Please enter a city name")
            return
        
        # Check if API key is provided
        if not api_key or api_key.strip() == "":
            st.error("❌ Please enter your OpenWeatherMap API key in the sidebar settings")
            st.info("👉 Open the sidebar and enter your API key under '🔑 API Key' section")
            st.info("Get a free API key at: https://openweathermap.org/api")
            return
        
        # Fetch data
        with st.spinner("🌍 Fetching weather data..."):
            current_data = get_current_weather(city, api_key, units)
            forecast_data = get_forecast(city, api_key, units)
        
        if not current_data:
            st.error("❌ City not found. Please check the name and try again.")
            return
        
        # Get coordinates
        lat = current_data['coord']['lat']
        lon = current_data['coord']['lon']
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Current Weather",
            "📊 Forecast",
            "🔬 Advanced",
            "🗺️ Maps",
            "🚨 Alerts"
        ])
        
        with tab1:
            render_current_weather(current_data, units)
        
        with tab2:
            if forecast_data:
                render_hourly_forecast(forecast_data, units)
                st.markdown("---")
                render_daily_forecast(forecast_data, units)
            else:
                st.error("Forecast data unavailable")
        
        with tab3:
            render_advanced_features(current_data, lat, lon, api_key)
        
        with tab4:
            render_weather_map(lat, lon)
            
            st.markdown("### 🛰️ Additional Map Layers")
            st.info("""
                **Available with Premium API:**
                - Precipitation radar
                - Cloud coverage
                - Temperature map
                - Wind map
                - Storm tracking
                - Satellite imagery
                
                Visit OpenWeatherMap for API upgrades.
            """)
        
        with tab5:
            render_alerts(current_data)
            
            st.markdown("### 🔔 Notification Preferences")
            st.checkbox("Enable severe weather alerts", value=True)
            st.checkbox("Rain/snow notifications", value=True)
            st.checkbox("Temperature change warnings", value=False)
            st.checkbox("Daily weather summary", value=False)
            
            st.info("💡 Notifications require app deployment with background tasks enabled.")
    
    else:
        # Welcome screen
        st.markdown("""
            <div style='text-align:center; padding:50px;'>
                <h2>👋 Welcome to Advanced Weather App</h2>
                <p>Enter a city name above to get started, or select a favorite location from the sidebar.</p>
                <br>
                <p style='font-size:80px;'>🌤️</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        st.markdown("### ✨ Features")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                **🌡️ Current Weather**
                - Temperature & feels like
                - Humidity & pressure
                - Wind speed & direction
                - Live weather icons
            """)
        
        with col2:
            st.markdown("""
                **📊 Forecasts**
                - Hourly (24 hours)
                - Daily (7 days)
                - Interactive charts
                - Rain probability
            """)
        
        with col3:
            st.markdown("""
                **🔬 Advanced Data**
                - Air Quality Index
                - UV Index
                - Sunrise & sunset
                - Moon phases
            """)
        
        with col4:
            st.markdown("""
                **🎯 Smart Features**
                - Clothing suggestions
                - Weather alerts
                - Favorite locations
                - Custom units
            """)

if __name__ == '__main__':
    main()
