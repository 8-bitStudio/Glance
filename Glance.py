import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import math

# =============================================================================
#  THEME CONFIGURATIONS
# =============================================================================
THEMES = {
    "Dark": {
        "bg_main": "#1e1e1e",
        "bg_panel": "#252526",
        "fg_main": "#d4d4d4",
        "accent": "#007acc",
        "highlight": "#ff4444",
        "input_bg": "#2d2d2d",
        "input_fg": "#ccc",
        "guide_lines": "#333333"
    },
    "Light": {
        "bg_main": "#f0f0f0",
        "bg_panel": "#e0e0e0",
        "fg_main": "#222222",
        "accent": "#0066cc",
        "highlight": "#d80000",
        "input_bg": "#ffffff",
        "input_fg": "#222222",
        "guide_lines": "#cccccc"
    }
}

class GlanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Glance")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # --- Settings State ---
        self.current_theme_name = "Dark"
        self.colors = THEMES["Dark"]
        self.font_family = "Courier New"
        self.font_size = 60
        self.settings_window = None  # Track the settings window instance
        
        # --- App State ---
        self.words = []
        self.current_index = 0
        self.is_running = False
        self.has_content = False

        # --- Build UI ---
        # We keep references to frames so we can update their colors later
        self.frames = {}
        self.labels = {}
        self.buttons = {}
        
        self._build_header()
        self._build_display_area()
        self._build_controls()
        self._build_input_area()
        self._build_status_bar()

        # Apply initial theme
        self.apply_theme(self.current_theme_name)

        # --- Bindings ---
        self.root.bind('<space>', lambda e: self.toggle_reading())
        self.root.bind('<Left>', lambda e: self.scrub_backward())
        self.root.bind('<Right>', lambda e: self.scrub_forward())
        
        # Auto-update word count/eta when typing in text box
        self.text_input.bind('<KeyRelease>', lambda e: self.prepare_words())

    # =========================================================================
    #  UI BUILDERS
    # =========================================================================
    def _build_header(self):
        self.frames['header'] = tk.Frame(self.root, height=50)
        self.frames['header'].pack(fill=tk.X, side=tk.TOP)
        self.frames['header'].pack_propagate(False)

        # Title
        self.labels['title'] = tk.Label(
            self.frames['header'], 
            text="GLANCE", 
            font=("Segoe UI", 16, "bold", "italic")
        )
        self.labels['title'].pack(side=tk.LEFT, padx=20)

        # Settings Button
        self.btn_settings = tk.Button(
            self.frames['header'],
            text="⚙ Settings",
            command=self.open_settings,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10)
        )
        self.btn_settings.pack(side=tk.RIGHT, padx=15)

    def _build_display_area(self):
        self.frames['display'] = tk.Frame(self.root)
        self.frames['display'].pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.canvas = tk.Canvas(self.frames['display'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._draw_guides)

    def _build_controls(self):
        self.frames['controls'] = tk.Frame(self.root, pady=15)
        self.frames['controls'].pack(fill=tk.X)

        # Controls Inner Row
        top_row = tk.Frame(self.frames['controls'])
        top_row.pack(fill=tk.X, padx=20)
        self.frames['controls_inner'] = top_row # Store for theming

        # Start Button
        self.btn_toggle = tk.Button(
            top_row, 
            text="START READING", 
            command=self.toggle_reading,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            padx=20, pady=5,
            cursor="hand2"
        )
        self.btn_toggle.pack(side=tk.LEFT)

        # Slider Section
        wpm_container = tk.Frame(top_row)
        wpm_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=30)
        self.frames['wpm_box'] = wpm_container

        self.labels['wpm'] = tk.Label(wpm_container, text="Speed (WPM)")
        self.labels['wpm'].pack(anchor="w")

        self.wpm_var = tk.IntVar(value=350)
        self.wpm_scale = tk.Scale(
            wpm_container, 
            from_=100, to=1000, 
            orient=tk.HORIZONTAL, 
            variable=self.wpm_var,
            highlightthickness=0,
            showvalue=True,
            command=self.on_wpm_change # Bind change to status update
        )
        self.wpm_scale.pack(fill=tk.X)

        # Reset
        self.btn_reset = tk.Button(
            top_row, 
            text="↺ Reset", 
            command=self.reset_reader,
            relief=tk.FLAT,
            padx=10
        )
        self.btn_reset.pack(side=tk.RIGHT)

        # Progress Bar
        self.frames['progress'] = tk.Frame(self.frames['controls'])
        self.frames['progress'].pack(fill=tk.X, padx=20, pady=(15, 0))
        
        self.progress_canvas = tk.Canvas(self.frames['progress'], height=6, highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X)
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 6, width=0)

    def _build_input_area(self):
        self.frames['input'] = tk.Frame(self.root, pady=20)
        self.frames['input'].pack(fill=tk.BOTH, expand=False, padx=20)

        # Header with Load Button
        header = tk.Frame(self.frames['input'])
        header.pack(fill=tk.X, pady=(0, 5))
        self.frames['input_header'] = header

        self.labels['content_src'] = tk.Label(header, text="Content Source", font=("Segoe UI", 10, "bold"))
        self.labels['content_src'].pack(side=tk.LEFT)

        self.btn_load = tk.Button(
            header, 
            text="📂 Load Text File", 
            command=self.load_text_file,
            relief=tk.FLAT,
            font=("Segoe UI", 9)
        )
        self.btn_load.pack(side=tk.RIGHT)

        # Text Box
        self.text_input = tk.Text(
            self.frames['input'], 
            height=6, 
            relief=tk.FLAT,
            font=("Consolas", 10),
            padx=10, pady=10
        )
        self.text_input.pack(fill=tk.X)
        
        intro_text = "Welcome to Glance.\nPaste your text here or load a file to begin."
        self.text_input.insert("1.0", intro_text)

    def _build_status_bar(self):
        self.status_bar = tk.Label(
            self.root, 
            text="Ready | 0 words loaded", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            font=("Segoe UI", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # =========================================================================
    #  SETTINGS & THEMING
    # =========================================================================

    def open_settings(self):
        # Check if settings window already exists and is open
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        # Create a popup window (Toplevel)
        sw = tk.Toplevel(self.root)
        self.settings_window = sw  # Store reference
        sw.title("Settings")
        sw.geometry("400x450") # Made taller for font size
        sw.resizable(False, False)
        sw.configure(bg=self.colors["bg_panel"])

        # Title
        tk.Label(sw, text="Appearance", font=("Segoe UI", 12, "bold"), 
                 bg=self.colors["bg_panel"], fg=self.colors["fg_main"]).pack(anchor="w", padx=20, pady=(20, 10))

        # --- Theme Selection ---
        tk.Label(sw, text="Theme Mode", bg=self.colors["bg_panel"], fg=self.colors["fg_main"]).pack(anchor="w", padx=20)
        
        theme_var = tk.StringVar(value=self.current_theme_name)
        
        def on_theme_change():
            self.apply_theme(theme_var.get())
            # Refresh popup colors instantly too
            sw.configure(bg=self.colors["bg_panel"])

        modes_frame = tk.Frame(sw, bg=self.colors["bg_panel"])
        modes_frame.pack(anchor="w", padx=20, pady=5)

        for mode in ["Dark", "Light", "System"]:
            rb = tk.Radiobutton(
                modes_frame, text=mode, variable=theme_var, value=mode,
                command=on_theme_change,
                bg=self.colors["bg_panel"], fg=self.colors["fg_main"],
                selectcolor=self.colors["bg_panel"],
                activebackground=self.colors["bg_panel"],
                activeforeground=self.colors["fg_main"]
            )
            rb.pack(side=tk.LEFT, padx=5)

        # --- Font Selection ---
        tk.Label(sw, text="Reader Font", font=("Segoe UI", 12, "bold"), 
                 bg=self.colors["bg_panel"], fg=self.colors["fg_main"]).pack(anchor="w", padx=20, pady=(20, 10))

        font_frame = tk.Frame(sw, bg=self.colors["bg_panel"])
        font_frame.pack(fill=tk.X, padx=20)

        # Get list of fonts
        available_fonts = sorted(font.families())
        
        self.font_combo = ttk.Combobox(font_frame, values=available_fonts, state="readonly")
        self.font_combo.set(self.font_family)
        self.font_combo.pack(fill=tk.X)
        
        def on_font_change(event):
            self.font_family = self.font_combo.get()
            # Redraw if paused to show preview
            if self.words and not self.is_running and self.current_index < len(self.words):
                self.draw_word_on_canvas(self.words[self.current_index])
            # Also redraw completed text if visible
            elif self.words and not self.is_running and self.current_index >= len(self.words):
                 self._draw_guides()

        self.font_combo.bind("<<ComboboxSelected>>", on_font_change)

        # --- Font Size Selection ---
        tk.Label(sw, text="Font Size", font=("Segoe UI", 12, "bold"), 
                 bg=self.colors["bg_panel"], fg=self.colors["fg_main"]).pack(anchor="w", padx=20, pady=(20, 10))
        
        size_scale = tk.Scale(
            sw, from_=20, to=300, orient=tk.HORIZONTAL, # Increased max to 300
            bg=self.colors["bg_panel"], fg=self.colors["fg_main"],
            highlightthickness=0, troughcolor=self.colors["bg_main"],
            activebackground=self.colors["accent"]
        )
        size_scale.set(self.font_size)
        size_scale.pack(fill=tk.X, padx=20)
        
        def on_size_change(val):
            self.font_size = int(val)
            # Redraw immediately to see changes
            if self.words and not self.is_running:
                 if self.current_index < len(self.words):
                     self.draw_word_on_canvas(self.words[self.current_index])
                 else:
                     self._draw_guides() # Redraws "COMPLETED" with new size

        size_scale.config(command=on_size_change)

        # Close Button
        tk.Button(sw, text="Done", command=sw.destroy, bg=self.colors["accent"], fg="white", relief=tk.FLAT).pack(pady=30)

    def apply_theme(self, theme_name):
        if theme_name == "System":
            theme_name = "Dark" 
        
        self.current_theme_name = theme_name
        c = THEMES[theme_name]
        self.colors = c

        # Apply to Root
        self.root.configure(bg=c["bg_main"])

        # Apply to Frames
        for key, frame in self.frames.items():
            if 'header' in key or 'controls' in key:
                bg = c["bg_panel"]
            elif 'wpm' in key:
                bg = c["bg_panel"]
            elif 'input' in key:
                bg = c["bg_main"]
            else:
                bg = c["bg_main"]
            frame.configure(bg=bg)

        # Apply to Labels
        for lbl in self.labels.values():
            lbl.configure(bg=lbl.master.cget('bg'), fg=c["fg_main"])
            if lbl == self.labels['title']:
                lbl.configure(fg=c["accent"])

        # Apply to Canvases
        self.canvas.configure(bg=c["bg_main"])
        self._draw_guides() 
        self.progress_canvas.configure(bg=c["guide_lines"])
        self.progress_canvas.itemconfig(self.progress_rect, fill=c["accent"])

        # Apply to Text Inputs
        self.text_input.configure(bg=c["input_bg"], fg=c["input_fg"], insertbackground=c["fg_main"])

        # Apply to Buttons
        self.btn_settings.configure(bg=c["bg_panel"], fg=c["fg_main"], activebackground=c["bg_main"])
        self.btn_toggle.configure(bg=c["accent"], fg="white")
        self.btn_reset.configure(bg="#666" if theme_name == "Dark" else "#ccc", fg="white" if theme_name == "Dark" else "black")
        self.btn_load.configure(bg="#444" if theme_name == "Dark" else "#ddd", fg="white" if theme_name == "Dark" else "black")
        
        # Apply to Scales
        self.wpm_scale.configure(bg=c["bg_panel"], fg=c["fg_main"], troughcolor=c["bg_main"], activebackground=c["accent"])
        
        # Apply to Status Bar
        self.status_bar.configure(bg="#111" if theme_name=="Dark" else "#ddd", fg="#888" if theme_name=="Dark" else "#333")

        # Redraw current word
        if self.words and self.current_index < len(self.words):
            self.draw_word_on_canvas(self.words[self.current_index])

    # =========================================================================
    #  LOGIC (Standard ProFlow Logic)
    # =========================================================================

    def _draw_guides(self, event=None):
        """Draws guides AND handles recentering text on resize"""
        self.canvas.delete("guides")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        col = self.colors["guide_lines"]
        
        # Crosshair notches
        self.canvas.create_line(cx, cy - 60, cx, cy - 80, fill=col, width=2, tags="guides")
        self.canvas.create_line(cx, cy + 60, cx, cy + 80, fill=col, width=2, tags="guides")

        # FIX: Redraw text if visible so it stays centered when resizing
        if not self.is_running:
            if self.words and self.current_index < len(self.words):
                 self.draw_word_on_canvas(self.words[self.current_index])
            elif self.current_index >= len(self.words) and self.words:
                 # Re-center "COMPLETED" text and use current font size
                 self.canvas.delete("text")
                 self.canvas.create_text(
                    cx, cy, 
                    text="COMPLETED", 
                    fill=self.colors["accent"], 
                    font=(self.font_family, self.font_size, "bold"),
                    tags="text"
                )

    def load_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_input.delete("1.0", tk.END)
                    self.text_input.insert("1.0", content)
                    self.prepare_words() # Trigger update immediately
                    self.status_bar.config(text="File loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file:\n{e}")

    def on_wpm_change(self, _):
        """Called when slider moves"""
        # If running, the progress update handles the status bar
        # If not running, we should show the new Total Time
        if not self.is_running:
            self.update_status_with_eta()

    def update_status_with_eta(self):
        """Displays Total Word Count and Estimated Total Time"""
        if not self.words:
            self.status_bar.config(text="Ready | 0 words loaded")
            return
            
        count = len(self.words)
        wpm = self.wpm_var.get()
        if wpm <= 0: wpm = 1 # Safety
        
        total_minutes = count / wpm
        m = int(total_minutes)
        s = int((total_minutes % 1) * 60)
        
        self.status_bar.config(text=f"Ready | {count} words | Total Time: {m}m {s}s")

    def prepare_words(self):
        raw_text = self.text_input.get("1.0", tk.END)
        self.words = raw_text.split()
        if len(self.words) > 0:
            self.has_content = True
            # Only update status if not currently reading to avoid flickering
            if not self.is_running:
                self.update_status_with_eta()
            return True
        return False

    def get_orp_index(self, word):
        length = len(word)
        if length == 1: return 0
        if length >= 2 and length <= 5: return 1
        if length >= 6 and length <= 9: return 2
        if length >= 10 and length <= 13: return 3
        return 4 

    def draw_word_on_canvas(self, word):
        self.canvas.delete("text")
        if not word: return

        orp_idx = self.get_orp_index(word)
        left_part = word[:orp_idx]
        center_char = word[orp_idx]
        right_part = word[orp_idx+1:]

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        
        # Use dynamic fonts
        font_spec_main = (self.font_family, self.font_size, "bold")

        # Draw Center Char
        self.canvas.create_text(
            cx, cy, 
            text=center_char, 
            fill=self.colors["highlight"], 
            font=font_spec_main, 
            tags="text",
            anchor="center" 
        )

        # Measure center char to offset others
        temp_font = font.Font(family=self.font_family, size=self.font_size, weight="bold")
        center_width = temp_font.measure(center_char)

        self.canvas.create_text(
            cx - (center_width / 2), cy, 
            text=left_part, 
            fill=self.colors["fg_main"], 
            font=font_spec_main, 
            tags="text", 
            anchor="e"
        )

        self.canvas.create_text(
            cx + (center_width / 2), cy, 
            text=right_part, 
            fill=self.colors["fg_main"], 
            font=font_spec_main, 
            tags="text", 
            anchor="w"
        )

    def toggle_reading(self):
        if self.is_running:
            self.is_running = False
            self.btn_toggle.config(text="RESUME", bg=self.colors["accent"])
        else:
            if not self.has_content:
                if not self.prepare_words(): return
            
            # FIX: If we finished reading (index at end), reset to start automatically
            if self.current_index >= len(self.words):
                self.current_index = 0
            
            self.is_running = True
            self.btn_toggle.config(text="PAUSE", bg=self.colors["highlight"])
            self.run_loop()

    def reset_reader(self):
        self.is_running = False
        self.current_index = 0
        self.btn_toggle.config(text="START READING", bg=self.colors["accent"])
        self.canvas.delete("text")
        self.update_progress()
        self.update_status_with_eta() # Show total time again

    def scrub_forward(self):
        if self.words:
            self.current_index = min(len(self.words) - 1, self.current_index + 10)
            self.draw_word_on_canvas(self.words[self.current_index])
            self.update_progress()

    def scrub_backward(self):
        if self.words:
            self.current_index = max(0, self.current_index - 10)
            self.draw_word_on_canvas(self.words[self.current_index])
            self.update_progress()

    def update_progress(self):
        if not self.words: return
        pct = self.current_index / len(self.words)
        canvas_width = self.progress_canvas.winfo_width()
        self.progress_canvas.coords(self.progress_rect, 0, 0, canvas_width * pct, 6)
        
        # Stats
        wpm = self.wpm_var.get()
        words_left = len(self.words) - self.current_index
        minutes_left = words_left / wpm
        time_str = f"{int(minutes_left)}m {int((minutes_left % 1) * 60)}s"
        self.status_bar.config(text=f"Progress: {self.current_index}/{len(self.words)} | Remaining: {time_str}")

    def calculate_delay(self, word):
        base_wpm = self.wpm_var.get()
        base_delay = (60 / base_wpm) * 1000
        factor = 1.0
        if ',' in word or ';' in word: factor = 1.5
        elif '.' in word or '!' in word or '?' in word: factor = 2.0
        elif len(word) > 8: factor = 1.3
        return int(base_delay * factor)

    def run_loop(self):
        if not self.is_running: return

        if self.current_index < len(self.words):
            word = self.words[self.current_index]
            self.draw_word_on_canvas(word)
            self.update_progress()
            self.current_index += 1
            delay = self.calculate_delay(word)
            self.root.after(delay, self.run_loop)
        else:
            self.is_running = False
            self.btn_toggle.config(text="READ AGAIN", bg=self.colors["accent"])
            self.canvas.delete("text") # Ensure clear
            self.canvas.create_text(
                self.canvas.winfo_width()//2, 
                self.canvas.winfo_height()//2, 
                text="COMPLETED", 
                fill=self.colors["accent"], 
                font=(self.font_family, self.font_size, "bold"),
                tags="text" # FIX: Add tag so it gets deleted next time
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = GlanceApp(root)
    root.mainloop()
