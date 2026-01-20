import tkinter as tk
from tkinter import filedialog, messagebox, font
import math

# =============================================================================
#  CONFIGURATION & CONSTANTS
# =============================================================================
# Colors for the Dark Mode UI
COLOR_BG_MAIN = "#1e1e1e"        # Dark Grey Background
COLOR_BG_PANEL = "#252526"       # Slightly lighter for panels
COLOR_TEXT_MAIN = "#d4d4d4"      # Off-white text
COLOR_ACCENT = "#007acc"         # Blue accent for buttons/bars
COLOR_HIGHLIGHT = "#ff4444"      # The "Red Letter" color
COLOR_BUTTON_TEXT = "#ffffff"

# Default Settings
DEFAULT_WPM = 350
DEFAULT_FONT_SIZE = 60
DEFAULT_FONT_FAMILY = "Courier New" # Monospace fonts align better, but we handle variable width too

class ModernSpeedReader:
    def __init__(self, root):
        self.root = root
        self.root.title("ProFlow Speed Reader")
        self.root.geometry("900x700")
        self.root.configure(bg=COLOR_BG_MAIN)
        self.root.minsize(800, 600)

        # --- State Variables ---
        self.words = []
        self.current_index = 0
        self.is_running = False
        self.has_content = False
        
        # --- UI Construction ---
        self._build_header()
        self._build_display_area()
        self._build_controls()
        self._build_input_area()
        self._build_status_bar()

        # --- Bindings ---
        # Allow spacebar to toggle play/pause
        self.root.bind('<space>', lambda e: self.toggle_reading())
        # Allow Left/Right arrows to scrub
        self.root.bind('<Left>', lambda e: self.scrub_backward())
        self.root.bind('<Right>', lambda e: self.scrub_forward())

    def _build_header(self):
        """Builds the top title bar."""
        header_frame = tk.Frame(self.root, bg=COLOR_BG_PANEL, height=50)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False) # Force height

        title = tk.Label(
            header_frame, 
            text="PROFLOW READER", 
            fg=COLOR_ACCENT, 
            bg=COLOR_BG_PANEL, 
            font=("Segoe UI", 14, "bold", "italic")
        )
        title.pack(side=tk.LEFT, padx=20)

    def _build_display_area(self):
        """
        The main visual area. We use a Canvas to draw the text manually.
        This allows us to split the word into three parts: 
        [Left Part] [Red Center Letter] [Right Part]
        """
        self.display_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN)
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # The canvas where the word "floats"
        self.canvas = tk.Canvas(
            self.display_frame, 
            bg=COLOR_BG_MAIN, 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Draw guides (the subtle lines focusing your eye)
        self.canvas.bind("<Configure>", self._draw_guides)

    def _draw_guides(self, event=None):
        """Draws the crosshair/focus lines on the canvas."""
        self.canvas.delete("guides")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        center_x = w // 2
        center_y = h // 2

        # Top and Bottom notch marks to guide the eye
        self.canvas.create_line(center_x, center_y - 60, center_x, center_y - 80, fill="#333333", width=2, tags="guides")
        self.canvas.create_line(center_x, center_y + 60, center_x, center_y + 80, fill="#333333", width=2, tags="guides")

    def _build_controls(self):
        """The control panel (Play, WPM slider, Progress)."""
        control_panel = tk.Frame(self.root, bg=COLOR_BG_PANEL, pady=15)
        control_panel.pack(fill=tk.X, padx=0)

        # -- Top Row of Controls: Slider & Buttons --
        top_row = tk.Frame(control_panel, bg=COLOR_BG_PANEL)
        top_row.pack(fill=tk.X, padx=20)

        # Play/Pause Button
        self.btn_toggle = tk.Button(
            top_row, 
            text="START READING", 
            command=self.toggle_reading,
            bg=COLOR_ACCENT, 
            fg="white", 
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.btn_toggle.pack(side=tk.LEFT)

        # WPM Slider
        wpm_container = tk.Frame(top_row, bg=COLOR_BG_PANEL)
        wpm_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=30)
        
        tk.Label(wpm_container, text="Speed (WPM)", bg=COLOR_BG_PANEL, fg="#888").pack(anchor="w")
        self.wpm_var = tk.IntVar(value=DEFAULT_WPM)
        self.wpm_scale = tk.Scale(
            wpm_container, 
            from_=100, 
            to=1000, 
            orient=tk.HORIZONTAL, 
            variable=self.wpm_var,
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_MAIN,
            highlightthickness=0,
            troughcolor="#333",
            activebackground=COLOR_ACCENT
        )
        self.wpm_scale.pack(fill=tk.X)

        # Reset Button
        tk.Button(
            top_row, 
            text="↺ Reset", 
            command=self.reset_reader,
            bg="#444", 
            fg="white", 
            relief=tk.FLAT,
            padx=10
        ).pack(side=tk.RIGHT)

        # -- Bottom Row of Controls: Progress Bar --
        self.progress_frame = tk.Frame(control_panel, bg=COLOR_BG_PANEL)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=(15, 0))

        # We use a canvas for a custom progress bar that looks nicer than default
        self.progress_canvas = tk.Canvas(self.progress_frame, height=6, bg="#333", highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X)
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 6, fill=COLOR_ACCENT, width=0)

    def _build_input_area(self):
        """The text box area where users paste content."""
        self.input_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN, pady=20)
        self.input_frame.pack(fill=tk.BOTH, expand=False, padx=20)

        # Label + Load File Button
        header = tk.Frame(self.input_frame, bg=COLOR_BG_MAIN)
        header.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(header, text="Content Source", fg="#888", bg=COLOR_BG_MAIN, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        load_btn = tk.Button(
            header, 
            text="📂 Load Text File", 
            command=self.load_text_file,
            bg="#333", 
            fg="white", 
            relief=tk.FLAT,
            font=("Segoe UI", 9)
        )
        load_btn.pack(side=tk.RIGHT)

        # Text Area
        self.text_input = tk.Text(
            self.input_frame, 
            height=6, 
            bg="#2d2d2d", 
            fg="#ccc", 
            insertbackground="white", # Cursor color
            relief=tk.FLAT,
            font=("Consolas", 10),
            padx=10, pady=10
        )
        self.text_input.pack(fill=tk.X)
        
        intro_text = (
            "Welcome to ProFlow.\n"
            "1. Paste your article, book chapter, or study notes here.\n"
            "2. Or click 'Load Text File' to open a .txt document.\n"
            "3. Adjust your WPM speed above and hit START.\n"
            "   (Tip: Use Spacebar to Play/Pause)"
        )
        self.text_input.insert("1.0", intro_text)

    def _build_status_bar(self):
        self.status_bar = tk.Label(
            self.root, 
            text="Ready | 0 words loaded", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            bg="#111", 
            fg="#666",
            font=("Segoe UI", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # =========================================================================
    #  LOGIC & PROCESSING
    # =========================================================================

    def load_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_input.delete("1.0", tk.END)
                    self.text_input.insert("1.0", content)
                    messagebox.showinfo("Success", "File loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file:\n{e}")

    def prepare_words(self):
        """Takes text from input, cleans it, and prepares the list."""
        raw_text = self.text_input.get("1.0", tk.END)
        # Simple splitting, but you could add logic here to split hyphens, etc.
        self.words = raw_text.split()
        if len(self.words) > 0:
            self.has_content = True
            self.status_bar.config(text=f"Ready | {len(self.words)} words loaded")
            return True
        return False

    def get_orp_index(self, word):
        """
        Calculates the 'Optical Recognition Point' (ORP).
        The eye focuses best slightly to the left of the center.
        """
        length = len(word)
        if length == 1: return 0
        if length >= 2 and length <= 5: return 1
        if length >= 6 and length <= 9: return 2
        if length >= 10 and length <= 13: return 3
        return 4 # Very long words

    def draw_word_on_canvas(self, word):
        """
        Draws the word on the canvas with the ORP letter centered and red.
        """
        self.canvas.delete("text") # Clear previous word

        if not word: return

        # 1. Find the pivot character
        orp_idx = self.get_orp_index(word)
        
        left_part = word[:orp_idx]
        center_char = word[orp_idx]
        right_part = word[orp_idx+1:]

        # 2. Geometry
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        
        font_spec = (DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE, "bold")

        # 3. Draw Center Character (The Anchor)
        # We draw this EXACTLY in the center of the screen
        self.canvas.create_text(
            cx, cy, 
            text=center_char, 
            fill=COLOR_HIGHLIGHT, 
            font=font_spec, 
            tags="text",
            anchor="center" 
        )

        # 4. Measure the center char width so we know where to put the others
        # We need a temporary font measurement
        temp_font = font.Font(family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE, weight="bold")
        center_width = temp_font.measure(center_char)

        # 5. Draw Left Part (Anchored East so it ends at the center char)
        # Offset to the left by half the center char's width
        self.canvas.create_text(
            cx - (center_width / 2), cy, 
            text=left_part, 
            fill=COLOR_TEXT_MAIN, 
            font=font_spec, 
            tags="text", 
            anchor="e" # East anchor
        )

        # 6. Draw Right Part (Anchored West so it starts after center char)
        self.canvas.create_text(
            cx + (center_width / 2), cy, 
            text=right_part, 
            fill=COLOR_TEXT_MAIN, 
            font=font_spec, 
            tags="text", 
            anchor="w" # West anchor
        )

    # =========================================================================
    #  PLAYBACK LOOP
    # =========================================================================

    def toggle_reading(self):
        if self.is_running:
            # Pause
            self.is_running = False
            self.btn_toggle.config(text="RESUME", bg=COLOR_ACCENT)
        else:
            # Start
            if not self.has_content:
                success = self.prepare_words()
                if not success: return
            
            self.is_running = True
            self.btn_toggle.config(text="PAUSE", bg="#e04f4f") # Red for pause
            self.run_loop()

    def reset_reader(self):
        self.is_running = False
        self.current_index = 0
        self.btn_toggle.config(text="START READING", bg=COLOR_ACCENT)
        self.canvas.delete("text")
        self.update_progress()
        self.status_bar.config(text=f"Reset | {len(self.words)} words loaded")

    def scrub_forward(self):
        """Skip ahead 10 words"""
        if self.words:
            self.current_index = min(len(self.words) - 1, self.current_index + 10)
            self.draw_word_on_canvas(self.words[self.current_index])
            self.update_progress()

    def scrub_backward(self):
        """Go back 10 words"""
        if self.words:
            self.current_index = max(0, self.current_index - 10)
            self.draw_word_on_canvas(self.words[self.current_index])
            self.update_progress()

    def update_progress(self):
        """Updates the progress bar and status text."""
        if not self.words: return
        
        # Bar
        pct = self.current_index / len(self.words)
        canvas_width = self.progress_canvas.winfo_width()
        self.progress_canvas.coords(self.progress_rect, 0, 0, canvas_width * pct, 6)

        # Text
        wpm = self.wpm_var.get()
        words_left = len(self.words) - self.current_index
        minutes_left = words_left / wpm
        time_str = f"{int(minutes_left)}m {int((minutes_left % 1) * 60)}s"
        
        self.status_bar.config(
            text=f"Progress: {self.current_index}/{len(self.words)} | Time Remaining: {time_str}"
        )

    def calculate_dynamic_delay(self, word):
        """
        Adjusts speed based on word difficulty.
        Long words or punctuation = slower.
        """
        base_wpm = self.wpm_var.get()
        # Base ms per word: (60 / WPM) * 1000
        base_delay = (60 / base_wpm) * 1000
        
        factor = 1.0

        # Slow down for punctuation
        if ',' in word or ';' in word:
            factor = 1.5
        elif '.' in word or '!' in word or '?' in word:
            factor = 2.0
        # Slow down slightly for long words
        elif len(word) > 8:
            factor = 1.3
        
        return int(base_delay * factor)

    def run_loop(self):
        if not self.is_running: return

        if self.current_index < len(self.words):
            word = self.words[self.current_index]
            
            # Draw
            self.draw_word_on_canvas(word)
            self.update_progress()
            
            # Increment
            self.current_index += 1
            
            # Schedule next
            delay = self.calculate_dynamic_delay(word)
            self.root.after(delay, self.run_loop)
        else:
            # Done
            self.is_running = False
            self.btn_toggle.config(text="READ AGAIN", bg="#4CAF50")
            self.canvas.delete("text")
            self.canvas.create_text(
                self.canvas.winfo_width()//2, 
                self.canvas.winfo_height()//2, 
                text="COMPLETED", 
                fill=COLOR_ACCENT, 
                font=("Segoe UI", 40, "bold")
            )

# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Create the root window
    root = tk.Tk()
    
    # Initialize the application
    app = ModernSpeedReader(root)
    
    # Start the event loop
    root.mainloop()