from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import random
import difflib
import os
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///map.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_link = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope='playlist-modify-private',
                                               cache_path='.cache'))

def create_random_artist_playlist(num_songs, artist_name):
    results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    if not results['artists']['items']:
        return None

    artist_id = results['artists']['items'][0]['id']
    top_tracks = sp.artist_top_tracks(artist_id)['tracks']

    if not top_tracks:
        return None

    selected_tracks = random.sample(top_tracks, min(num_songs, min(20, len(top_tracks))))
    track_ids = [track['id'] for track in selected_tracks]

    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=f'Random {artist_name.capitalize()} Playlist', public=False)
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_ids)

    return playlist['external_urls']['spotify']

def get_available_genres():
    available_genres = sp.recommendation_genre_seeds()['genres']
    return available_genres

def create_playlist(num_songs, genre):
    valid_genres = get_available_genres()
    if genre.lower() not in valid_genres:
        close_matches = difflib.get_close_matches(genre.lower(), valid_genres)
        return None, close_matches[0] if close_matches else None

    results = sp.search(q=f'genre:{genre}', type='track', limit=50)
    tracks = results['tracks']['items']

    if len(tracks) == 0:
        return None, None

    selected_tracks = random.sample(tracks, min(num_songs, len(tracks)))
    track_ids = [track['id'] for track in selected_tracks]

    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=f'Random {genre.capitalize()} Playlist', public=False)
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_ids)

    return playlist['external_urls']['spotify'], None

def save_playlist_to_db(playlist_link, genre, username):
    new_playlist = Playlist(playlist_link=playlist_link, genre=genre, username=username)
    db.session.add(new_playlist)
    db.session.commit()

@app.route('/')
def index():
    return render_template('home.html')

# Log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            db.session.commit()

            session['username'] = username
            session.modified = True
            
            flash('Login successful', 'success')
            return redirect(url_for('generator'))
        
        flash('Invalid username or password', 'danger')
    return render_template('login_register.html', login=True)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Unique username check
        user_username_exists = User.query.filter_by(username=username).first()
        if user_username_exists:
            flash('Username already exists', 'danger')
            return redirect(url_for('login_register'))
        
        # Unique email check
        user_email_exists = User.query.filter_by(email=email).first()
        if user_email_exists:
            flash('Email already in use', 'danger')
            return redirect(url_for('login_register'))
        
        # Email format validation
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            flash('Invalid email address', 'danger')
            return redirect(url_for('login_register'))
        
        # Identical passwords check
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('login_register'))
        
        # Check for strong password
        password_regex = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
        if not re.match(password_regex, password):
            flash('Password must be at least 8 characters long and include a number and a special character', 'danger')
            return redirect(url_for('login_register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')

        return redirect(url_for('login_register'))
    return render_template('login_register.html', register=True)

# Log out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_register'))

@app.route('/generator')
@login_required
def generator():
    return render_template('generator.html')

@app.route('/genre_playlist')
@login_required
def genre_playlist():
    return render_template('genre_playlist.html')

@app.route('/generate_genre_playlist', methods=['POST'])
@login_required
def generate_genre_playlist():
    num_songs = int(request.form['num_songs'])
    genre = request.form['genre']
    playlist_url, suggested_genre = create_playlist(num_songs, genre)

    if playlist_url:
        new_playlist = Playlist(
            playlist_link=playlist_url,
            genre=genre,
            username=current_user.username
        )
        db.session.add(new_playlist)
        db.session.commit()

        return render_template('generator.html', genre_playlist_url=playlist_url)
    elif suggested_genre:
        return render_template('generator.html', genre_error=f"Did you mean '{suggested_genre}'?", genre_input=genre)
    else:
        return render_template('generator.html', genre_error=f"No tracks found for genre: {genre}")

    
@app.route('/randomizer')
@login_required
def randomizer():
    return render_template('randomizer.html')

@app.route('/get_random_playlist', methods=['POST'])
@login_required
def get_random_playlist():
    playlist = Playlist.query.order_by(db.func.random()).first()
    if playlist:
        return render_template('randomizer.html', random_playlist_url=playlist.playlist_link)
    else:
        return render_template('randomizer.html', playlist_error='No playlists available')

@app.route('/login_register')
def login_register():
    return render_template('login_register.html')

if __name__ == '__main__':
    app.run(debug=True)