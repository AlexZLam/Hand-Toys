# Hand Gesture Control System 🎮🖐️

A hand gesture recognition system built with **OpenCV**, **MediaPipe**, and **PyAutoGUI**.  
Control your computer using intuitive hand gestures — including **volume control**, **media playback**, **mouse movement/clicks**, and **on‑screen visualization**.

---

## 📂 Project Structure

- **HandToysTxt.txt** → Main application script. Handles webcam input, gesture detection, and maps gestures to system actions (volume, media, mouse, etc.).
- **handTrackingModuleTxt.txt** → Custom hand tracking module built on MediaPipe. Provides helper functions to detect hands and extract landmark positions.

---

## ⚙️ Features

- **Hand Detection**: Detects left and right hands with landmarks using MediaPipe.  
- **Volume Control**: Adjusts system volume by measuring distance between thumb and index finger.  
- **Media Control**: Play/pause, next track, previous track based on hand gestures.  
- **Mouse Control**: Move cursor and perform left/right clicks with gestures.  
- **Lock/Unlock Controls**: Toggle media/volume control lock with pinky‑thumb gesture.  
- **Drawing & Visualization**: Draw landmarks, bounding boxes, extended lines, and hand center coordinates.  
- **On‑Screen Buttons**: Toggle features (Hand, Volume, Media, Draw, FPS, Lock, Mouse Move, Mouse Click) via clickable UI buttons.  
- **FPS Display**: Shows real‑time frames per second for performance monitoring.  

---

## 🛠️ Requirements

Install dependencies before running:

```bash
pip install opencv-python mediapipe numpy pyautogui pycaw keyboard
