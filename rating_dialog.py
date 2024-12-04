import tkinter as tk
from tkinter import ttk, messagebox

class RatingDialog:
    def __init__(self, parent, library, track_key, callback):
        """
        Initialize Rating Dialog
        
        Args:
            parent: Parent window (Tkinter root or Toplevel)
            library: JsonLibrary instance
            track_key: Key of the track being rated
            callback: Function to call after successful rating update
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update Rating")
        self.dialog.geometry("300x200")  # Made slightly taller for better spacing
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Store references
        self.library = library
        self.track_key = track_key
        self.callback = callback
        
        # Center the dialog relative to parent
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 150,
            parent.winfo_rooty() + parent.winfo_height()//2 - 100
        ))
        
        self._create_widgets()
        self._setup_bindings()
        
    def _create_widgets(self):
        """Create and setup all dialog widgets"""
        # Title label
        track_name = self.library.get_name(self.track_key)
        current_rating = self.library.get_rating(self.track_key)
        
        title_text = f"Rate: {track_name}\nCurrent Rating: {current_rating}"
        ttk.Label(
            self.dialog,
            text=title_text,
            font=('Helvetica', 10),
            justify='center'
        ).pack(pady=10)
        
        # Star rating frame
        star_frame = ttk.Frame(self.dialog)
        star_frame.pack(pady=10)
        self.star_labels = []
        for i in range(5):
            label = ttk.Label(
                star_frame,
                text="★",
                font=('Helvetica', 16),
                cursor='hand2'
            )
            label.pack(side=tk.LEFT, padx=4)
            label.bind('<Button-1>', lambda e, rating=i+1: self.set_rating(rating))
            self.star_labels.append(label)
        
        # Rating entry frame
        entry_frame = ttk.Frame(self.dialog)
        entry_frame.pack(pady=10)
        
        ttk.Label(
            entry_frame,
            text="Or enter rating (1-5):",
            font=('Helvetica', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.rating_var = tk.StringVar()
        self.entry = ttk.Entry(
            entry_frame,
            textvariable=self.rating_var,
            width=5,
            justify='center'
        )
        self.entry.pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=15)
        
        ttk.Button(
            button_frame,
            text="Update",
            command=self.validate_and_update,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            style='Custom.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        # Update initial star display
        if current_rating > 0:
            self.update_star_display(current_rating)
            self.rating_var.set(str(current_rating))
    
    def update_star_display(self, rating):
        """Update the visual star display"""
        for i, label in enumerate(self.star_labels):
            if i < rating:
                label.configure(foreground='gold')
            else:
                label.configure(foreground='gray')
    
    def set_rating(self, rating):
        """Set rating from star click"""
        self.rating_var.set(str(rating))
        self.update_star_display(rating)
    
    def _setup_bindings(self):
        """Setup keyboard bindings"""
        self.entry.focus_set()
        self.entry.bind('<Return>', lambda e: self.validate_and_update())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        self.rating_var.trace_add('write', lambda *args: self.handle_rating_input())
    
    def handle_rating_input(self):
        """Handle rating input changes"""
        try:
            rating = int(self.rating_var.get())
            if 1 <= rating <= 5:
                self.update_star_display(rating)
        except ValueError:
            pass
    
    def validate_and_update(self):
        """Validate input and update rating"""
        try:
            new_rating = int(self.rating_var.get())
            if 1 <= new_rating <= 5:
                if self.library.update_rating(self.track_key, new_rating):
                    self.callback()  # Refresh display
                    self.dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update rating")
            else:
                messagebox.showerror("Error", "Rating must be between 1 and 5")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")