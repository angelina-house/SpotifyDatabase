""" # Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Stormy@0704',
    'database': 'spotify_db'
}

# Spotify authentication configuration
CLIENT_ID = '8b1f1dfdc20e4652933901bb9d7c45a2'
CLIENT_SECRET = 'a8156ca37a6f41fab768c815bcf1b8cf'
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative' """

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database_manager import DatabaseManager
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Stormy@0704',
    'database': 'spotify_db'
}

# Spotify authentication configuration
CLIENT_ID = '8b1f1dfdc20e4652933901bb9d7c45a2'
CLIENT_SECRET = 'a8156ca37a6f41fab768c815bcf1b8cf'
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative'

# Flask app configuration
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session management

# Initialize the database manager
db_manager = DatabaseManager(db_config)

def get_spotify_oauth():
    """Create a SpotifyOAuth instance."""
    return SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=None)  # Disable token caching

@app.route('/login')
def login():
    """Redirect user to Spotify login."""
    session.clear()  # Clear session to ensure fresh login
    auth_manager = get_spotify_oauth()
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle Spotify authentication callback and store access token in session."""
    auth_manager = get_spotify_oauth()
    session.clear()  # Clear any previous session data
    code = request.args.get('code')
    token_info = auth_manager.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('index'))

def get_spotify_client():
    """Get a Spotify client for the current user."""
    if 'token_info' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    token_info = session['token_info']
    if get_spotify_oauth().is_token_expired(token_info):
        token_info = get_spotify_oauth().refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return spotipy.Spotify(auth=token_info['access_token'])

@app.route('/')
def index():
    """Main page with user-specific Spotify playlists."""
    spotify_client = get_spotify_client()
    if not isinstance(spotify_client, spotipy.Spotify):
        return spotify_client  # Redirect to login if client is not authenticated
    playlists = spotify_client.current_user_playlists(limit=50)['items']  # Fetch up to 50 playlists
    tables = db_manager.get_table_names()
    return render_template('index.html', tables=tables, playlists=playlists)

@app.route('/get_playlist_tracks/<playlist_id>', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Return JSON data of tracks in the selected playlist."""
    spotify_client = get_spotify_client()
    if not isinstance(spotify_client, spotipy.Spotify):
        return spotify_client  # Redirect to login if client is not authenticated
    playlist_tracks = spotify_client.playlist_tracks(playlist_id)
    track_details = [{
        'track_name': track['track'].get('name', 'Unknown Name'),
        'artist': (track['track'].get('artists') or [{}])[0].get('name', 'Unknown Artist'),
        'album': track['track'].get('album', {}).get('name', 'Unknown Album'),
        'uri': track['track'].get('uri', 'No URI')
    } for track in playlist_tracks['items'] if track.get('track')]

    return jsonify(track_details)

@app.route('/add_playlist_to_db/<playlist_id>', methods=['POST'])
def add_playlist_to_db(playlist_id):
    """Fetch playlist info and add it to the playlists table."""
    spotify_client = get_spotify_client()
    if not isinstance(spotify_client, spotipy.Spotify):
        return spotify_client  # Redirect to login if client is not authenticated
    playlist = spotify_client.playlist(playlist_id)
    playlist_name = playlist.get('name', 'Unknown Name')
    owner = playlist['owner'].get('display_name', 'Unknown Owner')
    total_tracks = playlist.get('tracks', {}).get('total', 0)

    # Add playlist to the database
    db_manager.add_playlist(playlist_id, playlist_name, owner, total_tracks)

    return jsonify({"status": "success", "message": f"Playlist '{playlist_name}' added to the database!"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=8888)