# database_manager.py

import mysql.connector  # type: ignore
import pandas as pd  # type: ignore
from datetime import datetime

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.connection = mysql.connector.connect(**config)
        self.cursor = self.connection.cursor()
        self.setup_tables()

    def setup_tables(self):
        """Create the necessary tables if they don't exist."""
        # Create top_tracks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS top_tracks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                track_name VARCHAR(255),
                artist VARCHAR(255),
                album VARCHAR(255),
                track_uri VARCHAR(255)
            );
        """)

        # Create user table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                Email VARCHAR(255),
                Password VARCHAR(60),
                Username VARCHAR(30) NOT NULL,
                UserID VARCHAR(36) UNIQUE NOT NULL
            );
        """)

        # Create playlists table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                playlist_id VARCHAR(255) UNIQUE,
                playlist_name VARCHAR(255),
                owner VARCHAR(255),
                total_tracks INT,
                userID VARCHAR(36),
                FOREIGN KEY (userID) REFERENCES user(UserID)            
            );
        """)

        # Create Songs table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                SongID VARCHAR(22) UNIQUE NOT NULL PRIMARY KEY,
                SongName VARCHAR(255) NOT NULL,
                Artist VARCHAR(100) NOT NULL,
                Album VARCHAR(100) NOT NULL,
                Genre VARCHAR(100),
                Instrumentalness DOUBLE,
                Acousticness DOUBLE,
                Duration_ms INT,
                Type VARCHAR(10),
                Tempo DOUBLE,
                Danceability DOUBLE,
                Mode BOOLEAN,
                Speechiness DOUBLE,
                Loudness DOUBLE,
                Liveness DOUBLE,
                Time_Signature INT,
                Energy DOUBLE,
                Valence DOUBLE,
                SKey INTEGER  
            );
        """)

        # Create playlistSong table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlistSong (
                PlaylistID VARCHAR(255) NOT NULL,
                SongID VARCHAR(22) NOT NULL,
                PRIMARY KEY (SongID, PlaylistID),
                FOREIGN KEY (SongID) REFERENCES songs(SongID),
                FOREIGN KEY (PlaylistID) REFERENCES playlists(playlist_id)
            );
        """)

        # Create users table for storing authentication tokens
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                spotify_user_id VARCHAR(255) UNIQUE,
                display_name VARCHAR(255),
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at DATETIME
            );
        """)
        self.connection.commit()

    def add_playlist(self, playlist_id, playlist_name, owner, total_tracks, userID):
        """Add a playlist to the playlists table."""
        insert_query = """
            INSERT INTO playlists (playlist_id, playlist_name, owner, total_tracks, userID)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE playlist_name=%s, owner=%s, total_tracks=%s
        """
        self.cursor.execute(insert_query, (playlist_id, playlist_name, owner, total_tracks, userID, playlist_name, owner, total_tracks))
        self.connection.commit()

    def add_tracks(self, tracks):
        """Add tracks to the top_tracks table."""
        insert_query = """
            INSERT INTO top_tracks (track_name, artist, album, track_uri)
            VALUES (%s, %s, %s, %s)
        """
        for track in tracks:
            track_data = (
                track['track_name'],
                track['artist'],
                track['album'],
                track['uri']
            )
            self.cursor.execute(insert_query, track_data)
        self.connection.commit()

    def add_songs(self, songs):
        """Add Songs to the songs table."""
        insert_query = """
            INSERT INTO songs (SongID, SongName, Artist, Album)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE SongName=VALUES(SongName);
        """
        for song in songs:
            song_data = (
                song['SongID'],
                song['SongName'],
                song['Artist'],
                song['Album']
            )
            print("Inserting song:", song_data)  # Debugging statement
            self.cursor.execute(insert_query, song_data)
        self.connection.commit()

    def add_or_update_user(self, spotify_user_id, display_name, access_token, refresh_token, token_expires_at):
        """Add a new user or update existing user's tokens."""
        insert_query = """
            INSERT INTO users (spotify_user_id, display_name, access_token, refresh_token, token_expires_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                display_name = VALUES(display_name),
                access_token = VALUES(access_token),
                refresh_token = VALUES(refresh_token),
                token_expires_at = VALUES(token_expires_at)
        """
        self.cursor.execute(insert_query, (spotify_user_id, display_name, access_token, refresh_token, token_expires_at))
        self.connection.commit()

    def get_all_users(self):
        """Retrieve all authenticated users."""
        self.cursor.execute("SELECT spotify_user_id, display_name FROM users")
        return self.cursor.fetchall()

    def get_user_tokens(self, spotify_user_id):
        """Retrieve tokens for a specific user."""
        self.cursor.execute("SELECT access_token, refresh_token, token_expires_at FROM users WHERE spotify_user_id = %s", (spotify_user_id,))
        return self.cursor.fetchone()

    def get_table_names(self):
        """Fetch all table names in the database."""
        self.cursor.execute("SHOW TABLES")
        tables = [table[0] for table in self.cursor.fetchall()]
        return tables

    def fetch_table_data(self, table_name):
        """Fetch data from a specified table."""
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        return pd.DataFrame(rows, columns=columns)

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.connection.close()
