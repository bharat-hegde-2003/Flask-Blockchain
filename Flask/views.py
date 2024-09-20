from flask import render_template, request, jsonify
from app import app, db
from models import Data, BlockchainLog, User, VolunteerProject, Volunteer, BlockModel

@app.route('/')
def index():
    return "Welcome to the Flask Project"

# Example route to retrieve data
@app.route('/data', methods=['GET'])
def get_data():
    data = Data.query.all()
    return jsonify([{"name": d.name, "method": d.method, "amount": float(d.amount)} for d in data])

# Example route to add new data
@app.route('/data', methods=['POST'])
def add_data():
    name = request.form['name']
    method = request.form['method']
    amount = request.form['amount']
    card_num = request.form['card_num']
    date = request.form['date']

    new_data = Data(name=name, method=method, amount=amount, card_num=card_num, date=date)
    db.session.add(new_data)
    db.session.commit()

    return jsonify({"message": "Data added successfully!"})

# Blockchain save and load routes
@app.route('/blockchain', methods=['GET'])
def load_blockchain():
    blockchain = BlockchainLog.load_blockchain()
    return jsonify(blockchain)

@app.route('/blockchain', methods=['POST'])
def save_blockchain():
    blockchain = request.json.get('blockchain')
    BlockchainLog.save_blockchain(blockchain)
    return jsonify({"message": "Blockchain saved!"})
