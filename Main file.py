import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
from mutagen.mp3 import MP3
import time 
from threading import Thread
from youtube_search import YoutubeSearch
import string
import yt_dlp
from json_library import JsonLibrary
from YouTube_Streamer import YouTubeStreamer
from rating_dialog import RatingDialog

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.paused_position = 0 



    def load(self, song_path):
        pygame.mixer.music.load(song_path)
        self.current_song = song_path
        self.paused_position = 0  # Reset paused position when loading new song


    def play(self, start_pos=0):
        if self.is_paused:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.play(start=start_pos)
        self.is_playing = True
        self.is_paused = False
        
    def pause(self):
        pygame.mixer.music.pause()
        self.is_playing = False
        self.is_paused = True
        
    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        
    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)

class YoutubeDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)
    
    def sanitize_filename(self, title):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in title if c in valid_chars)
        return filename[:50]
    
    def download_audio(self, url, progress_callback=None):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_callback] if progress_callback else None,
                'default_search': 'ytsearch',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:
                    # It's a playlist or a search result
                    info = info['entries'][0]
                filename = ydl.prepare_filename(info)
                mp3_path = os.path.splitext(filename)[0] + '.mp3'
                return mp3_path
                
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

class Song:
    def __init__(self, path, title=None, source="local"):
        self.path = path
        self.source = source
        self.title = title or os.path.basename(path)
        self.duration = self._get_duration()
    
    def _get_duration(self):
        try:
            audio = MP3(self.path)
            return audio.info.length
        except:
            return 0

class JukeboxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Jukebox")
        self.root.geometry("800x800")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.library = JsonLibrary()
        self.youtube_streamer = YouTubeStreamer()
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # or 'alt', 'default', 'classic' depending on your OS
        self.style.configure('Custom.TButton', 
                           padding=5, 
                           font=('Helvetica', 10))
        self.style.configure('Custom.TFrame', 
                           background='#f0f0f0')
        
        self.player = MusicPlayer()
        self.youtube_downloader = YoutubeDownloader()
        self.playlist = []
        self.current_song_index = -1
        self.current_duration = 0
        self.current_position = 0

        self.is_dragging = False  
        self.start_time = 0    # Track when playback started
        self.seek_position = 0 # Track manual seek position
        
        self._create_gui()
        self._create_updater()
        
    def _create_gui(self):
        # Main container with padding and background
        main_frame = ttk.Frame(self.root, padding="20", style='Custom.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        
        # YouTube Search Section
        youtube_frame = ttk.LabelFrame(main_frame, text="YouTube Search", padding="10")
        youtube_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        youtube_frame.columnconfigure(0, weight=3)
        
        self.youtube_var = tk.StringVar()
        self.youtube_entry = ttk.Entry(
            youtube_frame,
            textvariable=self.youtube_var,
            font=('Helvetica', 11)
        )
        self.youtube_entry.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E))
        
        button_frame = ttk.Frame(youtube_frame)
        button_frame.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="Search",
            command=self.search_youtube,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Download",
            command=self.download_youtube,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=2)

        media_controls = ttk.Frame(button_frame)
        media_controls.pack(side=tk.LEFT, padx=10)


        

        
        
        # Track ID input and Local Library button
        track_frame = ttk.Frame(youtube_frame)
        track_frame.grid(row=0, column=2, padx=5)
        
        self.input_txt = ttk.Entry(track_frame, width=5)
        self.input_txt.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            track_frame,
            text="View Local Track",
            command=self.getlocallib,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=2)

        
        # Search Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        results_frame.columnconfigure(0, weight=1)
        
        self.search_results = tk.Listbox(
            results_frame,
            height=5,
            font=('Helvetica', 10),
            selectmode=tk.SINGLE,
            activestyle='dotbox',
            bg='white'
        )
        self.search_results.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.search_results.bind('<Double-Button-1>', self.download_selected)



        search_controls = ttk.Frame(results_frame)
        search_controls.grid(row=1, column=0, pady=5)
        
        ttk.Button(
            search_controls,
            text="Stream",
            command=lambda: self.stream_youtube(),
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=5)

     
        # Playlist and Library Section (side by side)
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # Playlist
        playlist_frame = ttk.LabelFrame(content_frame, text="Playlist", padding="10")
        playlist_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.playlist_box = tk.Listbox(
            playlist_frame,
            height=10,
            font=('Helvetica', 10),
            selectmode=tk.SINGLE,
            activestyle='dotbox',
            bg='white'
        )
        self.playlist_box.pack(fill=tk.BOTH, expand=True)
        playlist_scrollbar = ttk.Scrollbar(playlist_frame, orient=tk.VERTICAL, command=self.playlist_box.yview)
        playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_box.config(yscrollcommand=playlist_scrollbar.set)
        
        # Local Library Results
        library_frame = ttk.LabelFrame(content_frame, text="Local Library", padding="10")
        library_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.result = tk.Listbox(
            library_frame,
            height=10,
            font=('Helvetica', 10),
            selectmode=tk.SINGLE,
            activestyle='dotbox',
            bg='white'
        )
        self.result.pack(fill=tk.BOTH, expand=True)
        library_scrollbar = ttk.Scrollbar(library_frame, orient=tk.VERTICAL, command=self.result.yview)
        library_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result.config(yscrollcommand=library_scrollbar.set)

        self.result.bind('<Button-1>', self.handle_result_click)

        # Playback Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Playback Controls", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        # Playlist management buttons (left side)
        playlist_controls = ttk.Frame(button_frame)
        playlist_controls.pack(side=tk.LEFT, padx=20)

        ttk.Button(
            playlist_controls,
            text="Clear Playlist",
            command=self.clearplaylist,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            playlist_controls,
            text="Add Local Files",
            command=self.add_local_songs,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=5)

        # Playback control buttons (center)
        playback_controls = ttk.Frame(button_frame)
        playback_controls.pack(side=tk.LEFT, padx=20)

        ttk.Button(
            playback_controls,
            text="⏪ 10s",
            command=lambda: self.seek_relative(-10),
            style='Custom.TButton',
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            playback_controls,
            text="⏯️",
            command=self.toggle_play_pause,
            style='Custom.TButton',
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            playback_controls,
            text="10s ⏩",
            command=lambda: self.seek_relative(10),
            style='Custom.TButton',
            width=8
        ).pack(side=tk.LEFT, padx=2)


        self.result.bind('<Double-Button-1>', self.play_from_library)

        # Volume Control (right side)
        volume_frame = ttk.Frame(control_frame)
        volume_frame.grid(row=3, column=2, pady=5)

        ttk.Label(
            volume_frame,
            text="Volume:",
            font=('Helvetica', 9)
        ).pack(side=tk.LEFT, padx=5)

        self.volume_scale = ttk.Scale(
            volume_frame,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            command=self.change_volume,
            length=100
        )
        self.volume_scale.set(0.5)
        self.volume_scale.pack(side=tk.LEFT, padx=5)
        
        # Now Playing Label
        self.now_playing_var = tk.StringVar(value="No song playing")
        ttk.Label(
            control_frame,
            textvariable=self.now_playing_var,
            font=('Helvetica', 11, 'bold')
        ).grid(row=0, column=0, columnspan=3, pady=5)
        
        # Time Labels and Progress Bar
        self.time_var = tk.StringVar(value="0:00 / 0:00")
        ttk.Label(
            control_frame,
            textvariable=self.time_var,
            font=('Helvetica', 9)
        ).grid(row=1, column=0, pady=5)
        
        # Custom Progress Bar Frame
        self.progress_frame = ttk.Frame(control_frame)
        self.progress_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10)
        control_frame.columnconfigure(1, weight=1)
        
        # Create canvas for custom progress bar
        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            height=20,
            bg='#e0e0e0',
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, expand=True)
        
        # Create progress bar elements
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 20,
            fill='#4a90e2',
            width=0
        )
        
        # Bind canvas events
   
        self.progress_canvas.bind('<Button-1>', self.start_seek)
        self.progress_canvas.bind('<B1-Motion>', self.update_seek)
        self.progress_canvas.bind('<ButtonRelease-1>', self.end_seek)

                
        # Bind events
        self.playlist_box.bind('<Double-Button-1>', lambda e: self.play())
        self.root.bind('<space>', lambda e: self.toggle_play_pause())
        
    def _create_updater(self):
        def update_progress():
            while True:
                if self.current_song_index >= 0:
                    try:
                        song = self.playlist[self.current_song_index]
                        
                        if song.source == "stream":
                            if self.youtube_streamer.is_playing:
                                position = self.youtube_streamer.get_position()
                                duration = self.youtube_streamer.get_duration()
                                
                                # Update progress bar and time
                                if duration > 0:
                                    progress = position / duration
                                    progress = min(1.0, max(0, progress))
                                    
                                    canvas_width = self.progress_canvas.winfo_width()
                                    bar_width = canvas_width * progress
                                    
                                    self.root.after(0, lambda: (
                                        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 20),
                                        self.time_var.set(f"{time.strftime('%M:%S', time.gmtime(position))} / {time.strftime('%M:%S', time.gmtime(duration))}")
                                    ))
                        
                        elif self.player.is_playing and not self.player.is_paused:
                            elapsed_time = time.time() - self.start_time
                            
                            # Update progress bar and time
                            progress = (elapsed_time / song.duration) if song.duration > 0 else 0
                            progress = min(1.0, max(0, progress))
                            
                            canvas_width = self.progress_canvas.winfo_width()
                            bar_width = canvas_width * progress
                            
                            self.root.after(0, lambda: (
                                self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 20),
                                self.time_var.set(f"{time.strftime('%M:%S', time.gmtime(elapsed_time))} / {time.strftime('%M:%S', time.gmtime(song.duration))}")
                            ))
                            
                            if elapsed_time >= song.duration:
                                self.root.after(0, self.play_next)
                                
                    except Exception as e:
                        print(f"Error updating progress: {e}")
                        
                time.sleep(0.1)
        
        self.update_thread = Thread(target=update_progress, daemon=True)
        self.update_thread.start()
    
    def start_seek(self, event):
        if self.current_song_index >= 0:
            self.is_dragging = True
            self.update_seek(event)
    
    def update_seek(self, event):
        if self.current_song_index >= 0 and self.is_dragging:
            canvas_width = self.progress_canvas.winfo_width()
            click_position = max(0, min(event.x, canvas_width)) / canvas_width
            
            song = self.playlist[self.current_song_index]
            new_position = click_position * song.duration
            
            # Update visual only while dragging
            bar_width = canvas_width * click_position
            self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 20)
            
            # Update time label
            current_str = time.strftime('%M:%S', time.gmtime(new_position))
            duration_str = time.strftime('%M:%S', time.gmtime(song.duration))
            self.time_var.set(f"{current_str} / {duration_str}")

            self.seek_position = new_position
    
    def end_seek(self, event):
        if self.current_song_index >= 0 and self.is_dragging:
            self.is_dragging = False
            was_playing = self.player.is_playing and not self.player.is_paused
            pygame.mixer.music.play(start=self.seek_position)
            if not was_playing:
                pygame.mixer.music.pause()
            self.start_time = time.time() - self.seek_position  # Update start time based on seek position
        
    def toggle_play_pause(self):
        if self.current_song_index < 0:
            if self.playlist:
                self.play()
            return
            
        song = self.playlist[self.current_song_index]
        if song.source == "stream":
            if self.youtube_streamer.is_playing:
                self.youtube_streamer.pause()
            else:
                self.youtube_streamer.resume()
        else:
            if self.player.is_playing:
                self.player.current_position = time.time() - self.start_time
                self.pause()
            else:
                if self.player.is_paused:
                    self.start_time = time.time() - self.player.current_position
                    self.player.play()
                else:
                    self.play()
    
    def play_next(self):
        if self.current_song_index < len(self.playlist) - 1:
            self.current_song_index += 1
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.selection_set(self.current_song_index)
            self.playlist_box.see(self.current_song_index)
            self.play()

    def change_volume(self, value):
        volume = float(value)
        if self.current_song_index >= 0:
            song = self.playlist[self.current_song_index]
            if song.source == "stream":
                self.youtube_streamer.set_volume(int(volume * 100))
            else:
                self.player.set_volume(volume)

    def stream_youtube(self):
        """Stream the selected YouTube video"""
        selection = self.search_results.curselection()
        if not selection:
            return
            
        selected_item = self.search_results.get(selection[0])
        url = selected_item.split(" | ")[1].strip()
        
        try:
            # Load and play the stream
            stream_info = self.youtube_streamer.load(url)
            if stream_info:
                # Create a virtual Song object for the stream
                song = Song(
                    path=url,  # Use URL as path for streams
                    title=stream_info['title'],
                    source="stream"
                )
                
                # Add to playlist if not already there
                if song.path not in [s.path for s in self.playlist]:
                    self.playlist.append(song)
                    self.playlist_box.insert(tk.END, f"[STREAM] {song.title}")
                
                # Find the song index in playlist
                for i, s in enumerate(self.playlist):
                    if s.path == song.path:
                        self.current_song_index = i
                        break
                
                # Update selection in playlist
                self.playlist_box.selection_clear(0, tk.END)
                self.playlist_box.selection_set(self.current_song_index)
                self.playlist_box.see(self.current_song_index)
                
                # Start playback
                self.youtube_streamer.play()
                self.now_playing_var.set(f"Now streaming: {song.title}")
                
        except Exception as e:
            messagebox.showerror("Streaming Error", str(e))


    def search_youtube(self):
        """Modified search method to use YouTube API"""
        query = self.youtube_var.get().strip()
        if not query:
            return
            
        try:
            # Clear previous results
            self.search_results.delete(0, tk.END)
            
            # Use YouTubeStreamer's search instead of youtube_search
            results = self.youtube_streamer.search_videos(query, max_results=5)
            
            # Display results
            for result in results:
                title = result['title']
                duration = result.get('duration', 'Unknown duration')
                url = result['url']
                self.search_results.insert(tk.END, f"{title} ({duration}) | {url}")
                
        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def getlocallib(self):
            """View track from library"""
            key = self.input_txt.get()                    
            name = self.library.get_name(key)                        
            if name is not None:
                artist = self.library.get_artist(key)               
                rating = self.library.get_rating(key)              
                play_count = self.library.get_play_count(key)
                file_path = self.library.get_file_path(key)       
                track_details = f"{key}. {name}\n{artist}\nrating: {rating}\nplays: {play_count}"
                set_text(self.result, track_details.split('\n'))
                # Store the key for later use
                self.result.key = key
            else:
                set_text(self.result, [f"Track {key} not found"])
                self.result.key = None

    def play_from_library(self, event=None):
        """Play selected song from library"""
        if hasattr(self.result, 'key') and self.result.key is not None:
            key = self.result.key
            file_path = self.library.get_file_path(key)
            
            if file_path and os.path.exists(file_path):
                # Create a Song object
                song = Song(
                    file_path,
                    title=self.library.get_name(key),
                    source="library"
                )
                
                # Add to playlist if not already there
                if song.path not in [s.path for s in self.playlist]:
                    self.playlist.append(song)
                    self.playlist_box.insert(tk.END, song.title)
                
                # Find the song index in playlist
                for i, s in enumerate(self.playlist):
                    if s.path == song.path:
                        self.current_song_index = i
                        break
                
                # Update selection in playlist
                self.playlist_box.selection_clear(0, tk.END)
                self.playlist_box.selection_set(self.current_song_index)
                self.playlist_box.see(self.current_song_index)
                
                # Play the song
                self.play()
                
                # Increment play count
                self.library.increment_play_count(key)
            else:
                messagebox.showerror("Error", "Could not find the song file. Please check the file path in the library JSON file.")



    



    def download_selected(self, event):
        selection = self.search_results.curselection()
        if not selection:
            return
            
        selected_item = self.search_results.get(selection[0])
        url = selected_item.split(" | ")[1].strip()
        self.youtube_var.set(url)
        self.download_youtube()
    
    def download_youtube(self):
        query = self.youtube_var.get().strip()
        if not query:
            return
        
        # If the input is not a URL, convert it to a YouTube search
        if not query.startswith(('http://', 'https://')):
            query = f"ytsearch1:{query}"
        
        try:
            # Show download progress
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Downloading...")
            progress_window.geometry("300x150")
            
            progress_label = ttk.Label(progress_window, text="Downloading audio...")
            progress_label.pack(pady=20)
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(
                progress_window,
                variable=progress_var,
                maximum=100
            )
            progress_bar.pack(pady=10, padx=20, fill=tk.X)
            
            last_update_time = {'time': 0}
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        current_time = time.time()
                        if current_time - last_update_time['time'] < 0.1:
                            return
                        
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            percentage = (downloaded / total) * 100
                            # Update the progress in the main thread
                            self.root.after(0, lambda: progress_var.set(percentage))
                            last_update_time['time'] = current_time
                    except Exception as e:
                        print(f"Progress update error: {e}")
                        pass
            
            def download_thread():
                try:
                    output_path = self.youtube_downloader.download_audio(
                        query,
                        progress_callback=progress_hook
                    )
                    
                    song = Song(output_path, source="youtube")
                    self.playlist.append(song)
                    self.playlist_box.insert(tk.END, song.title)
                    
                    progress_window.destroy()
                    messagebox.showinfo("Success", "Song downloaded and added to playlist!")
                    
                except Exception as e:
                    progress_window.destroy()
                    messagebox.showerror("Download Error", str(e))
            
            Thread(target=download_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Download Error", str(e))
    
    def add_local_songs(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("MP3 Files", "*.mp3")]
        )
        for path in file_paths:
            song = Song(path, source="local")
            self.playlist.append(song)
            self.playlist_box.insert(tk.END, song.title)
            
    def play(self):
        """Modified play method to handle both local files and streams"""
        selection = self.playlist_box.curselection()
        if not selection:
            if self.playlist:
                self.playlist_box.selection_set(0)
                self.current_song_index = 0
            else:
                return
        else:
            self.current_song_index = selection[0]
            
        song = self.playlist[self.current_song_index]
        
        # Stop any current playback
        if self.player.is_playing:
            self.player.stop()
        if self.youtube_streamer.is_playing:
            self.youtube_streamer.stop()
        
        # Handle different types of playback
        if song.source == "stream":
            self.youtube_streamer.load(song.path)
            self.youtube_streamer.play()
            self.now_playing_var.set(f"Now streaming: {song.title}")
        else:
            self.player.load(song.path)
            self.start_time = time.time()
            self.player.current_position = 0
            self.now_playing_var.set(f"Now playing: {song.title}")
            self.player.play()


    def stop(self):
        """Stop playback for both local and streaming"""
        if self.current_song_index >= 0:
            song = self.playlist[self.current_song_index]
            if song.source == "stream":
                self.youtube_streamer.stop()
            else:
                self.player.stop()
        
        self.now_playing_var.set("No song playing")
        self.time_var.set("0:00 / 0:00")
        self.progress_canvas.coords(self.progress_bar, 0, 0, 0, 20)        

    def clearplaylist(self):
        self.stop()  # Stop any current playback
        self.playlist = []
        self.playlist_box.delete(0, tk.END)
        self.current_song_index = -1
        
    def pause(self):
        """Modified pause method to handle both local files and streams"""
        current_song = self.playlist[self.current_song_index] if self.current_song_index >= 0 else None
        
        if current_song and current_song.source == "stream":
            if self.youtube_streamer.is_playing:
                self.youtube_streamer.pause()
            else:
                self.youtube_streamer.resume()
        else:
            if self.player.is_playing:
                self.player.pause()
            else:
                self.start_time = time.time() - self.player.current_position
                self.player.play()
            
    def change_volume(self, value):
        self.player.set_volume(float(value))


    def stream_selected(self, event):
        """Stream or download the selected track based on user preference"""
        selection = self.search_results.curselection()
        if not selection:
            return
            
        selected_item = self.search_results.get(selection[0])
        url = selected_item.split(" | ")[1].strip()
        
        # Ask user whether to stream or download
        response = messagebox.askyesno(
            "Playback Option",
            "Would you like to stream this track?\n(Click 'No' to download instead)"
        )
        
        if response:
            self.youtube_var.set(url)
            self.stream_youtube()
        else:
            self.youtube_var.set(url)
            self.download_youtube()    



    def handle_result_click(self, event):
        """Handle clicks on the result listbox"""
        if not hasattr(self.result, 'key') or self.result.key is None:
            return
            
        # Create button frame if it doesn't exist
        if not hasattr(self, 'rating_button_frame'):
            self.rating_button_frame = ttk.Frame(self.root)
            self.rating_button_frame.grid(row=4, column=0, columnspan=2, pady=5)
            
            ttk.Button(
                self.rating_button_frame,
                text="Update Rating",
                command=self.show_rating_dialog,
                style='Custom.TButton'
            ).pack(padx=5)



    def show_rating_dialog(self):
            """Show dialog to update rating"""
            if not hasattr(self.result, 'key') or self.result.key is None:
                return
                
            RatingDialog(
                parent=self.root,
                library=self.library,
                track_key=self.result.key,
                callback=self.getlocallib
            )

    def end_seek(self, event):
        if self.current_song_index >= 0 and self.is_dragging:
            self.is_dragging = False
            song = self.playlist[self.current_song_index]
            
            if song.source == "stream":
                self.youtube_streamer.seek(self.seek_position)
            else:
                was_playing = self.player.is_playing and not self.player.is_paused
                pygame.mixer.music.play(start=self.seek_position)
                if not was_playing:
                    pygame.mixer.music.pause()
                self.start_time = time.time() - self.seek_position  # Update start time based on seek position
                if not was_playing:
                    pygame.mixer.music.pause()
                self.start_time = time.time() - self.seek_position  # Update start time based on seek position
            
    def seek_relative(self, seconds):
        """Modified seek method to handle both local files and streams"""
        current_song = self.playlist[self.current_song_index] if self.current_song_index >= 0 else None
        
        if current_song:
            if current_song.source == "stream":
                current_position = self.youtube_streamer.get_position()
                new_position = max(0, current_position + seconds)
                self.youtube_streamer.seek(new_position)
            else:
                # Existing local file seeking logic
                current_time = time.time() - self.start_time
                song = self.playlist[self.current_song_index]
                new_position = max(0, min(song.duration, current_time + seconds))
                was_playing = self.player.is_playing and not self.player.is_paused
                pygame.mixer.music.play(start=new_position)
                if not was_playing:
                    pygame.mixer.music.pause()
                self.start_time = time.time() - new_position
                self.seek_position = new_position

    def on_closing(self):
        """Clean up resources before closing"""
        self.stop()  # Stop any playback
        if self.youtube_streamer:
            self.youtube_streamer.stop()
        self.root.destroy()            

def main():
    root = tk.Tk()
    app = JukeboxGUI(root)
    root.mainloop()

def set_text(listbox, content):
    listbox.delete(0, tk.END)
    if isinstance(content, list):
        for item in content:
            listbox.insert(tk.END, item)
    else:
        listbox.insert(tk.END, content)

if __name__ == "__main__":
    main()