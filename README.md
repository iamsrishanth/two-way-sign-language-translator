# 🤟 Two-Way Sign Language Translator

A comprehensive application that enables two-way communication between American Sign Language (ASL) users and spoken language users.

## Features

### 🖐️ ASL → Voice (Sign to Speak)

- Real-time hand gesture recognition using webcam
- Converts ASL fingerspelling to text
- Text-to-speech output to speak recognized words
- Word suggestions with spell checking
- Supports all 26 letters of the alphabet

### 🎤 Voice → ASL (Speak to Sign)

- Voice recognition using Google Speech API
- Converts spoken words to ASL fingerspelling animations
- Text input option for manual entry
- Animated display of ASL hand signs for each letter
- Progress tracking during playback

## Prerequisites

- Python 3.9+ recommended
- Webcam for ASL recognition
- Microphone for voice input
- Internet connection for speech recognition

## Setup

1. **Clone or Download** the repository

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Two-Way Translator (Recommended)

The combined application with both modes:

```bash
python two_way_translator.py
```

**Features:**

- Switch between ASL→Voice and Voice→ASL modes using radio buttons
- Camera feed with hand tracking visualization
- Real-time letter recognition and sentence building
- Voice input with animated ASL output

### Individual Applications

#### ASL to Voice Only

```bash
python asl_to_voice.py
```

#### Voice to ASL Only

```bash
python voice_to_asl.py
```

#### Legacy GUI Application

```bash
python final_pred.py
```

## Usage Guide

### ASL → Voice Mode

1. Select "ASL → Voice (Sign to Speak)" mode
2. Position your hand in front of the webcam
3. Make ASL fingerspelling gestures
4. The recognized letters will build into words
5. Click "Speak" to hear the text spoken aloud
6. Use suggestion buttons for word completion

### Voice → ASL Mode

1. Select "Voice → ASL (Speak to Sign)" mode
2. Click "Start Listening" and speak clearly
3. Or type text in the input field and click "Convert"
4. Watch the animated ASL fingerspelling for each letter
5. Use Stop button to pause animation

## Requirements

Core dependencies (see `requirements.txt` for full list):

- TensorFlow 2.18.0
- OpenCV
- MediaPipe
- CVZone
- SpeechRecognition
- PyAudio
- Pillow
- pyttsx3
- pyenchant

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model Not Found | Ensure `cnn8grps_rad1_model.h5` is in the project directory |
| Webcam Issues | Check webcam connection and close other apps using it |
| PyAudio Error | On Windows: `pip install pipwin && pipwin install pyaudio` |
| Speech Recognition Fails | Check internet connection and microphone access |
| No Sound Output | Verify speakers/headphones and pyttsx3 installation |

## Project Structure

```
two-way-sign-language-translator/
├── two_way_translator.py    # Combined two-way translator
├── asl_to_voice.py          # ASL to Voice standalone
├── voice_to_asl.py          # Voice to ASL standalone
├── final_pred.py            # Original GUI application
├── prediction_wo_gui.py     # Headless prediction script
├── cnn8grps_rad1_model.h5   # Trained CNN model
├── requirements.txt         # Python dependencies
├── asl_images/              # Generated ASL images cache
└── AtoZ_3.1/                # Training data
```

## License

This project is for educational purposes.
