# 🎵 MusicMatch Database Setup Guide

This comprehensive guide will help you set up the complete MusicMatch database schema with Supabase and integrate it with your existing Spotify analysis notebooks.

## 📋 Prerequisites

1. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
2. **Spotify Developer Account**: You already have this set up
3. **Supabase CLI**: Install the Supabase CLI for database migrations
4. **Python Dependencies**: Install all required packages

### 🛠️ Install Required Software

```bash
# Install Supabase CLI (choose your OS)
# macOS
brew install supabase/tap/supabase

# Windows (via Scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Windows (via Chocolatey)
choco install supabase

# Linux
curl -fsSL https://raw.githubusercontent.com/supabase/supabase/main/install.sh | sh

# Install Python packages
pip install -r requirements.txt
```

## 🗄️ Database Setup

### Option 1: Using Supabase CLI (Recommended)

1. **Create a new Supabase project**:
   - Go to [database.new](https://database.new)
   - Click "New Project"
   - Choose your organization
   - Enter project name: "musicmatch" or your preferred name
   - Enter a strong database password
   - Select a region close to you
   - Click "Create new project"

2. **Initialize Supabase project locally**:
```bash
cd your-music-match-project

# Initialize Supabase (this creates supabase/ folder)
supabase init

# Link to your remote project
supabase link --project-ref YOUR_PROJECT_REF

# Get your project ref from: Project Settings > General > Reference ID
```

3. **Apply our schema using migrations**:
```bash
# Copy our migration file to the Supabase migrations folder
# From: migrations/20250712000001_initial_musicmatch_schema.sql
# To: supabase/migrations/20250712000001_initial_musicmatch_schema.sql

# Or create a new migration and copy the content:
supabase migration new initial_musicmatch_schema

# Then copy the content from our migration file into the new file
# Apply migration to remote database
supabase db push
```

### Option 2: Direct SQL Execution (Alternative)

1. Go to your Supabase Dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `migrations/20250712000001_initial_musicmatch_schema.sql`
4. Execute the script

## 🔧 Environment Configuration

Create a `.env` file in your project root:

```bash
# Spotify API (you already have these)
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=your_spotify_redirect_uri

# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Last.fm API (optional - for enhanced genre data)
LASTFM_API_KEY=your_lastfm_api_key
```

**To find your Supabase credentials:**
1. Go to your Supabase project dashboard
2. Click "Settings" → "API"
3. Copy the Project URL and API keys

**To get Last.fm API key (optional):**
1. Go to [last.fm/api](https://www.last.fm/api)
2. Create an account and request API access
3. Add the API key to your `.env` file

## 🚀 Quick Start Guide

### Step 1: Set Up Database
1. Follow the database setup instructions above
2. Ensure your `.env` file is properly configured
3. Verify connection by running the test in the next section

### Step 2: Run Notebooks in Order

**📝 Important**: All notebooks now have database integration! Run them in this order:

1. **`blend.ipynb`** - ⭐ **START HERE** 
   - Sets up your user profile
   - Syncs top artists and genre preferences
   - Tests database connection

2. **`user_top_items.ipynb`**
   - Saves your top artists and tracks
   - Computes audio preferences
   - Essential for compatibility scoring

3. **`user_saved_items.ipynb`**
   - Syncs your saved tracks and albums
   - Builds your music library profile

4. **`playlists.ipynb`**
   - Saves your playlists and tracks
   - Important for collaborative features

5. **`lastfm.ipynb`** - 🎯 **Optional but Recommended**
   - Enhances genre data with Last.fm
   - Improves matching accuracy

### Step 3: Verify Your Setup

After running the notebooks, you should have:
- ✅ User profile in database
- ✅ Top artists and tracks saved
- ✅ Genre preferences computed
- ✅ Audio features analyzed
- ✅ Saved music library synced

# Initialize database connection
db = MusicMatchDB()

# Get current user and sync to database
user_data = sp.current_user()
db_user = db.create_or_update_user(user_data)
user_id = db_user["id"]

print(f"Database user ID: {user_id}")
```

### 2. Modify Your Data Collection

**In `user_top_items.ipynb`:**
```python
# After getting top artists
artists = sp.current_user_top_artists(limit=50, time_range='long_term')

# Save to database
db.save_user_top_artists(user_id, artists['items'], 'long_term')

# Also compute genre preferences
db.compute_user_genre_preferences(user_id, 'long_term')
```

**In `user_saved_items.ipynb`:**
```python
# After getting saved tracks
tracks = sp.current_user_saved_tracks(limit=50)

# Save to database
db.save_user_saved_tracks(user_id, tracks['items'])
```

**In `playlists.ipynb`:**
```python
# After getting playlists
playlists = sp.current_user_playlists(limit=10)

# Save to database
db.save_user_playlists(user_id, playlists['items'])

# For each playlist, save tracks
for playlist in playlists['items']:
    playlist_tracks = sp.playlist_tracks(playlist['id'])
    db.save_playlist_tracks(playlist['id'], playlist_tracks['items'])
```

### 3. Add Audio Features Analysis

Create a new notebook cell to fetch audio features:

```python
# Get user's top tracks
top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')
track_ids = [track['id'] for track in top_tracks['items']]

# Get audio features
audio_features = sp.audio_features(track_ids)

# Save to database
db.batch_save_audio_features(audio_features)

# Compute user's audio preferences
audio_prefs_result = db.supabase.table("user_top_tracks").select(
    "track_id, track_audio_features(*)"
).eq("user_id", user_id).eq("time_range", "medium_term").execute()

# Calculate averages
if audio_prefs_result.data:
    features = [item["track_audio_features"] for item in audio_prefs_result.data if item["track_audio_features"]]
    
    if features:
        avg_features = {
            "user_id": user_id,
            "avg_danceability": sum(f["danceability"] for f in features) / len(features),
            "avg_energy": sum(f["energy"] for f in features) / len(features),
            "avg_valence": sum(f["valence"] for f in features) / len(features),
            "avg_acousticness": sum(f["acousticness"] for f in features) / len(features),
            "avg_tempo": sum(f["tempo"] for f in features) / len(features),
            "time_range": "medium_term"
        }
        
        db.supabase.table("user_audio_preferences").upsert(avg_features).execute()
        print("Audio preferences computed and saved!")
```

## ✅ Testing Your Setup

### 1. Test Database Connection

```python
from database_helper import MusicMatchDB

# Test connection
try:
    db = MusicMatchDB()
    result = db.supabase.table("users").select("count", count="exact").execute()
    print(f"✅ Database connected! Total users: {result.count}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### 2. Verify Data Population

After running your notebooks, check that data was saved:

```python
# Check your user profile
user_data = sp.current_user()
db_user = db.get_user_by_spotify_id(user_data["id"])
if db_user:
    user_id = db_user["id"]
    print(f"✅ User found: {db_user['display_name']}")
    
    # Check music profile
    profile = db.get_user_music_profile(user_id)
    print(f"📊 Saved tracks: {profile['saved_tracks_count']}")
    print(f"🎭 Top genres: {len(profile['genre_preferences'])}")
    print(f"👨‍🎤 Top artists: {len(profile['top_artists'])}")
else:
    print("❌ User not found in database")
```

### 3. Test Compatibility Calculation

```python
# If you have another user in the database, test compatibility
users = db.supabase.table("users").select("id, display_name").limit(2).execute()
if len(users.data) >= 2:
    user1_id = users.data[0]["id"]
    user2_id = users.data[1]["id"]
    
    # Calculate compatibility
    compatibility = db.calculate_user_compatibility(user1_id, user2_id)
    print(f"🎯 Compatibility between users: {compatibility['overall_compatibility']:.2f}")
else:
    print("ℹ️ Need at least 2 users to test compatibility")
```

### 2. Test Data Sync

```python
# Run the complete sync
user_id = example_sync_user_data(sp, db)

# Check what was saved
profile = db.get_user_music_profile(user_id)
print("User profile:", profile)
```

### 3. Test Queries

```python
# Test some of the example queries
# Get user's top genres
genres_result = db.supabase.table("user_genre_preferences").select(
    "genre, weight, frequency"
).eq("user_id", user_id).eq("time_range", "medium_term").order("weight", desc=True).execute()

print("Top genres:", genres_result.data)
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "Database connection failed"**
- Check your `.env` file has correct Supabase credentials
- Verify your Supabase project is active
- Ensure `supabase-py` is installed: `pip install supabase`

**❌ "No such table: users"**
- Your migration didn't run properly
- Re-run: `supabase db push` or execute the SQL manually
- Check the Supabase dashboard → SQL Editor for errors

**❌ "User sync failed"**
- Check your Spotify token is valid
- Verify Spotify scopes include `user-read-private`
- Clear token cache and re-authenticate

**❌ "Audio features failed"**
- Some tracks don't have audio features
- The code handles this with error checking
- Check Spotify API rate limits

**❌ Import errors**
- Run: `pip install -r requirements.txt`
- Restart your Jupyter kernel
- Check all files are in the same directory

### Performance Tips

1. **Batch Processing**: The code already uses batch operations for efficiency
2. **Rate Limiting**: Built-in delays prevent Spotify API rate limits
3. **Incremental Updates**: Run notebooks periodically to keep data fresh
4. **Database Indexes**: The schema includes optimized indexes

## 🎯 Next Steps: Building Your Music Social App

Now that your database is set up and populated, you can build exciting features:

### Immediate Features You Can Build

1. **Music Compatibility Dashboard**
   ```python
   # Find your most compatible users
   compatibility_scores = db.supabase.table("compatibility_scores").select(
       "*, user1:users!user1_id(display_name), user2:users!user2_id(display_name)"
   ).order("overall_compatibility", desc=True).limit(10).execute()
   ```

2. **Genre Preference Visualizations**
   ```python
   # Create charts of your genre preferences
   import matplotlib.pyplot as plt
   import pandas as pd
   
   # Get your genre data
   profile = db.get_user_music_profile(user_id)
   genres_df = pd.DataFrame(profile['genre_preferences'])
   
   # Create visualization
   plt.figure(figsize=(12, 6))
   plt.bar(genres_df['genre'][:10], genres_df['weight'][:10])
   plt.title('Your Top 10 Music Genres')
   plt.xticks(rotation=45)
   plt.show()
   ```

3. **Blend Playlist Generator**
   ```python
   # Create a playlist combining two users' tastes
   blend_tracks = db.create_blend_playlist_tracks(user1_id, user2_id, limit=20)
   
   # Create the playlist on Spotify
   playlist = sp.user_playlist_create(
       user=sp.current_user()["id"],
       name=f"Blend: {user1_name} + {user2_name}",
       description="Generated by MusicMatch compatibility algorithm"
   )
   
   # Add tracks to playlist
   track_uris = [f"spotify:track:{track['track_id']}" for track in blend_tracks]
   sp.playlist_add_items(playlist['id'], track_uris)
   ```

### Advanced Features to Consider

1. **Real-time Compatibility Updates**
2. **Music-based Chat Starters**
3. **Event/Concert Matching**
4. **Collaborative Playlist Creation**
5. **Music Discovery Recommendations**
6. **Audio Feature-based Matching**

### Database Analytics Queries

```sql
-- Find users with similar audio preferences
SELECT 
    u1.display_name as user1,
    u2.display_name as user2,
    cs.audio_feature_similarity
FROM compatibility_scores cs
JOIN users u1 ON cs.user1_id = u1.id
JOIN users u2 ON cs.user2_id = u2.id
WHERE cs.audio_feature_similarity > 0.8
ORDER BY cs.audio_feature_similarity DESC;

-- Find the most popular genres across all users
SELECT 
    genre,
    COUNT(*) as user_count,
    AVG(weight) as avg_weight
FROM user_genre_preferences
GROUP BY genre
ORDER BY user_count DESC, avg_weight DESC
LIMIT 20;

-- Find users who might like a specific artist
SELECT DISTINCT
    u.display_name,
    uta.position
FROM users u
JOIN user_top_artists uta ON u.id = uta.user_id
JOIN artists a ON uta.artist_id = a.id
WHERE a.name = 'Your Artist Name'
ORDER BY uta.position;
```

## 📚 Additional Resources

- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **Spotify Web API Reference**: [developer.spotify.com/documentation/web-api](https://developer.spotify.com/documentation/web-api)
- **Last.fm API Documentation**: [last.fm/api](https://www.last.fm/api)
- **Music Information Retrieval**: [musicinformationretrieval.com](https://musicinformationretrieval.com)

## 🤝 Contributing

This is a comprehensive music social platform foundation. Consider:
- Adding more sophisticated genre analysis
- Implementing machine learning for better recommendations
- Creating a web interface
- Adding social features like following and messaging
- Integrating with other music services

---

**🎉 Congratulations!** You now have a fully functional music-based social platform backend with:
- ✅ Complete user music profiles
- ✅ Advanced compatibility scoring
- ✅ Genre-based matching
- ✅ Audio feature analysis
- ✅ Playlist management
- ✅ Enhanced genre extraction
- ✅ Scalable database architecture

Your database is production-ready and can handle thousands of users and millions of tracks!
