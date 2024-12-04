# YouTube_Streamer.py
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import yt_dlp
import pygame
import threading
import time
import os

class YouTubeStreamer:
    def __init__(self, api_key=None):
        """
        Initialize the YouTube streamer with API key
        """
        pygame.mixer.init()
        self.api_key = api_key or 'AIzaSyAdrdc-Gxd4MrCDfFoqjOTFNbHch9vPVwA'
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.current_stream = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 50
        self._position = 0
        self._duration = 0
        self._position_lock = threading.Lock()
        self._temp_dir = "temp_streams"
        if not os.path.exists(self._temp_dir):
            os.makedirs(self._temp_dir)

    def search_videos(self, query, max_results=5):
        """Search for YouTube videos"""
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video'
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                thumbnail = item['snippet']['thumbnails']['default']['url']
                
                # Get video duration
                video_response = self.youtube.videos().list(
                    part='contentDetails',
                    id=video_id
                ).execute()
                
                duration = video_response['items'][0]['contentDetails']['duration']
                
                videos.append({
                    'id': video_id,
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })
                
            return videos
            
        except HttpError as e:
            raise Exception(f"An HTTP error occurred: {e.resp.status} {e.content}")

    def load(self, video_url):
        """Load a YouTube video for streaming"""
        try:
            # Stop current stream if exists
            if self.current_stream:
                self.stop()

            # Get audio stream using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self._temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_path = os.path.splitext(filename)[0] + '.mp3'
                
                # Load the audio file
                pygame.mixer.music.load(mp3_path)
                
                # Store stream information
                self.current_stream = {
                    'title': info.get('title', 'Unknown Title'),
                    'duration': info.get('duration', 0),
                    'author': info.get('uploader', 'Unknown Artist'),
                    'url': video_url,
                    'file_path': mp3_path
                }
                
                # Set volume
                pygame.mixer.music.set_volume(self.volume / 100)
                
                return self.current_stream
                
        except Exception as e:
            raise Exception(f"Failed to load video: {str(e)}")

    def play(self):
        """Start or resume playback"""
        if self.current_stream:
            if self.is_paused:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            
    def pause(self):
        """Pause playback"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            
    def resume(self):
        """Resume playback"""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            
    def stop(self):
        """Stop playback and clear current stream"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        
        # Clean up temporary file
        if self.current_stream and 'file_path' in self.current_stream:
            try:
                os.remove(self.current_stream['file_path'])
            except:
                pass
        self.current_stream = None
            
    def seek(self, position):
        """Seek to position in seconds"""
        if self.current_stream:
            pygame.mixer.music.play(start=position)
            if self.is_paused:
                pygame.mixer.music.pause()
            
    def set_volume(self, volume):
        """Set volume level (0-100)"""
        self.volume = max(0, min(100, volume))
        pygame.mixer.music.set_volume(self.volume / 100)
            
    def get_position(self):
        """Get current playback position in seconds"""
        if self.is_playing:
            return pygame.mixer.music.get_pos() / 1000
        return 0
            
    def get_duration(self):
        """Get total duration in seconds"""
        if self.current_stream:
            return self.current_stream['duration']
        return 0