# app.py

from flask import Flask, render_template, request, jsonify # type: ignore
from database_manager import DatabaseManager
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore

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
# Define the required scope
SCOPE = 'user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative'


# Initialize the Flask app and database manager
app = Flask(__name__)
db_manager = DatabaseManager(db_config)

# Initialize Spotify client
spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET,
                                                           redirect_uri=REDIRECT_URI,
                                                           scope=SCOPE))

@app.route('/')
def index():
    """Main page with options to view tables or add playlists."""
    tables = db_manager.get_table_names()
    playlists = spotify_client.current_user_playlists(limit=50)['items']  # Fetch up to 50 playlists
    return render_template('index.html', tables=tables, playlists=playlists)

@app.route('/get_playlist_tracks/<playlist_id>', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Return JSON data of tracks in the selected playlist."""
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
    # Fetch playlist details
    playlist = spotify_client.playlist(playlist_id)
    playlist_name = playlist.get('name', 'Unknown Name')
    owner = playlist['owner'].get('display_name', 'Unknown Owner')
    total_tracks = playlist.get('tracks', {}).get('total', 0)

    # Add playlist to the database
    db_manager.add_playlist(playlist_id, playlist_name, owner, total_tracks)

    return jsonify({"status": "success", "message": f"Playlist '{playlist_name}' added to the database!"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)