
-- USER ANALYTICS QUERIES

-- Get a user's top genres (computed from their top artists)
SELECT 
    g.genre,
    g.weight,
    g.frequency,
    RANK() OVER (ORDER BY g.weight DESC) as genre_rank
FROM user_genre_preferences g
WHERE g.user_id = 'your-user-uuid'
  AND g.time_range = 'medium_term'
ORDER BY g.weight DESC
LIMIT 10;

-- Get a user's top artists with their genres
SELECT 
    uta.position,
    a.name as artist_name,
    a.genres,
    a.popularity,
    a.followers_count
FROM user_top_artists uta
JOIN artists a ON uta.artist_id = a.id
WHERE uta.user_id = 'your-user-uuid'
  AND uta.time_range = 'medium_term'
ORDER BY uta.position
LIMIT 20;

-- Get user's musical diversity score (number of unique genres in top artists)
SELECT 
    COUNT(DISTINCT genre) as genre_diversity,
    COUNT(*) as total_genre_instances,
    ROUND(COUNT(DISTINCT genre)::decimal / COUNT(*)::decimal, 2) as diversity_ratio
FROM user_genre_preferences
WHERE user_id = 'your-user-uuid'
  AND time_range = 'medium_term';

-- Get user's audio feature preferences (average from their top tracks)
SELECT 
    ROUND(AVG(af.danceability), 2) as avg_danceability,
    ROUND(AVG(af.energy), 2) as avg_energy,
    ROUND(AVG(af.valence), 2) as avg_valence,
    ROUND(AVG(af.acousticness), 2) as avg_acousticness,
    ROUND(AVG(af.tempo), 0) as avg_tempo,
    COUNT(*) as tracks_analyzed
FROM user_top_tracks utt
JOIN track_audio_features af ON utt.track_id = af.track_id
WHERE utt.user_id = 'your-user-uuid'
  AND utt.time_range = 'medium_term'
  AND utt.position <= 20;

-- =============================================================================
-- DISCOVERY & MATCHING QUERIES
-- =============================================================================

-- Find users with similar music taste (high genre overlap)
WITH user_genres AS (
    SELECT user_id, genre, weight
    FROM user_genre_preferences
    WHERE time_range = 'medium_term'
),
genre_similarities AS (
    SELECT 
        ug1.user_id as user1_id,
        ug2.user_id as user2_id,
        COUNT(*) as shared_genres,
        SUM(LEAST(ug1.weight, ug2.weight)) as similarity_score
    FROM user_genres ug1
    JOIN user_genres ug2 ON ug1.genre = ug2.genre AND ug1.user_id != ug2.user_id
    WHERE ug1.user_id = 'your-user-uuid'
    GROUP BY ug1.user_id, ug2.user_id
    HAVING COUNT(*) >= 3  -- At least 3 shared genres
)
SELECT 
    gs.user2_id,
    u.display_name,
    u.profile_image_url,
    gs.shared_genres,
    ROUND(gs.similarity_score, 2) as similarity_score
FROM genre_similarities gs
JOIN users u ON gs.user2_id = u.id
ORDER BY gs.similarity_score DESC
LIMIT 10;

-- Find users who like the same artists
SELECT 
    u.id as user_id,
    u.display_name,
    COUNT(*) as shared_artists,
    ARRAY_AGG(DISTINCT a.name) as shared_artist_names
FROM user_top_artists uta1
JOIN user_top_artists uta2 ON uta1.artist_id = uta2.artist_id 
    AND uta1.user_id != uta2.user_id
    AND uta1.time_range = uta2.time_range
JOIN users u ON uta2.user_id = u.id
JOIN artists a ON uta1.artist_id = a.id
WHERE uta1.user_id = 'your-user-uuid'
  AND uta1.time_range = 'medium_term'
  AND uta1.position <= 20
  AND uta2.position <= 20
GROUP BY u.id, u.display_name
HAVING COUNT(*) >= 2  -- At least 2 shared artists
ORDER BY COUNT(*) DESC
LIMIT 10;

-- Get compatibility scores for a user
SELECT 
    cs.*,
    CASE 
        WHEN cs.user1_id = 'your-user-uuid' THEN u2.display_name
        ELSE u1.display_name
    END as other_user_name,
    CASE 
        WHEN cs.user1_id = 'your-user-uuid' THEN u2.profile_image_url
        ELSE u1.profile_image_url
    END as other_user_image
FROM compatibility_scores cs
JOIN users u1 ON cs.user1_id = u1.id
JOIN users u2 ON cs.user2_id = u2.id
WHERE cs.user1_id = 'your-user-uuid' OR cs.user2_id = 'your-user-uuid'
ORDER BY cs.overall_compatibility DESC
LIMIT 20;

-- =============================================================================
-- PLAYLIST ANALYSIS QUERIES
-- =============================================================================

-- Analyze a user's playlists by genre distribution
WITH playlist_genres AS (
    SELECT 
        p.id as playlist_id,
        p.name as playlist_name,
        a.genres,
        COUNT(*) as track_count
    FROM playlists p
    JOIN playlist_tracks pt ON p.id = pt.playlist_id
    JOIN track_artists ta ON pt.track_id = ta.track_id
    JOIN artists a ON ta.artist_id = a.id
    WHERE p.user_id = 'your-user-uuid'
      AND NOT p.is_blended
    GROUP BY p.id, p.name, a.genres
)
SELECT 
    playlist_name,
    UNNEST(genres) as genre,
    SUM(track_count) as genre_track_count
FROM playlist_genres
WHERE array_length(genres, 1) > 0
GROUP BY playlist_name, UNNEST(genres)
ORDER BY playlist_name, genre_track_count DESC;

-- Find most popular tracks across all users
SELECT 
    t.name as track_name,
    STRING_AGG(DISTINCT a.name, ', ') as artists,
    t.popularity,
    COUNT(DISTINCT ust.user_id) as saved_by_users,
    AVG(af.valence) as avg_valence,
    AVG(af.energy) as avg_energy
FROM tracks t
JOIN user_saved_tracks ust ON t.id = ust.track_id
JOIN track_artists ta ON t.id = ta.track_id
JOIN artists a ON ta.artist_id = a.id
LEFT JOIN track_audio_features af ON t.id = af.track_id
GROUP BY t.id, t.name, t.popularity
HAVING COUNT(DISTINCT ust.user_id) >= 5  -- Saved by at least 5 users
ORDER BY COUNT(DISTINCT ust.user_id) DESC
LIMIT 20;

-- =============================================================================
-- BLEND PLAYLIST CREATION QUERIES
-- =============================================================================

-- Find tracks that both users in a potential match like (for blend playlists)
WITH user1_tracks AS (
    SELECT DISTINCT track_id
    FROM user_saved_tracks
    WHERE user_id = 'user1-uuid'
    UNION
    SELECT DISTINCT track_id
    FROM user_top_tracks
    WHERE user_id = 'user1-uuid' AND time_range = 'medium_term' AND position <= 30
),
user2_tracks AS (
    SELECT DISTINCT track_id
    FROM user_saved_tracks
    WHERE user_id = 'user2-uuid'
    UNION
    SELECT DISTINCT track_id
    FROM user_top_tracks
    WHERE user_id = 'user2-uuid' AND time_range = 'medium_term' AND position <= 30
),
shared_tracks AS (
    SELECT track_id
    FROM user1_tracks
    INTERSECT
    SELECT track_id
    FROM user2_tracks
)
SELECT 
    t.name as track_name,
    STRING_AGG(DISTINCT a.name, ', ') as artists,
    t.popularity,
    af.danceability,
    af.energy,
    af.valence
FROM shared_tracks st
JOIN tracks t ON st.track_id = t.id
JOIN track_artists ta ON t.id = ta.track_id
JOIN artists a ON ta.artist_id = a.id
LEFT JOIN track_audio_features af ON t.id = af.track_id
GROUP BY t.id, t.name, t.popularity, af.danceability, af.energy, af.valence
ORDER BY t.popularity DESC
LIMIT 50;

-- Find complementary tracks (different styles but compatible audio features)
WITH user1_preferences AS (
    SELECT 
        AVG(af.danceability) as avg_danceability,
        AVG(af.energy) as avg_energy,
        AVG(af.valence) as avg_valence
    FROM user_top_tracks utt
    JOIN track_audio_features af ON utt.track_id = af.track_id
    WHERE utt.user_id = 'user1-uuid' AND utt.time_range = 'medium_term'
),
user2_preferences AS (
    SELECT 
        AVG(af.danceability) as avg_danceability,
        AVG(af.energy) as avg_energy,
        AVG(af.valence) as avg_valence
    FROM user_top_tracks utt
    JOIN track_audio_features af ON utt.track_id = af.track_id
    WHERE utt.user_id = 'user2-uuid' AND utt.time_range = 'medium_term'
)
SELECT 
    t.name as track_name,
    STRING_AGG(DISTINCT a.name, ', ') as artists,
    t.popularity,
    af.danceability,
    af.energy,
    af.valence,
    -- Calculate how well this track fits both users' preferences
    ROUND(
        1.0 - (
            ABS(af.danceability - (u1.avg_danceability + u2.avg_danceability) / 2) +
            ABS(af.energy - (u1.avg_energy + u2.avg_energy) / 2) +
            ABS(af.valence - (u1.avg_valence + u2.avg_valence) / 2)
        ) / 3.0, 
        2
    ) as compatibility_score
FROM tracks t
JOIN track_artists ta ON t.id = ta.track_id
JOIN artists a ON ta.artist_id = a.id
JOIN track_audio_features af ON t.id = af.track_id
CROSS JOIN user1_preferences u1
CROSS JOIN user2_preferences u2
WHERE t.popularity > 50  -- Only reasonably popular tracks
ORDER BY compatibility_score DESC
LIMIT 30;

-- =============================================================================
-- CHAT STARTER GENERATION QUERIES
-- =============================================================================

-- Generate conversation starters based on shared music interests
SELECT 
    'shared_artist' as starter_type,
    'I see you also love ' || a.name || '! What''s your favorite song by them?' as starter_text,
    jsonb_build_object(
        'artist_name', a.name,
        'artist_id', a.id,
        'mutual_rank_user1', uta1.position,
        'mutual_rank_user2', uta2.position
    ) as metadata
FROM user_top_artists uta1
JOIN user_top_artists uta2 ON uta1.artist_id = uta2.artist_id
JOIN artists a ON uta1.artist_id = a.id
WHERE uta1.user_id = 'user1-uuid'
  AND uta2.user_id = 'user2-uuid'
  AND uta1.time_range = 'medium_term'
  AND uta2.time_range = 'medium_term'
  AND uta1.position <= 20
  AND uta2.position <= 20
ORDER BY (uta1.position + uta2.position)  -- Prioritize highly ranked shared artists
LIMIT 5

UNION ALL

-- Genre-based conversation starters
SELECT 
    'shared_genre' as starter_type,
    'We both seem to be into ' || g1.genre || ' music. Any recent discoveries in that genre?' as starter_text,
    jsonb_build_object(
        'genre', g1.genre,
        'user1_weight', g1.weight,
        'user2_weight', g2.weight
    ) as metadata
FROM user_genre_preferences g1
JOIN user_genre_preferences g2 ON g1.genre = g2.genre
WHERE g1.user_id = 'user1-uuid'
  AND g2.user_id = 'user2-uuid'
  AND g1.time_range = 'medium_term'
  AND g2.time_range = 'medium_term'
ORDER BY (g1.weight + g2.weight) DESC
LIMIT 3;

-- =============================================================================
-- ADMIN/ANALYTICS QUERIES
-- =============================================================================

-- Platform usage statistics
SELECT 
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT ua.user_id) as users_with_preferences,
    COUNT(DISTINCT cs.user1_id) + COUNT(DISTINCT cs.user2_id) as users_with_compatibility,
    AVG(uta.position) as avg_artist_diversity,
    COUNT(DISTINCT p.id) as total_playlists,
    COUNT(*) FILTER (WHERE p.is_blended) as blend_playlists
FROM users u
LEFT JOIN user_audio_preferences ua ON u.id = ua.user_id
LEFT JOIN compatibility_scores cs ON u.id = cs.user1_id OR u.id = cs.user2_id
LEFT JOIN user_top_artists uta ON u.id = uta.user_id
LEFT JOIN playlists p ON u.id = p.user_id;

-- Most popular genres across the platform
SELECT 
    genre,
    COUNT(DISTINCT user_id) as users_with_genre,
    AVG(weight) as avg_preference_weight,
    SUM(frequency) as total_artist_instances
FROM user_genre_preferences
WHERE time_range = 'medium_term'
GROUP BY genre
ORDER BY COUNT(DISTINCT user_id) DESC
LIMIT 20;

-- Audio feature trends across users
SELECT 
    ROUND(AVG(avg_danceability), 2) as platform_avg_danceability,
    ROUND(AVG(avg_energy), 2) as platform_avg_energy,
    ROUND(AVG(avg_valence), 2) as platform_avg_valence,
    ROUND(AVG(avg_acousticness), 2) as platform_avg_acousticness,
    ROUND(AVG(avg_tempo), 0) as platform_avg_tempo
FROM user_audio_preferences
WHERE time_range = 'medium_term';

-- =============================================================================
-- PERFORMANCE MONITORING QUERIES
-- =============================================================================

-- Check database size and table statistics
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
  AND tablename IN ('users', 'tracks', 'artists', 'user_top_artists', 'compatibility_scores')
ORDER BY tablename, attname;

-- Check for missing data that might affect matching
SELECT 
    'user_top_artists' as table_name,
    COUNT(DISTINCT user_id) as users_with_data,
    COUNT(*) as total_records
FROM user_top_artists
WHERE time_range = 'medium_term'

UNION ALL

SELECT 
    'user_genre_preferences' as table_name,
    COUNT(DISTINCT user_id) as users_with_data,
    COUNT(*) as total_records
FROM user_genre_preferences
WHERE time_range = 'medium_term'

UNION ALL

SELECT 
    'track_audio_features' as table_name,
    COUNT(DISTINCT track_id) as tracks_with_features,
    COUNT(*) as total_records
FROM track_audio_features;
