# MusicMatch Backend API

A comprehensive FastAPI backend for Spotify music data extraction, analysis, and user matching using Supabase database integration.

## 🎯 Features

- **🔐 Spotify Authentication**: OAuth 2.0 PKCE flow for secure user authentication
- **📊 Data Synchronization**: Sync top artists, tracks, playlists, and audio features from Spotify
- **🎭 Genre Analysis**: Extract and analyze user music genres with intelligent extraction
- **⭐ Audio Features**: Process and store Spotify audio features (danceability, energy, valence, etc.)
- **🤝 User Matching**: Compute compatibility scores between users based on music taste
- **🎵 Playlist Management**: Sync and manage user playlists
- **💾 Database Integration**: Persistent storage with Supabase PostgreSQL
- **⚡ Background Processing**: Async task processing for heavy operations
- **📚 Interactive Documentation**: Auto-generated Swagger UI and ReDoc

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React/Vue)   │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────┐
│      FastAPI Backend                │
│  ┌───────────────────────────────┐  │
│  │  API Endpoints                │  │
│  │  • Auth, Sync, Profile        │  │
│  │  • Artists, Tracks, Playlists │  │
│  │  • Genres, Audio Features     │  │
│  │  • Compatibility              │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Business Logic               │  │
│  │  • Genre Extraction           │  │
│  │  • Compatibility Algorithm    │  │
│  │  • Data Processing            │  │
│  └───────────────────────────────┘  │
└──┬─────────────────────────────────┬─┘
   │                                  │
   │ Spotify API                      │ Supabase
   │ ↓                                ↓
┌──────────────┐            ┌─────────────────┐
│ Spotify      │            │ PostgreSQL      │
│ Web API      │            │ Database        │
│ • Auth       │            │ • Users         │
│ • Music Data │            │ • Artists       │
│              │            │ • Tracks        │
│              │            │ • Playlists     │
│              │            │ • Genres        │
└──────────────┘            └─────────────────┘
```

## 📦 Tech Stack

- **Framework**: FastAPI (Python web framework)
- **Server**: Uvicorn (ASGI server)
- **Database**: Supabase (PostgreSQL with vector support)
- **Music API**: Spotipy (Spotify Web API wrapper)
- **Genre Processing**: fuzzywuzzy, Last.fm API
- **Data Validation**: Pydantic
- **CORS**: Built-in CORS middleware for frontend integration

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Spotify Developer Account (free)
- Supabase Account (free)

### 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd Spotify

# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn[standard]

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual credentials
```

### 3. Configuration

Create `.env` file:

```env
# Spotify API (from https://developer.spotify.com/dashboard)
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://localhost:8000/auth/callback

# Supabase (from https://supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Last.fm (optional, from https://www.last.fm/api)
LASTFM_API_KEY=your_api_key
```

### 4. Start the Server

```bash
# Development mode with auto-reload
uvicorn backend:app --reload

# Production mode
uvicorn backend:app --host 0.0.0.0 --port 8000
```

### 5. Access the API

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **API Base**: http://localhost:8000

## 📚 API Endpoints Overview

### Authentication
- `GET /auth/login` - Get Spotify login URL
- `GET /auth/callback` - OAuth callback handler

### User Management
- `POST /api/sync/user` - Sync all user data
- `GET /api/user/{user_id}` - Get user info
- `GET /api/profile/{user_id}` - Get music profile
- `GET /api/sync/status/{user_id}` - Get sync status

### Music Data
- `GET /api/top-artists/{user_id}` - Get top artists
- `GET /api/top-tracks/{user_id}` - Get top tracks
- `GET /api/saved-tracks/{user_id}` - Get saved tracks
- `GET /api/playlists/{user_id}` - Get playlists
- `GET /api/playlist/{playlist_id}/tracks` - Get playlist tracks

### Genres & Features
- `GET /api/genres/{user_id}` - Get genre preferences
- `POST /api/genres/extract` - Extract genres from tags
- `GET /api/audio-features/{track_id}` - Get track audio features
- `POST /api/audio-features` - Save multiple audio features

### Compatibility & Matching
- `POST /api/compatibility` - Compute user compatibility
- `GET /api/matches/{user_id}` - Get potential matches

### System
- `GET /health` - Health check
- `GET /api/stats` - Database statistics

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔄 Data Sync Workflow

```
User Authenticates
        ↓
    ┌─────────────────────────────┐
    │   Sync All User Data        │
    ├─────────────────────────────┤
    │ ✓ Top Artists (3 time ranges)
    │ ✓ Top Tracks (3 time ranges)
    │ ✓ Saved Tracks
    │ ✓ Playlists & Tracks
    │ ✓ Audio Features
    │ ✓ Genre Preferences
    └──────────┬──────────────────┘
               ↓
    ┌─────────────────────────────┐
    │   Data Stored in Supabase   │
    ├─────────────────────────────┤
    │ ✓ User Profile
    │ ✓ Artists & Genres
    │ ✓ Tracks & Audio Features
    │ ✓ Playlists
    │ ✓ Computed Preferences
    └──────────┬──────────────────┘
               ↓
    ┌─────────────────────────────┐
    │   Available for Queries     │
    ├─────────────────────────────┤
    │ ✓ User Profile API
    │ ✓ Music Analysis
    │ ✓ Compatibility Matching
    │ ✓ Recommendations
    └─────────────────────────────┘
```

## 🎯 Common Usage Scenarios

### Scenario 1: User Onboarding
```python
from musicmatch_client import MusicMatchClient

client = MusicMatchClient()
client.authenticate()  # Opens Spotify login
client.sync_user_data()  # Sync all data
profile = client.get_user_profile()  # Get music profile
```

### Scenario 2: Music Analysis
```python
# Get top genres
genres = client.get_genres(limit=10)

# Get top artists with details
artists = client.get_top_artists(limit=5)

# Get audio features for top tracks
tracks = client.get_top_tracks(limit=5)
for track in tracks:
    features = client.get_audio_features(track['tracks']['id'])
```

### Scenario 3: User Matching
```python
# Find compatible users
matches = client.get_matches(limit=20)

# Check specific compatibility
compatibility = client.compute_compatibility(user1_id, user2_id)
```

## 🗄️ Database Schema

Key tables:
- **users**: User profiles and metadata
- **artists**: Artist information and genres
- **tracks**: Track details and album info
- **albums**: Album information
- **audio_features**: Spotify audio analysis data
- **user_top_artists**: User's top artists per time range
- **user_top_tracks**: User's top tracks per time range
- **user_genre_preferences**: Computed genre preferences
- **playlists**: User playlists
- **compatibility_scores**: User-to-user compatibility

See [schema.sql](schema.sql) for complete schema

## 🔒 Security Considerations

1. **OAuth 2.0**: Uses PKCE flow for secure authentication
2. **Row Level Security (RLS)**: Database enforces user data isolation
3. **API Keys**: Supabase RLS policies protect data access
4. **CORS**: Configurable CORS for safe cross-origin requests
5. **Rate Limiting**: Respects Spotify API rate limits

## 📊 Performance Tips

1. **Background Sync**: Large syncs run in background tasks
2. **Caching**: Implement frontend caching for frequent queries
3. **Batch Operations**: Use batch endpoints for multiple items
4. **Database Indexing**: Supabase automatically indexes key fields
5. **Query Optimization**: Use specific time_range and limit parameters

## 🧪 Testing

```bash
# Test with Python client
python musicmatch_client.py

# Test with cURL
curl http://localhost:8000/health

# Test with Swagger UI
# Visit http://localhost:8000/docs and try endpoints
```

## 📝 Logging

The API logs important events:
- User authentication
- Data synchronization
- API errors
- Database operations

Check console output for logs during development

## 🐛 Troubleshooting

### Issue: Database Connection Error
**Solution**: Verify `.env` has correct Supabase credentials

### Issue: Spotify Authentication Fails
**Solution**: Check CLIENT_ID, CLIENT_SECRET, and REDIRECT_URI match Spotify app settings

### Issue: Port 8000 Already in Use
**Solution**: Use different port: `uvicorn backend:app --reload --port 8001`

### Issue: No Data After Sync
**Solution**: 
1. Check sync status: `GET /api/sync/status/{user_id}`
2. Verify Spotify account has music data
3. Wait 30 seconds (background processing)

See [QUICKSTART.md](QUICKSTART.md) for more troubleshooting

## 📚 Additional Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)**: Complete API reference
- **[QUICKSTART.md](QUICKSTART.md)**: Quick start guide with examples
- **[schema.sql](schema.sql)**: Database schema
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**: Project overview

## 🔗 External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Spotipy Documentation](https://spotipy.readthedocs.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions:
1. Check the documentation files
2. Review error messages in API response
3. Check server logs for detailed information
4. Open an issue on GitHub

---

**Made with ❤️ for music lovers and developers**

Start the server and visit `http://localhost:8000/docs` to begin! 🎉
