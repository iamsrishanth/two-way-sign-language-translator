# Running the Two-Way Sign Language Translator

## Prerequisites

- Python 3.9 is recommended (as per project requirements).
- A webcam is required for gesture recognition.

## Setup

1.  **Clone or Download** the repository.
2.  **Open a terminal** and navigate to the project directory.
3.  **Create a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # On Windows
    # source venv/bin/activate  # On macOS/Linux
    ```
4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

### GUI Application (Recommended)

To run the main application with the graphical user interface:

```bash
python final_pred.py
```

- Click "Speak" to convert text to speech.
- Click "Clear" to reset the text.

### Headless Prediction

To run the prediction script without the main GUI (opens cv2 windows):

```bash
python prediction_wo_gui.py
```

## Troubleshooting

- **Model Not Found**: Ensure `cnn8grps_rad1_model.h5` is in the same directory as the scripts.
- **Webcam Issues**: Ensure your webcam is connected and not used by another application.
