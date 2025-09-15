-- Migration: 20250712000001_initial_musicmatch_schema.sql
-- Description: Initial schema for MusicMatch - music-based social app
-- Created: July 12, 2025

-- =============================================================================
-- EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- CORE USER MANAGEMENT
-- =============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    spotify_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    display_name TEXT,
    profile_image_url TEXT,
    country TEXT,
    product TEXT,
    followers_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_distance_km INTEGER DEFAULT 50,
    min_age INTEGER DEFAULT 18,
    max_age INTEGER DEFAULT 35,
    looking_for TEXT[] DEFAULT ARRAY['friends'],
    show_in_discovery BOOLEAN DEFAULT TRUE,
    receive_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- =============================================================================
-- MUSIC DATA ENTITIES
-- =============================================================================

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

CREATE TABLE albums (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    album_type TEXT,
    total_tracks INTEGER DEFAULT 0,
    release_date DATE,
    release_date_precision TEXT,
    image_url TEXT,
    popularity INTEGER DEFAULT 0,
    external_urls JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE album_artists (
    album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, artist_id)
);

CREATE TABLE tracks (
    id TEXT PRIMARY KEY,
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

CREATE TABLE track_artists (
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    artist_order INTEGER DEFAULT 0,
    PRIMARY KEY (track_id, artist_id)
);

CREATE TABLE track_audio_features (
    track_id TEXT PRIMARY KEY REFERENCES tracks(id) ON DELETE CASCADE,
    danceability DECIMAL(3,2),
    energy DECIMAL(3,2),
    key INTEGER,
    loudness DECIMAL(6,3),
    mode INTEGER,
    speechiness DECIMAL(3,2),
    acousticness DECIMAL(3,2),
    instrumentalness DECIMAL(3,2),
    liveness DECIMAL(3,2),
    valence DECIMAL(3,2),
    tempo DECIMAL(6,3),
    time_signature INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PLAYLISTS & USER INTERACTIONS
-- =============================================================================

CREATE TABLE playlists (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    is_collaborative BOOLEAN DEFAULT FALSE,
    is_blended BOOLEAN DEFAULT FALSE,
    blend_user1_id UUID REFERENCES users(id),
    blend_user2_id UUID REFERENCES users(id),
    external_urls JSONB DEFAULT '{}',
    snapshot_id TEXT,
    tracks_total INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT blend_users_check CHECK (
        (is_blended = FALSE) OR 
        (is_blended = TRUE AND blend_user1_id IS NOT NULL AND blend_user2_id IS NOT NULL)
    )
);

CREATE TABLE playlist_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    added_by_user_id UUID REFERENCES users(id),
    UNIQUE(playlist_id, position),
    UNIQUE(playlist_id, track_id, position)
);

CREATE TABLE user_saved_tracks (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, track_id)
);

CREATE TABLE user_saved_albums (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, album_id)
);

-- =============================================================================
-- USER MUSIC ANALYTICS
-- =============================================================================

CREATE TABLE user_top_artists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    time_range TEXT NOT NULL,
    position INTEGER NOT NULL,
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, artist_id, time_range, retrieved_at::DATE)
);

CREATE TABLE user_top_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    time_range TEXT NOT NULL,
    position INTEGER NOT NULL,
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, track_id, time_range, retrieved_at::DATE)
);

CREATE TABLE user_genre_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    genre TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    weight DECIMAL(3,2) DEFAULT 0.0,
    time_range TEXT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, genre, time_range)
);

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
    preferred_keys INTEGER[],
    preferred_modes INTEGER[],
    time_range TEXT NOT NULL DEFAULT 'medium_term',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SOCIAL FEATURES
-- =============================================================================

CREATE TABLE compatibility_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    genre_overlap_score DECIMAL(3,2) DEFAULT 0.0,
    artist_similarity_score DECIMAL(3,2) DEFAULT 0.0,
    audio_feature_similarity DECIMAL(3,2) DEFAULT 0.0,
    overall_compatibility DECIMAL(3,2) DEFAULT 0.0,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user1_id, user2_id),
    CONSTRAINT user_order_check CHECK (user1_id < user2_id)
);

CREATE TABLE user_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_type TEXT NOT NULL DEFAULT 'mutual',
    status TEXT NOT NULL DEFAULT 'pending',
    matched_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    last_interaction_at TIMESTAMPTZ,
    UNIQUE(user1_id, user2_id),
    CONSTRAINT match_user_order_check CHECK (user1_id < user2_id)
);

CREATE TABLE chat_starters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES user_matches(id) ON DELETE CASCADE,
    starter_type TEXT NOT NULL,
    content TEXT NOT NULL,
    related_track_id TEXT REFERENCES tracks(id),
    related_artist_id TEXT REFERENCES artists(id),
    related_genre TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_used BOOLEAN DEFAULT FALSE
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX idx_users_spotify_id ON users(spotify_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_artists_name ON artists USING gin(name gin_trgm_ops);
CREATE INDEX idx_artists_genres ON artists USING gin(genres);
CREATE INDEX idx_tracks_name ON tracks USING gin(name gin_trgm_ops);
CREATE INDEX idx_tracks_popularity ON tracks(popularity DESC);
CREATE INDEX idx_user_top_artists_user_time ON user_top_artists(user_id, time_range, position);
CREATE INDEX idx_user_top_tracks_user_time ON user_top_tracks(user_id, time_range, position);
CREATE INDEX idx_user_genre_preferences_user ON user_genre_preferences(user_id, time_range);
CREATE INDEX idx_compatibility_scores_users ON compatibility_scores(user1_id, user2_id);
CREATE INDEX idx_compatibility_scores_overall ON compatibility_scores(overall_compatibility DESC);
CREATE INDEX idx_user_matches_status ON user_matches(status);
CREATE INDEX idx_user_matches_users ON user_matches(user1_id, user2_id);
CREATE INDEX idx_playlists_user_id ON playlists(user_id);
CREATE INDEX idx_playlists_blended ON playlists(is_blended) WHERE is_blended = TRUE;
CREATE INDEX idx_playlist_tracks_playlist ON playlist_tracks(playlist_id, position);

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

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

CREATE POLICY "Users can view their own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can manage their own preferences" ON user_preferences FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own playlists" ON playlists FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view playlists they're involved in" ON playlists
    FOR SELECT USING (
        auth.uid() = user_id OR 
        auth.uid() = blend_user1_id OR 
        auth.uid() = blend_user2_id OR
        is_public = TRUE
    );

CREATE POLICY "Users can manage their own saved tracks" ON user_saved_tracks FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their own saved albums" ON user_saved_albums FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view their own top artists" ON user_top_artists FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view their own top tracks" ON user_top_tracks FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view their own genre preferences" ON user_genre_preferences FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view their own audio preferences" ON user_audio_preferences FOR ALL USING (auth.uid() = user_id);

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
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

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

CREATE OR REPLACE FUNCTION compute_genre_overlap(user1_uuid UUID, user2_uuid UUID, time_range_param TEXT DEFAULT 'medium_term')
RETURNS DECIMAL(3,2) AS $$
DECLARE
    overlap_count INTEGER := 0;
    total_genres INTEGER := 0;
BEGIN
    SELECT COUNT(DISTINCT g1.genre) INTO overlap_count
    FROM user_genre_preferences g1
    INNER JOIN user_genre_preferences g2 ON g1.genre = g2.genre
    WHERE g1.user_id = user1_uuid 
    AND g2.user_id = user2_uuid
    AND g1.time_range = time_range_param 
    AND g2.time_range = time_range_param;
    
    SELECT COUNT(DISTINCT genre) INTO total_genres
    FROM user_genre_preferences
    WHERE user_id IN (user1_uuid, user2_uuid)
    AND time_range = time_range_param;
    
    IF total_genres = 0 THEN
        RETURN 0.0;
    ELSE
        RETURN (overlap_count::DECIMAL / total_genres::DECIMAL);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Schema versioning
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial MusicMatch schema with user profiles, music data, and social features');
