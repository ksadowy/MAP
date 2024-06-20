from flask import Flask, render_template, request, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import random
import difflib
import os

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['POST'])
def login():
    # Logic for user login goes here
    return redirect(url_for('genre_playlist'))

@app.route('/register', methods=['POST'])
def register():
    # Logic for user registration goes here
    return redirect(url_for('genre_playlist'))

@app.route('/genre_playlist')
def genre_playlist():
    return render_template('genre_playlist.html')

@app.route('/generate_genre_playlist', methods=['POST'])
def generate_genre_playlist():
    num_songs = int(request.form['num_songs'])
    genre = request.form['genre']
    playlist_url, suggested_genre = create_playlist(num_songs, genre)

    if playlist_url:
        return render_template('genre_playlist.html', genre_playlist_url=playlist_url)
    elif suggested_genre:
        return render_template('genre_playlist.html', genre_error=f"Did you mean '{suggested_genre}'?", genre_input=genre)
    else:
        return render_template('genre_playlist.html', genre_error=f"No tracks found for genre: {genre}")

@app.route('/login_register')
def login_register():
    return render_template('login_register.html')

if __name__ == '__main__':
    app.run(debug=True)