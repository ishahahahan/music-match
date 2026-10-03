# MusicMatch API Documentation

## Overview

The MusicMatch API is a FastAPI backend that consolidates Spotify data extraction, genre analysis, and user matching functionality. It provides RESTful endpoints to sync music data from Spotify, compute user preferences, and calculate compatibility between users.

## Base URL

```
http://localhost:8000
```

## Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
pip install fastapi
pip install uvicorn[standard]
```

### Environment Setup

Create a `.env` file in the project root:

```env
# Spotify API
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://localhost:8000/auth/callback

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Last.fm (optional)
LASTFM_API_KEY=your_lastfm_api_key
```

### Running the Server

```bash
# With auto-reload
uvicorn backend:app --reload

# Production
uvicorn backend:app --host 0.0.0.0 --port 8000

# With specific workers
uvicorn backend:app --workers 4
```

The API will be available at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs` (Swagger UI)
Alternative docs: `http://localhost:8000/redoc` (ReDoc)

---

## API Endpoints

### Authentication

#### 1. Get Login URL
```http
GET /auth/login
```

**Description:** Generate Spotify authentication URL

**Response:**
```json
{
  "status": "success",
  "auth_url": "https://accounts.spotify.com/authorize?...",
  "message": "Visit this URL to authenticate with Spotify"
}
```

#### 2. Handle OAuth Callback
```http
GET /auth/callback?code={auth_code}&state={state}
```

**Description:** Exchange authorization code for access token

**Parameters:**
- `code` (query): Authorization code from Spotify
- `state` (query): Optional state parameter

**Response:**
```json
{
  "status": "success",
  "access_token": "BQD...",
  "refresh_token": "AQD...",
  "expires_in": 3600,
  "message": "Authentication successful! Use the access_token for API requests."
}
```

---

### User Data Synchronization

#### 1. Sync All User Data
```http
POST /api/sync/user
```

**Description:** Comprehensive sync of all user data from Spotify

**Request Body:**
```json
{
  "access_token": "BQD...",
  "time_ranges": ["short_term", "medium_term", "long_term"]
}
```

**Query Parameters:**
- `access_token`: Spotify access token (required)

**Response:**
```json
{
  "status": "success",
  "message": "Sync started",
  "data": {
    "user_id": "uuid",
    "user_name": "John Doe",
    "email": "john@example.com",
    "sync_started": true
  }
}
```

**What Gets Synced:**
- Top artists (all time ranges)
- Top tracks (all time ranges)
- Saved tracks
- Playlists
- Genre preferences
- Audio features

#### 2. Get Sync Status
```http
GET /api/sync/status/{user_id}
```

**Description:** Check sync status for a user

**Response:**
```json
{
  "status": "success",
  "message": "Sync status retrieved",
  "data": {
    "user_id": "uuid",
    "saved_tracks_count": 150,
    "genres_count": 45,
    "top_artists_count": 50,
    "last_synced": "2024-01-15T10:30:00"
  }
}
```

---

### User Profile

#### 1. Get User Information
```http
GET /api/user/{user_id}
```

**Description:** Get user profile from database

**Response:**
```json
{
  "status": "success",
  "message": "User retrieved",
  "data": {
    "id": "uuid",
    "spotify_id": "spotify123",
    "email": "john@example.com",
    "display_name": "John Doe",
    "country": "US",
    "product": "premium",
    "followers_count": 150,
    "profile_image_url": "https://..."
  }
}
```

#### 2. Get User Music Profile
```http
GET /api/profile/{user_id}
```

**Description:** Comprehensive music profile with all preferences

**Response:**
```json
{
  "status": "success",
  "message": "Profile retrieved",
  "data": {
    "top_artists": [...],
    "genre_preferences": [...],
    "saved_tracks_count": 150
  }
}
```

---

### Top Artists

#### 1. Get Top Artists
```http
GET /api/top-artists/{user_id}?time_range=long_term&limit=50
```

**Description:** Get user's top artists

**Query Parameters:**
- `time_range`: `short_term`, `medium_term`, or `long_term` (default: `long_term`)
- `limit`: Number of artists to return, 1-50 (default: 50)

**Response:**
```json
{
  "status": "success",
  "message": "Top 50 artists retrieved",
  "data": [
    {
      "position": 1,
      "time_range": "long_term",
      "artists": {
        "name": "Artist Name",
        "genres": ["genre1", "genre2"],
        "popularity": 85,
        "followers_count": 1000000
      }
    }
  ]
}
```

#### 2. Sync Top Artists
```http
POST /api/sync/top-artists?access_token={token}
```

**Description:** Sync top artists from Spotify

**Query Parameters:**
- `access_token`: Spotify access token (required)

**Response:**
```json
{
  "status": "success",
  "message": "Top artists synced successfully",
  "data": {
    "user_id": "uuid"
  }
}
```

---

### Top Tracks

#### 1. Get Top Tracks
```http
GET /api/top-tracks/{user_id}?time_range=long_term&limit=50
```

**Description:** Get user's top tracks

**Query Parameters:**
- `time_range`: `short_term`, `medium_term`, or `long_term` (default: `long_term`)
- `limit`: Number of tracks to return, 1-50 (default: 50)

**Response:**
```json
{
  "status": "success",
  "message": "Top 50 tracks retrieved",
  "data": [
    {
      "position": 1,
      "time_range": "long_term",
      "tracks": {
        "name": "Track Name",
        "popularity": 85,
        "duration_ms": 180000
      }
    }
  ]
}
```

#### 2. Sync Top Tracks
```http
POST /api/sync/top-tracks?access_token={token}
```

**Description:** Sync top tracks and audio features from Spotify

**Query Parameters:**
- `access_token`: Spotify access token (required)

---

### Saved Tracks

#### 1. Get Saved Tracks
```http
GET /api/saved-tracks/{user_id}?limit=50
```

**Description:** Get user's saved/liked tracks

**Query Parameters:**
- `limit`: Number of tracks to return, 1-50 (default: 50)

#### 2. Sync Saved Tracks
```http
POST /api/sync/saved-tracks?access_token={token}
```

**Description:** Sync saved tracks from Spotify

---

### Playlists

#### 1. Get User Playlists
```http
GET /api/playlists/{user_id}?limit=50
```

**Description:** Get all user playlists

**Query Parameters:**
- `limit`: Number of playlists to return (default: 50)

**Response:**
```json
{
  "status": "success",
  "message": "Retrieved 10 playlists",
  "data": [
    {
      "id": "playlist123",
      "name": "My Awesome Playlist",
      "description": "A great playlist",
      "is_public": true,
      "tracks_total": 50,
      "image_url": "https://..."
    }
  ]
}
```

#### 2. Sync All Playlists
```http
POST /api/sync/playlists?access_token={token}
```

**Description:** Sync all user playlists

#### 3. Get Playlist Tracks
```http
GET /api/playlist/{playlist_id}/tracks?limit=50
```

**Description:** Get tracks from a specific playlist

#### 4. Sync Playlist Tracks
```http
POST /api/sync/playlist/{playlist_id}?access_token={token}
```

**Description:** Sync tracks for a specific playlist

---

### Genres

#### 1. Get User Genres
```http
GET /api/genres/{user_id}?time_range=long_term&limit=50
```

**Description:** Get user's genre preferences with weights

**Query Parameters:**
- `time_range`: `short_term`, `medium_term`, or `long_term` (default: `long_term`)
- `limit`: Number of genres to return (default: 50)

**Response:**
```json
{
  "status": "success",
  "message": "Retrieved 45 genres",
  "data": [
    {
      "genre": "pop",
      "weight": 0.85,
      "frequency": 25
    },
    {
      "genre": "rock",
      "weight": 0.65,
      "frequency": 18
    }
  ]
}
```

#### 2. Extract Genres from Last.fm Tags
```http
POST /api/genres/extract
```

**Description:** Extract clean genres from Last.fm tags

**Request Body:**
```json
{
  "lastfm_tags": ["rock", "alternative rock", "seen live", "2020s", "indie rock"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Genres extracted successfully",
  "data": {
    "input_tags_count": 5,
    "output_genres_count": 3,
    "genres": ["rock", "alternative rock", "indie rock"]
  }
}
```

#### 3. Compute User Genres
```http
POST /api/genres/compute/{user_id}?time_range=long_term
```

**Description:** Compute genre preferences from top artists

**Query Parameters:**
- `time_range`: `short_term`, `medium_term`, or `long_term` (default: `long_term`)

---

### Audio Features

#### 1. Get Track Audio Features
```http
GET /api/audio-features/{track_id}
```

**Description:** Get audio features for a specific track

**Response:**
```json
{
  "status": "success",
  "message": "Audio features retrieved",
  "data": {
    "track_id": "track123",
    "danceability": 0.75,
    "energy": 0.82,
    "key": 0,
    "loudness": -5.3,
    "mode": 1,
    "speechiness": 0.04,
    "acousticness": 0.12,
    "instrumentalness": 0.0,
    "liveness": 0.15,
    "valence": 0.88,
    "tempo": 128.5,
    "time_signature": 4
  }
}
```

#### 2. Save Audio Features
```http
POST /api/audio-features?access_token={token}
```

**Description:** Fetch and save audio features for multiple tracks

**Request Body:**
```json
{
  "track_ids": ["track1", "track2", "track3"]
}
```

**Query Parameters:**
- `access_token`: Spotify access token (required)

---

### User Compatibility

#### 1. Compute Compatibility Score
```http
POST /api/compatibility
```

**Description:** Calculate compatibility between two users

**Request Body:**
```json
{
  "user1_id": "uuid1",
  "user2_id": "uuid2"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Compatibility computed successfully",
  "data": {
    "user1_id": "uuid1",
    "user2_id": "uuid2",
    "genre_overlap_score": 0.75,
    "artist_similarity_score": 0.65,
    "audio_feature_similarity": 0.70,
    "overall_compatibility": 0.70,
    "computed_at": "2024-01-15T10:30:00"
  }
}
```

#### 2. Get Potential Matches
```http
GET /api/matches/{user_id}?limit=20
```

**Description:** Get potential matches for a user

**Query Parameters:**
- `limit`: Maximum number of matches, 1-100 (default: 20)

---

### Health & Status

#### 1. Health Check
```http
GET /health
```

**Description:** Check API health status

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### 2. Get API Statistics
```http
GET /api/stats
```

**Description:** Get database statistics

**Response:**
```json
{
  "status": "success",
  "message": "Statistics retrieved",
  "data": {
    "total_users": 150,
    "total_artists": 5000,
    "total_tracks": 25000,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

---

## Authentication Flow

### Step 1: Get Login URL
```bash
curl http://localhost:8000/auth/login
```

### Step 2: User Visits URL
Visit the URL returned by the previous endpoint to authenticate with Spotify.

### Step 3: Spotify Redirects to Callback
Spotify redirects to: `http://localhost:8000/auth/callback?code=AUTH_CODE`

### Step 4: Exchange Code for Token
```bash
curl "http://localhost:8000/auth/callback?code=AUTH_CODE"
```

### Step 5: Use Access Token
Use the returned access token for API requests:
```bash
curl -X POST "http://localhost:8000/api/sync/user" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_TOKEN"}'
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- **200**: Success
- **400**: Bad request (validation error)
- **404**: Resource not found
- **503**: Service unavailable (database connection failed)

---

## Response Format

All successful responses follow this format:

```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": {...},
  "error": null,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Rate Limiting

The API respects Spotify's rate limits:
- Default: 429 requests per minute per IP
- If rate limited, retry after the `Retry-After` header

---

## Usage Examples

### Example 1: Complete User Sync Workflow

```bash
# 1. Get login URL
curl http://localhost:8000/auth/login

# 2. User authenticates (manually via browser)

# 3. Get token from callback URL
TOKEN="BQD..."

# 4. Sync all user data
curl -X POST "http://localhost:8000/api/sync/user" \
  -H "Content-Type: application/json" \
  -d "{\"access_token\": \"$TOKEN\"}"

# 5. Check sync status
USER_ID="uuid"
curl http://localhost:8000/api/sync/status/$USER_ID

# 6. Get user profile
curl http://localhost:8000/api/profile/$USER_ID
```

### Example 2: Get Top Artists with Genres

```bash
curl http://localhost:8000/api/top-artists/uuid?time_range=long_term&limit=10
curl http://localhost:8000/api/genres/uuid?time_range=long_term
```

### Example 3: Compare Two Users

```bash
curl -X POST "http://localhost:8000/api/compatibility" \
  -H "Content-Type: application/json" \
  -d '{"user1_id": "uuid1", "user2_id": "uuid2"}'
```

---

## Integration with Frontend

### JavaScript/React Example

```javascript
// 1. Get login URL
async function initiateLogin() {
  const response = await fetch('http://localhost:8000/auth/login');
  const data = await response.json();
  window.location.href = data.auth_url;
}

// 2. Handle callback (in redirect page)
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('access_token');

// 3. Sync user data
async function syncUserData(token) {
  const response = await fetch('http://localhost:8000/api/sync/user', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      access_token: token,
      time_ranges: ['short_term', 'medium_term', 'long_term']
    })
  });
  const data = await response.json();
  return data;
}

// 4. Get user profile
async function getUserProfile(userId) {
  const response = await fetch(`http://localhost:8000/api/profile/${userId}`);
  const data = await response.json();
  return data.data;
}
```

---

## Troubleshooting

### Database Connection Issues
- Check `.env` file has correct Supabase credentials
- Verify Supabase project is active
- Check network connectivity

### Spotify Authentication Issues
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check REDIRECT_URI matches Spotify app settings
- Ensure token hasn't expired

### No Data in Database
- Run `/api/sync/user` endpoint first
- Check sync status with `/api/sync/status/{user_id}`
- Verify user has sufficient Spotify data (top artists, tracks, etc.)

---

## Support

For issues or questions:
1. Check API documentation at `http://localhost:8000/docs`
2. Review error messages in API response
3. Check server logs for detailed error information

