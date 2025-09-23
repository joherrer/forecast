import os
from datetime import datetime

from flask import Flask, render_template, redirect, flash, url_for, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from helpers import login_required, get_forecast_info

# Load environment variables from .env file
load_dotenv()

# Configure application
app = Flask(__name__)

# Set up secret key 
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configure session to use filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
Session(app)

# Configure database with SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'forecast.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define users database model (table)
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    
    # Stablish relationship with favorites
    favorites = relationship('Favorites', back_populates='user')
    
# Define favorites database model (table)
class Favorites(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot = db.Column(db.String(80), nullable=False)
    
    # Stablish relationship with users
    user = relationship('Users', back_populates='favorites')
    
# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'no-cache'
    return response

# Filter convert timestamp to datetime return just hour
@app.template_filter('datetime_hour')
def timestamp_to_datetime_hour(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    hour = dt.strftime('%I %p').lower()
    if hour.startswith('0'):
        hour = hour[1:]
    return hour

# Filter convert degrees into cardinal and display arrow
@app.template_filter('cardinal_direction')
def degrees_to_cardinal(degrees):
    directions = ['N ↓', 'NNE ↙', 'NE ↙', 'ENE ↙', 'E ←', 'ESE ↖', 'SE ↖', 'SSE ↖',
                  'S ↑', 'SSW ↗', 'SW ↗', 'WSW ↗', 'W →', 'WNW ↘', 'NW ↘', 'NNW ↘']
    index = round(degrees / 22.5) % 16
    return directions[index]

# Dictionary spot names with id
spots = {
    'The Spit': '5d81295f9f26b100014e2eee', 'Main Beach': '584204204e65fad6a77092ce', 'Surfers Paradise': '584204204e65fad6a77092d0',
    'Broadbeach': '584204204e65fad6a77092d3', 'Mermaid Beach': '584204204e65fad6a77092d5', 'Miami': '5d7c127712781b00019f8799',
    'Burleigh Heads': '5842041f4e65fad6a7708be8', 'Palm Beach': '584204204e65fad6a77092d6', 'Currumbin Alley': '5842041f4e65fad6a7708c2e',
    'Tugun': '584204204e65fad6a77092da', 'Bilinga': '640b8f57606c451c6df13338', 'Kirra': '5842041f4e65fad6a7708be9',
    'Greenmount': '5aea4194cd9646001ab81b0f', 'Rainbow Bay': '584204204e65fad6a77092db', 'Snapper Rocks': '5842041f4e65fad6a7708be5',
    'Duranbah': '5842041f4e65fad6a7708c11'
}

# Homepage route
@app.route('/', methods=['GET', 'POST'])
def index():

    # User reached route via GET (as by clicking a link or via redirect)  
    if request.method == 'GET':
        return render_template('index.html')
   
    # User reached route via POST (as by submitting a form via POST)
    else:
        return redirect(url_for('index'))
      
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():

    # Forget any user
    session.clear()
    
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == 'GET':

        # Check for error messages in the URL
        error_message = request.args.get('error')

        return render_template('login.html', error=error_message)
      
    # User reached route via POST (as by submitting a form via POST)
    else:
        
        # Ensure username was submitted
        username = request.form.get('username').strip()
        if not username:
            return redirect(url_for('login', error='Must provide username'))
        
        # Ensure password was submitted
        password = request.form.get('password')
        if not password:
            return redirect(url_for('login', error='Must provide password'))
        
        # Query database for username
        user = Users.query.filter_by(username=username.strip()).first()
        
        # Ensure username exists and password is correct
        if user is None:
            return redirect(url_for('login', error='Invalid username'))

        elif not check_password_hash(user.hash, password):
            return redirect(url_for('login', error='Invalid password'))
        
        # Remember which user has logged in
        session['user_id'] = user.id

        # Redirect user to homepage
        return redirect(url_for('index'))
           
# Register route 
@app.route('/register', methods=['GET', 'POST'])
def register():   

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == 'GET':
        return render_template('register.html')    
    
    # User reached route via POST (as by submitting a form via POST)
    else:
        
        # Ensure username was submitted
        username = request.form.get('username').strip()
        if not username:
            flash('Must provide username', 'warning')
            return redirect(url_for('register'))
        
        # Ensure password and confirmation was submitted and match
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
        
        # Query for usernames if exist in database
        user = Users.query.filter_by(username=username.strip()).first()
        
        # Ensure username do not exists
        if user:
            flash('Username already exists', 'warning')
            return redirect(url_for('register'))
        
        # Create password hashed
        password_hashed = generate_password_hash(password)
        
        # Create new user object and add it to the SQLAlchemy session
        new_user = Users(username=username, hash=password_hashed)
        db.session.add(new_user)
        db.session.commit()
        
        # Set the user id in the session
        session['user_id'] = new_user.id
        
        # Redirect user to homepage
        return redirect(url_for('index'))     
       
# Logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    
    #Forget any username
    session.clear()
    
    # Redirect user to homepage
    return redirect(url_for('index'))
                      
# Spots route
@app.route('/spots', methods=['GET', 'POST'])
def spots_route():  
    
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == 'GET':
        return render_template('spots.html', spots=spots)
    
    # User reached route via POST (as by submitting a form via POST)
    else:
        return redirect(url_for('spots_route'))

# Spot forecast route
@app.route('/spots/<spot_route>', methods=['GET', 'POST'])
def spot_forecast(spot_route):
    
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == 'GET':
        
        # Get spot name, check if in spots and use data for forecast
        spot_name = spot_route.replace('_', ' ').title()
        if spot_name in spots:
            id = spots[spot_name]
            wave_info = get_forecast_info('wave', id)
            wind_info = get_forecast_info('wind', id)
            weather_info = get_forecast_info('weather', id)
            conditions_info = get_forecast_info('conditions', id)
            current_date = datetime.now().strftime('%a, %d %B %Y')
            return render_template('forecast.html', spot_name=spot_name, document_wave=wave_info, document_wind=wind_info, document_weather=weather_info , document_conditions=conditions_info, current_date=current_date)
        
        # If spot not in spots dictionary    
        else:
            flash('Spot not found', 'warning')
            return redirect(url_for('spots_route'))

    # User reached route via POST (as by submitting a form via POST)
    else:
        return redirect(url_for('spots_route'))

# Favorites route
@app.route('/favorites', methods=['GET', 'POST'])
@login_required
def favorites():
    
    # Get user id
    user_id = session['user_id']
    
    # Get favorite spots from user
    favorites_table = Favorites.query.filter_by(user_id=user_id).all()
    
    # Extract spot values from favorites table
    spots_fav = [favorite.spot for favorite in favorites_table]
        
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == 'GET':
        return render_template('favorites.html', spots=spots, spots_fav=spots_fav)
    
    # User reached route via POST (as by submitting a form via POST)
    else:
             
        # Redirect to favorites page
        return redirect(url_for('favorites'))
    
# Add route
@app.route('/add', methods=['POST'])
@login_required
def add():
     
    # Get user id
    user_id = session['user_id']
    
    # Ensure a spot its being selected
    spot = request.form.get('spot')    
    if not spot:
        flash('Must select spot to add', 'warning')
        return redirect(url_for('favorites'))
    
    # Check if the spot already exists in favorites
    existing_favorite = Favorites.query.filter_by(user_id=user_id, spot=spot).first()
    if existing_favorite:
        flash('Spot already exists', 'warning')
        return redirect(url_for('favorites'))

    # Create a new Favorites object and add it to the session
    new_favorite = Favorites(user_id=user_id, spot=spot)
    db.session.add(new_favorite)
    db.session.commit()

    # Display confirmation message
    flash('Spot added to favorites', 'success')
    
    # Redirect to favorites page
    return redirect(url_for('favorites'))

# Remove route
@app.route('/remove', methods=['POST'])
@login_required
def remove():

    # Get user id
    user_id = session['user_id']

    # Ensure spotfav is being selected
    spotfav = request.form.get('spotfav')    
    if not spotfav:
        flash('Must select spot to remove', 'warning')
        return redirect(url_for('favorites'))
    
    # Ensure spotfav is in favorites
    removing_spot = Favorites.query.filter_by(user_id=user_id, spot=spotfav).first()
    if not removing_spot:
        flash('Spot not found in favorites', 'warning')
        return redirect(url_for('favorites'))
    
    # Delete spot from favorites
    db.session.delete(removing_spot)
    db.session.commit()
    
    # Display confirmation message
    flash('Spot removed from favorites', 'success')

    # Redirect to favorites page
    return redirect(url_for('favorites'))
      
# Python run command opens app  
if __name__ == '__main__':
    app.run(debug=True)
