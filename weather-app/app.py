from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = 'e626199cf7e68f3a8d51cbfe922a9253'

@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None
    if request.method == 'POST':
        city = request.form['city']
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
        response = requests.get(url)
        weather = response.json()
    return render_template('index.html', weather=weather)

if __name__ == '__main__':
    app.run(debug=True)