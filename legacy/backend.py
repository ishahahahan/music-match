"""
MusicMatch Backend API
======================
FastAPI backend for Spotify data extraction and analysis integrated with Supabase database.

This API provides endpoints to:
- Authenticate users and sync Spotify data
- Extract and store user music data (top artists, tracks, playlists, etc.)
- Compute genre preferences and audio features
- Calculate compatibility scores between users
- Access user music profiles and recommendations

Requirements:
- FastAPI: pip install fastapi
- Uvicorn: pip install uvicorn[standard]
- All dependencies from requirements.txt

Environment Variables (.env):
- CLIENT_ID: Spotify API Client ID
- CLIENT_SECRET: Spotify API Client Secret
- REDIRECT_URI: Spotify OAuth redirect URI
- SUPABASE_URL: Supabase project URL
- SUPABASE_ANON_KEY: Supabase anonymous key
- SUPABASE_SERVICE_ROLE_KEY: Supabase service role key (optional)
- LASTFM_API_KEY: Last.fm API key (optional)

Run with: uvicorn backend:app --reload
"""

import os
import json
import time
import spotipy
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import requests

from database_helper import MusicMatchDB
from lastfm import GenreExtractor

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="MusicMatch API",
    description="Spotify data extraction and music matching API",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Initialize database connection
try:
    db = MusicMatchDB()
    print("✅ Database connection established")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    db = None

# Initialize genre extractor
genre_extractor = GenreExtractor()

# Spotify API configuration
SPOTIFY_SCOPE = "user-library-read user-read-currently-playing app-remote-control user-modify-playback-state user-read-playback-state user-read-recently-played playlist-read-private playlist-modify-public playlist-modify-private user-follow-read user-follow-modify user-top-read user-read-playback-position user-read-email user-read-private user-library-modify user-read-playback-state playlist-read-collaborative"

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SyncRequest(BaseModel):
    """Request model for syncing user data"""
    access_token: str
    time_ranges: Optional[List[str]] = ["short_term", "medium_term", "long_term"]

class PlaylistSyncRequest(BaseModel):
    """Request model for syncing playlist data"""
    playlist_id: str
    limit: Optional[int] = 50

class AudioFeaturesRequest(BaseModel):
    """Request model for fetching audio features"""
    track_ids: List[str]

class CompatibilityRequest(BaseModel):
    """Request model for computing compatibility"""
    user1_id: str
    user2_id: str

class GenreExtractionRequest(BaseModel):
    """Request model for extracting genres"""
    lastfm_tags: List[str]

class APIResponse(BaseModel):
    """Standard API response model"""
    status: str
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "MusicMatch API",
        "version": "1.0.0",
        "status": "online",
        "database": "connected" if db else "disconnected",
        "endpoints": {
            "auth": "/auth/callback",
            "sync": "/api/sync/user",
            "user": "/api/user/{user_id}",
            "playlists": "/api/playlists/{user_id}",
            "profile": "/api/profile/{user_id}"
        }
    }

@app.get("/auth/callback")
async def auth_callback(code: str, state: Optional[str] = None):
    """
    Spotify OAuth callback endpoint
    Call this with the authorization code from Spotify
    """
    try:
        auth_manager = SpotifyOAuth(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            redirect_uri=os.getenv("REDIRECT_URI"),
            scope=SPOTIFY_SCOPE
        )
        
        token = auth_manager.get_access_token(code)
        
        return {
            "status": "success",
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token"),
            "expires_in": token.get("expires_in"),
            "message": "Authentication successful! Use the access_token for API requests."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/login")
async def login():
    """Generate Spotify login URL"""
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope=SPOTIFY_SCOPE
    )
    
    auth_url = auth_manager.get_authorize_url()
    
    return {
        "status": "success",
        "auth_url": auth_url,
        "message": "Visit this URL to authenticate with Spotify"
    }

# =============================================================================
# USER DATA SYNC ENDPOINTS
# =============================================================================

@app.post("/api/sync/user")
async def sync_user_data(request: SyncRequest, background_tasks: BackgroundTasks):
    """
    Sync all user data from Spotify to database
    
    Query Parameters:
    - access_token: Spotify access token
    - time_ranges: List of time ranges (short_term, medium_term, long_term)
    
    Returns: User ID and sync status
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        # Create Spotify client with provided token
        sp = spotipy.Spotify(auth=request.access_token, requests_timeout=20)
        
        # Get current user
        user_data = sp.current_user()
        
        # Create/update user in database
        db_user = db.create_or_update_user(user_data)
        user_id = db_user["id"]
        
        # Run sync in background
        background_tasks.add_task(
            _background_sync_all_data,
            sp,
            user_id,
            request.time_ranges
        )
        
        return APIResponse(
            status="success",
            message="Sync started",
            data={
                "user_id": user_id,
                "user_name": user_data["display_name"],
                "email": user_data["email"],
                "sync_started": True
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sync failed: {str(e)}")

async def _background_sync_all_data(sp, user_id: str, time_ranges: List[str]):
    """Background task to sync all user data"""
    try:
        # Sync top artists for each time range
        for time_range in time_ranges:
            print(f"Syncing top artists for {time_range}...")
            top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
            db.save_user_top_artists(user_id, top_artists["items"], time_range)
            db.compute_user_genre_preferences(user_id, time_range)
            time.sleep(0.5)
        
        # Sync top tracks for each time range
        for time_range in time_ranges:
            print(f"Syncing top tracks for {time_range}...")
            top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
            db.save_user_top_tracks(user_id, top_tracks["items"], time_range)
            
            # Get audio features for tracks
            track_ids = [track["id"] for track in top_tracks["items"]]
            audio_features = sp.audio_features(track_ids)
            db.batch_save_audio_features(audio_features)
            time.sleep(0.5)
        
        # Sync saved tracks
        print("Syncing saved tracks...")
        saved_tracks = sp.current_user_saved_tracks(limit=50)
        db.save_user_saved_tracks(user_id, saved_tracks["items"])
        
        # Sync playlists
        print("Syncing playlists...")
        playlists = sp.current_user_playlists(limit=50)
        db.save_user_playlists(user_id, playlists["items"])
        
        print(f"✅ Sync completed for user {user_id}")
        
    except Exception as e:
        print(f"❌ Background sync failed: {str(e)}")

@app.get("/api/sync/status/{user_id}")
async def get_sync_status(user_id: str):
    """Get sync status for a user"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        # Get user profile to check if data exists
        profile = db.get_user_music_profile(user_id)
        
        return APIResponse(
            status="success",
            message="Sync status retrieved",
            data={
                "user_id": user_id,
                "saved_tracks_count": profile.get("saved_tracks_count", 0),
                "genres_count": len(profile.get("genre_preferences", [])),
                "top_artists_count": len(profile.get("top_artists", [])),
                "last_synced": datetime.now().isoformat()
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get sync status: {str(e)}")

# =============================================================================
# USER PROFILE ENDPOINTS
# =============================================================================

@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    """Get user information from database"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            status="success",
            message="User retrieved",
            data=result.data[0]
        ).dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get user: {str(e)}")

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """
    Get comprehensive music profile for a user
    
    Returns:
    - Top artists across different time ranges
    - Genre preferences with weights
    - Saved tracks count
    - Audio feature preferences
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        profile = db.get_user_music_profile(user_id)
        
        return APIResponse(
            status="success",
            message="Profile retrieved",
            data=profile
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get profile: {str(e)}")

# =============================================================================
# TOP ARTISTS ENDPOINTS
# =============================================================================

@app.get("/api/top-artists/{user_id}")
async def get_top_artists(
    user_id: str,
    time_range: str = Query("long_term", regex="^(short_term|medium_term|long_term)$"),
    limit: int = Query(50, ge=1, le=50)
):
    """
    Get user's top artists for a specific time range
    
    Query Parameters:
    - time_range: short_term (last 4 weeks), medium_term (last 6 months), long_term (all time)
    - limit: Number of artists to return (max 50)
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("user_top_artists").select(
            "position, time_range, artists!inner(name, genres, popularity, followers_count)"
        ).eq("user_id", user_id).eq("time_range", time_range).order("position").limit(limit).execute()
        
        return APIResponse(
            status="success",
            message=f"Top {len(result.data)} artists retrieved",
            data=result.data
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get top artists: {str(e)}")

@app.post("/api/sync/top-artists")
async def sync_top_artists(access_token: str = Query(...)):
    """
    Sync user's top artists from Spotify
    
    Query Parameters:
    - access_token: Spotify access token
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        sp = spotipy.Spotify(auth=access_token, requests_timeout=20)
        user_data = sp.current_user()
        
        db_user = db.create_or_update_user(user_data)
        user_id = db_user["id"]
        
        # Sync all time ranges
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
            db.save_user_top_artists(user_id, top_artists["items"], time_range)
            db.compute_user_genre_preferences(user_id, time_range)
        
        return APIResponse(
            status="success",
            message="Top artists synced successfully",
            data={"user_id": user_id}
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync top artists: {str(e)}")

# =============================================================================
# TOP TRACKS ENDPOINTS
# =============================================================================

@app.get("/api/top-tracks/{user_id}")
async def get_top_tracks(
    user_id: str,
    time_range: str = Query("long_term", regex="^(short_term|medium_term|long_term)$"),
    limit: int = Query(50, ge=1, le=50)
):
    """
    Get user's top tracks for a specific time range
    
    Query Parameters:
    - time_range: short_term (last 4 weeks), medium_term (last 6 months), long_term (all time)
    - limit: Number of tracks to return (max 50)
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("user_top_tracks").select(
            "position, time_range, tracks!inner(name, popularity, duration_ms, albums!inner(name, release_date), artists!inner(name))"
        ).eq("user_id", user_id).eq("time_range", time_range).order("position").limit(limit).execute()
        
        return APIResponse(
            status="success",
            message=f"Top {len(result.data)} tracks retrieved",
            data=result.data
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get top tracks: {str(e)}")

@app.post("/api/sync/top-tracks")
async def sync_top_tracks(access_token: str = Query(...)):
    """
    Sync user's top tracks from Spotify
    
    Query Parameters:
    - access_token: Spotify access token
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        sp = spotipy.Spotify(auth=access_token, requests_timeout=20)
        user_data = sp.current_user()
        
        db_user = db.create_or_update_user(user_data)
        user_id = db_user["id"]
        
        # Sync all time ranges and get audio features
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
            db.save_user_top_tracks(user_id, top_tracks["items"], time_range)
            
            # Get audio features
            track_ids = [track["id"] for track in top_tracks["items"]]
            audio_features = sp.audio_features(track_ids)
            db.batch_save_audio_features(audio_features)
        
        return APIResponse(
            status="success",
            message="Top tracks synced successfully",
            data={"user_id": user_id}
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync top tracks: {str(e)}")

# =============================================================================
# SAVED TRACKS ENDPOINTS
# =============================================================================

@app.get("/api/saved-tracks/{user_id}")
async def get_saved_tracks(user_id: str, limit: int = Query(50, ge=1, le=50)):
    """Get user's saved tracks"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("user_saved_tracks").select(
            "saved_at, tracks!inner(name, popularity, duration_ms, albums!inner(name))"
        ).eq("user_id", user_id).order("saved_at", desc=True).limit(limit).execute()
        
        return APIResponse(
            status="success",
            message=f"Retrieved {len(result.data)} saved tracks",
            data=result.data
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get saved tracks: {str(e)}")

@app.post("/api/sync/saved-tracks")
async def sync_saved_tracks(access_token: str = Query(...)):
    """Sync user's saved tracks from Spotify"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        sp = spotipy.Spotify(auth=access_token, requests_timeout=20)
        user_data = sp.current_user()
        
        db_user = db.create_or_update_user(user_data)
        user_id = db_user["id"]
        
        saved_tracks = sp.current_user_saved_tracks(limit=50)
        db.save_user_saved_tracks(user_id, saved_tracks["items"])
        
        return APIResponse(
            status="success",
            message="Saved tracks synced successfully",
            data={"user_id": user_id, "tracks_synced": len(saved_tracks["items"])}
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync saved tracks: {str(e)}")

# =============================================================================
# PLAYLISTS ENDPOINTS
# =============================================================================

@app.get("/api/playlists/{user_id}")
async def get_user_playlists(user_id: str, limit: int = Query(50, ge=1, le=50)):
    """Get user's playlists"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("playlists").select(
            "id, name, description, is_public, tracks_total, image_url"
        ).eq("user_id", user_id).order("name").limit(limit).execute()
        
        return APIResponse(
            status="success",
            message=f"Retrieved {len(result.data)} playlists",
            data=result.data
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get playlists: {str(e)}")

@app.post("/api/sync/playlists")
async def sync_playlists(access_token: str = Query(...)):
    """Sync user's playlists from Spotify"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        sp = spotipy.Spotify(auth=access_token, requests_timeout=20)
        user_data = sp.current_user()
        
        db_user = db.create_or_update_user(user_data)
        user_id = db_user["id"]
        
        playlists = sp.current_user_playlists(limit=50)
        db.save_user_playlists(user_id, playlists["items"])
        
        return APIResponse(
            status="success",
            message="Playlists synced successfully",
            data={"user_id": user_id, "playlists_synced": len(playlists["items"])}
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync playlists: {str(e)}")

@app.get("/api/playlist/{playlist_id}/tracks")
async def get_playlist_tracks(playlist_id: str, limit: int = Query(50, ge=1, le=50)):
    """Get tracks from a specific playlist"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("playlist_tracks").select(
            "position, added_at, tracks!inner(name, popularity, duration_ms)"
        ).eq("playlist_id", playlist_id).order("position").limit(limit).execute()
        
        return APIResponse(
            status="success",
            message=f"Retrieved {len(result.data)} tracks",
            data=result.data
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get playlist tracks: {str(e)}")

@app.post("/api/sync/playlist/{playlist_id}")
async def sync_playlist_tracks(playlist_id: str, access_token: str = Query(...)):
    """Sync tracks for a specific playlist"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        sp = spotipy.Spotify(auth=access_token, requests_timeout=20)
        
        playlist_tracks = sp.playlist_tracks(playlist_id, limit=50)
        db.save_playlist_tracks(playlist_id, playlist_tracks["items"])
        
        return APIResponse(
            status="success",
            message="Playlist tracks synced successfully",
            data={"playlist_id": playlist_id, "tracks_synced": len(playlist_tracks["items"])}
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync playlist tracks: {str(e)}")

# =============================================================================
# GENRES ENDPOINTS
# =============================================================================

@app.get("/api/genres/{user_id}")
async def get_user_genres(
    user_id: str,
    time_range: str = Query("long_term", regex="^(short_term|medium_term|long_term)$"),
    limit: int = Query(50, ge=1, le=50)
):
    """
    Get user's genre preferences
    
    Query Parameters:
    - time_range: short_term, medium_term, or long_term
    - limit: Number of genres to return
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("user_genre_preferences").select(
            "genre, weight, frequency"
        ).eq("user_id", user_id).eq("time_range", time_range).order("weight", desc=True).limit(limit).execute()
        
        return APIResponse(
            status="success",
            message=f"Retrieved {len(result.data)} genres",
            data=result.data
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get genres: {str(e)}")

@app.post("/api/genres/extract")
async def extract_genres(request: GenreExtractionRequest):
    """
    Extract and clean genres from Last.fm tags
    
    Request Body:
    - lastfm_tags: List of tags from Last.fm API
    
    Returns:
    - List of cleaned genre names
    """
    try:
        genres = genre_extractor.extract_genres(request.lastfm_tags)
        
        return APIResponse(
            status="success",
            message="Genres extracted successfully",
            data={
                "input_tags_count": len(request.lastfm_tags),
                "output_genres_count": len(genres),
                "genres": genres
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract genres: {str(e)}")

@app.post("/api/genres/compute/{user_id}")
async def compute_user_genres(user_id: str, time_range: str = Query("long_term")):
    """Compute genre preferences from user's top artists"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        genres = db.compute_user_genre_preferences(user_id, time_range)
        
        return APIResponse(
            status="success",
            message="Genre preferences computed successfully",
            data={
                "user_id": user_id,
                "time_range": time_range,
                "genres_count": len(genres),
                "genres": genres
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to compute genres: {str(e)}")

# =============================================================================
# AUDIO FEATURES ENDPOINTS
# =============================================================================

@app.post("/api/audio-features")
async def save_audio_features(request: AudioFeaturesRequest, access_token: str = Query(...)):
    """
    Get audio features for tracks and save to database
    
    Request Body:
    - track_ids: List of Spotify track IDs
    
    Query Parameters:
    - access_token: Spotify access token
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        sp = spotipy.Spotify(auth=access_token, requests_timeout=20)
        
        audio_features = sp.audio_features(request.track_ids)
        db.batch_save_audio_features(audio_features)
        
        return APIResponse(
            status="success",
            message="Audio features saved successfully",
            data={
                "tracks_processed": len([f for f in audio_features if f]),
                "tracks_total": len(request.track_ids)
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save audio features: {str(e)}")

@app.get("/api/audio-features/{track_id}")
async def get_track_audio_features(track_id: str):
    """Get audio features for a specific track"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = db.supabase.table("track_audio_features").select("*").eq("track_id", track_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Audio features not found")
        
        return APIResponse(
            status="success",
            message="Audio features retrieved",
            data=result.data[0]
        ).dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get audio features: {str(e)}")

# =============================================================================
# COMPATIBILITY ENDPOINTS
# =============================================================================

@app.post("/api/compatibility")
async def compute_compatibility(request: CompatibilityRequest):
    """
    Compute compatibility score between two users
    
    Request Body:
    - user1_id: First user UUID
    - user2_id: Second user UUID
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        compatibility = db.compute_compatibility_score(request.user1_id, request.user2_id)
        
        return APIResponse(
            status="success",
            message="Compatibility computed successfully",
            data=compatibility
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to compute compatibility: {str(e)}")

@app.get("/api/matches/{user_id}")
async def get_potential_matches(user_id: str, limit: int = Query(20, ge=1, le=100)):
    """
    Get potential matches for a user based on compatibility
    
    Query Parameters:
    - limit: Maximum number of matches to return
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        matches = db.get_potential_matches(user_id, limit)
        
        return APIResponse(
            status="success",
            message=f"Retrieved {len(matches)} potential matches",
            data=matches
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get matches: {str(e)}")

# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_api_stats():
    """Get API statistics"""
    if not db:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        # Get various statistics from database
        users_result = db.supabase.table("users").select("count", count="exact").execute()
        artists_result = db.supabase.table("artists").select("count", count="exact").execute()
        tracks_result = db.supabase.table("tracks").select("count", count="exact").execute()
        
        return APIResponse(
            status="success",
            message="Statistics retrieved",
            data={
                "total_users": users_result.count,
                "total_artists": artists_result.count,
                "total_tracks": tracks_result.count,
                "timestamp": datetime.now().isoformat()
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get statistics: {str(e)}")