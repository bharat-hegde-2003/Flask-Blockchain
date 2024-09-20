import os
import logging
import requests
from flask import Flask, render_template, redirect, url_for, request, jsonify, session, abort
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from flask_migrate import Migrate
from models import db, Data, BlockchainLog, VolunteerProject, Volunteer, User
from forms import ModelDataForm, VolunteerProjectForm, VolunteerForm
from blockchain import Blockchain
from config import Config

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy and Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Logging setup
logger = logging.getLogger(__name__)

# Create the database and tables if they don't exist
with app.app_context():
    db.create_all()

# Peer-to-Peer Network Functions
peers = []

def add_peer(peer_url):
    if peer_url not in peers:
        peers.append(peer_url)

def broadcast_new_block(block):
    for peer in peers:
        try:
            requests.post(f'{peer}/new_block/', json={'block': block})
        except Exception as e:
            logger.error(f"Error broadcasting block to {peer}: {e}")

def get_blockchain_from_peer(peer):
    try:
        response = requests.get(f'{peer}/blockchain/')
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to retrieve blockchain from {peer}: {e}")
        return None

# Blockchain-Related Routes
@app.route('/blockchain', methods=['GET'])
def blockchain_view():
    blockchain_chain = BlockchainLog.load_blockchain()
    blocks = blockchain_chain if blockchain_chain else []
    return render_template('blockchain_view.html', blocks=blocks)

def log_action_in_blockchain(data_instance, action):
    blockchain_chain = BlockchainLog.load_blockchain()
    blockchain = Blockchain()
    blockchain.chain = blockchain_chain

    blockchain.new_transaction(
        name=data_instance.name,
        method=data_instance.method,
        amount=float(data_instance.amount),
        card_num=data_instance.card_num,
        date=data_instance.date,
        action=action,
    )

    proof = blockchain.proof_of_work(blockchain.last_block['proof'])
    previous_hash = blockchain.hash(blockchain.last_block)
    block = blockchain.new_block(proof, previous_hash)

    BlockchainLog.save_blockchain(blockchain.chain)
    broadcast_new_block(block)

@app.route('/blockchain_json', methods=['GET'])
def blockchain_json():
    blockchain_chain = BlockchainLog.load_blockchain()
    blocks = blockchain_chain if blockchain_chain else []
    return jsonify({'blocks': blocks})

@app.route('/compare_blockchain_with_data', methods=['GET'])
def compare_blockchain_with_data():
    blockchain_chain = BlockchainLog.load_blockchain()
    differences = []

    for block in blockchain_chain:
        for transaction in block['transactions']:
            try:
                data_instance = Data.query.filter_by(
                    name=transaction['name'],
                    method=transaction['method'],
                    amount=transaction['amount'],
                    card_num=transaction['card_num'],
                    date=transaction['date']
                ).one()
            except NoResultFound:
                differences.append({
                    'status': 'Missing in Database',
                    'transaction': transaction,
                    'database': None,
                    'altered_fields': None
                })
                continue
            except MultipleResultsFound:
                return abort(500, 'Multiple objects found for the query.')

            altered_fields = []
            if data_instance.name != transaction['name']:
                altered_fields.append(('name', transaction['name'], data_instance.name))
            if data_instance.method != transaction['method']:
                altered_fields.append(('method', transaction['method'], data_instance.method))
            if float(data_instance.amount) != transaction['amount']:
                altered_fields.append(('amount', transaction['amount'], data_instance.amount))
            if data_instance.card_num != transaction['card_num']:
                altered_fields.append(('card_num', transaction['card_num'], data_instance.card_num))
            if data_instance.date != transaction['date']:
                altered_fields.append(('date', transaction['date'], data_instance.date))

            if altered_fields:
                differences.append({
                    'status': 'Altered Data',
                    'transaction': transaction,
                    'database': {
                        'name': data_instance.name,
                        'method': data_instance.method,
                        'amount': data_instance.amount,
                        'card_num': data_instance.card_num,
                        'date': data_instance.date,
                    },
                    'altered_fields': altered_fields
                })

    return render_template('compare.html', differences=differences)

# Form Handling Routes
@app.route('/formhandle', methods=['GET', 'POST'])
def formhandle():
    form = ModelDataForm()
    if form.validate_on_submit():
        data_instance = Data(
            name=form.name.data,
            method=form.method.data,
            amount=form.amount.data,
            card_num=form.card_num.data,
            date=form.date.data
        )
        db.session.add(data_instance)
        db.session.commit()
        log_action_in_blockchain(data_instance, 'create')  # Log action
        return redirect(url_for('show'))
    return render_template('data.html', form=form)

@app.route('/show', methods=['GET'])
def show():
    data = Data.query.all()
    return render_template('show.html', data=data)

# User Registration and Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = User(username=username, password=password, email=email)
        user.save()
        return render_template('registration_success.html', user=user)
    return render_template('register.html')

@app.route('/show_keys/<int:user_id>', methods=['GET'])
def show_keys(user_id):
    user = User.query.get(user_id)
    return render_template('registration_success.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.authenticate(username=username, password=password)
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password", 400

    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout_view():
    session.clear()
    return redirect(url_for('login_view'))

# Volunteer Management Routes
@app.route('/volunteer_dashboard', methods=['GET'])
def volunteer_dashboard():
    projects = VolunteerProject.query.all()
    return render_template('volunteer_dashboard.html', projects=projects)

@app.route('/enlist_project', methods=['GET', 'POST'])
def enlist_project():
    form = VolunteerProjectForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            project = VolunteerProject(
                title=form.title.data,
                description=form.description.data,
                date=form.date.data
            )
            db.session.add(project)
            db.session.commit()
            return redirect(url_for('volunteer_dashboard'))
    return render_template('enlist_project.html', form=form)

@app.route('/volunteer_list/<int:project_id>', methods=['GET'])
def volunteer_list(project_id):
    project = VolunteerProject.query.get_or_404(project_id)
    volunteers = Volunteer.query.filter_by(project=project).all()
    return render_template('volunteer_list.html', project=project, volunteers=volunteers)

@app.route('/volunteer_project_detail/<int:project_id>', methods=['GET'])
def volunteer_project_detail(project_id):
    project = VolunteerProject.query.get_or_404(project_id)
    return render_template('volunteer_project_detail.html', project=project)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    total_projects = VolunteerProject.query.count()
    total_data = Data.query.count()
    blockchain_chain = BlockchainLog.load_blockchain()
    total_blocks = len(blockchain_chain)

    return render_template('dashboard.html', total_projects=total_projects, total_data=total_data, total_blocks=total_blocks)

@app.route('/retrieve_data', methods=['GET'])
def retrieve_data():
    data = Data.query.all()
    return render_template('data_retrieve.html', data=data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
