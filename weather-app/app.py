from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = 'e626199cf7e68f3a8d51cbfe922a9253'

@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None
    forecast = None
    if request.method == 'POST':
        city = request.form['city']
        
        # Current weather
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
        weather = requests.get(weather_url).json()
        
        # 5 day forecast
        forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric'
        forecast_data = requests.get(forecast_url).json()
        
        # Get one reading per day (every 8th reading = 24 hours apart)
        forecast = forecast_data['list'][::8]  # Get every 8th reading for daily forecast
        print(forecast)  # Debugging: Print the forecast data to check its structure
        
    return render_template('index.html', weather=weather, forecast=forecast)

if __name__ == '__main__':
    app.run(debug=True)