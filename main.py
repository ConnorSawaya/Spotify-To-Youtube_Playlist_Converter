import streamlit as st
import os
from spotify_scraper import SpotifyClient
from googleapiclient.discovery import build
from serpapi import GoogleSearch
import pandas as pd
from dotenv import load_dotenv

query = ""


# Api Setup using ENV variables so u losers cant steal my keys!! 
load_dotenv()
serpapi_api_key = os.getenv("SERPAPI_API_KEY")




st.set_page_config(page_title="Spotify -> YouTube Converter", page_icon ="🎵")

st.title("Spotify To YouTube Porter")
st.markdown("Convert Your Spotify Playlists to YouTube Playlists Quickly And Easily")



# Checks Content from the playlist and returns it with all the info needed for Searching it on YT

def get_spotify_tracks(playlist_url):
    client = SpotifyClient() # Instance of spotify client to fetch data
    try:
        playlist = client.get_playlist_info(playlist_url)
        track_list = []
        
        # Ensure tracks exists and is a list
        tracks = playlist.get("tracks", [])
        
        for track in tracks:
            name = track.get("name", "Unknown Title")
            # Defensive check for artist list
            artists = track.get("artist", [])
            artist_name = artists[0].get('name', '') if artists else ''
            track_list.append(f"{name} {artist_name}".strip())
            
        return track_list, playlist.get("name", "Unnamed Playlist") 
        
    except Exception as e:
        st.error(f"Spotify Error: {e}") 
        return [], None
    




    
def get_youtube_link(query, serpapi_api_key): # We pass the query and api key as perams 
    # We define the params inside the function so they are fresh for every song
    if not serpapi_api_key:
        return "Error: SerpApi Not Found"
    params = {
        "engine": "youtube",
        "search_query": query, # Removed the 'youtube' prefix here
        "api_key": serpapi_api_key
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "error" in results:
            return f"SerpApi Error: {results['error']}"
        
        # Check if video_results exists in the response
        if "video_results" in results and len(results["video_results"]) > 0:
            # Grab the link from the first result
            return results["video_results"][0].get("link")
            
    except Exception as e:
        return f"Error: {e}"
    return "Not Found 🥲"
  

# Main Ui and StreamLit Setup!

spotify_url = st.text_input("🔗 Paste Spotify Playlist URL", placeholder="https://open.spotify.com/playlist/...")

if st.button("Convert"): # Streamlit Button For Converrting it and tieing it all together
    

    if not spotify_url: # Spotify URL Check
        st.warning("Please enter a Spotify playlist URL!") 
    else:
        status = st.status("Processing...")
        with status:
            # Fetching From Spotfy
            st.write("Fetching Tracks From Spotify...")
            tracks, p_name = get_spotify_tracks(spotify_url)

            if tracks:
                st.success("Found Tracks")
                st.write(f"Found {len(tracks)} tracks in playlist: {p_name}")

                # Fetching Data From Youtube
                results = []
                progress_bar = st.progress(0)
                for i, track in enumerate(tracks):
                    st.write(f"Searching Youtube For: {track}")
                    url = get_youtube_link(track, serpapi_api_key)

                    results.append({"Song": track, "Youtube Link": url})
                    progress_bar.progress((i + 1) / len(tracks))
                status.update(label="Conversion Done!", state="complete", expanded=False)

                # Show THE RESULTS 🥳🥳🥳
                st.subheader(f"Results For: {p_name}")
                df = pd.DataFrame(results)

                # Show it as a Table
                # Show it as a Table with clickable links
                st.dataframe(
                    df, 
                    use_container_width=True,
                    column_config={
                        "Youtube Link": st.column_config.LinkColumn("Youtube Link")
                    }
                )
                                
                # Downloadable Button
                csv = df.to_csv(index=False).encode("utf-8") # Converts DataFrame to CSV and encodes
                st.download_button(
                    label="Download As CSV",
                    data = csv,
                    file_name=f"{p_name}_spotify_to_youtube.csv", # Sets the defult nameing convention for the downloaded file
                    mime="text/csv", # Tells the browser its a CSV file
                )
            else:
                st.error("Couldn't fetch tracks. Please Check Your Spotify Playlist URl and make sure it's public!")
with st._bottom:
    st.divider()
    st.caption("Made By Connor | [https://github.com/ConnorSawaya](https://github.com/ConnorSawaya)")

    
                    


            


