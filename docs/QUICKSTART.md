# MusicMatch API - Quick Start Guide

## 🚀 Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install fastapi uvicorn[standard]
```

### 2. Configure Environment

Create `.env` file:

```env
# Spotify API (get from https://developer.spotify.com)
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://localhost:8000/auth/callback

# Supabase (get from https://supabase.com)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Last.fm (optional, get from https://www.last.fm/api)
LASTFM_API_KEY=your_api_key
```

### 3. Start the Server

```bash
uvicorn backend:app --reload
```

Server runs at: `http://localhost:8000`

API Docs: `http://localhost:8000/docs` (interactive Swagger UI)

---

## 🔐 Quick API Workflow

### Option A: Using cURL

```bash
# 1. Get Spotify login URL
curl http://localhost:8000/auth/login

# 2. Visit the URL in browser to authorize
# Spotify will redirect back to callback

# 3. Get the access token from callback URL
ACCESS_TOKEN="BQD..."

# 4. Sync all user data (this runs in background)
curl -X POST http://localhost:8000/api/sync/user \
  -H "Content-Type: application/json" \
  -d '{"access_token":"'$ACCESS_TOKEN'"}'

# Response includes user_id
# 5. Get user profile
USER_ID="uuid"
curl http://localhost:8000/api/profile/$USER_ID
```

### Option B: Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Get login URL
response = requests.get(f"{BASE_URL}/auth/login")
auth_url = response.json()["auth_url"]
print(f"Visit: {auth_url}")

# 2. After authorizing, get token from callback
access_token = "BQD..."

# 3. Sync user data
response = requests.post(
    f"{BASE_URL}/api/sync/user",
    json={"access_token": access_token}
)
user_id = response.json()["data"]["user_id"]

# 4. Get user profile
profile = requests.get(f"{BASE_URL}/api/profile/{user_id}")
print(profile.json()["data"])
```

### Option C: Using Swagger UI

1. Go to `http://localhost:8000/docs`
2. Click "Authorize" and follow Spotify login
3. Try endpoints directly in the interface

---

## 📊 Common Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | GET | Get Spotify login URL |
| `/api/sync/user` | POST | Sync all Spotify data |
| `/api/profile/{user_id}` | GET | Get user music profile |
| `/api/top-artists/{user_id}` | GET | Get top artists |
| `/api/top-tracks/{user_id}` | GET | Get top tracks |
| `/api/genres/{user_id}` | GET | Get genre preferences |
| `/api/playlists/{user_id}` | GET | Get playlists |
| `/api/compatibility` | POST | Check user compatibility |
| `/health` | GET | API health check |

---

## 📝 Example: Full Workflow

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def main():
    # 1. Authenticate
    print("1️⃣ Getting login URL...")
    login_response = requests.get(f"{BASE_URL}/auth/login")
    auth_url = login_response.json()["auth_url"]
    print(f"Visit: {auth_url}")
    print("After authorizing, paste the access token:")
    access_token = input("Access Token: ").strip()
    
    # 2. Sync data
    print("\n2️⃣ Syncing Spotify data...")
    sync_response = requests.post(
        f"{BASE_URL}/api/sync/user",
        json={"access_token": access_token}
    )
    result = sync_response.json()
    user_id = result["data"]["user_id"]
    user_name = result["data"]["user_name"]
    print(f"✅ Syncing for {user_name}...")
    
    # Wait for background sync
    time.sleep(3)
    
    # 3. Get profile
    print("\n3️⃣ Fetching user profile...")
    profile_response = requests.get(f"{BASE_URL}/api/profile/{user_id}")
    profile = profile_response.json()["data"]
    
    print(f"\n🎵 Music Profile for {user_name}:")
    print(f"  • Saved tracks: {profile['saved_tracks_count']}")
    print(f"  • Top genres: {len(profile['genre_preferences'])}")
    print(f"  • Top artists: {len(profile['top_artists'])}")
    
    # 4. Show top genres
    print("\n🎭 Top 5 Genres:")
    for genre in profile['genre_preferences'][:5]:
        print(f"  • {genre['genre']}: {genre['weight']:.2f}")
    
    # 5. Get top artists
    print("\n⭐ Top 5 Artists:")
    artists_response = requests.get(
        f"{BASE_URL}/api/top-artists/{user_id}",
        params={"limit": 5}
    )
    artists = artists_response.json()["data"]
    for item in artists:
        artist = item["artists"]
        print(f"  {item['position']}. {artist['name']} ({artist['popularity']}% popularity)")
    
    # 6. Compare with another user
    print("\n🤝 Checking compatibility with another user...")
    # (You would need another user_id for this)

if __name__ == "__main__":
    main()
```

---

## 🔧 Available Sync Endpoints

### Sync Everything
```bash
POST /api/sync/user?access_token=TOKEN
```
Syncs: top artists, top tracks, saved tracks, playlists, audio features, genres

### Sync Specific Data
```bash
POST /api/sync/top-artists?access_token=TOKEN
POST /api/sync/top-tracks?access_token=TOKEN
POST /api/sync/saved-tracks?access_token=TOKEN
POST /api/sync/playlists?access_token=TOKEN
```

### Sync Playlist Details
```bash
POST /api/sync/playlist/{playlist_id}?access_token=TOKEN
```

---

## 📊 Query Examples

### Get Top 10 Artists (Last 6 Months)
```bash
GET /api/top-artists/{user_id}?time_range=medium_term&limit=10
```

### Get Top 5 Genres (All Time)
```bash
GET /api/genres/{user_id}?time_range=long_term&limit=5
```

### Extract Genres from Last.fm Tags
```bash
POST /api/genres/extract
{
  "lastfm_tags": ["rock", "alternative", "seen live", "2020s"]
}
```

### Find Compatible Users
```bash
POST /api/compatibility
{
  "user1_id": "uuid1",
  "user2_id": "uuid2"
}

GET /api/matches/{user_id}?limit=20
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Use different port
uvicorn backend:app --reload --port 8001
```

### Database Connection Error
```
❌ Database connection failed
```
**Fix:** Check `.env` file has correct Supabase credentials

### Spotify Auth Failed
```
Authentication failed: ...
```
**Fix:** Verify CLIENT_ID, CLIENT_SECRET, REDIRECT_URI match Spotify app settings

### No Data After Sync
1. Check sync completed: `GET /api/sync/status/{user_id}`
2. Verify Spotify account has music data
3. Wait 30 seconds (background sync takes time)

---

## 📈 What Gets Synced

### User Data
- Profile info (name, email, followers)
- Country, subscription type

### Music Data
- **Top Artists** (for 4 weeks, 6 months, all time)
  - Name, genres, popularity, followers
- **Top Tracks** (for 4 weeks, 6 months, all time)
  - Name, album, artists, popularity, duration
- **Audio Features** (for top tracks)
  - Danceability, energy, key, loudness, valence, tempo, etc.
- **Saved Tracks** (liked songs)
  - Track info, when saved

### Playlists
- Playlist name, description, public/private status
- All tracks in each playlist (with order, date added)

### Computed Data
- **Genre Preferences** (computed from top artists)
  - Genre name, frequency, weight (importance)

---

## 🚀 Next Steps

1. **Explore the API:**
   - Visit `http://localhost:8000/docs` for interactive docs
   - Try each endpoint

2. **Build Frontend:**
   - Use JavaScript/React examples from API docs
   - Implement user authentication flow

3. **Add User Matching:**
   - Compute compatibility between users
   - Find potential matches

4. **Advanced Analysis:**
   - Analyze audio feature preferences
   - Genre trend analysis
   - Playlist recommendations

---

## 📚 API Documentation

Full API documentation available at: `API_DOCUMENTATION.md`

Key sections:
- Complete endpoint reference
- Request/response examples
- Authentication flow
- Error handling
- Frontend integration examples

---

## ⚡ Performance Tips

1. **Use `time_ranges` parameter** to sync specific time periods
2. **Run syncs at off-peak times** to avoid rate limits
3. **Cache responses** in frontend where possible
4. **Use background tasks** for large data syncs

---

## 🆘 Need Help?

1. Check API docs: `http://localhost:8000/docs`
2. Review server logs for errors
3. Check `.env` file configuration
4. Verify Supabase connection
5. Ensure Spotify API credentials are correct

---

## 🎯 Common Use Cases

### Use Case 1: User Onboarding
```
1. User logs in with Spotify
2. Sync all their data
3. Display music profile
4. Show genre preferences
5. Find matches with compatible users
```

### Use Case 2: Music Analysis
```
1. Get top artists for time period
2. Fetch audio features
3. Compute genre preferences
4. Analyze patterns
```

### Use Case 3: User Matching
```
1. Compute compatibility between two users
2. Get potential matches
3. Show compatibility score breakdown
4. Suggest conversation starters
```

---

**Ready to go! Start the server and visit `http://localhost:8000/docs` 🎉**
