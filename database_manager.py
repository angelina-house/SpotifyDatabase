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
        # """Create the necessary tables if they don't exist.""" 
        # # Create top_tracks table
        # self.cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS top_tracks (
        #         id INT AUTO_INCREMENT PRIMARY KEY,
        #         track_name VARCHAR(255),
        #         artist VARCHAR(255),
        #         album VARCHAR(255),
        #         track_uri VARCHAR(255)
        #     );
        # """)
        
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
                SongID VARCHAR(100) UNIQUE NOT NULL PRIMARY KEY
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

    def add_tracks(self, tracks):
        """Add tracks to the songs table."""
        insert_query = """ 
            INSERT INTO songs (SongName, Artist, Album, SongID)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE SongName=VALUES(SongName), Artist=VALUES(Artist), Album=VALUES(Album)
        """ 

        for track in tracks:
            print(track)  
            track_data = (
                track['songName'],
                track['Artist'],
                track['Album'],
                track['SongID']
            )
            self.cursor.execute(insert_query, track_data)
        self.connection.commit()

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
