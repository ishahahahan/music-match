from dotenv import load_dotenv
import os, base64, json
from requests import post, get

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_str = client_id + ":" + client_secret
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def search_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)
    
    # open("artists.json", "w").write(json.dumps(json_result))
    artist_id = json_result["artists"]["items"][0]["id"]
    print(f"Artist ID: {artist_id}")
    return artist_id
    # print(json_result)
    
def artist_albums(artist_id, token):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?limit=5"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result

# Add this function for user authorization
def get_user_token(code):
    auth_str = client_id + ":" + client_secret
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://127.0.0.1:3000"
    }
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    open("token.json", "w").write(json.dumps(json_result))

auth_token = get_token()
print(f"Token: {auth_token}")
# artist_id = search_artist(token, "Taylor Swift")
# headers = get_auth_header(token)
# search = "Ross and Rachel"
# url = "https://api.spotify.com/v1/me"
# result = get(url, headers=headers)
# json_result = json.loads(result.content)
# open("search.json", "w").write(json.dumps(json_result))

# albums = artist_albums(artist_id, token)
# open("albums.json", "w").write(json.dumps(albums))
# print(albums)

