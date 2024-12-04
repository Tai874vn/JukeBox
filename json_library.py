import json
import os

class JsonLibrary:
    def __init__(self, json_file="library_data.json"):
        self.json_file = json_file
        self.library = self._load_library()

    def _load_library(self):
        """Load library from JSON file"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading library: {e}")
            return {}

    def _save_library(self):
        """Save library to JSON file"""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.library, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving library: {e}")
            return False

    def get_name(self, key):
        """Get track name by key"""
        try:
            return self.library[key]['name']
        except KeyError:
            return None

    def get_artist(self, key):
        """Get artist by key"""
        try:
            return self.library[key]['artist']
        except KeyError:
            return None

    def get_rating(self, key):
        """Get rating by key"""
        try:
            return self.library[key]['rating']
        except KeyError:
            return -1

    def get_play_count(self, key):
        """Get play count by key"""
        try:
            return self.library[key]['play_count']
        except KeyError:
            return -1

    def get_file_path(self, key):
        """Get file path by key"""
        try:
            return self.library[key]['file_path']
        except KeyError:
            return None

    def increment_play_count(self, key):
        """Increment play count for a track"""
        try:
            self.library[key]['play_count'] += 1
            return self._save_library()
        except KeyError:
            return False
            
    def update_rating(self, key, rating):
        """Update rating for a track"""
        try:
            if key in self.library:
                self.library[key]['rating'] = rating
                return self._save_library()
            return False
        except Exception as e:
            print(f"Error updating rating: {e}")
            return False