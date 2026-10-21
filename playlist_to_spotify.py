#!/usr/bin/env python3
"""Copy a YouTube playlist's track order into a new private Spotify playlist."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from urllib.parse import urlparse

import spotipy
import yt_dlp
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


@dataclass
class Match:
    source: str
    track: dict | None


def get_playlist(url: str) -> tuple[str, list[str]]:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(url, download=False)
    if not data or not data.get("entries"):
        raise ValueError("No videos were found. Check that this is a public or accessible playlist URL.")
    titles = [e.get("title", "").strip() for e in data["entries"] if e and e.get("title", "").strip()]
    return data.get("title") or "YouTube playlist", titles


def split_title(raw: str) -> tuple[str, str]:
    # Common YouTube music title formats: "Artist - Song", "Song (Official Video)".
    cleaned = re.sub(r"\s*\[(?:official|lyrics|lyric|music video|audio)[^\]]*\]", "", raw, flags=re.I)
    cleaned = re.sub(r"\s*\((?:official|lyrics|lyric|music video|audio)[^)]*\)", "", cleaned, flags=re.I)
    pieces = re.split(r"\s+[-–—]\s+", cleaned, maxsplit=1)
    if len(pieces) == 2:
        return pieces[0].strip(), pieces[1].strip()
    return "", cleaned.strip()


def spotify_client() -> spotipy.Spotify:
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    redirect = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback").strip()
    if not client_id or not client_secret:
        raise RuntimeError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in a .env file (see README).")
    auth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect,
                        scope="playlist-modify-private", open_browser=True, cache_path=".spotify_token_cache")
    return spotipy.Spotify(auth_manager=auth)


def find_track(sp: spotipy.Spotify, title: str) -> dict | None:
    artist, song = split_title(title)
    query = f'track:"{song}" artist:"{artist}"' if artist else f'track:"{song}"'
    results = sp.search(q=query, type="track", limit=5)
    items = results.get("tracks", {}).get("items", [])
    if not items and artist:
        items = sp.search(q=f"{song} {artist}", type="track", limit=5).get("tracks", {}).get("items", [])
    if not items:
        return None
    # Spotify's ranked first result is generally best; exact normalized title match preferred.
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.casefold())
    for item in items:
        if norm(item["name"]) == norm(song):
            return item
    return items[0]


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].startswith(("https://", "http://")):
        print("Usage: python playlist_to_spotify.py <YouTube playlist URL>")
        return 2
    load_dotenv()
    try:
        playlist_name, titles = get_playlist(sys.argv[1])
        print(f'YouTube playlist: {playlist_name}\nTracks found: {len(titles)}\n')
        sp = spotify_client()
        matches = []
        for i, title in enumerate(titles, 1):
            track = find_track(sp, title)
            matches.append(Match(title, track))
            if track:
                artist_names = ", ".join(a["name"] for a in track["artists"])
                print(f"{i:>3}. {title}  ->  {track['name']} — {artist_names}")
            else:
                print(f"{i:>3}. {title}  ->  NOT FOUND")

        found = [m.track for m in matches if m.track]
        if not found:
            print("\nNo Spotify tracks matched; nothing was created.")
            return 1
        print(f"\nMatched {len(found)} of {len(titles)}. Unmatched songs will be skipped.")
        answer = input("Create a new private Spotify playlist with these tracks in this order? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled; no Spotify playlist was created.")
            return 0

        user = sp.current_user()
        created = sp.user_playlist_create(user=user["id"], name=playlist_name, public=False,
                                          description=f"Copied from YouTube playlist: {sys.argv[1]}")
        uris = [track["uri"] for track in found]
        for start in range(0, len(uris), 100):
            sp.playlist_add_items(created["id"], uris[start:start + 100])
        print(f"\nCreated: {created['external_urls']['spotify']}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
