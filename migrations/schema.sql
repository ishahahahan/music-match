-- Database Schema for Supabase/PostgreSQL

-- CORE USER

-- Users table (extends Supabase Auth)
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    spotify_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    display_name TEXT,
    profile_image_url TEXT,
    country TEXT,
    product TEXT, -- free, premium
    followers_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- User preferences for matching
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_distance_km INTEGER DEFAULT 50,
    min_age INTEGER DEFAULT 18,
    max_age INTEGER DEFAULT 35,
    looking_for TEXT[] DEFAULT ARRAY['friends'], -- ['friends', 'dating', 'music_buddies']
    show_in_discovery BOOLEAN DEFAULT TRUE,
    receive_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- MUSIC DATA ENTITIES

-- Artists table
CREATE TABLE artists (
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    genres TEXT[] DEFAULT ARRAY[]::TEXT[],
    popularity INTEGER DEFAULT 0,
    followers_count INTEGER DEFAULT 0,
    image_url TEXT,
    external_urls JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Albums table  
CREATE TABLE albums (
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    album_type TEXT, -- album, single, compilation
    total_tracks INTEGER DEFAULT 0,
    release_date DATE,
    release_date_precision TEXT, -- year, month, day
    image_url TEXT,
    popularity INTEGER DEFAULT 0,
    external_urls JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Album artists relationship (many-to-many)
CREATE TABLE album_artists (
    album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, artist_id)
);

-- Tracks table
CREATE TABLE tracks (
    id TEXT PRIMARY KEY, -- Spotify track ID
    name TEXT NOT NULL,
    album_id TEXT REFERENCES albums(id),
    track_number INTEGER,
    disc_number INTEGER DEFAULT 1,
    duration_ms INTEGER NOT NULL,
    explicit BOOLEAN DEFAULT FALSE,
    popularity INTEGER DEFAULT 0,
    preview_url TEXT,
    external_urls JSONB DEFAULT '{}',
    is_local BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Track artists relationship (many-to-many)
CREATE TABLE track_artists (
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    artist_order INTEGER DEFAULT 0, -- for featuring order
    PRIMARY KEY (track_id, artist_id)
);

-- Audio features for tracks (Spotify Audio Features API)
CREATE TABLE track_audio_features (
    track_id TEXT PRIMARY KEY REFERENCES tracks(id) ON DELETE CASCADE,
    danceability DECIMAL(3,2), -- 0.0 to 1.0
    energy DECIMAL(3,2), -- 0.0 to 1.0
    key INTEGER, -- 0 to 11 (C, C#, D, etc.)
    loudness DECIMAL(6,3), -- typically -60 to 0 dB
    mode INTEGER, -- 0 (minor) or 1 (major)
    speechiness DECIMAL(3,2), -- 0.0 to 1.0
    acousticness DECIMAL(3,2), -- 0.0 to 1.0
    instrumentalness DECIMAL(3,2), -- 0.0 to 1.0
    liveness DECIMAL(3,2), -- 0.0 to 1.0
    valence DECIMAL(3,2), -- 0.0 to 1.0 (musical positivity)
    tempo DECIMAL(6,3), -- BPM
    time_signature INTEGER, -- 3, 4, 5, 6, 7
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PLAYLISTS & USER INTERACTIONS
-- =============================================================================

-- Playlists
CREATE TABLE playlists (
    id TEXT PRIMARY KEY, -- Spotify playlist ID for external, UUID for internal
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    is_collaborative BOOLEAN DEFAULT FALSE,
    is_blended BOOLEAN DEFAULT FALSE, -- Created by MusicMatch blend feature
    blend_user1_id UUID REFERENCES users(id), -- For blended playlists
    blend_user2_id UUID REFERENCES users(id), -- For blended playlists
    external_urls JSONB DEFAULT '{}',
    snapshot_id TEXT, -- Spotify versioning
    tracks_total INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT blend_users_check CHECK (
        (is_blended = FALSE) OR 
        (is_blended = TRUE AND blend_user1_id IS NOT NULL AND blend_user2_id IS NOT NULL)
    )
);

-- Playlist tracks relationship (ordered)
CREATE TABLE playlist_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    added_by_user_id UUID REFERENCES users(id),
    UNIQUE(playlist_id, position),
    UNIQUE(playlist_id, track_id, position) -- Prevent duplicates at same position
);

-- User saved tracks
CREATE TABLE user_saved_tracks (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, track_id)
);

-- User saved albums
CREATE TABLE user_saved_albums (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, album_id)
);

-- =============================================================================
-- USER MUSIC ANALYTICS & PREFERENCES
-- =============================================================================

-- User top artists (time-based snapshots)
CREATE TABLE user_top_artists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    time_range TEXT NOT NULL, -- short_term, medium_term, long_term
    position INTEGER NOT NULL, -- 1-50 ranking
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, artist_id, time_range, retrieved_at::DATE)
);

-- User top tracks (time-based snapshots)
CREATE TABLE user_top_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    time_range TEXT NOT NULL, -- short_term, medium_term, long_term
    position INTEGER NOT NULL, -- 1-50 ranking
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, track_id, time_range, retrieved_at::DATE)
);

-- User genre preferences (computed from top artists)
CREATE TABLE user_genre_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    genre TEXT NOT NULL,
    frequency INTEGER DEFAULT 1, -- How many top artists have this genre
    weight DECIMAL(3,2) DEFAULT 0.0, -- Computed preference weight 0.0-1.0
    time_range TEXT NOT NULL, -- short_term, medium_term, long_term
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, genre, time_range)
);

-- User audio feature preferences (aggregated from top tracks)
CREATE TABLE user_audio_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    avg_danceability DECIMAL(3,2),
    avg_energy DECIMAL(3,2),
    avg_speechiness DECIMAL(3,2),
    avg_acousticness DECIMAL(3,2),
    avg_instrumentalness DECIMAL(3,2),
    avg_liveness DECIMAL(3,2),
    avg_valence DECIMAL(3,2),
    avg_tempo DECIMAL(6,3),
    preferred_keys INTEGER[], -- Array of preferred musical keys
    preferred_modes INTEGER[], -- Array of preferred modes (0=minor, 1=major)
    time_range TEXT NOT NULL DEFAULT 'medium_term',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SOCIAL FEATURES & MATCHING
-- =============================================================================

-- User compatibility scores
CREATE TABLE compatibility_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Individual compatibility metrics
    genre_overlap_score DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    artist_similarity_score DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    audio_feature_similarity DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    
    -- Overall compatibility
    overall_compatibility DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    
    -- Metadata
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user1_id, user2_id),
    CONSTRAINT user_order_check CHECK (user1_id < user2_id) -- Prevent duplicates
);

-- User matches/connections
CREATE TABLE user_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_type TEXT NOT NULL DEFAULT 'mutual', -- mutual, one_way
    status TEXT NOT NULL DEFAULT 'pending', -- pending, accepted, rejected, blocked
    matched_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    last_interaction_at TIMESTAMPTZ,
    
    UNIQUE(user1_id, user2_id),
    CONSTRAINT match_user_order_check CHECK (user1_id < user2_id)
);

-- Chat starters/icebreakers based on music
CREATE TABLE chat_starters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES user_matches(id) ON DELETE CASCADE,
    starter_type TEXT NOT NULL, -- shared_artist, shared_track, shared_genre, audio_similarity
    content TEXT NOT NULL, -- Pre-generated conversation starter
    related_track_id TEXT REFERENCES tracks(id),
    related_artist_id TEXT REFERENCES artists(id),
    related_genre TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_used BOOLEAN DEFAULT FALSE
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- User lookup indexes
CREATE INDEX idx_users_spotify_id ON users(spotify_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Music data indexes
CREATE INDEX idx_artists_name ON artists USING gin(name gin_trgm_ops);
CREATE INDEX idx_artists_genres ON artists USING gin(genres);
CREATE INDEX idx_tracks_name ON tracks USING gin(name gin_trgm_ops);
CREATE INDEX idx_tracks_popularity ON tracks(popularity DESC);

-- User music preferences indexes
CREATE INDEX idx_user_top_artists_user_time ON user_top_artists(user_id, time_range, position);
CREATE INDEX idx_user_top_tracks_user_time ON user_top_tracks(user_id, time_range, position);
CREATE INDEX idx_user_genre_preferences_user ON user_genre_preferences(user_id, time_range);

-- Compatibility and matching indexes
CREATE INDEX idx_compatibility_scores_users ON compatibility_scores(user1_id, user2_id);
CREATE INDEX idx_compatibility_scores_overall ON compatibility_scores(overall_compatibility DESC);
CREATE INDEX idx_user_matches_status ON user_matches(status);
CREATE INDEX idx_user_matches_users ON user_matches(user1_id, user2_id);

-- Playlist indexes
CREATE INDEX idx_playlists_user_id ON playlists(user_id);
CREATE INDEX idx_playlists_blended ON playlists(is_blended) WHERE is_blended = TRUE;
CREATE INDEX idx_playlist_tracks_playlist ON playlist_tracks(playlist_id, position);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_saved_tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_saved_albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_top_artists ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_top_tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_genre_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_audio_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE compatibility_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_starters ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for user data
CREATE POLICY "Users can manage their own preferences" ON user_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own playlists" ON playlists
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view playlists they're involved in" ON playlists
    FOR SELECT USING (
        auth.uid() = user_id OR 
        auth.uid() = blend_user1_id OR 
        auth.uid() = blend_user2_id OR
        is_public = TRUE
    );

CREATE POLICY "Users can manage their own saved tracks" ON user_saved_tracks
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own saved albums" ON user_saved_albums
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own top artists" ON user_top_artists
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own top tracks" ON user_top_tracks
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own genre preferences" ON user_genre_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own audio preferences" ON user_audio_preferences
    FOR ALL USING (auth.uid() = user_id);

-- RLS for compatibility and matching
CREATE POLICY "Users can view compatibility scores involving them" ON compatibility_scores
    FOR SELECT USING (auth.uid() = user1_id OR auth.uid() = user2_id);

CREATE POLICY "Users can view matches involving them" ON user_matches
    FOR ALL USING (auth.uid() = user1_id OR auth.uid() = user2_id);

CREATE POLICY "Users can view chat starters for their matches" ON chat_starters
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_matches 
            WHERE id = match_id 
            AND (user1_id = auth.uid() OR user2_id = auth.uid())
        )
    );

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_artists_updated_at BEFORE UPDATE ON artists
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_albums_updated_at BEFORE UPDATE ON albums
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_playlists_updated_at BEFORE UPDATE ON playlists
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_compatibility_scores_updated_at BEFORE UPDATE ON compatibility_scores
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_user_audio_preferences_updated_at BEFORE UPDATE ON user_audio_preferences
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- =============================================================================
-- EXTENSIONS AND OPTIMIZATIONS
-- =============================================================================

-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Function to compute genre overlap between two users
CREATE OR REPLACE FUNCTION compute_genre_overlap(user1_uuid UUID, user2_uuid UUID, time_range_param TEXT DEFAULT 'medium_term')
RETURNS DECIMAL(3,2) AS $$
DECLARE
    overlap_count INTEGER := 0;
    total_genres INTEGER := 0;
BEGIN
    -- Count overlapping genres
    SELECT COUNT(DISTINCT g1.genre) INTO overlap_count
    FROM user_genre_preferences g1
    INNER JOIN user_genre_preferences g2 ON g1.genre = g2.genre
    WHERE g1.user_id = user1_uuid 
    AND g2.user_id = user2_uuid
    AND g1.time_range = time_range_param 
    AND g2.time_range = time_range_param;
    
    -- Count total unique genres between both users
    SELECT COUNT(DISTINCT genre) INTO total_genres
    FROM user_genre_preferences
    WHERE user_id IN (user1_uuid, user2_uuid)
    AND time_range = time_range_param;
    
    -- Return overlap ratio
    IF total_genres = 0 THEN
        RETURN 0.0;
    ELSE
        RETURN (overlap_count::DECIMAL / total_genres::DECIMAL);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get music-based conversation starters
CREATE OR REPLACE FUNCTION generate_chat_starters(match_uuid UUID)
RETURNS TABLE(starter_text TEXT, starter_type TEXT, related_data JSONB) AS $$
BEGIN
    RETURN QUERY
    WITH match_info AS (
        SELECT user1_id, user2_id FROM user_matches WHERE id = match_uuid
    ),
    shared_artists AS (
        SELECT a.name, a.id, COUNT(*) as shared_count
        FROM match_info m
        CROSS JOIN user_top_artists uta1 ON uta1.user_id = m.user1_id
        INNER JOIN user_top_artists uta2 ON uta2.artist_id = uta1.artist_id AND uta2.user_id = m.user2_id
        INNER JOIN artists a ON a.id = uta1.artist_id
        WHERE uta1.time_range = 'medium_term' AND uta2.time_range = 'medium_term'
        GROUP BY a.name, a.id
        ORDER BY shared_count DESC, RANDOM()
        LIMIT 3
    ),
    shared_genres AS (
        SELECT g1.genre, COUNT(*) as shared_strength
        FROM match_info m
        CROSS JOIN user_genre_preferences g1 ON g1.user_id = m.user1_id
        INNER JOIN user_genre_preferences g2 ON g2.user_id = m.user2_id AND g2.genre = g1.genre
        WHERE g1.time_range = 'medium_term' AND g2.time_range = 'medium_term'
        GROUP BY g1.genre
        ORDER BY shared_strength DESC, RANDOM()
        LIMIT 2
    )
    SELECT 
        'I see you also love ' || sa.name || '! What''s your favorite song by them?' as starter_text,
        'shared_artist' as starter_type,
        jsonb_build_object('artist_name', sa.name, 'artist_id', sa.id) as related_data
    FROM shared_artists sa
    
    UNION ALL
    
    SELECT 
        'We both seem to be into ' || sg.genre || ' music. Any recent discoveries in that genre?' as starter_text,
        'shared_genre' as starter_type,
        jsonb_build_object('genre', sg.genre) as related_data
    FROM shared_genres sg;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE users IS 'Core user profiles extending Supabase Auth';
COMMENT ON TABLE artists IS 'Spotify artist data with genres and metadata';
COMMENT ON TABLE tracks IS 'Spotify track information with popularity and metadata';
COMMENT ON TABLE track_audio_features IS 'Spotify Audio Features API data for musical analysis';
COMMENT ON TABLE playlists IS 'User playlists including MusicMatch generated blend playlists';
COMMENT ON TABLE user_top_artists IS 'Time-based snapshots of user top artists from Spotify';
COMMENT ON TABLE user_top_tracks IS 'Time-based snapshots of user top tracks from Spotify';
COMMENT ON TABLE compatibility_scores IS 'Computed compatibility metrics between users';
COMMENT ON TABLE chat_starters IS 'Music-based conversation starters for matched users';

-- Schema version for migrations
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial MusicMatch schema with user profiles, music data, and social features');
