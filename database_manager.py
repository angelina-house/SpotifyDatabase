# database_manager.py

import mysql.connector # type: ignore
import pandas as pd # type: ignore

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

    def add_playlist(self, playlist_id, playlist_name, owner, total_tracks):
        """Add a playlist to the playlists table."""
        insert_query = """
            INSERT INTO playlists (playlist_id, playlist_name, owner, total_tracks)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE playlist_name=%s, owner=%s, total_tracks=%s
        """
        self.cursor.execute(insert_query, (playlist_id, playlist_name, owner, total_tracks, playlist_name, owner, total_tracks))
        self.connection.commit()

    def add_tracks(self, tracks, playlist_name, owner):  # HUNTER adds playlst name and owner! 
        """Add tracks to the songs table with source and user."""
        insert_query = """ 
            INSERT INTO songs (SongName, Artist, Album, SongID, Source, User)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE SongName=VALUES(SongName), Artist=VALUES(Artist), Album=VALUES(Album), Source=VALUES(Source), User=VALUES(User)
        """ 

        for track in tracks:
            print(track) 
            track_data = (
                track['songName'],
                track['Artist'],
                track['Album'],
                track['SongID'],
                playlist_name,  # Add playlist name as Source
                owner            # Add owner (user) as User
            )
            self.cursor.execute(insert_query, track_data)
        self.connection.commit()




# ALL NEW STUFF FOR 'BLENDING' 


    # def blend_playlists(self, playlist_id_a, playlist_id_b, spotify_client):
    #     """Blend two playlists into the 'blended' table."""
    #     # Fetch tracks from both playlists
    #     playlist_a_tracks = self.get_playlist_tracks(playlist_id_a, spotify_client)
    #     playlist_b_tracks = self.get_playlist_tracks(playlist_id_b, spotify_client)

    #     # Determine the number of songs to blend
    #     total_tracks_a = len(playlist_a_tracks)
    #     total_tracks_b = len(playlist_b_tracks)

    #     # Determine the dispersion rate
    #     num_songs_from_a = total_tracks_a
    #     num_songs_from_b = total_tracks_b

    #     # The number of complete cycles to blend
    #     cycle_length = num_songs_from_a + num_songs_from_b
    #     blend = []

    #     # Track which playlist each song comes from (alternating)
    #     while playlist_a_tracks or playlist_b_tracks:
    #         # If there are songs left in playlist A, take one song
    #         if playlist_a_tracks:
    #             track = playlist_a_tracks.pop(0)
    #             track['source'] = playlist_id_a  # Assign source to playlist A
    #             blend.append(track)

    #         # If there are songs left in playlist B, take one song
    #         if playlist_b_tracks:
    #             track = playlist_b_tracks.pop(0)
    #             track['source'] = playlist_id_b  # Assign source to playlist B
    #             blend.append(track)

    #     # Insert blended tracks into the 'blended' table
    #     for track in blend:
    #         song_data = {
    #             'songName': track['track_name'],
    #             'Artist': track['artist'],
    #             'Album': track['album'],
    #             'SongID': track['uri'],
    #             'Source': track['source'],  # Now correctly alternates between both playlists
    #             'User': track['owner'] if track['owner'] != 'Unknown Owner' else 'Unknown User'  # Correct owner handling
    #         }

    #         self.insert_song_data([song_data], track['source'], track['owner'])




    # def get_playlist_tracks(self, playlist_id, spotify_client):
    #     """Fetch tracks for a given playlist."""
    #     playlist_tracks = spotify_client.playlist_tracks(playlist_id)
    #     track_details = [{
    #         'track_name': track['track'].get('name', 'Unknown Name'),
    #         'artist': (track['track'].get('artists') or [{}])[0].get('name', 'Unknown Artist'),
    #         'album': track['track'].get('album', {}).get('name', 'Unknown Album'),
    #         'uri': track['track'].get('uri', 'No URI'),
    #         'owner': track['track'].get('owner', {}).get('display_name', 'Unknown Owner'),
    #         'source': playlist_id  # Include the playlist ID for reference
    #     } for track in playlist_tracks['items'] if track.get('track')]

    #     return track_details


    # def insert_song_data(self, song_data):
    #     """Insert blended song data into the 'blended' table."""
    #     for song in song_data:
    #         insert_query = '''
    #             INSERT INTO blended (SongName, Artist, Album, SongID, Source, User)
    #             VALUES (%s, %s, %s, %s, %s, %s)
    #             ON DUPLICATE KEY UPDATE SongName=VALUES(SongName), Artist=VALUES(Artist), Album=VALUES(Album), Source=VALUES(Source), User=VALUES(User)
    #         '''
    #         track_data = (
    #             song['songName'],
    #             song['Artist'],
    #             song['Album'],
    #             song['SongID'],
    #             song['Source'],
    #             song['User']
    #         )
    #         self.cursor.execute(insert_query, track_data)
    #     self.connection.commit()




#-----------------






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
