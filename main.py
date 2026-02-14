import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv # Make sure to pip install python-dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build

# --- FORCE LOAD VARIABLES ---
# This looks for the .env file in your folder and loads it into memory
load_dotenv(override=True)

SP_ID = os.getenv("SPOTIPY_CLIENT_ID")
SP_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# --- PAGE CONFIG ---
st.set_page_config(page_title="Playlist Porter", page_icon="🎵")

st.title("🎵 Playlist Porter")

# --- DEBUG STATUS ---
with st.sidebar:
    st.header("System Status")
    if SP_ID and SP_SECRET:
        st.success("✅ Spotify Keys Loaded")
    else:
        st.error("❌ Keys Still Not Found")
        st.info("Check that your .env file is in the same folder as main.py")
    
    yt_api_key = st.text_input("YouTube API Key", type="password")

# --- LOGIC ---
def get_spotify_tracks(playlist_url):
    try:
        auth_manager = SpotifyClientCredentials(client_id=SP_ID, client_secret=SP_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
        results = sp.playlist_items(playlist_id)
        return [f"{i['track']['name']} {i['track']['artists'][0]['name']}" for i in results['items'] if i['track']]
    except Exception as e:
        return None, str(e)

def get_youtube_link(query, api_key):
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.search().list(q=query, part="snippet", maxResults=1, type="video")
        response = request.execute()
        v_id = response["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={v_id}"
    except:
        return "Search Failed"

# --- UI ---
url = st.text_input("🔗 Spotify Playlist URL")

if st.button("Convert", use_container_width=True):
    if not yt_api_key or not url:
        st.warning("Provide both the YT Key and the Spotify URL.")
    elif not SP_ID:
        st.error("Spotify credentials missing from .env!")
    else:
        with st.status("Converting...") as status:
            tracks = get_spotify_tracks(url)
            if tracks:
                results = []
                table_placeholder = st.empty()
                for i, track in enumerate(tracks):
                    link = get_youtube_link(track, yt_api_key)
                    results.append({"Track": track, "Link": link})
                    table_placeholder.dataframe(pd.DataFrame(results), column_config={"Link": st.column_config.LinkColumn()})
                status.update(label="Complete!", state="complete")
                
                # Export as text
                output = "\n".join([f"{r['Track']}: {r['Link']}" for r in results])
                st.download_button("Download Links", output, file_name="playlist.txt")
