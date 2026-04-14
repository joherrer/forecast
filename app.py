import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import get_forecast_info, login_required

# Load environment variables from .env file.
load_dotenv()

# Configure application.
app = Flask(__name__)

# Set up secret key.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise RuntimeError('SECRET_KEY is required.')

# Configure server-side sessions.
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
Session(app)

# Enable CSRF protection.
csrf = CSRFProtect(app)

# Configure database with SQLAlchemy.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(basedir, 'forecast.db'),
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    favorites = relationship('Favorites', back_populates='user')
    
class Favorites(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot = db.Column(db.String(80), nullable=False)
    user = relationship('Users', back_populates='favorites')
    
# Create database tables if they don't exist.
with app.app_context():
    db.create_all()

# Disable client-side caching for dynamic pages.
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'no-cache'
    return response

@app.template_filter('datetime_hour')
def timestamp_to_datetime_hour(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    hour = dt.strftime('%I %p').lower()
    if hour.startswith('0'):
        hour = hour[1:]
    return hour

@app.template_filter('cardinal_direction')
def degrees_to_cardinal(degrees):
    directions = ['N ↓', 'NNE ↙', 'NE ↙', 'ENE ↙', 'E ←', 'ESE ↖', 'SE ↖', 'SSE ↖',
                  'S ↑', 'SSW ↗', 'SW ↗', 'WSW ↗', 'W →', 'WNW ↘', 'NW ↘', 'NNW ↘']
    index = round(degrees / 22.5) % 16
    return directions[index]

# Spot names mapped to Surfline spot IDs.
spots = {
    'The Spit': '5d81295f9f26b100014e2eee',
    'Main Beach': '584204204e65fad6a77092ce',
    'Surfers Paradise': '584204204e65fad6a77092d0',
    'Broadbeach': '584204204e65fad6a77092d3',
    'Mermaid Beach': '584204204e65fad6a77092d5',
    'Miami': '5d7c127712781b00019f8799',
    'Burleigh Heads': '5842041f4e65fad6a7708be8',
    'Palm Beach': '584204204e65fad6a77092d6',
    'Currumbin Alley': '5842041f4e65fad6a7708c2e',
    'Tugun': '584204204e65fad6a77092da',
    'Bilinga': '640b8f57606c451c6df13338',
    'Kirra': '5842041f4e65fad6a7708be9',
    'Greenmount': '5aea4194cd9646001ab81b0f',
    'Rainbow Bay': '584204204e65fad6a77092db',
    'Snapper Rocks': '5842041f4e65fad6a7708be5',
    'Duranbah': '5842041f4e65fad6a7708c11',
}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')
      
@app.route('/login', methods=['GET', 'POST'])
def login():

    # Visiting the login page always logs out any existing user session.
    if request.method == 'GET':
        session.clear()
        error_message = request.args.get('error')
        return render_template('login.html', error=error_message)
      
    username = (request.form.get('username') or '').strip()
    if not username:
        return redirect(url_for('login', error='Must provide username'))
    
    password = request.form.get('password')
    if not password:
        return redirect(url_for('login', error='Must provide password'))
    
    user = Users.query.filter_by(username=username).first()
    if user is None or not check_password_hash(user.hash, password):
        return redirect(url_for('login', error='Invalid username or password'))
    
    session['user_id'] = user.id
    return redirect(url_for('index'))
           
@app.route('/register', methods=['GET', 'POST'])
def register():   
    if request.method == 'GET':
        return render_template('register.html')    
    
    username = (request.form.get('username') or '').strip()
    if not username:
        flash('Must provide username', 'warning')
        return redirect(url_for('register'))
    
    password = request.form.get('password')
    if not password:
        flash('Must provide password', 'warning')
        return redirect(url_for('register'))
    
    confirmation = request.form.get('confirmation')
    if not confirmation:
        flash('Must confirm password', 'warning')
        return redirect(url_for('register'))
    
    if password != confirmation:
        flash('Passwords do not match', 'warning')
        return redirect(url_for('register'))
    
    user = Users.query.filter_by(username=username).first()
    if user:
        flash('Username already exists', 'warning')
        return redirect(url_for('register'))
    
    password_hashed = generate_password_hash(password)
    new_user = Users(username=username, hash=password_hashed)
    db.session.add(new_user)
    db.session.commit()
    
    session['user_id'] = new_user.id
    return redirect(url_for('index'))
       
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))
                      
@app.route('/spots', methods=['GET'])
def spots_route():  
    return render_template('spots.html', spots=spots)

@app.route('/spots/<spot_route>', methods=['GET'])
def spot_forecast(spot_route):

    # Convert URL value to match dictionary keys.
    spot_name = spot_route.replace('_', ' ').title()
    spot_id = spots.get(spot_name)
    if not spot_id:
        flash('Spot not found', 'warning')
        return redirect(url_for('spots_route'))

    wave = get_forecast_info('wave', spot_id)
    wind = get_forecast_info('wind', spot_id)
    weather = get_forecast_info('weather', spot_id)
    conditions = get_forecast_info('conditions', spot_id)
    current_date = datetime.now().strftime('%a, %d %B %Y')

    return render_template(
        'forecast.html',
        spot_name=spot_name,
        wave=wave,
        wind=wind,
        weather=weather,
        conditions=conditions,
        current_date=current_date
    )

@app.route('/favorites', methods=['GET', 'POST'])
@login_required
def favorites():
    user_id = session['user_id']
    if request.method == 'POST':
        # Use one POST route and branch by action to keep form handling in one place.
        action = request.form.get('action')

        if action == 'add':
            spot = request.form.get('spot')
            if not spot:
                flash('Must select spot to add', 'warning')
                return redirect(url_for('favorites'))

            existing_favorite = Favorites.query.filter_by(user_id=user_id, spot=spot).first()
            if existing_favorite:
                flash('Spot already exists', 'warning')
                return redirect(url_for('favorites'))

            new_favorite = Favorites(user_id=user_id, spot=spot)
            db.session.add(new_favorite)
            db.session.commit()
            flash('Spot added to favorites', 'success')
            return redirect(url_for('favorites'))

        if action == 'remove':
            spot = request.form.get('spot')
            if not spot:
                flash('Must select spot to remove', 'warning')
                return redirect(url_for('favorites'))

            favorite_to_remove = Favorites.query.filter_by(user_id=user_id, spot=spot).first()
            if not favorite_to_remove:
                flash('Spot not found in favorites', 'warning')
                return redirect(url_for('favorites'))

            db.session.delete(favorite_to_remove)
            db.session.commit()
            flash('Spot removed from favorites', 'success')
            return redirect(url_for('favorites'))

        flash('Invalid action.', 'warning')
        return redirect(url_for('favorites'))

    favorites_table = Favorites.query.filter_by(user_id=user_id).all()
    spots_fav = [favorite.spot for favorite in favorites_table]
    return render_template('favorites.html', spots=spots, spots_fav=spots_fav)
      
if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '0') == '1')
