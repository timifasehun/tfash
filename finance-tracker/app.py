from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE): # If the data file doesn't exist, return an empty list
        return []
    with open(DATA_FILE, 'r') as f: # Open the data file in read mode
        return json.load(f) # read it and convert to Python list
    
def save_data(transactions):
    with open(DATA_FILE, 'w') as f:
        json.dump(transactions, f)
        
@app.route('/')
def home():
    @app.route('/add', methods=['POST'])
    def add_transaction():
        transactions = load_data()
    
        transaction = {
        'type': request.form['type'],
        'category': request.form['category'],
        'description': request.form['description'],
        'amount': float(request.form['amount'])
        }
    
        transactions.append(transaction)
        save_data(transactions)
    
    return redirect('/')

    return render_template('index.html', transactions=transactions) 

if __name__ == '__main__':
    app.run(debug=True)