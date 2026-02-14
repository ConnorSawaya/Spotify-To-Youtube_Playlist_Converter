import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build

# --- INITIAL SETUP --- stuff
load_dotenv(override=True)
# Api ENV
SP_ID = os.getenv("SPOTIPY_CLIENT_ID")
SP_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
YT_KEY = os.getenv("YOUTUBE_API_KEY")

st.set_page_config(page_title="Playlist Porter", page_icon="🎵")
st.title("🎵 Playlist Porter")

# Must match your Spotify Dashboard exactly!
REDIRECT_URI = "https://spotify-to-youtubeplaylistconverter-production.up.railway.app/"

# --- AUTHENTICATION LOGIC ---
sp_oauth = SpotifyOAuth( # perms
    client_id=SP_ID,
    client_secret=SP_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="playlist-read-private",
    show_dialog=True,
    cache_path=".cache"
)

# 1. Check if we are returning from Spotify with a login code
if "code" in st.query_params:
    try:
        # Trade the URL code for a real Access Token
        sp_oauth.get_access_token(st.query_params["code"])
        # Clear the URL so we don't loop
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login swap failed: {e}")

# 2. Check if we have a valid token in our cache
token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())

if not token_info: # if token not already set
    # If no token, show the login button and STOP the rest of the app
    auth_url = sp_oauth.get_authorize_url()
    st.info("👋 Welcome! Please link your Spotify account to begin.")
    st.link_button("🔑 Login with Spotify", auth_url) # Spotify login button
    st.stop()

# 3. If we are here, we are successfully logged in
sp = spotipy.Spotify(auth=token_info['access_token'])

with st.sidebar: # sidebar stuff
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
    elif not YT_KEY: #
        st.error("YouTube API Key missing from environment!") # if Yt api is not set
    else:
        with st.status("Converting Playlist...") as status:
            try:
                # Extract Playlist ID
                playlist_id = url.split("playlist/")[1].split("?")[0]
                results = sp.playlist_items(playlist_id)
                tracks = [f"{i['track']['name']} {i['track']['artists'][0]['name']}" for i in results['items'] if i['track']]
                
                final_results = []
                table_placeholder = st.empty()
                
                # YouTube Search
                youtube = build("youtube", "v3", developerKey=YT_KEY) # passes api key
                
                for track in tracks:
                    search_query = youtube.search().list(q=track, part="snippet", maxResults=1, type="video")
                    resp = search_query.execute()
                    
                    if resp["items"]:
                        v_id = resp["items"][0]["id"]["videoId"]
                        link = f"https://www.youtube.com/watch?v={v_id}"
                    else:
                        link = "No video found"
                    
                    final_results.append({"Track": track, "YouTube Link": link})
                    # Upadte a streamlit ui if theress a change
                    table_placeholder.dataframe(pd.DataFrame(final_results), use_container_width=True, hide_index=True)
                
                status.update(label="Done!", state="complete")
                
                # Export Button with all the data(like the links
                txt_data = "\n".join([f"{r['Track']}: {r['YouTube Link']}" for r in final_results])
                st.download_button(" Download Playlist as TXT", txt_data, file_name="my_playlist.txt")
                
            except Exception as e:
                st.error(f"An error occurred: {e}") # if a error happened it says why


