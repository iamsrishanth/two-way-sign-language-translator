"""
Two-Way Sign Language Translator
Combines ASL-to-Voice and Voice-to-ASL functionality in a single application.
"""

import numpy as np
import math
import cv2
import os
import sys
import traceback
import time
import threading
import pyttsx3
import speech_recognition as sr
from keras.models import load_model
from cvzone.HandTrackingModule import HandDetector
from string import ascii_uppercase
import enchant
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Initialize global components
ddd = enchant.Dict("en-US")
hd = HandDetector(maxHands=1)
hd2 = HandDetector(maxHands=1)
offset = 29

os.environ["THEANO_FLAGS"] = "device=cuda, assert_no_cpu_op=True"


# ==================== ASL Image Generator (for Voice-to-ASL) ====================

class ASLImageGenerator:
    """Generates ASL hand sign images locally"""
    
    ASL_DESCRIPTIONS = {
        'a': "Fist with thumb beside", 'b': "Flat hand, thumb tucked",
        'c': "Curved hand, C-shape", 'd': "Index up, others touch thumb",
        'e': "Fingers bent, thumb tucked", 'f': "OK sign, 3 fingers up",
        'g': "Point sideways", 'h': "Point sideways, 2 fingers",
        'i': "Pinky up, fist", 'j': "Pinky up, draw J",
        'k': "Index & middle up, thumb between", 'l': "L-shape, thumb & index",
        'm': "3 fingers over thumb", 'n': "2 fingers over thumb",
        'o': "O-shape, fingers touch thumb", 'p': "K hand, point down",
        'q': "G hand, point down", 'r': "Cross index & middle",
        's': "Fist, thumb over fingers", 't': "Thumb between index & middle",
        'u': "Index & middle together up", 'v': "Peace sign / Victory",
        'w': "3 fingers up spread", 'x': "Index bent hook",
        'y': "Thumb & pinky out (hang loose)", 'z': "Index draws Z in air",
    }
    
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
        cache_key = f"{letter}_{size[0]}x{size[1]}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        img = Image.new('RGB', size, '#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        margin = 20
        ellipse_bbox = [margin, margin, size[0] - margin, size[1] - margin]
        draw.ellipse(ellipse_bbox, fill='#16213e', outline='#e94560', width=3)
        
        emoji = self.ASL_EMOJIS.get(letter, '🤚')
        description = self.ASL_DESCRIPTIONS.get(letter, 'Hand sign')
        
        try:
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
        
        letter_text = letter.upper()
        letter_bbox = draw.textbbox((0, 0), letter_text, font=letter_font)
        letter_width = letter_bbox[2] - letter_bbox[0]
        letter_x = (size[0] - letter_width) // 2
        draw.text((letter_x, 40), letter_text, fill='#e94560', font=letter_font)
        
        try:
            emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            emoji_x = (size[0] - emoji_width) // 2
            draw.text((emoji_x, 100), emoji, fill='white', font=emoji_font)
        except:
            pass
        
        desc_bbox = draw.textbbox((0, 0), description, font=desc_font)
        desc_width = desc_bbox[2] - desc_bbox[0]
        desc_x = (size[0] - desc_width) // 2
        draw.text((desc_x, size[1] - 50), description, fill='#a0a0a0', font=desc_font)
        
        self.image_cache[cache_key] = img
        return img


# ==================== Two-Way Translator Application ====================

class TwoWayTranslatorApp:
    """Main application combining ASL-to-Voice and Voice-to-ASL"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤟 Two-Way Sign Language Translator")
        self.root.geometry("1400x800")
        self.root.configure(bg='#1a1a2e')
        
        # Mode: 'asl_to_voice' or 'voice_to_asl'
        self.current_mode = tk.StringVar(value='asl_to_voice')
        
        # ASL to Voice components
        self.vs = None
        self.model = None
        self.speak_engine = pyttsx3.init()
        self.speak_engine.setProperty("rate", 100)
        voices = self.speak_engine.getProperty("voices")
        self.speak_engine.setProperty("voice", voices[0].id)
        
        # Voice to ASL components
        self.recognizer = sr.Recognizer()
        self.image_generator = ASLImageGenerator()
        self.current_images = []
        self.animation_index = 0
        self.is_playing = False
        
        # ASL recognition state
        self.ct = {'blank': 0}
        for i in ascii_uppercase:
            self.ct[i] = 0
        self.str = " "
        self.word = " "
        self.current_symbol = ""
        self.prev_char = ""
        self.count = -1
        self.ten_prev_char = [" "] * 10
        self.ccc = 0
        self.pts = []
        
        self.word1 = " "
        self.word2 = " "
        self.word3 = " "
        self.word4 = " "
        
        self.setup_ui()
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)
        
    def setup_ui(self):
        """Setup the main user interface with mode switching"""
        # Title
        title_frame = tk.Frame(self.root, bg='#1a1a2e')
        title_frame.pack(pady=10)
        
        tk.Label(
            title_frame,
            text="🤟 Two-Way Sign Language Translator",
            font=('Helvetica', 28, 'bold'),
            fg='#e94560',
            bg='#1a1a2e'
        ).pack()
        
        # Mode Selection
        mode_frame = tk.Frame(self.root, bg='#16213e', padx=20, pady=10)
        mode_frame.pack(fill='x', padx=30, pady=10)
        
        tk.Label(
            mode_frame,
            text="Select Mode:",
            font=('Helvetica', 14, 'bold'),
            fg='white',
            bg='#16213e'
        ).pack(side='left', padx=10)
        
        self.asl_to_voice_btn = tk.Radiobutton(
            mode_frame,
            text="🖐️ ASL → Voice (Sign to Speak)",
            variable=self.current_mode,
            value='asl_to_voice',
            font=('Helvetica', 12),
            fg='white',
            bg='#16213e',
            selectcolor='#e94560',
            activebackground='#16213e',
            activeforeground='white',
            command=self.switch_mode
        )
        self.asl_to_voice_btn.pack(side='left', padx=20)
        
        self.voice_to_asl_btn = tk.Radiobutton(
            mode_frame,
            text="🎤 Voice → ASL (Speak to Sign)",
            variable=self.current_mode,
            value='voice_to_asl',
            font=('Helvetica', 12),
            fg='white',
            bg='#16213e',
            selectcolor='#e94560',
            activebackground='#16213e',
            activeforeground='white',
            command=self.switch_mode
        )
        self.voice_to_asl_btn.pack(side='left', padx=20)
        
        # Main content frame
        self.content_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # ASL to Voice Frame
        self.asl_frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        self.setup_asl_to_voice_ui()
        
        # Voice to ASL Frame
        self.voice_frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        self.setup_voice_to_asl_ui()
        
        # Show initial mode
        self.switch_mode()
        
    def setup_asl_to_voice_ui(self):
        """Setup ASL to Voice interface"""
        # Camera panel - fixed 640x480 pixel size
        cam_frame = tk.Frame(self.asl_frame, bg='#0f3460', width=650, height=490)
        cam_frame.pack(side='left', padx=10, pady=10)
        cam_frame.pack_propagate(False)
        
        tk.Label(cam_frame, text="Camera Feed", font=('Helvetica', 12, 'bold'),
                 fg='#00d9ff', bg='#0f3460').pack(pady=5)
        self.camera_panel = tk.Label(cam_frame, bg='#0f3460')
        self.camera_panel.pack(padx=5, pady=5, expand=True)
        
        # Hand tracking panel - fixed 400x400 pixel size
        track_frame = tk.Frame(self.asl_frame, bg='#0f3460', width=420, height=420)
        track_frame.pack(side='left', padx=10, pady=10)
        track_frame.pack_propagate(False)
        
        tk.Label(track_frame, text="Hand Tracking", font=('Helvetica', 12, 'bold'),
                 fg='#00d9ff', bg='#0f3460').pack(pady=5)
        self.hand_panel = tk.Label(track_frame, bg='#0f3460')
        self.hand_panel.pack(padx=5, pady=5, expand=True)
        
        # Info panel
        info_frame = tk.Frame(self.asl_frame, bg='#16213e', padx=20, pady=20)
        info_frame.pack(side='right', fill='y', padx=10)
        
        tk.Label(info_frame, text="Current Character:", font=('Helvetica', 14, 'bold'),
                 fg='#a0a0a0', bg='#16213e').pack()
        self.char_label = tk.Label(info_frame, text="", font=('Helvetica', 48, 'bold'),
                                   fg='#e94560', bg='#16213e')
        self.char_label.pack(pady=10)
        
        tk.Label(info_frame, text="Sentence:", font=('Helvetica', 14, 'bold'),
                 fg='#a0a0a0', bg='#16213e').pack(pady=(20, 5))
        self.sentence_label = tk.Label(info_frame, text="", font=('Helvetica', 18),
                                        fg='white', bg='#16213e', wraplength=300)
        self.sentence_label.pack(pady=5)
        
        tk.Label(info_frame, text="Suggestions:", font=('Helvetica', 12, 'bold'),
                 fg='#ff6b6b', bg='#16213e').pack(pady=(20, 5))
        
        # Suggestion buttons
        self.sugg_btn1 = tk.Button(info_frame, text="", font=('Helvetica', 11),
                                   command=lambda: self.apply_suggestion(1), bg='#0f3460', fg='white')
        self.sugg_btn1.pack(fill='x', pady=2)
        self.sugg_btn2 = tk.Button(info_frame, text="", font=('Helvetica', 11),
                                   command=lambda: self.apply_suggestion(2), bg='#0f3460', fg='white')
        self.sugg_btn2.pack(fill='x', pady=2)
        self.sugg_btn3 = tk.Button(info_frame, text="", font=('Helvetica', 11),
                                   command=lambda: self.apply_suggestion(3), bg='#0f3460', fg='white')
        self.sugg_btn3.pack(fill='x', pady=2)
        self.sugg_btn4 = tk.Button(info_frame, text="", font=('Helvetica', 11),
                                   command=lambda: self.apply_suggestion(4), bg='#0f3460', fg='white')
        self.sugg_btn4.pack(fill='x', pady=2)
        
        # Control buttons
        btn_frame = tk.Frame(info_frame, bg='#16213e')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="🔊 Speak", font=('Helvetica', 12, 'bold'),
                  command=self.speak_text, bg='#e94560', fg='white',
                  padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Clear", font=('Helvetica', 12, 'bold'),
                  command=self.clear_text, bg='#4a4a6a', fg='white',
                  padx=15, pady=5).pack(side='left', padx=5)
        
    def setup_voice_to_asl_ui(self):
        """Setup Voice to ASL interface"""
        # Status label
        self.voice_status = tk.Label(
            self.voice_frame,
            text="Click 'Start Listening' or type text below",
            font=('Helvetica', 14),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.voice_status.pack(pady=10)
        
        # Recognized text display
        text_frame = tk.Frame(self.voice_frame, bg='#16213e', padx=20, pady=10)
        text_frame.pack(fill='x', padx=50, pady=10)
        
        tk.Label(text_frame, text="Recognized Text:", font=('Helvetica', 12, 'bold'),
                 fg='#a0a0a0', bg='#16213e').pack(anchor='w')
        self.voice_text_display = tk.Label(text_frame, text="...", font=('Helvetica', 18),
                                            fg='white', bg='#16213e', wraplength=800)
        self.voice_text_display.pack(pady=5)
        
        # Current letter indicator
        self.current_char_label = tk.Label(self.voice_frame, text="",
                                           font=('Helvetica', 24, 'bold'),
                                           fg='#e94560', bg='#1a1a2e')
        self.current_char_label.pack(pady=10)
        
        # ASL Image display
        self.asl_image_frame = tk.Frame(self.voice_frame, bg='#0f3460', width=400, height=400)
        self.asl_image_frame.pack(pady=20)
        self.asl_image_frame.pack_propagate(False)
        
        self.asl_image_label = tk.Label(self.asl_image_frame, bg='#0f3460',
                                        text="ASL signs will appear here",
                                        font=('Helvetica', 14), fg='#a0a0a0')
        self.asl_image_label.pack(expand=True)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.voice_frame, mode='determinate', length=700)
        self.progress_bar.pack(pady=10)
        self.progress_label = tk.Label(self.voice_frame, text="", font=('Helvetica', 10),
                                       fg='#a0a0a0', bg='#1a1a2e')
        self.progress_label.pack()
        
        # Buttons
        btn_frame = tk.Frame(self.voice_frame, bg='#1a1a2e')
        btn_frame.pack(pady=15)
        
        self.listen_btn = tk.Button(btn_frame, text="🎤 Start Listening",
                                    font=('Helvetica', 14, 'bold'),
                                    fg='white', bg='#e94560', padx=30, pady=10,
                                    command=self.start_listening)
        self.listen_btn.pack(side='left', padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ Stop",
                                  font=('Helvetica', 14, 'bold'),
                                  fg='white', bg='#4a4a6a', padx=30, pady=10,
                                  command=self.stop_animation, state='disabled')
        self.stop_btn.pack(side='left', padx=10)
        
        # Text input
        input_frame = tk.Frame(self.voice_frame, bg='#1a1a2e')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Or type text:", font=('Helvetica', 11),
                 fg='#a0a0a0', bg='#1a1a2e').pack(side='left', padx=5)
        self.text_entry = tk.Entry(input_frame, font=('Helvetica', 12), width=40,
                                   bg='#16213e', fg='white', insertbackground='white')
        self.text_entry.pack(side='left', padx=5)
        self.text_entry.bind('<Return>', lambda e: self.process_text_input())
        tk.Button(input_frame, text="Convert", font=('Helvetica', 11),
                  fg='white', bg='#0f3460', command=self.process_text_input).pack(side='left', padx=5)
        
    def switch_mode(self):
        """Switch between ASL-to-Voice and Voice-to-ASL modes"""
        # Hide both frames
        self.asl_frame.pack_forget()
        self.voice_frame.pack_forget()
        
        if self.current_mode.get() == 'asl_to_voice':
            self.asl_frame.pack(fill='both', expand=True)
            self.start_camera()
        else:
            self.voice_frame.pack(fill='both', expand=True)
            self.stop_camera()
            
    def start_camera(self):
        """Start the camera for ASL recognition"""
        if self.vs is None:
            self.vs = cv2.VideoCapture(0)
        if self.model is None:
            try:
                self.model = load_model('cnn8grps_rad1_model.h5')
                print("Model loaded successfully")
            except Exception as e:
                print(f"Error loading model: {e}")
                messagebox.showerror("Error", f"Could not load model: {e}")
                return
        self.video_loop()
        
    def stop_camera(self):
        """Stop the camera"""
        if self.vs is not None:
            self.vs.release()
            self.vs = None
            
    def video_loop(self):
        """Main video loop for ASL recognition"""
        if self.current_mode.get() != 'asl_to_voice' or self.vs is None:
            return
            
        try:
            ok, frame = self.vs.read()
            if not ok:
                self.root.after(30, self.video_loop)
                return
                
            cv2image = cv2.flip(frame, 1)
            hands = hd.findHands(cv2image, draw=False, flipType=True)
            cv2image_copy = np.array(cv2image)
            cv2image_rgb = cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB)
            
            # Display camera feed - larger size
            current_image = Image.fromarray(cv2image_rgb)
            current_image = current_image.resize((640, 480), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=current_image)
            self.camera_panel.imgtk = imgtk
            self.camera_panel.config(image=imgtk)
            
            if hands[0]:
                hand = hands[0]
                handmap = hand[0]
                x, y, w, h = handmap['bbox']
                image = cv2image_copy[max(0, y - offset):y + h + offset, 
                                      max(0, x - offset):x + w + offset]
                
                white = np.ones((400, 400, 3), np.uint8) * 255
                
                if image.size > 0:
                    handz = hd2.findHands(image, draw=False, flipType=True)
                    self.ccc += 1
                    
                    if handz[0]:
                        hand2 = handz[0]
                        handmap2 = hand2[0]
                        self.pts = handmap2['lmList']
                        
                        os_x = ((400 - w) // 2) - 15
                        os_y = ((400 - h) // 2) - 15
                        
                        # Draw hand skeleton
                        for t in range(0, 4):
                            cv2.line(white, (self.pts[t][0] + os_x, self.pts[t][1] + os_y),
                                    (self.pts[t + 1][0] + os_x, self.pts[t + 1][1] + os_y), (0, 255, 0), 3)
                        for t in range(5, 8):
                            cv2.line(white, (self.pts[t][0] + os_x, self.pts[t][1] + os_y),
                                    (self.pts[t + 1][0] + os_x, self.pts[t + 1][1] + os_y), (0, 255, 0), 3)
                        for t in range(9, 12):
                            cv2.line(white, (self.pts[t][0] + os_x, self.pts[t][1] + os_y),
                                    (self.pts[t + 1][0] + os_x, self.pts[t + 1][1] + os_y), (0, 255, 0), 3)
                        for t in range(13, 16):
                            cv2.line(white, (self.pts[t][0] + os_x, self.pts[t][1] + os_y),
                                    (self.pts[t + 1][0] + os_x, self.pts[t + 1][1] + os_y), (0, 255, 0), 3)
                        for t in range(17, 20):
                            cv2.line(white, (self.pts[t][0] + os_x, self.pts[t][1] + os_y),
                                    (self.pts[t + 1][0] + os_x, self.pts[t + 1][1] + os_y), (0, 255, 0), 3)
                        
                        cv2.line(white, (self.pts[5][0] + os_x, self.pts[5][1] + os_y),
                                (self.pts[9][0] + os_x, self.pts[9][1] + os_y), (0, 255, 0), 3)
                        cv2.line(white, (self.pts[9][0] + os_x, self.pts[9][1] + os_y),
                                (self.pts[13][0] + os_x, self.pts[13][1] + os_y), (0, 255, 0), 3)
                        cv2.line(white, (self.pts[13][0] + os_x, self.pts[13][1] + os_y),
                                (self.pts[17][0] + os_x, self.pts[17][1] + os_y), (0, 255, 0), 3)
                        cv2.line(white, (self.pts[0][0] + os_x, self.pts[0][1] + os_y),
                                (self.pts[5][0] + os_x, self.pts[5][1] + os_y), (0, 255, 0), 3)
                        cv2.line(white, (self.pts[0][0] + os_x, self.pts[0][1] + os_y),
                                (self.pts[17][0] + os_x, self.pts[17][1] + os_y), (0, 255, 0), 3)
                        
                        for i in range(21):
                            cv2.circle(white, (self.pts[i][0] + os_x, self.pts[i][1] + os_y), 2, (0, 0, 255), 1)
                        
                        self.predict(white)
                        
                        # Display hand tracking - larger size
                        hand_image = Image.fromarray(white)
                        hand_image = hand_image.resize((400, 400), Image.Resampling.LANCZOS)
                        handtk = ImageTk.PhotoImage(image=hand_image)
                        self.hand_panel.imgtk = handtk
                        self.hand_panel.config(image=handtk)
                        
                        # Update UI
                        self.char_label.config(text=self.current_symbol)
                        self.sentence_label.config(text=self.str.strip())
                        self.sugg_btn1.config(text=self.word1)
                        self.sugg_btn2.config(text=self.word2)
                        self.sugg_btn3.config(text=self.word3)
                        self.sugg_btn4.config(text=self.word4)
                        
        except Exception as e:
            print(f"Video loop error: {e}")
            
        self.root.after(30, self.video_loop)
        
    def distance(self, x, y):
        """Calculate distance between two points"""
        return math.sqrt(((x[0] - y[0]) ** 2) + ((x[1] - y[1]) ** 2))
        
    def predict(self, test_image):
        """Predict ASL letter from hand image"""
        if self.model is None or len(self.pts) < 21:
            return
            
        white = test_image.reshape(1, 400, 400, 3)
        prob = np.array(self.model.predict(white, verbose=0)[0], dtype='float32')
        ch1 = np.argmax(prob, axis=0)
        prob[ch1] = 0
        ch2 = np.argmax(prob, axis=0)
        
        pl = [ch1, ch2]
        
        # Apply prediction rules (simplified from original)
        # Group conditions for letter recognition
        if ch1 == 0:
            ch1 = 'S'
            if self.pts[4][0] < self.pts[6][0]:
                ch1 = 'A'
            if self.pts[4][1] > self.pts[8][1]:
                ch1 = 'E'
        elif ch1 == 2:
            ch1 = 'C' if self.distance(self.pts[12], self.pts[4]) > 42 else 'O'
        elif ch1 == 3:
            ch1 = 'G' if self.distance(self.pts[8], self.pts[12]) > 72 else 'H'
        elif ch1 == 4:
            ch1 = 'L'
        elif ch1 == 5:
            ch1 = 'P'
        elif ch1 == 6:
            ch1 = 'X'
        elif ch1 == 7:
            ch1 = 'Y' if self.distance(self.pts[8], self.pts[4]) > 42 else 'J'
        elif ch1 == 1:
            if self.pts[6][1] > self.pts[8][1] and self.pts[10][1] > self.pts[12][1]:
                ch1 = 'B'
            elif self.pts[6][1] > self.pts[8][1] and self.pts[10][1] < self.pts[12][1]:
                ch1 = 'D'
            else:
                ch1 = 'F'
        
        # Check for special gestures
        if self.pts[6][1] > self.pts[8][1] and self.pts[10][1] < self.pts[12][1] and \
           self.pts[14][1] < self.pts[16][1] and self.pts[18][1] > self.pts[20][1]:
            ch1 = " "
            
        if self.pts[4][0] < self.pts[5][0] and self.pts[6][1] > self.pts[8][1] and \
           self.pts[10][1] > self.pts[12][1] and self.pts[14][1] > self.pts[16][1]:
            ch1 = "next"
            
        # Handle character addition
        if ch1 == "next" and self.prev_char != "next":
            if self.ten_prev_char[(self.count - 2) % 10] != "next":
                if self.ten_prev_char[(self.count - 2) % 10] == "Backspace":
                    self.str = self.str[:-1]
                else:
                    self.str = self.str + self.ten_prev_char[(self.count - 2) % 10]
                    
        self.prev_char = ch1
        self.current_symbol = ch1 if isinstance(ch1, str) else ""
        self.count += 1
        self.ten_prev_char[self.count % 10] = ch1
        
        # Update word suggestions
        if len(self.str.strip()) != 0:
            st = self.str.rfind(" ")
            word = self.str[st + 1:]
            self.word = word
            if len(word.strip()) != 0:
                suggestions = ddd.suggest(word)
                self.word1 = suggestions[0] if len(suggestions) >= 1 else " "
                self.word2 = suggestions[1] if len(suggestions) >= 2 else " "
                self.word3 = suggestions[2] if len(suggestions) >= 3 else " "
                self.word4 = suggestions[3] if len(suggestions) >= 4 else " "
                
    def apply_suggestion(self, num):
        """Apply word suggestion"""
        words = [self.word1, self.word2, self.word3, self.word4]
        if num <= len(words) and words[num - 1].strip():
            idx_space = self.str.rfind(" ")
            self.str = self.str[:idx_space + 1] + words[num - 1].upper()
            
    def speak_text(self):
        """Speak the recognized text"""
        if self.str.strip():
            self.speak_engine.say(self.str)
            self.speak_engine.runAndWait()
            
    def clear_text(self):
        """Clear recognized text"""
        self.str = " "
        self.word1 = self.word2 = self.word3 = self.word4 = " "
        self.sentence_label.config(text="")
        self.char_label.config(text="")
        
    # Voice to ASL methods
    def start_listening(self):
        """Start listening for voice input"""
        self.listen_btn.config(state='disabled')
        self.voice_status.config(text="🎤 Listening... Speak now!", fg='#00ff00')
        self.root.update()
        
        thread = threading.Thread(target=self.listen_thread)
        thread.daemon = True
        thread.start()
        
    def listen_thread(self):
        """Thread for speech recognition"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                text = self.recognizer.recognize_google(audio)
                self.root.after(0, lambda: self.process_recognized_text(text.lower()))
        except Exception as e:
            self.root.after(0, lambda: self.process_recognized_text(None))
            
    def process_recognized_text(self, text):
        """Process recognized text"""
        self.listen_btn.config(state='normal')
        
        if text:
            self.voice_text_display.config(text=text)
            self.voice_status.config(text="✅ Speech recognized! Showing ASL...", fg='#00ff00')
            self.display_asl(text)
        else:
            self.voice_status.config(text="❌ Could not recognize speech. Try again.", fg='#ff6b6b')
            
    def process_text_input(self):
        """Process text input"""
        text = self.text_entry.get().strip()
        if text:
            self.voice_text_display.config(text=text)
            self.voice_status.config(text="Showing ASL for typed text...", fg='#00d9ff')
            self.display_asl(text)
            
    def display_asl(self, text):
        """Display ASL for text"""
        self.current_images = []
        for word in text.split():
            clean_word = ''.join(c for c in word if c.isalnum())
            for char in clean_word:
                if char.isalpha():
                    image = self.image_generator.create_asl_image(char)
                    self.current_images.append({'type': 'letter', 'char': char, 'image': image})
                    
        if not self.current_images:
            return
            
        self.animation_index = 0
        self.is_playing = True
        self.stop_btn.config(state='normal')
        self.progress_bar['maximum'] = len(self.current_images)
        self.progress_bar['value'] = 0
        self.animate_next()
        
    def animate_next(self):
        """Animate next ASL sign"""
        if not self.is_playing or self.animation_index >= len(self.current_images):
            self.is_playing = False
            self.stop_btn.config(state='disabled')
            self.voice_status.config(text="✅ Complete! Click to listen again.", fg='#00d9ff')
            return
            
        current = self.current_images[self.animation_index]
        self.progress_bar['value'] = self.animation_index + 1
        self.current_char_label.config(text=f"Letter: {current['char'].upper()}")
        self.progress_label.config(text=f"Fingerspelling: {current['char'].upper()}")
        
        image = current['image'].copy()
        image.thumbnail((350, 350), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.asl_image_label.config(image=photo, text='')
        self.asl_image_label.image = photo
        
        self.animation_index += 1
        self.root.after(800, self.animate_next)
        
    def stop_animation(self):
        """Stop animation"""
        self.is_playing = False
        self.stop_btn.config(state='disabled')
        self.voice_status.config(text="Animation stopped.", fg='#a0a0a0')
        
    def destructor(self):
        """Clean up resources"""
        self.stop_camera()
        self.root.destroy()
        cv2.destroyAllWindows()
        
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    print("=" * 60)
    print("🤟 Two-Way Sign Language Translator")
    print("=" * 60)
    print()
    print("Modes available:")
    print("  1. ASL → Voice: Show hand signs to camera, get text/speech")
    print("  2. Voice → ASL: Speak or type, see ASL fingerspelling")
    print()
    print("Starting application...")
    
    try:
        app = TwoWayTranslatorApp()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
