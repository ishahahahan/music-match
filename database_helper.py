"""
MusicMatch Database Integration
==============================
This module provides helper functions to interact with the MusicMatch Supabase database
and integrate with Spotify API data from your existing notebooks.

Requirements:
- supabase-py: pip install supabase
- python-dotenv: pip install python-dotenv (already installed)
- spotipy: pip install spotipy (already installed)

Environment Variables (.env):
- SUPABASE_URL=your_supabase_url
- SUPABASE_ANON_KEY=your_supabase_anon_key
- SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key (for admin operations)
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

class MusicMatchDB:
    def __init__(self, use_service_role: bool = False):
        """
        Initialize connection to Supabase
        
        Args:
            use_service_role: If True, uses service role key (bypass RLS for admin operations)
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        
        if use_service_role:
            self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        else:
            self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    # =============================================================================
    # USER MANAGEMENT
    # =============================================================================
    
    def create_or_update_user(self, spotify_user_data: Dict) -> Dict:
        """
        Create or update user from Spotify user data
        
        Args:
            spotify_user_data: User data from sp.current_user() or sp.me()
            
        Returns:
            Dict with user data
        """
        user_data = {
            "spotify_id": spotify_user_data["id"],
            "email": spotify_user_data.get("email"),
            "display_name": spotify_user_data.get("display_name"),
            "country": spotify_user_data.get("country"),
            "product": spotify_user_data.get("product"),
            "followers_count": spotify_user_data.get("followers", {}).get("total", 0),
            "last_active_at": datetime.now().isoformat()
        }
        
        # Get profile image if available
        if spotify_user_data.get("images") and len(spotify_user_data["images"]) > 0:
            user_data["profile_image_url"] = spotify_user_data["images"][0]["url"]
        
        result = self.supabase.table("users").upsert(user_data).execute()
        return result.data[0] if result.data else None
    
    def get_user_by_spotify_id(self, spotify_id: str) -> Optional[Dict]:
        """Get user by Spotify ID"""
        result = self.supabase.table("users").select("*").eq("spotify_id", spotify_id).execute()
        return result.data[0] if result.data else None
    
    # =============================================================================
    # ARTISTS MANAGEMENT
    # =============================================================================
    
    def upsert_artist(self, artist_data: Dict) -> Dict:
        """
        Insert or update artist from Spotify artist data
        
        Args:
            artist_data: Artist data from Spotify API
            
        Returns:
            Dict with artist data
        """
        formatted_data = {
            "id": artist_data["id"],
            "name": artist_data["name"],
            "genres": artist_data.get("genres", []),
            "popularity": artist_data.get("popularity", 0),
            "followers_count": artist_data.get("followers", {}).get("total", 0),
            "external_urls": artist_data.get("external_urls", {})
        }
        
        # Get artist image if available
        if artist_data.get("images") and len(artist_data["images"]) > 0:
            formatted_data["image_url"] = artist_data["images"][0]["url"]
            
        result = self.supabase.table("artists").upsert(formatted_data).execute()
        return result.data[0] if result.data else None
    
    def batch_upsert_artists(self, artists_data: List[Dict]) -> List[Dict]:
        """Batch upsert multiple artists"""
        formatted_artists = []
        for artist in artists_data:
            formatted_data = {
                "id": artist["id"],
                "name": artist["name"],
                "genres": artist.get("genres", []),
                "popularity": artist.get("popularity", 0),
                "followers_count": artist.get("followers", {}).get("total", 0),
                "external_urls": artist.get("external_urls", {})
            }
            
            if artist.get("images") and len(artist["images"]) > 0:
                formatted_data["image_url"] = artist["images"][0]["url"]
                
            formatted_artists.append(formatted_data)
        
        result = self.supabase.table("artists").upsert(formatted_artists).execute()
        return result.data
    
    # =============================================================================
    # TRACKS MANAGEMENT
    # =============================================================================
    
    def upsert_track(self, track_data: Dict) -> Dict:
        """
        Insert or update track from Spotify track data
        
        Args:
            track_data: Track data from Spotify API
            
        Returns:
            Dict with track data
        """
        formatted_data = {
            "id": track_data["id"],
            "name": track_data["name"],
            "duration_ms": track_data["duration_ms"],
            "explicit": track_data.get("explicit", False),
            "popularity": track_data.get("popularity", 0),
            "preview_url": track_data.get("preview_url"),
            "external_urls": track_data.get("external_urls", {}),
            "is_local": track_data.get("is_local", False)
        }
        
        # Handle album relationship
        if track_data.get("album"):
            formatted_data["album_id"] = track_data["album"]["id"]
            # Also upsert the album
            self.upsert_album(track_data["album"])
        
        # Track number and disc number
        if "track_number" in track_data:
            formatted_data["track_number"] = track_data["track_number"]
        if "disc_number" in track_data:
            formatted_data["disc_number"] = track_data["disc_number"]
            
        result = self.supabase.table("tracks").upsert(formatted_data).execute()
        
        # Handle artist relationships
        if track_data.get("artists"):
            self.upsert_track_artists(track_data["id"], track_data["artists"])
        
        return result.data[0] if result.data else None
    
    def upsert_album(self, album_data: Dict) -> Dict:
        """Insert or update album from Spotify album data"""
        formatted_data = {
            "id": album_data["id"],
            "name": album_data["name"],
            "album_type": album_data.get("album_type"),
            "total_tracks": album_data.get("total_tracks", 0),
            "external_urls": album_data.get("external_urls", {})
        }
        
        # Handle release date
        if album_data.get("release_date"):
            formatted_data["release_date"] = album_data["release_date"]
            formatted_data["release_date_precision"] = album_data.get("release_date_precision", "day")
        
        # Handle album image
        if album_data.get("images") and len(album_data["images"]) > 0:
            formatted_data["image_url"] = album_data["images"][0]["url"]
        
        result = self.supabase.table("albums").upsert(formatted_data).execute()
        
        # Handle album artists
        if album_data.get("artists"):
            self.upsert_album_artists(album_data["id"], album_data["artists"])
        
        return result.data[0] if result.data else None
    
    def upsert_track_artists(self, track_id: str, artists: List[Dict]):
        """Create track-artist relationships"""
        # First, ensure all artists exist
        for artist in artists:
            self.upsert_artist(artist)
        
        # Delete existing relationships
        self.supabase.table("track_artists").delete().eq("track_id", track_id).execute()
        
        # Create new relationships
        relationships = []
        for idx, artist in enumerate(artists):
            relationships.append({
                "track_id": track_id,
                "artist_id": artist["id"],
                "artist_order": idx
            })
        
        if relationships:
            self.supabase.table("track_artists").insert(relationships).execute()
    
    def upsert_album_artists(self, album_id: str, artists: List[Dict]):
        """Create album-artist relationships"""
        # Ensure all artists exist
        for artist in artists:
            self.upsert_artist(artist)
        
        # Delete existing relationships
        self.supabase.table("album_artists").delete().eq("album_id", album_id).execute()
        
        # Create new relationships
        relationships = []
        for artist in artists:
            relationships.append({
                "album_id": album_id,
                "artist_id": artist["id"]
            })
        
        if relationships:
            self.supabase.table("album_artists").insert(relationships).execute()
    
    # =============================================================================
    # USER MUSIC DATA (FROM YOUR NOTEBOOKS)
    # =============================================================================
    
    def save_user_top_artists(self, user_id: str, artists_data: List[Dict], time_range: str = "medium_term"):
        """
        Save user's top artists from sp.current_user_top_artists()
        
        Args:
            user_id: User's UUID from the database
            artists_data: Data from sp.current_user_top_artists()['items']
            time_range: 'short_term', 'medium_term', or 'long_term'
        """
        # First, upsert all artists
        self.batch_upsert_artists(artists_data)
        
        # Prepare top artists data
        top_artists = []
        for idx, artist in enumerate(artists_data):
            top_artists.append({
                "user_id": user_id,
                "artist_id": artist["id"],
                "time_range": time_range,
                "position": idx + 1,
                "retrieved_at": datetime.now().isoformat()
            })
        
        # Delete existing data for this time range and date
        today = datetime.now().date().isoformat()
        self.supabase.table("user_top_artists").delete().eq("user_id", user_id).eq("time_range", time_range).gte("retrieved_at", today).execute()
        
        # Insert new data
        result = self.supabase.table("user_top_artists").insert(top_artists).execute()
        return result.data
    
    def save_user_top_tracks(self, user_id: str, tracks_data: List[Dict], time_range: str = "medium_term"):
        """
        Save user's top tracks from sp.current_user_top_tracks()
        
        Args:
            user_id: User's UUID from the database
            tracks_data: Data from sp.current_user_top_tracks()['items']
            time_range: 'short_term', 'medium_term', or 'long_term'
        """
        # First, upsert all tracks
        for track in tracks_data:
            self.upsert_track(track)
        
        # Prepare top tracks data
        top_tracks = []
        for idx, track in enumerate(tracks_data):
            top_tracks.append({
                "user_id": user_id,
                "track_id": track["id"],
                "time_range": time_range,
                "position": idx + 1,
                "retrieved_at": datetime.now().isoformat()
            })
        
        # Delete existing data for this time range and date
        today = datetime.now().date().isoformat()
        self.supabase.table("user_top_tracks").delete().eq("user_id", user_id).eq("time_range", time_range).gte("retrieved_at", today).execute()
        
        # Insert new data
        result = self.supabase.table("user_top_tracks").insert(top_tracks).execute()
        return result.data
    
    def save_user_saved_tracks(self, user_id: str, saved_tracks_data: List[Dict]):
        """
        Save user's saved tracks from sp.current_user_saved_tracks()
        
        Args:
            user_id: User's UUID from the database
            saved_tracks_data: Data from sp.current_user_saved_tracks()['items']
        """
        saved_tracks = []
        
        for item in saved_tracks_data:
            track = item["track"]
            # Upsert the track
            self.upsert_track(track)
            
            saved_tracks.append({
                "user_id": user_id,
                "track_id": track["id"],
                "saved_at": item["added_at"]
            })
        
        # Upsert saved tracks (will handle duplicates)
        result = self.supabase.table("user_saved_tracks").upsert(saved_tracks).execute()
        return result.data
    
    def compute_user_genre_preferences(self, user_id: str, time_range: str = "medium_term"):
        """
        Compute genre preferences from user's top artists
        Similar to the genre frequency analysis in your blend.ipynb
        """
        # Get user's top artists for this time range
        top_artists_result = self.supabase.table("user_top_artists").select(
            "artist_id, position, artists!inner(genres)"
        ).eq("user_id", user_id).eq("time_range", time_range).execute()
        
        if not top_artists_result.data:
            return []
        
        # Count genre frequencies
        genre_freq = {}
        total_artists = len(top_artists_result.data)
        
        for item in top_artists_result.data:
            artist_genres = item["artists"]["genres"]
            position = item["position"]
            # Weight by position (earlier positions have higher weight)
            weight = (total_artists - position + 1) / total_artists
            
            for genre in artist_genres:
                if genre in genre_freq:
                    genre_freq[genre] += weight
                else:
                    genre_freq[genre] = weight
        
        # Convert to database format
        genre_preferences = []
        for genre, weighted_freq in genre_freq.items():
            genre_preferences.append({
                "user_id": user_id,
                "genre": genre,
                "frequency": len([item for item in top_artists_result.data if genre in item["artists"]["genres"]]),
                "weight": round(weighted_freq / total_artists, 2),
                "time_range": time_range,
                "computed_at": datetime.now().isoformat()
            })
        
        # Delete existing preferences for this time range
        self.supabase.table("user_genre_preferences").delete().eq("user_id", user_id).eq("time_range", time_range).execute()
        
        # Insert new preferences
        if genre_preferences:
            result = self.supabase.table("user_genre_preferences").insert(genre_preferences).execute()
            return result.data
        
        return []
    
    # =============================================================================
    # PLAYLISTS
    # =============================================================================
    
    def save_user_playlists(self, user_id: str, playlists_data: List[Dict]):
        """
        Save user's playlists from sp.current_user_playlists()
        """
        playlists = []
        
        for playlist in playlists_data:
            playlist_data = {
                "id": playlist["id"],
                "user_id": user_id,
                "name": playlist["name"],
                "description": playlist.get("description"),
                "is_public": playlist.get("public", False),
                "is_collaborative": playlist.get("collaborative", False),
                "external_urls": playlist.get("external_urls", {}),
                "snapshot_id": playlist.get("snapshot_id"),
                "tracks_total": playlist.get("tracks", {}).get("total", 0)
            }
            
            # Handle playlist image
            if playlist.get("images") and len(playlist["images"]) > 0:
                playlist_data["image_url"] = playlist["images"][0]["url"]
            
            playlists.append(playlist_data)
        
        # Upsert playlists
        if playlists:
            result = self.supabase.table("playlists").upsert(playlists).execute()
            return result.data
        
        return []
    
    def save_playlist_tracks(self, playlist_id: str, tracks_data: List[Dict]):
        """
        Save tracks for a specific playlist from sp.playlist_tracks()
        """
        playlist_tracks = []
        
        for idx, item in enumerate(tracks_data):
            track = item["track"]
            if not track or not track.get("id"):  # Skip null tracks
                continue
                
            # Upsert the track
            self.upsert_track(track)
            
            playlist_tracks.append({
                "playlist_id": playlist_id,
                "track_id": track["id"],
                "position": idx + 1,
                "added_at": item["added_at"]
            })
        
        # Delete existing playlist tracks
        self.supabase.table("playlist_tracks").delete().eq("playlist_id", playlist_id).execute()
        
        # Insert new playlist tracks
        if playlist_tracks:
            result = self.supabase.table("playlist_tracks").insert(playlist_tracks).execute()
            return result.data
        
        return []
    
    # =============================================================================
    # AUDIO FEATURES
    # =============================================================================
    
    def save_track_audio_features(self, track_id: str, audio_features: Dict):
        """
        Save audio features from sp.audio_features()
        
        Args:
            track_id: Spotify track ID
            audio_features: Audio features data from Spotify API
        """
        if not audio_features:
            return None
            
        features_data = {
            "track_id": track_id,
            "danceability": audio_features.get("danceability"),
            "energy": audio_features.get("energy"),
            "key": audio_features.get("key"),
            "loudness": audio_features.get("loudness"),
            "mode": audio_features.get("mode"),
            "speechiness": audio_features.get("speechiness"),
            "acousticness": audio_features.get("acousticness"),
            "instrumentalness": audio_features.get("instrumentalness"),
            "liveness": audio_features.get("liveness"),
            "valence": audio_features.get("valence"),
            "tempo": audio_features.get("tempo"),
            "time_signature": audio_features.get("time_signature")
        }
        
        result = self.supabase.table("track_audio_features").upsert(features_data).execute()
        return result.data[0] if result.data else None
    
    def batch_save_audio_features(self, audio_features_list: List[Dict]):
        """Save multiple audio features at once"""
        features_data = []
        
        for features in audio_features_list:
            if not features:
                continue
                
            features_data.append({
                "track_id": features["id"],
                "danceability": features.get("danceability"),
                "energy": features.get("energy"),
                "key": features.get("key"),
                "loudness": features.get("loudness"),
                "mode": features.get("mode"),
                "speechiness": features.get("speechiness"),
                "acousticness": features.get("acousticness"),
                "instrumentalness": features.get("instrumentalness"),
                "liveness": features.get("liveness"),
                "valence": features.get("valence"),
                "tempo": features.get("tempo"),
                "time_signature": features.get("time_signature")
            })
        
        if features_data:
            result = self.supabase.table("track_audio_features").upsert(features_data).execute()
            return result.data
        
        return []
    
    # =============================================================================
    # COMPATIBILITY & MATCHING
    # =============================================================================
    
    def compute_compatibility_score(self, user1_id: str, user2_id: str) -> Optional[Dict]:
        """
        Compute compatibility score between two users
        Based on genre overlap, artist similarity, and audio features
        """
        # Ensure proper user ordering for database constraint
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        # Use the database function to compute genre overlap
        genre_overlap = self.supabase.rpc("compute_genre_overlap", {
            "user1_uuid": user1_id,
            "user2_uuid": user2_id,
            "time_range_param": "medium_term"
        }).execute()
        
        genre_score = genre_overlap.data if genre_overlap.data else 0.0
        
        # For now, set other scores to placeholder values
        # You can implement more sophisticated algorithms later
        artist_score = 0.0  # TODO: Implement artist similarity
        audio_score = 0.0   # TODO: Implement audio feature similarity
        
        # Overall compatibility (weighted average)
        overall_score = (genre_score * 0.4 + artist_score * 0.3 + audio_score * 0.3)
        
        compatibility_data = {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "genre_overlap_score": genre_score,
            "artist_similarity_score": artist_score,
            "audio_feature_similarity": audio_score,
            "overall_compatibility": overall_score,
            "computed_at": datetime.now().isoformat()
        }
        
        result = self.supabase.table("compatibility_scores").upsert(compatibility_data).execute()
        return result.data[0] if result.data else None
    
    def get_potential_matches(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Get potential matches for a user based on compatibility scores
        """
        result = self.supabase.table("compatibility_scores").select(
            "*, user1:users!compatibility_scores_user1_id_fkey(display_name, profile_image_url), user2:users!compatibility_scores_user2_id_fkey(display_name, profile_image_url)"
        ).or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}").order("overall_compatibility", desc=True).limit(limit).execute()
        
        return result.data
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_user_music_profile(self, user_id: str) -> Dict:
        """
        Get a comprehensive music profile for a user
        """
        profile = {}
        
        # Get top artists
        top_artists = self.supabase.table("user_top_artists").select(
            "position, time_range, artists(name, genres, popularity)"
        ).eq("user_id", user_id).order("time_range").order("position").execute()
        
        profile["top_artists"] = top_artists.data
        
        # Get genre preferences
        genres = self.supabase.table("user_genre_preferences").select(
            "*"
        ).eq("user_id", user_id).order("weight", desc=True).execute()
        
        profile["genre_preferences"] = genres.data
        
        # Get saved tracks count
        saved_tracks_count = self.supabase.table("user_saved_tracks").select(
            "track_id", count="exact"
        ).eq("user_id", user_id).execute()
        
        profile["saved_tracks_count"] = saved_tracks_count.count
        
        return profile


# =============================================================================
# EXAMPLE USAGE FUNCTIONS
# =============================================================================

def example_sync_user_data(spotify_client, musicmatch_db: MusicMatchDB):
    """
    Example function showing how to sync data from your notebooks to the database
    This mirrors the workflow in your existing notebooks
    """
    # Get current user
    user_data = spotify_client.current_user()
    print(f"Syncing data for user: {user_data['display_name']}")
    
    # Create or update user in database
    db_user = musicmatch_db.create_or_update_user(user_data)
    user_id = db_user["id"]
    
    # Sync top artists (like in your blend.ipynb)
    print("Syncing top artists...")
    for time_range in ["short_term", "medium_term", "long_term"]:
        top_artists = spotify_client.current_user_top_artists(limit=50, time_range=time_range)
        musicmatch_db.save_user_top_artists(user_id, top_artists["items"], time_range)
    
    # Sync top tracks
    print("Syncing top tracks...")
    for time_range in ["short_term", "medium_term", "long_term"]:
        top_tracks = spotify_client.current_user_top_tracks(limit=50, time_range=time_range)
        musicmatch_db.save_user_top_tracks(user_id, top_tracks["items"], time_range)
    
    # Sync saved tracks (like in your user_saved_items.ipynb)
    print("Syncing saved tracks...")
    saved_tracks = spotify_client.current_user_saved_tracks(limit=50)
    musicmatch_db.save_user_saved_tracks(user_id, saved_tracks["items"])
    
    # Sync playlists (like in your playlists.ipynb)
    print("Syncing playlists...")
    playlists = spotify_client.current_user_playlists()
    musicmatch_db.save_user_playlists(user_id, playlists["items"])
    
    # Compute genre preferences
    print("Computing genre preferences...")
    musicmatch_db.compute_user_genre_preferences(user_id, "medium_term")
    
    print("Sync completed!")
    
    return user_id

def example_get_audio_features(spotify_client, musicmatch_db: MusicMatchDB, user_id: str):
    """
    Example function to fetch and save audio features for user's top tracks
    This adds the audio analysis capability mentioned in your README
    """
    # Get user's top tracks
    top_tracks_result = musicmatch_db.supabase.table("user_top_tracks").select(
        "track_id"
    ).eq("user_id", user_id).eq("time_range", "medium_term").limit(20).execute()
    
    if not top_tracks_result.data:
        print("No top tracks found for user")
        return
    
    track_ids = [item["track_id"] for item in top_tracks_result.data]
    
    # Get audio features from Spotify (batch request)
    print(f"Fetching audio features for {len(track_ids)} tracks...")
    audio_features = spotify_client.audio_features(track_ids)
    
    # Save to database
    musicmatch_db.batch_save_audio_features(audio_features)
    print("Audio features saved!")

if __name__ == "__main__":
    # Example usage
    from your_existing_spotify_setup import sp  # Import your spotipy client
    
    # Initialize database connection
    db = MusicMatchDB()
    
    # Sync current user's data
    user_id = example_sync_user_data(sp, db)
    
    # Get audio features
    example_get_audio_features(sp, db, user_id)
    
    # Get user's music profile
    profile = db.get_user_music_profile(user_id)
    print("User music profile:", json.dumps(profile, indent=2, default=str))
