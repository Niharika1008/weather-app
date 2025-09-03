import datetime
import requests
import string
from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debugging prints (can remove later)
print("DEBUG: Project root is", os.getcwd())
print("DEBUG: API key from .env =", os.getenv("OWM_API_KEY"))

# API endpoints
OWM_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_API_ENDPOINT = "http://api.openweathermap.org/geo/1.0/direct"

# Load API key
api_key = os.getenv("OWM_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Home route
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("search")
        return redirect(url_for("get_weather", city=city))
    return render_template("index.html")

# Weather route
@app.route("/<city>", methods=["GET", "POST"])
def get_weather(city):
    city_name = string.capwords(city.strip())
    today = datetime.datetime.now()
    current_date = today.strftime("%A, %B %d")

    # Get latitude/longitude
    location_params = {
        "q": city_name,
        "appid": api_key,
        "limit": 3,
    }

    location_response = requests.get(GEOCODING_API_ENDPOINT, params=location_params)

    if location_response.status_code != 200:
        return render_template("error.html", message="Geocoding API request failed.")

    location_data = location_response.json()

    if not location_data or not isinstance(location_data, list):
        return render_template("error.html", message=f"City '{city_name}' not found.")

    lat = location_data[0].get("lat")
    lon = location_data[0].get("lon")

    if not lat or not lon:
        return render_template("error.html", message=f"Could not find coordinates for '{city_name}'.")

    # Current weather
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }
    weather_response = requests.get(OWM_ENDPOINT, weather_params)
    weather_response.raise_for_status()
    weather_data = weather_response.json()

    current_temp = round(weather_data['main']['temp'])
    current_weather = weather_data['weather'][0]['main']
    min_temp = round(weather_data['main']['temp_min'])
    max_temp = round(weather_data['main']['temp_max'])
    wind_speed = weather_data['wind']['speed']

    # Forecast
    forecast_response = requests.get(OWM_FORECAST_ENDPOINT, weather_params)
    forecast_data = forecast_response.json()

    five_day_temp_list = [
        round(item['main']['temp'])
        for item in forecast_data['list'] if '12:00:00' in item['dt_txt']
    ]
    five_day_weather_list = [
        item['weather'][0]['main']
        for item in forecast_data['list'] if '12:00:00' in item['dt_txt']
    ]

    five_day_unformatted = [
        today,
        today + datetime.timedelta(days=1),
        today + datetime.timedelta(days=2),
        today + datetime.timedelta(days=3),
        today + datetime.timedelta(days=4),
    ]
    five_day_dates_list = [date.strftime("%a") for date in five_day_unformatted]

    return render_template(
        "city.html",
        city_name=city_name,
        current_date=current_date,
        current_temp=current_temp,
        current_weather=current_weather,
        min_temp=min_temp,
        max_temp=max_temp,
        wind_speed=wind_speed,
        five_day_temp_list=five_day_temp_list,
        five_day_weather_list=five_day_weather_list,
        five_day_dates_list=five_day_dates_list,
    )

# Error route
@app.route("/error")
def error():
    message = request.args.get("message", "City not found or invalid input.")
    return render_template("error.html", message=message)

# Run app (local only)
if __name__ == "__main__":
    app.run(debug=True)
