# app.py

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database_manager import DatabaseManager
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from datetime import datetime

# Load environment variables (Recommended for security)
from dotenv import load_dotenv
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'spotify_db')
}

# Spotify authentication configuration
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '8b1f1dfdc20e4652933901bb9d7c45a2')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'a8156ca37a6f41fab768c815bcf1b8cf')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
SCOPE = 'user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative'

# Flask app configuration
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Initialize the database manager
db_manager = DatabaseManager(db_config)

def get_spotify_oauth():
    """Create a SpotifyOAuth instance."""
    return SpotifyOAuth(client_id=CLIENT_ID,
                       client_secret=CLIENT_SECRET,
                       redirect_uri=REDIRECT_URI,
                       scope=SCOPE,
                       cache_path=None)  # Disable token caching

def get_spotify_client(spotify_user_id):
    """Retrieve a Spotify client for the given user."""
    tokens = db_manager.get_user_tokens(spotify_user_id)
    if not tokens:
        return None
    access_token, refresh_token, token_expires_at = tokens

    # Check if the token is expired and refresh if necessary
    if datetime.utcnow() >= token_expires_at:
        sp_oauth = get_spotify_oauth()
        try:
            token_info = sp_oauth.refresh_access_token(refresh_token)
            access_token = token_info['access_token']
            refresh_token = token_info.get('refresh_token', refresh_token)
            expires_at = datetime.fromtimestamp(token_info['expires_at'])

            # Update tokens in the database
            db_manager.add_or_update_user(
                spotify_user_id=spotify_user_id,
                display_name='',  # Optionally, fetch and update the display name
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at
            )
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return None

    return spotipy.Spotify(auth=access_token)

@app.route('/')
def index():
    """Main page with options to view tables or add playlists."""
    tables = db_manager.get_table_names()
    users = db_manager.get_all_users()
    playlists = session.get('playlists')
    user_id = session.get('selected_user')
    return render_template('index.html', tables=tables, users=users, playlists=playlists, user_id=user_id)

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
    if code:
        try:
            token_info = auth_manager.get_access_token(code, as_dict=True)
            access_token = token_info['access_token']
            refresh_token = token_info['refresh_token']
            expires_at = datetime.fromtimestamp(token_info['expires_at'])

            # Initialize Spotify client with the token
            sp = spotipy.Spotify(auth=access_token)
            user_info = sp.current_user()
            spotify_user_id = user_info['id']
            display_name = user_info.get('display_name', spotify_user_id)

            # Save tokens to the database
            db_manager.add_or_update_user(
                spotify_user_id=spotify_user_id,
                display_name=display_name,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at
            )

            # Optionally, select the user and fetch their playlists
            session['selected_user'] = spotify_user_id
            playlists = sp.current_user_playlists(limit=50)['items']
            session['playlists'] = playlists

            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error during authentication callback: {e}")
            return "Authentication failed.", 400
    else:
        return "Authorization failed.", 400

@app.route('/select_user/<spotify_user_id>')
def select_user(spotify_user_id):
    """Select a user to view their playlists."""
    session['selected_user'] = spotify_user_id
    sp = get_spotify_client(spotify_user_id)
    if not sp:
        return "User not authenticated.", 400

    playlists = sp.current_user_playlists(limit=50)['items']
    session['playlists'] = playlists
    return redirect(url_for('index'))

@app.route('/get_playlist_tracks/<playlist_id>', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Return JSON data of tracks in the selected playlist."""
    selected_user = session.get('selected_user')
    if not selected_user:
        return jsonify({"error": "No user selected."}), 400

    sp = get_spotify_client(selected_user)
    if not sp:
        return jsonify({"error": "User not authenticated."}), 400

    try:
        playlist_tracks = sp.playlist_tracks(playlist_id)
        track_details = [{
            'track_name': track['track'].get('name', 'Unknown Name'),
            'artist': (track['track'].get('artists') or [{}])[0].get('name', 'Unknown Artist'),
            'album': track['track'].get('album', {}).get('name', 'Unknown Album'),
            'uri': track['track'].get('uri', 'No URI')
        } for track in playlist_tracks['items'] if track.get('track')]

        return jsonify(track_details)
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return jsonify({"error": "Failed to fetch playlist tracks."}), 500

@app.route('/add_playlist_to_db/<playlist_id>', methods=['POST'])
def add_playlist_to_db(playlist_id):
    """Fetch playlist info and add it to the playlists table."""
    selected_user = session.get('selected_user')
    if not selected_user:
        return jsonify({"error": "No user selected."}), 400

    sp = get_spotify_client(selected_user)
    if not sp:
        return jsonify({"error": "User not authenticated."}), 400

    try:
        # Fetch playlist details
        playlist = sp.playlist(playlist_id)
        playlist_name = playlist.get('name', 'Unknown Name')
        owner = playlist['owner'].get('display_name', 'Unknown Owner')
        total_tracks = playlist.get('tracks', {}).get('total', 0)

        # Add playlist to the database
        db_manager.add_playlist(playlist_id, playlist_name, owner, total_tracks, selected_user)

        # Optionally, add songs to the database
        # Implement logic to fetch and store songs as needed

        return jsonify({"status": "success", "message": f"Playlist '{playlist_name}' added to the database!"})
    except Exception as e:
        print(f"Error adding playlist to database: {e}")
        return jsonify({"error": "Failed to add playlist to database."}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=8888)
