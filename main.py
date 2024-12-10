# main.py

from database_manager import DatabaseManager
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore


# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'CPSC408!',
    'database': 'spotify_db'
}

# Set up Spotify authentication
CLIENT_ID = '8b1f1dfdc20e4652933901bb9d7c45a2'
CLIENT_SECRET = 'a8156ca37a6f41fab768c815bcf1b8cf'
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-top-read playlist-modify-public playlist-read-private'

spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET,
                                                           redirect_uri=REDIRECT_URI,
                                                           scope=SCOPE))

# Initialize database manager and GUI
db_manager = DatabaseManager(db_config)



# Close the database connection
db_manager.close()






# ---- Main test made to test the blend test locally  \/


# from database_manager import DatabaseManager
# import spotipy  # type: ignore
# from spotipy.oauth2 import SpotifyOAuth  # type: ignore

# # Database configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'CPSC408!',
#     'database': 'spotify_db'
# }

# # Set up Spotify authentication
# CLIENT_ID = '8b1f1dfdc20e4652933901bb9d7c45a2'
# CLIENT_SECRET = 'a8156ca37a6f41fab768c815bcf1b8cf'
# REDIRECT_URI = 'http://localhost:8888/callback'
# SCOPE = 'user-top-read playlist-modify-public playlist-read-private'

# spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
#                                                            client_secret=CLIENT_SECRET,
#                                                            redirect_uri=REDIRECT_URI,
#                                                            scope=SCOPE))

# # Initialize database manager
# db_manager = DatabaseManager(db_config)

# # Manually specify the playlists to blend (IDs for "Circa 11/20" and "d1 takes on sd")
# playlist_id_a = '0gHiC7BVsId35ZgQnFrBSw'  # Replace with actual playlist ID
# playlist_id_b = '1MqkuMFqCxNG615KDdLJXr'  # Replace with actual playlist ID

# # Blend the playlists
# db_manager.blend_playlists(playlist_id_a, playlist_id_b, spotify_client)

# # Close the database connection
# db_manager.close()

# print("Playlists blended successfully!")
