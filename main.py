import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build

# --- INITIAL SETUP ---
# Load local .env only if it exists (for local testing)
if os.path.exists(".env"):
    load_dotenv(override=True)

# API ENV - These must be set in the Railway "Variables" tab
SP_ID = os.getenv("SPOTIPY_CLIENT_ID")
SP_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
YT_KEY = os.getenv("YOUTUBE_API_KEY")

# Redirect URI: Uses Railway variable, defaults to local for dev
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8501/")

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

# 1. Handle returning from Spotify with the auth code in the URL
if "code" in st.query_params:
    try:
        # Exchange the code for an Access Token
        sp_oauth.get_access_token(st.query_params["code"])
        # Clear params to clean the URL and prevent loops
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login swap failed: {e}")

# 2. Check for a valid token in the cache
token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())

if not token_info:
    # If no valid token is found, force login
    auth_url = sp_oauth.get_authorize_url()
    st.info("👋 Welcome! Please link your Spotify account to begin.")
    st.link_button("🔑 Login with Spotify", auth_url)
    st.stop()

# 3. Successful Login - Initialize Spotify Client
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
        st.error("YouTube API Key missing! Add it to Railway Variables.")
    else:
        with st.status("Converting Playlist...") as status:
            try:
                # Extract Playlist ID safely
                if "playlist/" not in url:
                    st.error("Invalid URL. Please provide a Spotify Playlist link.")
                    st.stop()
                
                playlist_id = url.split("playlist/")[1].split("?")[0]
                results = sp.playlist_items(playlist_id)
                
                # Create track list: "Song Name Artist Name"
                tracks = [f"{i['track']['name']} {i['track']['artists'][0]['name']}" 
                          for i in results['items'] if i['track']]
                
                if not tracks:
                    st.warning("No tracks found in this playlist.")
                    st.stop()

                final_results = []
                table_placeholder = st.empty()
                
                # Initialize YouTube API
                youtube = build("youtube", "v3", developerKey=YT_KEY)
                
                for track in tracks:
                    # Search for the track on YouTube
                    search_query = youtube.search().list(
                        q=track, 
                        part="snippet", 
                        maxResults=1, 
                        type="video"
                    )
                    resp = search_query.execute()
                    
                    if resp.get("items"):
                        v_id = resp["items"][0]["id"]["videoId"]
                        link = f"https://www.youtube.com/watch?v={v_id}"
                    else:
                        link = "No video found"
                    
                    final_results.append({"Track": track, "YouTube Link": link})
                    
                    # Update table in real-time
                    df = pd.DataFrame(final_results)
                    table_placeholder.dataframe(df, use_container_width=True, hide_index=True)
                
                status.update(label="Conversion Complete!", state="complete")
                
                # Export results as a text file
                txt_data = "\n".join([f"{r['Track']}: {r['YouTube Link']}" for r in final_results])
                st.download_button("📂 Download Playlist (.txt)", txt_data, file_name="my_playlist.txt")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
