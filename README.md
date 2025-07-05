# MusicMatch

## Project Overview
MusicMatch is an innovative application that leverages music streaming APIs to connect users based on their musical preferences and listening habits. The platform aims to create meaningful connections through shared musical interests, helping users find friends and connections with compatible music tastes.

## Project Description
Music is a powerful medium that can reveal a lot about a person's personality, emotions, and lifestyle. Research shows that musical compatibility is strongly correlated with interpersonal compatibility and can serve as an effective foundation for meaningful relationships. MusicMatch leverages this insight to create a unique platform where users can:

- Connect with others who share similar music tastes
- Discover new music through connections with like-minded listeners
- Create and share playlists with potential connections
- Engage in conversations sparked by mutual musical interests
- Build relationships based on authentic musical compatibility

## Why Music Matters in Connections

The concept is based on research showing that:
- Music taste is a powerful indicator of personality traits and values
- Shared musical preferences create strong initial bonds between people
- Musical compatibility correlates with long-term friendship success
- Conversations about music lead to deeper and more meaningful interactions

## Technical Implementation

### Tech Stack
- **Data Analysis**: Python with Jupyter Notebooks
- **API Integration**: Spotipy library for music streaming API
- **Authentication**: OAuth 2.0 for secure account access
- **Environment Management**: dotenv for configuration

### Music API Features Utilized
1. **User Authentication & Authorization**
   - Comprehensive scope implementation for accessing user data
   - Secure OAuth flow with proper client credentials

2. **User Library Analysis**
   - Access to saved tracks and their metadata
   - Playlist creation and management
   - Top artists and tracks analysis across different time ranges

3. **Music Recommendation & Discovery**
   - Track features analysis for compatibility matching
   - Blend playlist functionality for shared music experiences

## Core Functionality

### User Profile Creation
The application creates rich user profiles based on:
- Top artists (short-term, medium-term, and long-term preferences)
- Favorite genres derived from artist preferences
- Listening patterns and preferences
- Saved tracks and curated playlists

### Matching Algorithm
Our sophisticated algorithm analyzes various factors to suggest compatible connections:
- Genre overlap and complementary preferences
- Artist similarity scores
- Playlist composition analysis
- Music feature preferences (danceability, energy, tempo, etc.)

### Compatibility Scoring
The matching algorithm calculates compatibility scores by analyzing:
- Genre diversity and overlap between users
- Artist commonality and complementary preferences
- Musical feature alignment (tempo, energy, valence preferences)
- Listening habits (time of day, frequency, exploration patterns)

### Interactive Features
- Create "blend" playlists between potential connections
- Share and recommend tracks to connections
- View compatibility scores based on musical taste
- Engage in conversations sparked by shared musical interests
- Music-based icebreakers for starting meaningful conversations

## Data Analysis Components
The project includes several Jupyter notebooks for data processing and analysis:
- `user_saved_items.ipynb`: Retrieves and analyzes user's saved tracks and albums
- `user_top_items.ipynb`: Analyzes user's top artists and tracks
- `playlists.ipynb`: Manages playlist data and metadata
- `blend.ipynb`: Implements functionality for creating blended playlists between users

## Installation and Setup

### Prerequisites
- Python 3.7+
- Music Streaming Developer Account
- API Client ID and Client Secret

### Setup Instructions
```bash
# Clone the repository
git clone https://github.com/ishahahahan/musicmatch.git

# Navigate to the project directory
cd musicmatch

# Install required packages
pip install -r requirements.txt

# Create a .env file with your API credentials
echo "CLIENT_ID=your_client_id" > .env
echo "CLIENT_SECRET=your_client_secret" > .env
echo "REDIRECT_URI=your_redirect_uri" > .env

# Launch Jupyter notebooks
jupyter notebook
```

## User Experience Flow
1. **Sign Up & Authentication**: Connect your music streaming account
2. **Profile Creation**: The app analyzes your music data to create your musical profile
3. **Preference Setting**: Set your preferences for matching (interests, location, etc.)
4. **Discover**: Browse potential connections based on musical compatibility
5. **Connect**: Initiate conversations with matches using music-based ice breakers
6. **Share & Listen**: Create blend playlists, share songs, and listen together

## Research Foundation
This project is based on academic research exploring the connection between musical preferences and personal compatibility. Key findings include:
- Musical preferences are strongly linked to personality traits (Big Five model)
- Shared music tastes correlate with shared values and worldviews
- Musical compatibility serves as a reliable predictor of interpersonal chemistry
- Music discussions create deeper connections than traditional social app conversations

## Future Development
- Mobile application development (iOS and Android)
- Enhanced recommendation algorithms using machine learning
- Real-time listening sessions between connected users
- Integration with music events and concerts
- Expanded social features and community building
- Advanced analytics for tracking connection quality

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
[Include your license information here]

## Contact
- GitHub: [@ishahahahan](https://github.com/ishahahahan)
