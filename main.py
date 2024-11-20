# main.py

from database_manager import DatabaseManager
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore
import tkinter as tk

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Stormy@0704',
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
root = tk.Tk()


# Start the GUI main loop
root.mainloop()

# Close the database connection
db_manager.close()