from flask import Flask, request, render_template_string
import openmeteo_requests
import requests_cache
from retry_requests import retry
from geopy.geocoders import Nominatim
import pytz
import time
from datetime import datetime
import os

app = Flask(__name__)

# Simple HTML template (embedded for simplicity)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather App</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; padding: 20px; }
        input[type="text"] { width: 70%; padding: 8px; font-size: 16px; }
        button { padding: 8px 16px; font-size: 16px; margin-left: 10px; }
        .error { color: red; }
        .result { background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 5px; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <h1>🌤️ Weather Lookup</h1>
    <form method="GET">
        <input type="text" name="city" placeholder="Enter city name (e.g., London)" value="{{ city or '' }}" required>
        <button type="submit">Get Weather</button>
    </form>

    {% if error %}
        <div class="error"><strong>Error:</strong> {{ error }}</div>
    {% endif %}

    {% if result %}
        <div class="result">
            <h2>Weather Status for - {{ city.upper() }} || {{ result.date_time }}</h2>
            <p><strong>Current Temperature:</strong> {{ "%.2f"|format(result.temp_city) }} °C</p>
            <p><strong>Current Weather:</strong> {{ result.weather_desc }}</p>
            <p><strong>Humidity:</strong> {{ result.hmdt }}%</p>
            <p><strong>Wind Speed:</strong> {{ "%.1f"|format(result.wind_spd) }} km/h</p>
            <p><strong>Rain:</strong> {{ "%.1f"|format(result.rain) }} mm</p>
            <p><strong>Visibility:</strong> {{ "%.1f"|format(result.visibility_km) }} km</p>
            <p><strong>Country:</strong> {{ result.country }}</p>
        </div>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET'])
def weather():
    city = request.args.get('city', '').strip()
    error = None
    result = None

    if city:
        try:
            # === 2. Geocode the city ===
            geolocator = Nominatim(user_agent="weather_app_flask_render")
            location = geolocator.geocode(city)
            if not location:
                raise Exception(f"City '{city}' not found. Please check spelling or try a larger nearby city.")

            lat, lon = location.latitude, location.longitude
            country = location.raw.get('display_name', '').split(',')[-1].strip() if location.raw else "Unknown"

            # === 3. Setup Open-Meteo API ===
            cache_session = requests_cache.CachedSession('.cache', expire_after=1800)
            retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
            openmeteo = openmeteo_requests.Client(session=retry_session)

            # === 4. Fetch HOURLY weather data ===
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "rain",
                    "weather_code",
                    "apparent_temperature",
                    "visibility",
                    "wind_speed_10m"
                ],
                "timezone": "auto",
                "forecast_days": 1
            }

            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]

            # === 5–7. Extract & find current data ===
            hourly = response.Hourly()
            start_time = hourly.Time()
            interval = hourly.Interval()

            temp_values = hourly.Variables(0).ValuesAsNumpy()
            n = len(temp_values)
            time_list = [start_time + i * interval for i in range(n)]

            now = int(time.time())
            current_idx = 0
            for i in range(n):
                if time_list[i] <= now:
                    current_idx = i
                else:
                    break

            temp_city = float(temp_values[current_idx])
            hmdt = int(round(float(hourly.Variables(1).ValuesAsNumpy()[current_idx])))
            rain = float(hourly.Variables(2).ValuesAsNumpy()[current_idx])
            wmo = int(hourly.Variables(3).ValuesAsNumpy()[current_idx])
            apparent = float(hourly.Variables(4).ValuesAsNumpy()[current_idx])
            visibility_km = float(hourly.Variables(5).ValuesAsNumpy()[current_idx]) / 1000
            wind_spd = float(hourly.Variables(6).ValuesAsNumpy()[current_idx])

            # === 8. Weather description ===
            wmo_desc = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                66: "Light freezing rain", 67: "Heavy freezing rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            weather_desc = wmo_desc.get(wmo, "Unknown")

            # === 9. Format local time ===
            utc_offset = response.UtcOffsetSeconds()
            local_time = datetime.fromtimestamp(time_list[current_idx] + utc_offset)
            date_time = local_time.strftime('%Y-%m-%d %H:%M:%S')

            result = {
                'temp_city': temp_city,
                'weather_desc': weather_desc,
                'hmdt': hmdt,
                'wind_spd': wind_spd,
                'rain': rain,
                'visibility_km': visibility_km,
                'country': country,
                'date_time': date_time
            }

        except Exception as e:
            error = str(e)

    return render_template_string(HTML_TEMPLATE, city=city, error=error, result=result)

# Required for Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)