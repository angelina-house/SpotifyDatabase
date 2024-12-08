# app.py

from flask import Flask, render_template, request, jsonify # type: ignore
from database_manager import DatabaseManager
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@5u93rD0m017',
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

# Helper function to fetch genre data
def get_artist_genres(artist_id):
    artist_data = spotify_client.artist(artist_id)  # Fetch artist details
    return artist_data.get('genres', [])  # Return genres or an empty list if none exist

def get_audio_features(track_ids):
    audio_features_list = []

    track_batches = [track_ids[i:i+100] for i in range(0, len(track_ids), 100)]
    for batch in track_batches:
        features = spotify_client.audio_features(batch)
        if features:
            for audio_features in features:
                if audio_features:  # Ensure data is valid
                    # Extract only the required audio features
                    filtered_features = {
                        'Acousticness': audio_features.get('acousticness', 0.0),
                        'Duration_ms': audio_features.get('duration_ms', 0),
                        'Type': audio_features.get('type', 'track'),
                        'Tempo': audio_features.get('tempo', 0.0),
                        'Danceability': audio_features.get('danceability', 0.0),
                        'Mode': bool(audio_features.get('mode', 0)),
                        'Speechiness': audio_features.get('speechiness', 0.0),
                        'Loudness': audio_features.get('loudness', 0.0),
                        'Liveness': audio_features.get('liveness', 0.0),
                        'Time_Signature': audio_features.get('time_signature', 4),
                        'Energy': audio_features.get('energy', 0.0),
                        'Valence': audio_features.get('valence', 0.0),
                        'SKey': audio_features.get('key', -1),
                    }
                    audio_features_list.append(filtered_features)

    return audio_features_list

# Helper function to fetch song data
def get_song_data(playlist_id):
    # Fetch playlist details
    songs = []
    playlist_tracks = spotify_client.playlist_tracks(playlist_id)
    # track_ids = [track['track']['id'] for track in playlist_tracks['items'] if track.get('track')]

    # Fetch audio features for the tracks
    # audio_features_list = get_audio_features(track_ids)

    for track in playlist_tracks['items']:
        track_data = track.get('track')
        if track_data:
            # audio_features = audio_features_list[i] if i < len(audio_features_list) else {}

            # Fetch Genre
            #artist_id = track_data['artists'][0]['id']  # Get the first artist's ID
            # genres = get_artist_genres(artist_id)  # Fetch genres

            songs.append({
                'SongID': track_data['id'],
                'SongName': track_data.get('name', 'Unkown Name'),
                'Artist': (track_data.get('artists') or [{}])[0].get('name', 'Unkown Artist'),
                'Album': track_data.get('album', {}).get('name', 'Unkown Album')
                #'Instrumentalness': audio_features.get('instrumentalness', 0.0),
                #'Acousticness': audio_features.get('acousticness', 0.0),
                #'Duration_ms': audio_features.get('duration_ms', 0),
                #'Type': audio_features.get('type', 'track'),
                #'Tempo': audio_features.get('tempo', 0.0),
                #'Danceability': audio_features.get('danceability', 0.0),
                #'Mode': bool(audio_features.get('mode', 0)),
                #'Speechiness': audio_features.get('speechiness', 0.0),
                #'Loudness': audio_features.get('loudness', 0.0),
                #'Liveness': audio_features.get('liveness', 0.0),
                #'Time_Signature': audio_features.get('time_signature', 4),
                #'Energy': audio_features.get('energy', 0.0),
                #'Valence': audio_features.get('valence', 0.0),
                #'SKey': audio_features.get('key', -1),
                # 'Genre': ', '.join(genres)
            })

    return {'songs': songs}
            
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

    data = get_song_data(playlist_id)
    db_manager.add_songs(data['songs'])

    return jsonify({"status": "success", "message": f"Playlist '{playlist_name}' and its songsadded to the database!"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)