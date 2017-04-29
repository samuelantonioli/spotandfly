#!/usr/bin/python
# tested with python 2.7.10 on macSierra
# youtube_dl
from __future__ import unicode_literals
import youtube_dl
# spotify
import spotipy
import spotipy.util as util
# youtube
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
# main
import sys

# for conversion to mp3:
# mac: brew install ffmpeg
# debian/ubuntu: sudo apt-get install ffmpeg

config = {
    # spotify (create at https://developer.spotify.com/my-applications)
    'CLIENT_ID': '<INSERT_YOUR_CLIENT_ID>',
    'CLIENT_SECRET': '<INSERT_YOUR_CLIENT_SECRET>',
    'REDIRECT_URI': 'http://localhost',
    # youtube (create at https://console.developers.google.com for YouTube Data API)
    'DEVELOPER_KEY': '<INSERT_YOUR_DEVELOPER_KEY>',
    'YOUTUBE_API_SERVICE_NAME': 'youtube',
    'YOUTUBE_API_VERSION': 'v3',
}

# spotify

def get_tracks_of_playlist(sp, username, playlist):
    playlist_tracks = []
    result = sp.user_playlist(
        username,
        playlist['id'],
        fields='tracks,next'
    )
    tracks = result['tracks']
    while True:
        if not tracks:
            break
        for i, item in enumerate(tracks['items']):
            try:
                track = item['track']
                playlist_tracks.append(
                    '{} - {}'.format(track['artists'][0]['name'], track['name'])
                )
            except Exception as e:
                print(e)
        if not tracks['next']:
            break
        tracks = sp.next(tracks)
    return playlist_tracks


def get_tracks_of_user(username, playlist_name):
    token = util.prompt_for_user_token(
        username,
        client_id=config['CLIENT_ID'],
        client_secret=config['CLIENT_SECRET'],
        redirect_uri=config['REDIRECT_URI']
    )
    if token:
        sp = spotipy.Spotify(auth=token)
        playlists = sp.user_playlists(username)
        for playlist in playlists['items']:
            if playlist['owner']['id'] == username and playlist['name'] == playlist_name:
                return get_tracks_of_playlist(sp, username, playlist)
        print('playlist with name "{}" not found.'.format(playlist_name))
    else:
        print('user not authenticated - allow this app to access your data.')
    return []

# youtube

def get_youtube_id(keyword):
    youtube = build(
        config['YOUTUBE_API_SERVICE_NAME'],
        config['YOUTUBE_API_VERSION'],
        developerKey=config['DEVELOPER_KEY']
    )
    search = youtube.search().list(
        q=keyword,
        part='id,snippet',
        order='viewCount',
        type='video',
        maxResults=1
    ).execute()
    for result in search.get('items', []):
        return result['id']['videoId']
    return None

def download_youtube_ids(youtube_ids, output_folder):
    # https://github.com/rg3/youtube-dl/blob/master/README.md#embedding-youtube-dl
    # outtmpl:
    # https://github.com/rg3/youtube-dl/issues/1865
    #
    # --extract-audio --audio-format mp3
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': u'{}/%(title)s.%(ext)s'.format(output_folder)
    }
    ids = filter(lambda x: not x is None, youtube_ids)
    urls = map(lambda x: 'http://www.youtube.com/watch?v={}'.format(x), ids)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

# main

def main():
    if len(sys.argv) > 3:
        username = sys.argv[1]
        playlist = sys.argv[2]
        output = sys.argv[3]
    else:
        print('tell me your username, the name of the playlist and the folder for the files.')
        print('usage: python spotandfly.py [username] [playlist] [output-folder]')
        sys.exit()

    tracks = get_tracks_of_user(username, playlist)
    youtube_ids = map(get_youtube_id, tracks)
    download_youtube_ids(youtube_ids, output)
    for youtube_id in youtube_ids:
        print('https://www.youtube.com/watch?v={}'.format(youtube_id))

if __name__ == '__main__':
    main()
