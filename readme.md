# 🌤️ Weather Now  
### Real-time weather for any city — instantly, accurately, beautifully

---

## ✨ Why Weather Now?

- **Type any city** → Get weather in 2 seconds  
- **Zero setup** — just `pip install` and run  
- **Professional-grade data** from Europe’s #1 weather model ([ECMWF IFS 0.25°](https://open-meteo.com/))  
- **Human-readable output** — no confusing numbers  

---

## 🌍 Works Everywhere

From **Indore** to **Iceland**, **Tokyo** to **Toronto** — just type the city name!  
*(Uses OpenStreetMap for geocoding + Open-Meteo for weather)*

---

## 🖥️ Sample Output

```text
============================================================
-------------------------------------------------------------
Weather Stats for - PARIS  || 2024-06-15 19:00:00
-------------------------------------------------------------
Current Temperature   : 22.40 deg C
Current Weather Desc  : Partly cloudy
Current Humidity      : 65 %
Current Wind Speed    : 14.2 kmph
Current Rain          : 0.0 mm
Visibility            : 25.0 km
Country               : France
====================================================
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install openmeteo-requests requests-cache retry-requests geopy
```

### 2. Run the app
```bash
python weather.py
```

### 3. Type a city name
```
Enter city name: Mumbai
```

---

## 📦 What You Get

- **Temperature**: Actual + "Feels Like" (°C)  
- **Conditions**: Rain, thunderstorms, fog, snow, etc.  
- **Wind & Visibility**: Speed (kmph) + visibility (km)  
- **Local Time**: Auto-detected timezone  
- **Country**: Auto-resolved from coordinates  

---

## 🔗 Data Sources

- **Weather Data**: [Open-Meteo](https://open-meteo.com/) (ECMWF IFS model)  
- **Geocoding**: [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)  

> 💡 **All data is free for non-commercial use with attribution.**

---

## 📜 License

**MIT License** — free to use, modify, and share!
```