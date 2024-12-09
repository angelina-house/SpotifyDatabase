# main.py

from database_manager import DatabaseManager
import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyOAuth  # type: ignore
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '🧐',
    'database': 'spotify_db'
}

# Spotify authentication configuration
CLIENT_ID = '8b1f1dfdc20e4652933901bb9d7c45a2'
CLIENT_SECRET = 'a8156ca37a6f41fab768c815bcf1b8cf'
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative'

# Initialize database manager
db_manager = DatabaseManager(db_config)

# Initialize GUI
root = tk.Tk()
root.title("Spotify Playlist Manager")

# Create main frames
auth_frame = ttk.Frame(root, padding="10")
auth_frame.grid(row=0, column=0, sticky="W")

users_frame = ttk.Frame(root, padding="10")
users_frame.grid(row=1, column=0, sticky="W")

playlists_frame = ttk.Frame(root, padding="10")
playlists_frame.grid(row=2, column=0, sticky="W")

action_frame = ttk.Frame(root, padding="10")
action_frame.grid(row=3, column=0, sticky="W")

# Authenticated Users Listbox
ttk.Label(users_frame, text="Authenticated Users:").pack()
user_listbox = tk.Listbox(users_frame, width=50)
user_listbox.pack()

# Playlists Listbox
ttk.Label(playlists_frame, text="Playlists:").pack()
playlist_listbox = tk.Listbox(playlists_frame, width=50)
playlist_listbox.pack()

# Add Playlist Button
add_button = ttk.Button(action_frame, text="Add Selected Playlist to DB", command=lambda: threading.Thread(target=add_playlist_to_db).start())
add_button.pack()

# Function to refresh the user list in the GUI
def refresh_user_list():
    """Refresh the list of authenticated users in the GUI."""
    users = db_manager.get_all_users()
    user_listbox.delete(0, tk.END)
    for user_id, display_name in users:
        user_listbox.insert(tk.END, f"{display_name} ({user_id})")

# Function to handle user authentication
def authenticate_user():
    """Authenticate a new user via Spotify OAuth."""
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=None  # Disable caching
    )
    auth_url = sp_oauth.get_authorize_url()
    
    # Open the authorization URL in the default browser
    webbrowser.open(auth_url)
    
    # Start a simple HTTP server to handle the callback
    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_path = urllib.parse.urlparse(self.path)
            if parsed_path.path == '/callback':
                query_params = urllib.parse.parse_qs(parsed_path.query)
                if 'code' in query_params:
                    code = query_params['code'][0]
                    token_info = sp_oauth.get_access_token(code, as_dict=True)
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
                    
                    # Send a simple response to the browser
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"Authentication successful! You can close this window.")
                    
                    # Refresh the user list in the GUI
                    refresh_user_list()
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization failed.")
            else:
                self.send_response(404)
                self.end_headers()
    
    # Run the server in a separate thread to avoid blocking the GUI
    def run_server():
        server = HTTPServer(('localhost', 8888), OAuthCallbackHandler)
        server.handle_request()
    
    threading.Thread(target=run_server, daemon=True).start()

# Function to fetch and display playlists for the selected user
def fetch_playlists():
    """Fetch and display playlists for the selected user."""
    selected = user_listbox.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a user.")
        return
    user_entry = user_listbox.get(selected[0])
    spotify_user_id = user_entry.split('(')[-1].strip(')')
    
    try:
        sp = get_spotify_client(spotify_user_id)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get Spotify client: {e}")
        return
    
    try:
        playlists = sp.current_user_playlists(limit=50)['items']
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch playlists: {e}")
        return
    
    playlist_listbox.delete(0, tk.END)
    for playlist in playlists:
        playlist_listbox.insert(tk.END, f"{playlist['name']} ({playlist['id']})")

# Function to get a Spotify client for a specific user
def get_spotify_client(spotify_user_id):
    """Retrieve a Spotify client for the given user."""
    tokens = db_manager.get_user_tokens(spotify_user_id)
    if not tokens:
        raise ValueError("User tokens not found. Please authenticate the user first.")
    access_token, refresh_token, token_expires_at = tokens
    
    # Check if the token is expired and refresh if necessary
    if datetime.utcnow() >= token_expires_at:
        sp_oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=None  # We manage caching manually
        )
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
    
    return spotipy.Spotify(auth=access_token)

# Function to add the selected playlist to the database
def add_playlist_to_db():
    """Add the selected playlist to the database."""
    selected_user = user_listbox.curselection()
    selected_playlist = playlist_listbox.curselection()
    if not selected_user or not selected_playlist:
        messagebox.showwarning("No Selection", "Please select a user and a playlist.")
        return
    user_entry = user_listbox.get(selected_user[0])
    spotify_user_id = user_entry.split('(')[-1].strip(')')
    playlist_entry = playlist_listbox.get(selected_playlist[0])
    playlist_id = playlist_entry.split('(')[-1].strip(')')
    
    try:
        sp = get_spotify_client(spotify_user_id)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get Spotify client: {e}")
        return
    
    try:
        # Fetch playlist details
        playlist = sp.playlist(playlist_id)
        playlist_name = playlist.get('name', 'Unknown Name')
        owner = playlist['owner'].get('display_name', 'Unknown Owner')
        total_tracks = playlist.get('tracks', {}).get('total', 0)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch playlist details: {e}")
        return
    
    try:
        # Add playlist to the database
        db_manager.add_playlist(playlist_id, playlist_name, owner, total_tracks, spotify_user_id)
        messagebox.showinfo("Success", f"Playlist '{playlist_name}' added to the database!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add playlist to database: {e}")

# Add a button to authenticate a new user
auth_button = ttk.Button(auth_frame, text="Authenticate with Spotify", command=lambda: threading.Thread(target=authenticate_user).start())
auth_button.pack()

# Add a button to fetch playlists for the selected user
fetch_button = ttk.Button(playlists_frame, text="Fetch Playlists", command=lambda: threading.Thread(target=fetch_playlists).start())
fetch_button.pack()

# Initially populate the user list
refresh_user_list()

# Start the GUI main loop
root.mainloop()

# Close the database connection when the GUI is closed
db_manager.close()
