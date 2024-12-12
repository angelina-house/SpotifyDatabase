# database_manager.py

import mysql.connector # type: ignore
import pandas as pd # type: ignore
import random

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.connection = mysql.connector.connect(**config)
        self.cursor = self.connection.cursor()
        self.setup_tables()

    def setup_tables(self):
        
        # Create playlists table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                playlist_id VARCHAR(255) UNIQUE,
                playlist_name VARCHAR(255),
                owner VARCHAR(255),
                total_tracks INT
            );
        """)

        # Create song table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                SongName VARCHAR(255) NOT NULL,
                Artist VARCHAR(100) NOT NULL,
                Album VARCHAR(100) NOT NULL,
                SongID VARCHAR(100) UNIQUE NOT NULL PRIMARY KEY,
                Source VARCHAR(255),
                User VARCHAR(255)
            );
        """)   

        # Create blended table, this is a temporary table that will get wiped before each use 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS blended (
                SongName VARCHAR(255) NOT NULL,
                Artist VARCHAR(100) NOT NULL,
                Album VARCHAR(100) NOT NULL,
                SongID VARCHAR(100) UNIQUE NOT NULL PRIMARY KEY,
                Source VARCHAR(255),
                User VARCHAR(255)
            );
        """) 
        self.connection.commit()

    # Clears blended table before each use
    def clear_temp_table(self):
        """Clear the blended table to ensure it's ready for new data."""
        self.cursor.execute("TRUNCATE TABLE blended;")
        self.connection.commit()


    # Adds the songs from sleceted playlist to 'blended' table
    def add_tracks_to_temp_table(self, tracks, playlist_name, owner):
        """Add tracks to the blended table."""
        insert_query = """
            INSERT INTO blended (SongName, Artist, Album, SongID, Source, User)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE SongName=VALUES(SongName), Artist=VALUES(Artist), Album=VALUES(Album), Source=VALUES(Source), User=VALUES(User)
        """
        for track in tracks:
            track_data = (
                track['songName'],
                track['Artist'],
                track['Album'],
                track['SongID'],
                playlist_name,
                owner
            )
            self.cursor.execute(insert_query, track_data)
        self.connection.commit()

    # Mixes up the songs in the temp table, making it appear 'mixed'
    def shuffle_temp_table(self):
        """Shuffle the data in the blended table."""
        self.cursor.execute("SELECT * FROM blended;")
        tracks = self.cursor.fetchall()
        random.shuffle(tracks)

        # Clear the table and reinsert shuffled tracks
        self.clear_temp_table()
        for track in tracks:
            insert_query = """
                INSERT INTO blended (SongName, Artist, Album, SongID, Source, User)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(insert_query, track)
        self.connection.commit()




    def add_playlist(self, playlist_id, playlist_name, owner, total_tracks):
        """Add a playlist to the playlists table."""
        insert_query = """
            INSERT INTO playlists (playlist_id, playlist_name, owner, total_tracks)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE playlist_name=%s, owner=%s, total_tracks=%s
        """
        self.cursor.execute(insert_query, (playlist_id, playlist_name, owner, total_tracks, playlist_name, owner, total_tracks))
        self.connection.commit()


    def get_table_names(self):
        """Fetch all table names in the database."""
        self.cursor.execute("SHOW TABLES")
        tables = [table[0] for table in self.cursor.fetchall()]
        return tables




    # Might be a better way to select the playlist to blend together  

    def blend_playlists(self, playlist_a_id, playlist_b_id, spotify_client):
        """Blend two playlists and store the result in the blended table."""
        self.clear_temp_table()

        # Fetch tracks from both playlists
        playlist_a_tracks = self.get_playlist_tracks(playlist_a_id, spotify_client)
        playlist_b_tracks = self.get_playlist_tracks(playlist_b_id, spotify_client)

        # Add tracks to the blended table
        self.add_tracks_to_temp_table(playlist_a_tracks, playlist_a_id, 'User A')
        self.add_tracks_to_temp_table(playlist_b_tracks, playlist_b_id, 'User B')

        # Shuffle the blended table
        self.shuffle_temp_table()




    def get_playlist_tracks(self, playlist_id, spotify_client):
        """Fetch tracks for a given playlist."""
        playlist_tracks = spotify_client.playlist_tracks(playlist_id)
        track_details = [{
            'track_name': track['track'].get('name', 'Unknown Name'),
            'artist': (track['track'].get('artists') or [{}])[0].get('name', 'Unknown Artist'),
            'album': track['track'].get('album', {}).get('name', 'Unknown Album'),
            'uri': track['track'].get('uri', 'No URI'),
            'owner': track['track'].get('owner', {}).get('display_name', 'Unknown Owner'),
            'source': playlist_id  # Include the playlist ID for reference
        } for track in playlist_tracks['items'] if track.get('track')]

        return track_details


    def insert_song_data(self, song_data):
        """Insert blended song data into the 'blended' table."""
        for song in song_data:
            insert_query = '''
                INSERT INTO blended (SongName, Artist, Album, SongID, Source, User)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE SongName=VALUES(SongName), Artist=VALUES(Artist), Album=VALUES(Album), Source=VALUES(Source), User=VALUES(User)
            '''
            track_data = (
                song['songName'],
                song['Artist'],
                song['Album'],
                song['SongID'],
                song['Source'],
                song['User']
            )
            self.cursor.execute(insert_query, track_data)
        self.connection.commit()


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


