# YouTube Playlist to Spotify

Copy the track order from a YouTube playlist into a new private Spotify playlist. This Python command-line tool reads YouTube video titles, searches Spotify for likely matches, shows you the proposed matches, and creates the Spotify playlist only after you confirm. It does not download audio.

## What it does

- Reads playlist titles and entries from a YouTube playlist URL.
- Searches Spotify for each title, preserving the source order and duplicate entries.
- Displays the Spotify match beside each YouTube title before making changes.
- Creates a new private Spotify playlist after confirmation.
- Reports unmatched tracks; unmatched entries are skipped.

## Requirements

- Python 3.10 or newer
- A Spotify Developer app and its Client ID and Client Secret
- An active Spotify Premium subscription on the **owner account of the Spotify Developer app**. Spotify requires this for apps in Development Mode; a 403 mentioning an active Premium subscription is this Spotify restriction, not a playlist URL problem. See [Spotify's quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes).

The app owner must also allowlist the Spotify account that will authorize the tool in the Developer Dashboard's **Users and Access** settings. Development Mode currently allows up to five authenticated users per app.

## Setup (Windows PowerShell)

1. Create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. In the app settings, add this Redirect URI exactly:

   ```text
   http://127.0.0.1:8888/callback
   ```

3. In this folder, copy `.env.example` to `.env` and fill in the app's Client ID and Client Secret. Keep `.env` private; it is excluded by `.gitignore`.
4. Open PowerShell in this folder and install dependencies:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

5. Run the tool with a playlist URL:

   ```powershell
   python playlist_to_spotify.py "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"
   ```

The first run opens Spotify authorization in your browser. Approve private playlist editing for the Spotify account you want to use. The authorization token is cached locally in `.spotify_token_cache`, which is also excluded from Git.

## Matching limitations

YouTube video titles are not consistent song metadata. Titles in `Artist - Song` format tend to match best. Covers, remixes, live recordings, ambiguous titles, non-music videos, and tracks missing from Spotify may lead to an incorrect or missing match. Always review the preview before confirming.

Some YouTube URLs, including personalized Mix URLs, may resolve to generated playlists whose displayed name is a video title and whose entries include recommendations. Check the playlist name and number of tracks shown before continuing.

## Privacy and safety

This tool runs locally. It sends YouTube titles to Spotify search and uses Spotify OAuth to create a playlist in your account. It does not download or upload audio. Do not publish your `.env` file or `.spotify_token_cache`; both are ignored by Git.
