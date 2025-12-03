import cv2
import time
import numpy as np
import handtrackingModule as htm
import math
import pyautogui
from pycaw.pycaw import AudioUtilities
import keyboard as key

# ------------------ CONFIG ------------------
wCam, hCam = 960, 540
screen_w, screen_h = pyautogui.size()

ENABLE_HAND_DETECTION = True
ENABLE_VOLUME_CONTROL = False
ENABLE_MEDIA_CONTROL = False
ENABLE_DRAWING = False
ENABLE_FPS_DISPLAY = True
ENABLE_LOCK_MEDIA = False
ENABLE_MOUSE_MOVE = False
ENABLE_MOUSE_CLICK = False
ENABLE_HAND_CENTER = True
ENABLE_COORD_DISPLAY = True
ENABLE_NORMAL_DISPLAY = True
ENABLE_VOLUME_Display = True


# ------------------ SETUP ------------------
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
moveCnt = 0
mouse_held = False
mouse_held_R = False
isLocked = 0
last_action_time = 0  

detector = htm.handDetector()

device = AudioUtilities.GetSpeakers()
volume = device.EndpointVolume
volume.SetMasterVolumeLevelScalar(0.5, None)  # start at 50%

#pyautogui.FAILSAFE = False

mTimer = 0

# ------------------ FUNCTIONS ------------------
def get_frame():
    success, img = cap.read()
    return cv2.flip(img, 1) if success else None

def detect_hands(img):
    if ENABLE_HAND_DETECTION:
        img = detector.findHands(img)
        hands = detector.findPositions(img, draw=False)  # returns list of dicts
        return img, hands
    return img, []

def draw_landmarks(img, x1, y1, x2, y2, cx, cy):
    if ENABLE_DRAWING:
        cv2.circle(img, (x1,y1), 7, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2,y2), 7, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1,y1), (x2,y2), (255,0,0), 2)
        cv2.circle(img, (cx,cy), 7, (255, 0, 255), cv2.FILLED)

def control_volume(length):
    if ENABLE_VOLUME_CONTROL:
        volScalar = np.interp(length, [10, 100], [0.0, 1.0])
        volume.SetMasterVolumeLevelScalar(volScalar, None)
        print("Volume scalar:", volScalar)
        return volScalar

def control_media(medLength, dx):
    global last_action_time

    if ENABLE_MEDIA_CONTROL:
        now = time.time()

        # Play/Pause when middle finger close to wrist
        if medLength < 50 and now - last_action_time > 0.5:
            key.send('play/pause media')
            last_action_time = now
            print("Play/Pause triggered")

        # Hand moved right → Next track
        if dx < -75 and now - last_action_time > 1:   # 1 second cooldown
            key.send('next track')
            last_action_time = now
            print("Next track triggered")

        # Hand moved left → Previous track
        if dx > 75 and now - last_action_time > 1:    # 1 second cooldown
            key.send('previous track')
            last_action_time = now
            print("Previous track triggered")


def display_fps(img, pTime):
    if ENABLE_FPS_DISPLAY:
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        cv2.putText(img, f'FPS: {int(fps)}', (20,30), cv2.FONT_HERSHEY_COMPLEX,
                    0.5, (0,0,255), 2)
        return cTime
    return time.time()

def displayCenterCoord(img, x, y):
    if ENABLE_COORD_DISPLAY:
        cv2.putText(img, f'X: {int(x)} Y: {int(y)}', (20,50), cv2.FONT_HERSHEY_COMPLEX,
                    0.5, (0,0,255), 2)

def displayVolume(img, volScalar):
    if ENABLE_VOLUME_Display and volScalar != None:
        cv2.putText(img, f'Volume: {round(volScalar, 2)}', (20,70), cv2.FONT_HERSHEY_COMPLEX,
                    0.5, (0,0,255), 2)

def lockMedia(lockLength):
    global isLocked, ENABLE_MEDIA_CONTROL, ENABLE_VOLUME_CONTROL
    if ENABLE_LOCK_MEDIA and lockLength < 15:
        if isLocked == 1:
            ENABLE_MEDIA_CONTROL = True
            ENABLE_VOLUME_CONTROL = True
            isLocked = 0
            print("Unlocked media/volume control")
            time.sleep(0.2)
        else:
            ENABLE_MEDIA_CONTROL = False
            ENABLE_VOLUME_CONTROL = False
            isLocked = 1
            print("Locked media/volume control")
            time.sleep(0.2)

def control_mouse_move(cx, cy):
    if ENABLE_MOUSE_MOVE:
        # Scale camera coords to full screen
        screen_x = (cx / (wCam / 2)) * screen_w
        screen_y = (cy / (hCam / 2)) * screen_h

        global prev_mouse_x, prev_mouse_y

        if prev_mouse_x is None or prev_mouse_y is None:
            prev_mouse_x, prev_mouse_y = screen_x, screen_y
            pyautogui.moveTo(screen_x, screen_y, duration=0.05)
            return

        dx = abs(screen_x - prev_mouse_x)
        dy = abs(screen_y - prev_mouse_y)

        threshold = 30
        if dx > threshold or dy > threshold:
            pyautogui.moveTo(screen_x, screen_y, duration=0.05)
            prev_mouse_x, prev_mouse_y = screen_x, screen_y
    

def control_mouse_click(length, cx, cy):
    global mouse_held

    if ENABLE_MOUSE_CLICK:
        if length < 35 and not mouse_held:
            pyautogui.mouseDown()  # press and hold
            mouse_held = True
            print("Mouse held down")
        elif length >= 35 and mouse_held:
            pyautogui.mouseUp()  # release
            mouse_held = False
            print("Mouse released")

        cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

def control_mouse_click_R(length, cx, cy):
    global mouse_held_R

    if ENABLE_MOUSE_CLICK:
        if length < 35 and not mouse_held_R:
            pyautogui.rightClick()  # press and hold
            mouse_held_R = True
            print("Mouse held down")
        elif length >= 35 and mouse_held_R:
            pyautogui.mouseUp()  # release
            mouse_held_R = False
            print("Mouse released")

        cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

def getHandCenter(points, img=None, draw=ENABLE_DRAWING, color = [255,255,0], medLength = []):
    if not points:
        return None, None

    # Compute average
    avgX = sum([p[0] for p in points]) // len(points)
    avgY = sum([p[1] for p in points]) // len(points)

    # Draw if requested
    if ENABLE_DRAWING and ENABLE_HAND_CENTER and img is not None:
        cv2.circle(img, (avgX, avgY), 10, (color), cv2.FILLED)
        cv2.line(img, (avgX, avgY), (screen_w, avgY), (255,0,0), 2)
        cv2.line(img, (avgX, avgY), (avgX,screen_h), (255,0,0), 2)
        cv2.line(img, (avgX, avgY), (avgX,0), (255,0,0), 2)
        cv2.line(img, (avgX, avgY), (0,avgY), (255,0,0), 2)
    return avgX, avgY

def draw_extended_line(img, start, through, color=(0,255,0), thickness=5, scale=5):
    h, w, _ = img.shape
    x1, y1 = start
    x2, y2 = through

    dx = x2 - x1
    dy = y2 - y1

    # distance between center and through point
    dist = math.hypot(dx, dy)

    # scale line length based on distance
    extend_len = int(dist * scale)

    # normalize direction vector
    if dist == 0:
        return  # avoid division by zero
    ux, uy = dx / dist, dy / dist

    # compute end point
    pt_end = (int(x1 + ux * extend_len), int(y1 + uy * extend_len))

    # clip to image boundaries
    pt_end = (max(0, min(w, pt_end[0])), max(0, min(h, pt_end[1])))

    if ENABLE_DRAWING:
        cv2.line(img, start, pt_end, color, thickness)

    return pt_end

def handBox(img, lmList, color=(0, 255, 255), thickness=2, padding=20):
    if lmList and len(lmList) > 0:
        # Extract all x and y coordinates from landmarks
        x_vals = [pt[1] for pt in lmList]
        y_vals = [pt[2] for pt in lmList]

        # Compute bounding box with padding
        x_min, x_max = min(x_vals) - padding, max(x_vals) + padding
        y_min, y_max = min(y_vals) - padding, max(y_vals) + padding

        # Draw rectangle
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, thickness)

        # Optionally return box coordinates
        return (x_min, y_min, x_max, y_max)
    return None

   


# ------------------ BUTTONS ------------------
button_flags = {
    "Hand": "ENABLE_HAND_DETECTION",
    "Volume": "ENABLE_VOLUME_CONTROL",
    "Media": "ENABLE_MEDIA_CONTROL",
    "Draw": "ENABLE_DRAWING",
    "FPS": "ENABLE_FPS_DISPLAY",
    "Lock": "ENABLE_LOCK_MEDIA",
    "MouseM": "ENABLE_MOUSE_MOVE",
    "MouseC": "ENABLE_MOUSE_CLICK"
}



button_positions = {}
button_height = 40
button_width = 75
spacing = 10

def draw_buttons(img):
    h, w, _ = img.shape
    y1 = h - button_height - 10
    y2 = h - 10
    x = 10
    button_positions.clear()

    for label, varname in button_flags.items():
        x1, x2 = x, x + button_width
        active = globals()[varname]
        color = (180, 180, 180) if active else (255, 255, 255)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 2)
        #state_text = "ON" if active else "OFF"
        cv2.putText(img, f"{label}", (x1+5, y1+25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
        button_positions[label] = (x1, y1, x2, y2)
        x += button_width + spacing

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        for label, (x1, y1, x2, y2) in button_positions.items():
            if x1 < x < x2 and y1 < y < y2:
                varname = button_flags[label]
                globals()[varname] = not globals()[varname]
                print(f"{label} toggled -> {globals()[varname]}")


# ------------------ MAIN LOOP ------------------
cv2.namedWindow('Img')
cv2.setMouseCallback('Img', mouse_callback)
# Track previous positions per hand
prev_positions = {"Left": None, "Right": None}

# Track previous mouse position for thresholding
prev_mouse_x, prev_mouse_y = None, None


while True:
    img = get_frame()
    if img is None:
        continue

    img, hands = detect_hands(img)

    for hand in hands:
        lmList = hand['lmList']
        handType = hand['type']  # 'Left' or 'Right'

        if len(lmList) == 0:
            continue

        # Landmarks
        x1,y1 = lmList[4][1],  lmList[4][2]    # thumb tip
        x2,y2 = lmList[8][1],  lmList[8][2]    # index tip
        x3,y3 = lmList[16][1], lmList[16][2]   # ring tip
        x4,y4 = lmList[12][1], lmList[12][2]   # middle tip
        x5,y5 = lmList[20][1], lmList[20][2]   # pinky tip

        x0,y0   = lmList[0][1],  lmList[0][2]   # wrist
        x01,y01 = lmList[5][1],  lmList[5][2]   # index base
        x02,y02 = lmList[9][1],  lmList[9][2]   # middle base
        x03,y03 = lmList[13][1], lmList[13][2]  # ring base
        x04,y04 = lmList[17][1], lmList[17][2]  # pinky base

        # Center based on wrist + bases
        base_points = [(x0,y0), (x01,y01), (x02,y02), (x03,y03), (x04,y04)]
        avgX, avgY = getHandCenter(base_points, img, color=[0,255,0])

        cx, cy = (x1+x2)//2, (y1+y2)//2
        cRx, cRy = (x1+x4)//2, (y1+y4)//2
        draw_landmarks(img, x1, y1, x2, y2, cx, cy)

        # Movement (per hand)
        if prev_positions[handType] is not None and avgX is not None:
            dx = avgX - prev_positions[handType][0]
        else:
            dx = 0

        prev_positions[handType] = (avgX, avgY)


        center = (avgX, avgY) if avgX is not None else (x0, y0)
        mid_thumb_index = (cx, cy)
        #ptEnd = draw_extended_line(img, center, mid_thumb_index, [150,255,0], 20, 6)

        volLength  = math.hypot(x2 - x1, y2 - y1)
        rightClckLength = math.hypot(x4-x1,y4-y1)
        medLength  = math.hypot(x4 - x0, y4 - y0)
        lockLength = math.hypot(x5 - x1, y5 - y1)
        box = handBox(img, lmList, color=(0,255,255), thickness=2, padding=10 )
        if box:
            x_min, y_min, x_max, y_max = box

        # Map actions by hand type
        if handType == 'Left':
            vol = control_volume(volLength)
            displayVolume(img, vol)
            control_media(medLength, dx)      # if you want media tied to left
            displayCenterCoord(img, avgX, avgY)
            lockMedia(lockLength)
            control_mouse_move(x2, y2)
            cv2.putText(img, 'Left', (center[0],y_max), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0,0,255), 2)
            control_mouse_click(volLength, cx, cy)
            control_mouse_click_R(rightClckLength, cRx, cRy)
        elif handType == 'Right':
            
            control_mouse_click(volLength, cx, cy)
            control_mouse_click_R(rightClckLength, cRx, cRy)
            displayCenterCoord(img, avgX, avgY)
            cv2.putText(img, 'Right', (center[0],y_max), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0,0,255), 2)

        
        

    pTime = display_fps(img, pTime)
    draw_buttons(img)
    cv2.imshow('Img', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
