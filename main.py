import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build

# --- INITIAL SETUP ---
if os.path.exists(".env"):
    load_dotenv(override=True)

# .strip() handles any accidental spaces in Railway dashboard
SP_ID = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
SP_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()
YT_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8501/").strip()

st.set_page_config(page_title="Playlist Porter", page_icon="🎵")
st.title("🎵 Playlist Porter")

# --- AUTHENTICATION LOGIC ---
sp_oauth = SpotifyOAuth(
    client_id=SP_ID,
    client_secret=SP_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="playlist-read-private",
    show_dialog=True,
    cache_path=".cache"
)

# 1. Catch the 'code' parameter after Spotify redirects back
params = st.query_params
if "code" in params:
    try:
        sp_oauth.get_access_token(params["code"])
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Auth Error: {e}")

# 2. Check for existing token
token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())

if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    st.info("👋 Welcome! Please link your Spotify account to begin.")
    st.link_button("🔑 Login with Spotify", auth_url)
    st.stop()

# 3. Successful session
sp = spotipy.Spotify(auth=token_info['access_token'])

with st.sidebar:
    st.success("✅ Spotify Connected")
    if st.button("Logout & Reset"):
        if os.path.exists(".cache"):
            os.remove(".cache")
        st.rerun()

# --- APP LOGIC ---
url = st.text_input("🔗 Paste Spotify Playlist URL", placeholder="https://open.spotify.com/playlist/...")

if st.button("Convert to YouTube", use_container_width=True):
    if not url:
        st.warning("Please enter a URL first.")
    elif not YT_KEY:
        st.error("YouTube API Key missing in Railway Variables!")
    else:
        with st.status("Converting...", expanded=True) as status:
            try:
                # Extract Playlist ID
                if "playlist/" not in url:
                    st.error("Invalid URL format.")
                    st.stop()
                
                playlist_id = url.split("playlist/")[1].split("?")[0]
                results = sp.playlist_items(playlist_id)
                tracks = [f"{i['track']['name']} {i['track']['artists'][0]['name']}" 
                          for i in results['items'] if i['track']]
                
                final_results = []
                table_placeholder = st.empty()
                youtube = build("youtube", "v3", developerKey=YT_KEY)
                
                for track in tracks:
                    status.update(label=f"Searching: {track}")
                    resp = youtube.search().list(q=track, part="snippet", maxResults=1, type="video").execute()
                    
                    link = f"https://www.youtube.com/watch?v={resp['items'][0]['id']['videoId']}" if resp["items"] else "Not found"
                    final_results.append({"Track": track, "YouTube Link": link})
                    table_placeholder.dataframe(pd.DataFrame(final_results), use_container_width=True, hide_index=True)
                
                status.update(label="Conversion Complete!", state="complete")
                txt_data = "\n".join([f"{r['Track']}: {r['YouTube Link']}" for r in final_results])
                st.download_button("📂 Download Playlist (.txt)", txt_data, file_name="my_playlist.txt")
                
            except Exception as e:
                st.error(f"Error: {e}")
