import openmeteo_requests
import requests_cache
from retry_requests import retry
from geopy.geocoders import Nominatim
import pytz
import time
from datetime import datetime

# === 1. Get city name from user ===
city = input("Enter city name: ").strip()
if not city:
    raise ValueError("City name cannot be empty!")

# === 2. Geocode the city ===
print(f"Looking up coordinates for '{city}'...")
geolocator = Nominatim(user_agent="weather_app_user_input")
location = geolocator.geocode(city)

if not location:
    raise Exception(f"City '{city}' not found. Please check spelling or try a larger nearby city.")

lat, lon = location.latitude, location.longitude
country = location.raw.get('display_name', '').split(',')[-1].strip() if location.raw else "Unknown"

print(f"Found: {location.address}")

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
    "timezone": "auto",  # Automatically detect timezone from coordinates
    "forecast_days": 1
}

try:
    responses = openmeteo.weather_api(url, params=params)
except Exception as e:
    raise Exception(f"Failed to fetch weather data: {e}")

response = responses[0]

# === 5. Extract data ===
hourly = response.Hourly()
start_time = hourly.Time()
interval = hourly.Interval()

# Get number of data points from first variable
temp_values = hourly.Variables(0).ValuesAsNumpy()
n = len(temp_values)

# Build time list
time_list = [start_time + i * interval for i in range(n)]

# Helper to convert to list
to_list = lambda x: x.tolist() if hasattr(x, 'tolist') else list(x)

# Extract all variables by index
temp_list        = to_list(temp_values)
hmdt_list        = to_list(hourly.Variables(1).ValuesAsNumpy())
rain_list        = to_list(hourly.Variables(2).ValuesAsNumpy())
wmo_list         = to_list(hourly.Variables(3).ValuesAsNumpy())
apparent_list    = to_list(hourly.Variables(4).ValuesAsNumpy())
visibility_list  = to_list(hourly.Variables(5).ValuesAsNumpy())
wind_list        = to_list(hourly.Variables(6).ValuesAsNumpy())

# === 6. Find latest <= now ===
now = int(time.time())
current_idx = 0
for i in range(n):
    if time_list[i] <= now:
        current_idx = i
    else:
        break

# === 7. Get current values ===
temp_city = float(temp_list[current_idx])
hmdt = int(round(float(hmdt_list[current_idx])))
rain = float(rain_list[current_idx])
wmo = int(wmo_list[current_idx])
apparent = float(apparent_list[current_idx])
visibility_km = float(visibility_list[current_idx]) / 1000  # meters → km
wind_spd = float(wind_list[current_idx])

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

# === 9. Format local date/time ===
utc_offset = response.UtcOffsetSeconds()
local_time = datetime.fromtimestamp(time_list[current_idx] + utc_offset)
date_time = local_time.strftime('%Y-%m-%d %H:%M:%S')

# === 10. Print in your exact format ===
print("\n" + "="*60)
print("-------------------------------------------------------------")
print("Weather Stats for - {}  || {}".format(city.upper(), date_time))
print("-------------------------------------------------------------")
print("Current Temperature   : {:.2f} deg C".format(temp_city))
print("Current Weather Desc  :", weather_desc)
print("Current Humidity      :", hmdt, '%')
print("Current Wind Speed    : {:.1f} kmph".format(wind_spd))
print("Current Rain          : {:.1f} mm".format(rain))
print("Visibility            : {:.1f} km".format(visibility_km))
print("Country               :", country)
print("====================================================")