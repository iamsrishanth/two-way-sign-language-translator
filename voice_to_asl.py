"""
Voice to American Sign Language (ASL) Translator
Converts spoken words to ASL fingerspelling images using locally generated signs.
"""

import speech_recognition as sr
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading


class ASLImageGenerator:
    """Generates ASL hand sign images locally"""
    
    # ASL hand sign descriptions for each letter
    ASL_DESCRIPTIONS = {
        'a': "Fist with thumb beside",
        'b': "Flat hand, thumb tucked",
        'c': "Curved hand, C-shape",
        'd': "Index up, others touch thumb",
        'e': "Fingers bent, thumb tucked",
        'f': "OK sign, 3 fingers up",
        'g': "Point sideways",
        'h': "Point sideways, 2 fingers",
        'i': "Pinky up, fist",
        'j': "Pinky up, draw J",
        'k': "Index & middle up, thumb between",
        'l': "L-shape, thumb & index",
        'm': "3 fingers over thumb",
        'n': "2 fingers over thumb",
        'o': "O-shape, fingers touch thumb",
        'p': "K hand, point down",
        'q': "G hand, point down",
        'r': "Cross index & middle",
        's': "Fist, thumb over fingers",
        't': "Thumb between index & middle",
        'u': "Index & middle together up",
        'v': "Peace sign / Victory",
        'w': "3 fingers up spread",
        'x': "Index bent hook",
        'y': "Thumb & pinky out (hang loose)",
        'z': "Index draws Z in air",
    }
    
    # Unicode hand emojis for visual representation
    ASL_EMOJIS = {
        'a': '✊', 'b': '🖐️', 'c': '👌', 'd': '☝️', 'e': '✊',
        'f': '👌', 'g': '👉', 'h': '👉', 'i': '🤙', 'j': '🤙',
        'k': '✌️', 'l': '🤟', 'm': '✊', 'n': '✊', 'o': '👌',
        'p': '👇', 'q': '👇', 'r': '✌️', 's': '✊', 't': '✊',
        'u': '✌️', 'v': '✌️', 'w': '🤟', 'x': '☝️', 'y': '🤙',
        'z': '☝️',
    }
    
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), 'asl_images')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.image_cache = {}
        
    def create_asl_image(self, letter, size=(300, 300)):
        """Create an ASL hand sign image for a letter"""
        letter = letter.lower()
        
        # Check cache first
        cache_key = f"{letter}_{size[0]}x{size[1]}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        # Create image with gradient background
        img = Image.new('RGB', size, '#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Draw circular background
        margin = 20
        ellipse_bbox = [margin, margin, size[0] - margin, size[1] - margin]
        draw.ellipse(ellipse_bbox, fill='#16213e', outline='#e94560', width=3)
        
        # Get emoji and description
        emoji = self.ASL_EMOJIS.get(letter, '🤚')
        description = self.ASL_DESCRIPTIONS.get(letter, 'Hand sign')
        
        # Try to load a font, fall back to default
        try:
            # Use a large font for the emoji representation
            emoji_font = ImageFont.truetype("seguiemj.ttf", 80)
            letter_font = ImageFont.truetype("arial.ttf", 60)
            desc_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                emoji_font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 80)
                letter_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
                desc_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
            except:
                emoji_font = ImageFont.load_default()
                letter_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
        
        # Draw the letter at top
        letter_text = letter.upper()
        letter_bbox = draw.textbbox((0, 0), letter_text, font=letter_font)
        letter_width = letter_bbox[2] - letter_bbox[0]
        letter_x = (size[0] - letter_width) // 2
        draw.text((letter_x, 40), letter_text, fill='#e94560', font=letter_font)
        
        # Draw emoji in center
        try:
            emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            emoji_x = (size[0] - emoji_width) // 2
            draw.text((emoji_x, 100), emoji, fill='white', font=emoji_font)
        except:
            # If emoji doesn't render, draw a hand outline
            self._draw_hand_outline(draw, size, letter)
        
        # Draw description at bottom
        desc_bbox = draw.textbbox((0, 0), description, font=desc_font)
        desc_width = desc_bbox[2] - desc_bbox[0]
        desc_x = (size[0] - desc_width) // 2
        draw.text((desc_x, size[1] - 50), description, fill='#a0a0a0', font=desc_font)
        
        # Cache and return
        self.image_cache[cache_key] = img
        return img
    
    def _draw_hand_outline(self, draw, size, letter):
        """Draw a simple hand outline as fallback"""
        center_x = size[0] // 2
        center_y = size[1] // 2
        
        # Draw a basic hand shape
        # Palm
        draw.ellipse([center_x - 40, center_y - 20, center_x + 40, center_y + 60], 
                     fill='#f0d9b5', outline='#d4a574', width=2)
        
        # Fingers based on letter
        letter = letter.lower()
        
        # Default: all fingers
        fingers = [(0, -80), (-30, -70), (30, -70), (-50, -40), (50, -40)]
        
        if letter in 'aemnst':
            fingers = []  # Fist
        elif letter in 'g':
            fingers = [(40, 0)]  # Pointing sideways
        elif letter in 'h':
            fingers = [(40, -10), (40, 10)]  # Two fingers sideways
        elif letter in 'ij':
            fingers = [(40, -60)]  # Pinky only
        elif letter in 'l':
            fingers = [(0, -80), (50, -40)]  # L shape
        elif letter in 'v':
            fingers = [(-15, -80), (15, -80)]  # Peace
        elif letter in 'w':
            fingers = [(-20, -80), (0, -80), (20, -80)]  # W
        elif letter in 'y':
            fingers = [(-50, -40), (50, -40)]  # Thumb and pinky
        
        for dx, dy in fingers:
            draw.ellipse([center_x + dx - 8, center_y + dy - 15,
                         center_x + dx + 8, center_y + dy + 15],
                        fill='#f0d9b5', outline='#d4a574', width=1)
    
    def create_word_image(self, word, size=(300, 300)):
        """Create an image representing an ASL word sign"""
        word = word.lower()
        
        # Check cache
        cache_key = f"word_{word}_{size[0]}x{size[1]}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        # Create image
        img = Image.new('RGB', size, '#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Draw background
        margin = 20
        draw.rounded_rectangle([margin, margin, size[0] - margin, size[1] - margin],
                              radius=20, fill='#16213e', outline='#00d9ff', width=3)
        
        # Word-specific descriptions
        word_descriptions = {
            'hello': "Wave hand side to side 👋",
            'thank you': "Touch chin, move hand forward 🙏",
            'please': "Rub chest in circle ✋",
            'sorry': "Make fist, rub chest in circle ✊",
            'yes': "Nod fist up and down ✊",
            'no': "Snap index & middle to thumb ✌️",
            'help': "Thumbs up on palm, lift up 👍",
            'love': "Cross arms over chest 🤟",
            'friend': "Hook index fingers together 🤝",
            'family': "F hands circle together 👨‍👩‍👧",
            'good': "Touch chin, move hand down 👌",
            'bad': "Touch chin, flip hand over 👎",
            'name': "Tap H fingers on H fingers ✌️",
            'what': "Shake open hands ❓",
            'where': "Shake index finger ❓",
            'when': "Circle index around index ⏰",
            'why': "Touch forehead, wiggle Y hand ❓",
            'how': "Rotate fists together 🤔",
            'water': "W hand taps chin 💧",
            'food': "Touch finger tips to mouth 🍽️",
            'eat': "Touch fingers to mouth 🍴",
            'drink': "C hand to mouth 🥤",
            'home': "Touch cheek, then ear 🏠",
            'work': "Tap fists together 💼",
            'school': "Clap hands twice 🏫",
            'learn': "Pull knowledge from book to head 📚",
            'understand': "Flick index up from forehead 💡",
            'know': "Tap fingers on forehead 🧠",
            'want': "Pull claw hands toward body 🤲",
            'need': "Index points down, X motion 📌",
            'like': "Pull thumb & middle from chest 👍",
            'nice': "Slide palm over palm ✨",
            'meet': "Bring index fingers together 🤝",
            'welcome': "Wave hand toward body 🙋",
        }
        
        description = word_descriptions.get(word, f"Sign for '{word}'")
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            desc_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
                desc_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
            except:
                title_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
        
        # Draw word
        word_text = word.upper()
        bbox = draw.textbbox((0, 0), word_text, font=title_font)
        word_width = bbox[2] - bbox[0]
        word_x = (size[0] - word_width) // 2
        draw.text((word_x, 60), word_text, fill='#e94560', font=title_font)
        
        # Draw hands emoji
        draw.text((size[0]//2 - 30, 120), "🤲", fill='white', font=title_font)
        
        # Draw description (word wrap if needed)
        lines = []
        words = description.split()
        current_line = ""
        for w in words:
            test_line = current_line + " " + w if current_line else w
            bbox = draw.textbbox((0, 0), test_line, font=desc_font)
            if bbox[2] - bbox[0] < size[0] - 60:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = w
        if current_line:
            lines.append(current_line)
        
        y_offset = 200
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=desc_font)
            line_width = bbox[2] - bbox[0]
            line_x = (size[0] - line_width) // 2
            draw.text((line_x, y_offset), line, fill='#a0a0a0', font=desc_font)
            y_offset += 25
        
        self.image_cache[cache_key] = img
        return img


class ASLTranslator:
    """Main class for Voice to ASL translation"""
    
    # Common ASL words (these will show word signs instead of fingerspelling)
    COMMON_WORDS = [
        'hello', 'thank you', 'please', 'sorry', 'yes', 'no', 'help', 'love',
        'friend', 'family', 'good', 'bad', 'name', 'what', 'where', 'when',
        'why', 'how', 'water', 'food', 'eat', 'drink', 'home', 'work',
        'school', 'learn', 'understand', 'know', 'want', 'need', 'like',
        'nice', 'meet', 'welcome'
    ]
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.image_generator = ASLImageGenerator()
        self.is_listening = False
        
    def listen_to_voice(self):
        """Listen to microphone and convert speech to text"""
        with sr.Microphone() as source:
            print("🎤 Adjusting for ambient noise... Please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Listening... Speak now!")
            
            try:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                print("🔄 Processing speech...")
                
                # Using Google's free speech recognition API
                text = self.recognizer.recognize_google(audio)
                print(f"✅ Recognized: {text}")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("⏰ Listening timed out. No speech detected.")
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"❌ Could not request results from Google Speech Recognition service: {e}")
                return None
    
    def get_asl_for_word(self, word):
        """Get ASL representation for a word - always fingerspell letter by letter"""
        word = word.lower().strip()
        
        # Fingerspell every word letter by letter
        result = []
        for char in word:
            if char.isalpha():
                image = self.image_generator.create_asl_image(char)
                result.append(('letter', char, image))
        
        return result
    
    def get_asl_for_text(self, text):
        """Convert text to ASL representation"""
        words = text.split()
        result = []
        
        for word in words:
            # Clean the word
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word:
                word_asl = self.get_asl_for_word(clean_word)
                if word_asl:
                    result.append((clean_word, word_asl))
        
        return result


class ASLTranslatorGUI:
    """GUI for the Voice to ASL Translator"""
    
    def __init__(self):
        self.translator = ASLTranslator()
        self.root = tk.Tk()
        self.root.title("🤟 Voice to ASL Translator")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a2e')
        
        self.current_images = []
        self.animation_index = 0
        self.is_playing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = tk.Frame(self.root, bg='#1a1a2e')
        title_frame.pack(pady=20)
        
        title_label = tk.Label(
            title_frame,
            text="🤟 Voice to ASL Translator",
            font=('Helvetica', 28, 'bold'),
            fg='#e94560',
            bg='#1a1a2e'
        )
        title_label.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Speak and see American Sign Language",
            font=('Helvetica', 12),
            fg='#a0a0a0',
            bg='#1a1a2e'
        )
        subtitle.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Click 'Start Listening' to begin",
            font=('Helvetica', 14),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.status_label.pack(pady=10)
        
        # Recognized text display
        text_frame = tk.Frame(self.root, bg='#16213e', padx=20, pady=10)
        text_frame.pack(fill='x', padx=30, pady=10)
        
        tk.Label(
            text_frame,
            text="Recognized Text:",
            font=('Helvetica', 12, 'bold'),
            fg='#a0a0a0',
            bg='#16213e'
        ).pack(anchor='w')
        
        self.text_display = tk.Label(
            text_frame,
            text="...",
            font=('Helvetica', 18),
            fg='#ffffff',
            bg='#16213e',
            wraplength=800
        )
        self.text_display.pack(pady=5)
        
        # Current letter/word indicator
        self.current_char_label = tk.Label(
            self.root,
            text="",
            font=('Helvetica', 24, 'bold'),
            fg='#e94560',
            bg='#1a1a2e'
        )
        self.current_char_label.pack(pady=10)
        
        # ASL Image display
        self.image_frame = tk.Frame(self.root, bg='#0f3460', width=400, height=400)
        self.image_frame.pack(pady=20)
        self.image_frame.pack_propagate(False)
        
        self.asl_image_label = tk.Label(
            self.image_frame,
            bg='#0f3460',
            text="ASL signs will appear here",
            font=('Helvetica', 14),
            fg='#a0a0a0'
        )
        self.asl_image_label.pack(expand=True)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.progress_frame.pack(fill='x', padx=50, pady=10)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=700
        )
        self.progress_bar.pack(pady=5)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Helvetica', 10),
            fg='#a0a0a0',
            bg='#1a1a2e'
        )
        self.progress_label.pack()
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#1a1a2e')
        button_frame.pack(pady=20)
        
        self.listen_button = tk.Button(
            button_frame,
            text="🎤 Start Listening",
            font=('Helvetica', 14, 'bold'),
            fg='white',
            bg='#e94560',
            activebackground='#ff6b6b',
            padx=30,
            pady=10,
            cursor='hand2',
            command=self.start_listening
        )
        self.listen_button.pack(side='left', padx=10)
        
        self.stop_button = tk.Button(
            button_frame,
            text="⏹ Stop",
            font=('Helvetica', 14, 'bold'),
            fg='white',
            bg='#4a4a6a',
            activebackground='#6a6a8a',
            padx=30,
            pady=10,
            cursor='hand2',
            command=self.stop_animation,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=10)
        
        # Text input option
        input_frame = tk.Frame(self.root, bg='#1a1a2e')
        input_frame.pack(pady=10)
        
        tk.Label(
            input_frame,
            text="Or type text:",
            font=('Helvetica', 11),
            fg='#a0a0a0',
            bg='#1a1a2e'
        ).pack(side='left', padx=5)
        
        self.text_entry = tk.Entry(
            input_frame,
            font=('Helvetica', 12),
            width=40,
            bg='#16213e',
            fg='white',
            insertbackground='white'
        )
        self.text_entry.pack(side='left', padx=5)
        self.text_entry.bind('<Return>', lambda e: self.process_text_input())
        
        tk.Button(
            input_frame,
            text="Convert",
            font=('Helvetica', 11),
            fg='white',
            bg='#0f3460',
            command=self.process_text_input,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Info label
        info_label = tk.Label(
            self.root,
            text="💡 Tip: Common words like 'hello', 'thank you', 'please' have full ASL signs.\n"
                 "Other words will be fingerspelled letter by letter.",
            font=('Helvetica', 10),
            fg='#6a6a8a',
            bg='#1a1a2e'
        )
        info_label.pack(side='bottom', pady=10)
    
    def start_listening(self):
        """Start listening for voice input"""
        self.listen_button.config(state='disabled')
        self.status_label.config(text="🎤 Listening... Speak now!", fg='#00ff00')
        self.root.update()
        
        # Run speech recognition in a separate thread
        thread = threading.Thread(target=self.listen_thread)
        thread.daemon = True
        thread.start()
    
    def listen_thread(self):
        """Thread for speech recognition"""
        text = self.translator.listen_to_voice()
        
        # Update UI from main thread
        self.root.after(0, lambda: self.process_recognized_text(text))
    
    def process_recognized_text(self, text):
        """Process the recognized text"""
        self.listen_button.config(state='normal')
        
        if text:
            self.text_display.config(text=text)
            self.status_label.config(text="✅ Speech recognized! Showing ASL...", fg='#00ff00')
            self.display_asl(text)
        else:
            self.status_label.config(text="❌ Could not recognize speech. Try again.", fg='#ff6b6b')
    
    def process_text_input(self):
        """Process text input from entry field"""
        text = self.text_entry.get().strip()
        if text:
            self.text_display.config(text=text)
            self.status_label.config(text="Showing ASL for typed text...", fg='#00d9ff')
            self.display_asl(text)
    
    def display_asl(self, text):
        """Display ASL for the given text"""
        asl_data = self.translator.get_asl_for_text(text)
        
        if not asl_data:
            self.status_label.config(text="No displayable characters found.", fg='#ff6b6b')
            return
        
        # Flatten all signs for animation
        self.current_images = []
        for word, signs in asl_data:
            for sign_type, char, image in signs:
                self.current_images.append({
                    'type': sign_type,
                    'char': char,
                    'word': word if sign_type == 'word' else None,
                    'image': image  # Now storing PIL Image directly
                })
        
        self.animation_index = 0
        self.is_playing = True
        self.stop_button.config(state='normal')
        self.progress_bar['maximum'] = len(self.current_images)
        self.progress_bar['value'] = 0
        
        self.animate_next()
    
    def animate_next(self):
        """Show the next ASL sign in sequence"""
        if not self.is_playing or self.animation_index >= len(self.current_images):
            self.is_playing = False
            self.stop_button.config(state='disabled')
            self.status_label.config(text="✅ Complete! Click to listen again.", fg='#00d9ff')
            return
        
        current = self.current_images[self.animation_index]
        
        # Update progress
        self.progress_bar['value'] = self.animation_index + 1
        
        if current['type'] == 'word':
            self.current_char_label.config(text=f"Word: {current['word'].upper()}")
            self.progress_label.config(text=f"Showing sign for '{current['word']}'")
        else:
            self.current_char_label.config(text=f"Letter: {current['char'].upper()}")
            self.progress_label.config(text=f"Fingerspelling: {current['char'].upper()}")
        
        # Display the locally generated image
        image = current['image']
        
        if image:
            # Resize image to fit frame
            image = image.copy()
            image.thumbnail((350, 350), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.asl_image_label.config(image=photo, text='')
            self.asl_image_label.image = photo
        else:
            self.asl_image_label.config(
                image='',
                text=f"[{current['char'].upper()}]\n(Image unavailable)"
            )
        
        self.animation_index += 1
        
        # Schedule next animation
        delay = 1500 if current['type'] == 'word' else 800
        self.root.after(delay, self.animate_next)
    
    def stop_animation(self):
        """Stop the current animation"""
        self.is_playing = False
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Animation stopped.", fg='#a0a0a0')
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    print("=" * 60)
    print("🤟 Voice to American Sign Language Translator")
    print("=" * 60)
    print()
    print("This application converts your voice to ASL fingerspelling")
    print("and common sign language gestures.")
    print()
    print("Requirements:")
    print("  - Microphone for voice input")
    print("  - Internet connection for speech recognition")
    print()
    print("Starting GUI...")
    print()
    
    try:
        app = ASLTranslatorGUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PyAudio is installed: pip install pyaudio")
        print("2. On Windows, you may need: pip install pipwin && pipwin install pyaudio")
        print("3. Ensure you have a working microphone connected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
