import re
import json
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from fuzzywuzzy import fuzz, process
from collections import Counter
import string

@dataclass
class GenreExtractionConfig:
    """Configuration for genre extraction"""
    fuzzy_threshold: int = 80
    min_tag_length: int = 2
    max_tag_length: int = 50
    keyword_threshold: float = 0.6
    context_weight: float = 0.3

class GenreExtractor:
    def __init__(self, config: GenreExtractionConfig = None):
        self.config = config or GenreExtractionConfig()
        self.known_genres = self._load_genre_taxonomy()
        self.genre_keywords = self._load_genre_keywords()
        self.non_genre_patterns = self._load_non_genre_patterns()
        self.non_genre_keywords = self._load_non_genre_keywords()
        self.genre_families = self._load_genre_families()
        
    def extract_genres(self, lastfm_tags: List[str]) -> List[str]:
        """
        Main function: Extract only genre tags from Last.fm tags
        
        Args:
            lastfm_tags: List of tags from Last.fm API
            
        Returns:
            List of cleaned genre names
        """
        if not lastfm_tags:
            return []
            
        # Step 1: Basic cleaning and filtering
        cleaned_tags = self._clean_tags(lastfm_tags)
        
        # Step 2: Rule-based filtering (remove obvious non-genres)
        filtered_tags = self._filter_non_genres(cleaned_tags)
        
        # Step 3: Genre matching and extraction
        genres = []
        for tag in filtered_tags:
            genre = self._extract_genre_from_tag(tag, filtered_tags)
            if genre:
                genres.append(genre)
        
        # Step 4: Deduplicate and normalize
        return self._deduplicate_and_normalize(genres)
    
    def _clean_tags(self, tags: List[str]) -> List[str]:
        """Basic tag cleaning"""
        cleaned = []
        for tag in tags:
            if not isinstance(tag, str):
                continue
                
            # Clean the tag
            tag = tag.lower().strip()
            tag = re.sub(r'[^\w\s-]', '', tag)  # Remove special chars except hyphens
            tag = re.sub(r'\s+', ' ', tag)      # Normalize whitespace
            
            # Length filtering
            if self.config.min_tag_length <= len(tag) <= self.config.max_tag_length:
                cleaned.append(tag)
                
        return cleaned
    
    def _filter_non_genres(self, tags: List[str]) -> List[str]:
        """Filter out obvious non-genre tags using regex patterns"""
        filtered = []
        
        for tag in tags:
            is_non_genre = False
            
            # Check against non-genre patterns
            for pattern in self.non_genre_patterns:
                if re.match(pattern, tag, re.IGNORECASE):
                    is_non_genre = True
                    break
                    
            if not is_non_genre:
                filtered.append(tag)
                
        return filtered
    
    def _extract_genre_from_tag(self, tag: str, all_tags: List[str]) -> Optional[str]:
        """Extract genre from a single tag using multiple methods"""
        
        # Method 1: Exact match
        if tag in self.known_genres:
            return self.known_genres[tag]  # Return normalized form
            
        # Method 2: Fuzzy matching
        fuzzy_match = self._fuzzy_match_genre(tag)
        if fuzzy_match:
            return fuzzy_match
            
        # Method 3: Keyword-based classification
        if self._is_genre_by_keywords(tag):
            return tag
            
        # Method 4: Context-based classification
        if self._is_genre_by_context(tag, all_tags):
            return tag
            
        return None
    
    def _fuzzy_match_genre(self, tag: str) -> Optional[str]:
        """Find closest genre match using fuzzy matching"""
        match = process.extractOne(
            tag, 
            list(self.known_genres.keys()),
            scorer=fuzz.ratio
        )
        
        if match and match[1] >= self.config.fuzzy_threshold:
            return self.known_genres[match[0]]
            
        return None
    
    def _is_genre_by_keywords(self, tag: str) -> bool:
        """Check if tag is genre-like using keyword matching"""
        # Check for genre-indicating keywords
        for keyword in self.genre_keywords:
            if keyword in tag.lower():
                # Make sure it's not a non-genre keyword
                if not any(ng_keyword in tag.lower() for ng_keyword in self.non_genre_keywords):
                    return True
        return False
    
    def _is_genre_by_context(self, tag: str, all_tags: List[str]) -> bool:
        """Check if tag is genre-like based on context with other tags"""
        # If this tag appears with many known genres, it's likely a genre
        known_genre_count = sum(1 for t in all_tags if t in self.known_genres)
        
        if known_genre_count >= 2:  # At least 2 known genres in context
            # Check if tag has musical characteristics
            musical_indicators = ['music', 'sound', 'beat', 'rhythm', 'style', 'wave']
            if any(indicator in tag.lower() for indicator in musical_indicators):
                return True
                
            # Check if tag is part of a known genre family
            for family, genres in self.genre_families.items():
                if any(genre in tag.lower() for genre in genres):
                    return True
        
        return False
    
    def _character_based_classification(self, tag: str) -> bool:
        """Simple character-based genre classification"""
        # Genre tags typically have certain characteristics
        
        # Length check - genres are usually not too long
        if len(tag) > 20:
            return False
            
        # Check for non-genre indicators
        if any(char in tag for char in ['!', '?', '#', '@']):
            return False
            
        # Genres often contain hyphens or are compound words
        word_count = len(tag.split())
        hyphen_count = tag.count('-')
        
        # Single words or hyphenated words are more likely to be genres
        if word_count <= 2 or hyphen_count > 0:
            return True
            
        return False
    
    def _deduplicate_and_normalize(self, genres: List[str]) -> List[str]:
        """Remove duplicates and normalize genre names"""
        # Remove duplicates while preserving order
        seen = set()
        unique_genres = []
        
        for genre in genres:
            normalized = self._normalize_genre_name(genre)
            if normalized not in seen:
                seen.add(normalized)
                unique_genres.append(normalized)
                
        return unique_genres
    
    def _normalize_genre_name(self, genre: str) -> str:
        """Normalize genre name to standard form"""
        # Add your normalization rules here
        normalizations = {
            'hiphop': 'hip-hop',
            'hip hop': 'hip-hop',
            'r&b': 'rnb',
            'r and b': 'rnb',
            'electronic music': 'electronic',
            'alt rock': 'alternative rock',
            'alternative': 'alternative rock',
        }
        
        return normalizations.get(genre.lower(), genre)
    
    def _load_genre_taxonomy(self) -> Dict[str, str]:
        """Load genre taxonomy (implement based on your data source)"""
        # This should load from your genre database/file
        # For now, returning a sample
        return {
            'rock': 'rock',
            'pop': 'pop',
            'hip-hop': 'hip-hop',
            'hiphop': 'hip-hop',
            'hip hop': 'hip-hop',
            'electronic': 'electronic',
            'jazz': 'jazz',
            'blues': 'blues',
            'country': 'country',
            'classical': 'classical',
            'reggae': 'reggae',
            'metal': 'metal',
            'punk': 'punk',
            'folk': 'folk',
            'indie': 'indie',
            'alternative': 'alternative',
            'rnb': 'rnb',
            'soul': 'soul',
            'funk': 'funk',
            'house': 'house',
            'techno': 'techno',
            'dubstep': 'dubstep',
            'ambient': 'ambient',
            'experimental': 'experimental',
            'trance': 'trance',
            'drum and bass': 'drum and bass',
            'dnb': 'drum and bass',
            'breakbeat': 'breakbeat',
            'garage': 'garage',
            'trap': 'trap',
            'drill': 'drill',
            'grime': 'grime',
            'synthwave': 'synthwave',
            'vaporwave': 'vaporwave',
            'chillwave': 'chillwave',
            'darkwave': 'darkwave',
            'new wave': 'new wave',
            'post-punk': 'post-punk',
            'post-rock': 'post-rock',
            'shoegaze': 'shoegaze',
            'dream pop': 'dream pop',
            'britpop': 'britpop',
            'grunge': 'grunge',
            'emo': 'emo',
            'screamo': 'screamo',
            'hardcore': 'hardcore',
            'metalcore': 'metalcore',
            'deathcore': 'deathcore',
            'black metal': 'black metal',
            'death metal': 'death metal',
            'thrash metal': 'thrash metal',
            'heavy metal': 'heavy metal',
            'power metal': 'power metal',
            'progressive metal': 'progressive metal',
            'doom metal': 'doom metal',
            'sludge metal': 'sludge metal',
            'stoner rock': 'stoner rock',
            'psychedelic rock': 'psychedelic rock',
            'garage rock': 'garage rock',
            'surf rock': 'surf rock',
            'rockabilly': 'rockabilly',
            'skiffle': 'skiffle',
            'bebop': 'bebop',
            'swing': 'swing',
            'big band': 'big band',
            'smooth jazz': 'smooth jazz',
            'fusion': 'fusion',
            'free jazz': 'free jazz',
            'cool jazz': 'cool jazz',
            'hard bop': 'hard bop',
            'delta blues': 'delta blues',
            'chicago blues': 'chicago blues',
            'electric blues': 'electric blues',
            'rhythm and blues': 'rhythm and blues',
            'motown': 'motown',
            'neo-soul': 'neo-soul',
            'northern soul': 'northern soul',
            'southern soul': 'southern soul',
            'gospel': 'gospel',
            'spiritual': 'spiritual',
            'bluegrass': 'bluegrass',
            'americana': 'americana',
            'alt-country': 'alt-country',
            'outlaw country': 'outlaw country',
            'honky-tonk': 'honky-tonk',
            'western swing': 'western swing',
            'dancehall': 'dancehall',
            'roots reggae': 'roots reggae',
            'dub reggae': 'dub reggae',
            'ska punk': 'ska punk',
            'two-tone': 'two-tone',
            'calypso': 'calypso',
            'soca': 'soca',
            'salsa': 'salsa',
            'merengue': 'merengue',
            'bachata': 'bachata',
            'cumbia': 'cumbia',
            'reggaeton': 'reggaeton',
            'latin pop': 'latin pop',
            'bossa nova': 'bossa nova',
            'samba': 'samba',
            'forró': 'forró',
            'mpb': 'mpb',
            'tropicália': 'tropicália',
            'fado': 'fado',
            'flamenco': 'flamenco',
            'tango': 'tango',
            'mariachi': 'mariachi',
            'ranchera': 'ranchera',
            'norteño': 'norteño',
            'conjunto': 'conjunto',
            'tejano': 'tejano',
            'zydeco': 'zydeco',
            'cajun': 'cajun',
            'celtic': 'celtic',
            'irish traditional': 'irish traditional',
            'scottish traditional': 'scottish traditional',
            'klezmer': 'klezmer',
            'polka': 'polka',
            'waltz': 'waltz',
            'mazurka': 'mazurka',
            'tarantella': 'tarantella',
            'fandango': 'fandango',
            # Add more genres...
        }
    
    def _load_non_genre_patterns(self) -> List[str]:
        """Load regex patterns for non-genre tags"""
        return [
            r'^\d{2}s$',                    # 90s, 80s
            r'^\d{4}s?$',                   # 1990s, 2000
            r'.*seen live.*',               # seen live
            r'.*favorites?.*',              # favorite, favorites
            r'.*recommended.*',             # recommended
            r'.*love.*',                    # love, loved
            r'.*awesome.*',                 # awesome
            r'.*best.*',                    # best
            r'.*top.*',                     # top
            r'.*favorite.*',                # favorite
            r'.*male.*',                    # male, female
            r'.*female.*',
            r'.*british.*',                 # british, american
            r'.*american.*',
            r'.*canadian.*',
            r'.*australian.*',
            r'.*german.*',
            r'.*french.*',
            r'.*italian.*',
            r'.*chill.*',                   # chill, chillout
            r'.*relax.*',                   # relaxing
            r'.*emotional.*',               # emotional
            r'.*romantic.*',                # romantic
            r'.*sad.*',                     # sad
            r'.*happy.*',                   # happy
            r'.*energetic.*',               # energetic
            r'.*melancholic.*',             # melancholic
            r'.*upbeat.*',                  # upbeat
            r'.*mellow.*',                  # mellow
            r'.*nostalgic.*',               # nostalgic
            r'.*party.*',                   # party
            r'.*dance.*',                   # dance (can be tricky)
            r'.*summer.*',                  # summer, winter
            r'.*winter.*',
            r'.*night.*',                   # night, morning
            r'.*morning.*',
            r'.*driving.*',                 # driving music
            r'.*workout.*',                 # workout
            r'.*study.*',                   # study music
            r'.*background.*',              # background music
            r'.*instrumental.*',            # instrumental (debatable)
            r'.*acoustic.*',                # acoustic (debatable)
            r'.*live.*',                    # live
            r'.*cover.*',                   # cover
            r'.*remix.*',                   # remix
            r'.*radio.*',                   # radio
            r'.*edit.*',                    # edit
            r'.*version.*',                 # version
            r'.*mix.*',                     # mix
            r'.*single.*',                  # single
            r'.*album.*',                   # album
            r'.*ep.*',                      # ep
            r'.*compilation.*',             # compilation
            r'.*soundtrack.*',              # soundtrack
            r'.*theme.*',                   # theme
            r'.*christmas.*',               # christmas
            r'.*holiday.*',                 # holiday
        ]
    
    def _load_genre_keywords(self) -> List[str]:
        """Load keywords that indicate a tag might be a genre"""
        return [
            'core', 'wave', 'step', 'hop', 'house', 'techno', 'trance',
            'metal', 'rock', 'punk', 'folk', 'jazz', 'blues', 'soul',
            'funk', 'disco', 'reggae', 'ska', 'dub', 'ambient', 'drone',
            'noise', 'industrial', 'gothic', 'dark', 'black', 'death',
            'thrash', 'speed', 'power', 'prog', 'post', 'neo', 'new',
            'old', 'classic', 'modern', 'contemporary', 'traditional',
            'experimental', 'alternative', 'indie', 'underground',
            'mainstream', 'commercial', 'lo-fi', 'hi-fi', 'electronica',
            'electronic', 'digital', 'analog', 'acoustic', 'electric',
            'bass', 'drum', 'beat', 'rhythm', 'tempo', 'bpm',
            'major', 'minor', 'key', 'scale', 'mode', 'harmony',
            'melody', 'vocal', 'instrumental', 'orchestral', 'symphonic',
            'chamber', 'ensemble', 'band', 'group', 'solo', 'duo',
            'trio', 'quartet', 'quintet', 'sextet', 'septet', 'octet'
        ]
    
    def _load_non_genre_keywords(self) -> List[str]:
        """Load keywords that indicate a tag is NOT a genre"""
        return [
            'seen', 'live', 'concert', 'favorite', 'best', 'top', 'love',
            'awesome', 'great', 'good', 'bad', 'terrible', 'amazing',
            'perfect', 'beautiful', 'ugly', 'boring', 'exciting',
            'recommended', 'suggestion', 'playlist', 'album', 'single',
            'ep', 'compilation', 'soundtrack', 'theme', 'cover', 'remix',
            'edit', 'version', 'mix', 'radio', 'clean', 'explicit',
            'censored', 'uncensored', 'remastered', 'deluxe', 'special',
            'limited', 'edition', 'bonus', 'track', 'disc', 'cd', 'vinyl',
            'digital', 'download', 'stream', 'youtube', 'spotify',
            'apple', 'amazon', 'google', 'bandcamp', 'soundcloud',
            'male', 'female', 'vocalist', 'singer', 'musician', 'artist',
            'band', 'group', 'duo', 'trio', 'quartet', 'solo',
            'british', 'american', 'canadian', 'australian', 'german',
            'french', 'italian', 'spanish', 'japanese', 'korean',
            'chinese', 'russian', 'brazilian', 'mexican', 'indian',
            'summer', 'winter', 'spring', 'autumn', 'fall', 'christmas',
            'holiday', 'birthday', 'party', 'wedding', 'funeral',
            'morning', 'afternoon', 'evening', 'night', 'midnight',
            'driving', 'walking', 'running', 'workout', 'exercise',
            'study', 'work', 'sleep', 'relax', 'chill', 'background',
            'emotional', 'sad', 'happy', 'angry', 'depressed', 'excited',
            'romantic', 'nostalgic', 'melancholic', 'upbeat', 'mellow',
            'energetic', 'calm', 'peaceful', 'aggressive', 'violent'
        ]
    
    def _load_genre_families(self) -> Dict[str, List[str]]:
        """Load genre families for context-based classification"""
        return {
            'rock': ['rock', 'alternative', 'indie', 'grunge', 'punk', 'metal'],
            'electronic': ['electronic', 'techno', 'house', 'trance', 'dubstep', 'ambient'],
            'hip_hop': ['hip-hop', 'rap', 'trap', 'drill', 'boom', 'bap'],
            'jazz': ['jazz', 'bebop', 'swing', 'fusion', 'smooth', 'free'],
            'blues': ['blues', 'rhythm', 'delta', 'chicago', 'electric'],
            'country': ['country', 'folk', 'bluegrass', 'americana', 'western'],
            'classical': ['classical', 'baroque', 'romantic', 'modern', 'opera'],
            'reggae': ['reggae', 'ska', 'dub', 'dancehall', 'roots'],
            'pop': ['pop', 'dance', 'disco', 'synthpop', 'electropop'],
            'r&b': ['rnb', 'soul', 'funk', 'motown', 'neo-soul']
        }


# Usage example
def main():
    # Initialize extractor
    extractor = GenreExtractor()
    
    # Example Last.fm tags
    lastfm_tags = ['2020', 'folk', 'folklore (deluxe version)', 'alternative', 'folk pop', 'indie folk', 'pop', 'chamber pop', 'indie', 'singer-songwriter']
    # print()
    # Extract genres
    genres = extractor.extract_genres(lastfm_tags)
    print("Extracted genres:", genres)


if __name__ == "__main__":
    main()