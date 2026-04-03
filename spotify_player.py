import spotipy
from spotipy.oauth2 import SpotifyOAuth
from concurrent.futures import ThreadPoolExecutor

# Spotify API credentials — set these in your Spotify Developer Dashboard
# https://developer.spotify.com/dashboard
CLIENT_ID = "CLIENT_ID_PLACEHOLDER"  # Replace with your Spotify Client ID
CLIENT_SECRET = "CLIENT_SECRET_PLACEHOLDER"  # Replace with your Spotify Client Secret
REDIRECT_URI = "https://localhost:8888/"
SCOPE = "user-modify-playback-state user-read-playback-state"

# Lazy-loaded client — avoids blocking OAuth at import time
_sp = None


def get_spotify_client():
    """Return the shared Spotify client, creating it on first use."""
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        ))
    return _sp


def _search_track(song_name: str, artist: str = None):
    query = f"track:{song_name}"
    if artist:
        query += f" artist:{artist}"
    results = get_spotify_client().search(q=query, type="track", limit=1)
    return results["tracks"]["items"]


def _get_devices() -> list:
    return get_spotify_client().devices()["devices"]


def play_song(song_name: str, artist: str = None):
    with ThreadPoolExecutor(max_workers=2) as executor:
        search_future = executor.submit(_search_track, song_name, artist)
        devices_future = executor.submit(_get_devices)
        try:
            tracks = search_future.result()
            devices = devices_future.result()
        except Exception as e:
            print(f"Spotify API error: {e}")
            return

    if not tracks:
        print(f"No results found for: {song_name}")
        return

    if not devices:
        print("No active Spotify devices found. Open Spotify on a device first.")
        return

    track = tracks[0]
    track_uri = track["uri"]
    track_name = track["name"]
    artist_name = track["artists"][0]["name"]

    try:
        get_spotify_client().start_playback(uris=[track_uri])
        print(f"Now playing: {track_name} by {artist_name}")
    except Exception as e:
        print(f"Playback error: {e}")

def pause_song():
    try:
        get_spotify_client().pause_playback()
        print("Playback paused.")
    except Exception as e:
        print(f"Error pausing playback: {e}")
