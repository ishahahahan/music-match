"""
MusicMatch API Client
====================
Python client library for easy interaction with the MusicMatch API

Usage:
    from musicmatch_client import MusicMatchClient
    
    client = MusicMatchClient("http://localhost:8000")
    client.authenticate()  # Opens browser for Spotify auth
    user_profile = client.get_user_profile()
"""

import requests
import webbrowser
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin


class MusicMatchClient:
    """Python client for MusicMatch API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
        """
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the API"""
        url = urljoin(self.base_url, endpoint)
        
        # Add access token to params if available
        if self.access_token and method == "POST":
            if "params" not in kwargs:
                kwargs["params"] = {}
            kwargs["params"]["access_token"] = self.access_token
        
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        
        return response.json()
    
    def authenticate(self) -> str:
        """
        Authenticate with Spotify
        Opens browser for user to authorize
        
        Returns:
            access_token: Spotify access token
        """
        print("🔐 Getting login URL...")
        login_data = self._request("GET", "/auth/login")
        auth_url = login_data["auth_url"]
        
        print(f"🌐 Opening browser for authentication...")
        webbrowser.open(auth_url)
        
        # Get token from user input
        self.access_token = input("📌 Enter the access token from the callback URL: ").strip()
        print("✅ Authentication successful!")
        
        return self.access_token
    
    # =================================================================
    # USER MANAGEMENT
    # =================================================================
    
    def sync_user_data(self, time_ranges: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync all user data from Spotify
        
        Args:
            time_ranges: List of time ranges to sync (default: all)
        
        Returns:
            Sync result with user_id
        """
        if not self.access_token:
            raise ValueError("Must authenticate first. Call .authenticate()")
        
        if time_ranges is None:
            time_ranges = ["short_term", "medium_term", "long_term"]
        
        print(f"📊 Syncing user data...")
        result = self._request(
            "POST",
            "/api/sync/user",
            json={"access_token": self.access_token, "time_ranges": time_ranges}
        )
        
        self.user_id = result["data"]["user_id"]
        print(f"✅ Sync started for {result['data']['user_name']}")
        
        return result
    
    def get_sync_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get sync status for a user"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        return self._request("GET", f"/api/sync/status/{user_id}")
    
    def get_user(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user information"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        return self._request("GET", f"/api/user/{user_id}")
    
    # =================================================================
    # USER PROFILE
    # =================================================================
    
    def get_user_profile(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive user music profile"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request("GET", f"/api/profile/{user_id}")
        return result["data"]
    
    # =================================================================
    # TOP ARTISTS
    # =================================================================
    
    def get_top_artists(
        self,
        user_id: Optional[str] = None,
        time_range: str = "long_term",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's top artists
        
        Args:
            user_id: User UUID (uses authenticated user if not provided)
            time_range: 'short_term', 'medium_term', or 'long_term'
            limit: Number of artists (1-50)
        
        Returns:
            List of top artists
        """
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "GET",
            f"/api/top-artists/{user_id}",
            params={"time_range": time_range, "limit": limit}
        )
        return result["data"]
    
    def sync_top_artists(self) -> Dict[str, Any]:
        """Sync top artists from Spotify"""
        print("📊 Syncing top artists...")
        result = self._request("POST", "/api/sync/top-artists")
        self.user_id = result["data"]["user_id"]
        return result
    
    # =================================================================
    # TOP TRACKS
    # =================================================================
    
    def get_top_tracks(
        self,
        user_id: Optional[str] = None,
        time_range: str = "long_term",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's top tracks
        
        Args:
            user_id: User UUID (uses authenticated user if not provided)
            time_range: 'short_term', 'medium_term', or 'long_term'
            limit: Number of tracks (1-50)
        
        Returns:
            List of top tracks
        """
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "GET",
            f"/api/top-tracks/{user_id}",
            params={"time_range": time_range, "limit": limit}
        )
        return result["data"]
    
    def sync_top_tracks(self) -> Dict[str, Any]:
        """Sync top tracks from Spotify"""
        print("📊 Syncing top tracks...")
        result = self._request("POST", "/api/sync/top-tracks")
        self.user_id = result["data"]["user_id"]
        return result
    
    # =================================================================
    # SAVED TRACKS
    # =================================================================
    
    def get_saved_tracks(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's saved tracks"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "GET",
            f"/api/saved-tracks/{user_id}",
            params={"limit": limit}
        )
        return result["data"]
    
    def sync_saved_tracks(self) -> Dict[str, Any]:
        """Sync saved tracks from Spotify"""
        print("📊 Syncing saved tracks...")
        result = self._request("POST", "/api/sync/saved-tracks")
        self.user_id = result["data"]["user_id"]
        return result
    
    # =================================================================
    # PLAYLISTS
    # =================================================================
    
    def get_playlists(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's playlists"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "GET",
            f"/api/playlists/{user_id}",
            params={"limit": limit}
        )
        return result["data"]
    
    def get_playlist_tracks(
        self,
        playlist_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tracks from a specific playlist"""
        result = self._request(
            "GET",
            f"/api/playlist/{playlist_id}/tracks",
            params={"limit": limit}
        )
        return result["data"]
    
    def sync_playlists(self) -> Dict[str, Any]:
        """Sync all playlists from Spotify"""
        print("📊 Syncing playlists...")
        result = self._request("POST", "/api/sync/playlists")
        return result
    
    def sync_playlist_tracks(self, playlist_id: str) -> Dict[str, Any]:
        """Sync tracks for a specific playlist"""
        print(f"📊 Syncing tracks for playlist {playlist_id}...")
        result = self._request("POST", f"/api/sync/playlist/{playlist_id}")
        return result
    
    # =================================================================
    # GENRES
    # =================================================================
    
    def get_genres(
        self,
        user_id: Optional[str] = None,
        time_range: str = "long_term",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's genre preferences"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "GET",
            f"/api/genres/{user_id}",
            params={"time_range": time_range, "limit": limit}
        )
        return result["data"]
    
    def extract_genres(self, lastfm_tags: List[str]) -> List[str]:
        """
        Extract clean genres from Last.fm tags
        
        Args:
            lastfm_tags: List of tags from Last.fm
        
        Returns:
            List of cleaned genre names
        """
        result = self._request(
            "POST",
            "/api/genres/extract",
            json={"lastfm_tags": lastfm_tags}
        )
        return result["data"]["genres"]
    
    def compute_genres(
        self,
        user_id: Optional[str] = None,
        time_range: str = "long_term"
    ) -> List[Dict[str, Any]]:
        """Compute genre preferences from top artists"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "POST",
            f"/api/genres/compute/{user_id}",
            params={"time_range": time_range}
        )
        return result["data"]["genres"]
    
    # =================================================================
    # AUDIO FEATURES
    # =================================================================
    
    def get_audio_features(self, track_id: str) -> Dict[str, Any]:
        """Get audio features for a track"""
        result = self._request("GET", f"/api/audio-features/{track_id}")
        return result["data"]
    
    def save_audio_features(self, track_ids: List[str]) -> Dict[str, Any]:
        """Fetch and save audio features for multiple tracks"""
        result = self._request(
            "POST",
            "/api/audio-features",
            json={"track_ids": track_ids}
        )
        return result["data"]
    
    # =================================================================
    # COMPATIBILITY
    # =================================================================
    
    def compute_compatibility(self, user1_id: str, user2_id: str) -> Dict[str, Any]:
        """Compute compatibility score between two users"""
        result = self._request(
            "POST",
            "/api/compatibility",
            json={"user1_id": user1_id, "user2_id": user2_id}
        )
        return result["data"]
    
    def get_matches(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get potential matches for a user"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        result = self._request(
            "GET",
            f"/api/matches/{user_id}",
            params={"limit": limit}
        )
        return result["data"]
    
    # =================================================================
    # UTILITIES
    # =================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self._request("GET", "/health")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API statistics"""
        result = self._request("GET", "/api/stats")
        return result["data"]
    
    def print_profile_summary(self, user_id: Optional[str] = None):
        """Print a nice summary of user's music profile"""
        user_id = user_id or self.user_id
        if not user_id:
            raise ValueError("Must provide user_id or authenticate first")
        
        profile = self.get_user_profile(user_id)
        user_info = self.get_user(user_id)
        
        print("\n" + "="*60)
        print("🎵 MUSIC PROFILE SUMMARY")
        print("="*60)
        
        print(f"\n👤 User: {user_info['data']['display_name']}")
        print(f"📧 Email: {user_info['data']['email']}")
        print(f"🌍 Country: {user_info['data']['country']}")
        print(f"👥 Followers: {user_info['data']['followers_count']:,}")
        
        print(f"\n📊 Statistics:")
        print(f"  • Saved tracks: {profile['saved_tracks_count']:,}")
        print(f"  • Top genres: {len(profile['genre_preferences'])}")
        print(f"  • Top artists: {len(profile['top_artists'])}")
        
        print(f"\n🎭 Top 5 Genres:")
        for i, genre in enumerate(profile['genre_preferences'][:5], 1):
            print(f"  {i}. {genre['genre']}: {genre['weight']:.2f} ({genre['frequency']} artists)")
        
        print(f"\n⭐ Top 5 Artists:")
        for artist in profile['top_artists'][:5]:
            print(f"  • {artist['artists']['name']} ({artist['artists']['popularity']}% popularity)")
        
        print("\n" + "="*60 + "\n")


# =====================================================================
# EXAMPLE USAGE
# =====================================================================

if __name__ == "__main__":
    import time
    
    print("🎵 MusicMatch Client Example\n")
    
    # Initialize client
    client = MusicMatchClient()
    
    # Authenticate
    try:
        client.authenticate()
    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled")
        exit(1)
    
    # Sync data
    print("\n📊 Syncing all user data...")
    sync_result = client.sync_user_data()
    print(f"✅ {sync_result['message']}")
    
    # Wait for background sync
    print("⏳ Waiting for data processing...")
    time.sleep(3)
    
    # Print summary
    try:
        client.print_profile_summary()
    except Exception as e:
        print(f"⚠️ Could not load profile yet: {e}")
        print("💡 Try again in a few moments after sync completes")
    
    # Get top artists
    print("\n📊 Fetching top artists...")
    try:
        artists = client.get_top_artists(limit=5)
        print("⭐ Top 5 Artists:")
        for item in artists:
            artist = item["artists"]
            print(f"  {item['position']}. {artist['name']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Get genres
    print("\n🎭 Fetching genres...")
    try:
        genres = client.get_genres(limit=10)
        print("Top 10 Genres:")
        for genre in genres:
            print(f"  • {genre['genre']}: {genre['weight']:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Health check
    print("\n💚 Checking API health...")
    health = client.health_check()
    print(f"Status: {health['status']} | Database: {health['database']}")
    
    print("\n✅ Done!")
