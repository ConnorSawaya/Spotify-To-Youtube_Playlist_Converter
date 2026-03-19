import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import requests
from googleapiclient.discovery import build

# --- INITIAL SETUP For env---
if os.path.exists(".env"):
    load_dotenv(override=True)

# .strip() handles any accidental spaces in Railway dashboard
SP_ID = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
SP_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()
YT_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

st.set_page_config(page_title="Playlist Porter", page_icon="🎵")
st.title("🎵 Playlist Porter")

# --- AUTHENTICATION LOGIC ---
def get_spotify_token():
    r = requests.post("https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SP_ID, SP_SECRET))
    return r.json().get("access_token")

def get_playlist_tracks(token, playlist_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=50", headers=headers)
    return r.json()

# --- APP LOGIC ---
url = st.text_input("🔗 Paste Spotify Playlist URL", placeholder="https://open.spotify.com/playlist/...")

if st.button("Convert to YouTube", use_container_width=True):
    if not url:
        st.warning("Please enter a URL first.") # if url is empty
    elif not YT_KEY:
        st.error("YouTube API Key missing in Railway Variables!")  # if the key si not setup
    else:
        with st.status("Converting...", expanded=True) as status:
            try:
                # gets playlist id
                if "playlist/" not in url:
                    st.error("Invalid URL format.")
                    st.stop()
                
                playlist_id = url.split("playlist/")[1].split("?")[0]
                token = get_spotify_token()
                data = get_playlist_tracks(token, playlist_id)
                if "error" in data:
                    st.error(f"Spotify error: {data['error']['message']}")
                    st.stop()
                tracks = [f"{i['track']['name']} {i['track']['artists'][0]['name']}" 
                          for i in data['items'] if i['track']]
                
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
