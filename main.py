import cv2 
import time
import numpy as np
import pyautogui
from modules.hand_tracker import HandTracker
from modules.mouse_control import move_mouse
from modules.keyboard_control import type_key, Button, draw_keyboard
from utils.drawing_utils import draw_text

# Initialize webcam
cap = cv2.VideoCapture(0)

# Set resolution
W_WIDTH, W_HEIGHT = 1280, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, W_HEIGHT)

cv2.namedWindow("AI Control", cv2.WND_PROP_FULLSCREEN)
cv2.resizeWindow("AI Control", W_WIDTH, W_HEIGHT)
cv2.setWindowProperty("AI Control", cv2.WND_PROP_TOPMOST, 1)

# Initialize hand tracker
tracker = HandTracker(max_hands=1, min_detection_confidence=0.7)

# Define Keyboard Layout
keys_layout = [
    [("~", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("BACK", 2)],
    [("TAB", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("]", 1), ("\\", 1.5)],
    [("CAPS", 2), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1), ("ENTER", 2)],
    [("SHIFT", 2.5), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("UP", 1), ("SHIFT", 1.5)],
    [("CTRL", 1.5), ("WIN", 1.5), ("ALT", 1.5), ("SPACE", 5), ("ALT", 1.5), ("LEFT", 1), ("DOWN", 1), ("RIGHT", 1), ("DEL", 1.5)]
]

def create_buttons(width, height):
    buttonList = []
    margin_x = 100 
    kb_height = int(height * 0.45) 
    kb_y_start = (height - kb_height) // 2 + 50 # Centered with room for status
    kb_width = width - (2 * margin_x) - 100 # Room for volume slider
    
    row_height = kb_height // len(keys_layout)
    for i, row in enumerate(keys_layout):
        total_weight = sum(item[1] for item in row)
        unit_width = kb_width / total_weight
        current_x = margin_x
        for key_text, weight in row:
            key_width = int(unit_width * weight) - 10
            pos = [current_x, kb_y_start + i * row_height]
            size = [key_width, row_height - 10]
            buttonList.append(Button(pos, key_text, size=size))
            current_x += int(unit_width * weight)
    return buttonList

buttonList = create_buttons(W_WIDTH, W_HEIGHT)

# Interaction Variables
active_modifiers = set()
last_click_time = 0
debounce_time = 0.4 
status_text = "Stabilizing AI Suite..."
pinch_start_time = 0
is_dragging = False
prev_scroll_y = 0

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    
    # 1. UI DECORATIONS (Workspaces)
    # Mouse Workspace (Top)
    cv2.rectangle(img, (100, 70), (w-100, 200), (50, 50, 50), 2)
    cv2.putText(img, "MOUSE PAD", (110, 95), cv2.FONT_HERSHEY_PLAIN, 1.5, (150, 150, 150), 2)

    img = tracker.find_hands(img)
    img = draw_keyboard(img, buttonList)

    landmarks = tracker.get_landmarks()
    if landmarks:
        # Landmarks: 4 (Thumb), 8 (Index), 20 (Pinky)
        x4, y4 = int(landmarks[4][0] * w), int(landmarks[4][1] * h)
        x8, y8 = int(landmarks[8][0] * w), int(landmarks[8][1] * h)
        x20, y20 = int(landmarks[20][0] * w), int(landmarks[20][1] * h)

        # 2. MOUSE CONTROL (Workspace: y < 220)
        if 100 < x4 < w-100 and 70 < y4 < 200: # Inside Mouse Pad
            # Landmarks: 4 (Thumb), 8 (Index), 12 (Middle)
            x12, y12 = int(landmarks[12][0] * w), int(landmarks[12][1] * h)
            
            dist_li = ((x4 - x8)**2 + (y4 - y8)**2)**0.5 # Left Click / Drag (Thumb-Index)
            dist_ri = ((x8 - x12)**2 + (y8 - y12)**2)**0.5 # Right Click / Scroll (Index-Middle)

            # Normalized Mouse Pad Coords
            rel_x = (landmarks[8][0] * w - 100) / (w - 200)
            rel_y = (landmarks[8][1] * h - 70) / 130
            move_mouse(max(0, min(1, rel_x)), max(0, min(1, rel_y)))
            cv2.circle(img, (x8, y8), 15, (255, 255, 0), cv2.FILLED)
            
            # LEFT CLICK / DRAG (Thumb+Index)
            if dist_li < 40:
                if not is_dragging:
                    if pinch_start_time == 0:
                        pinch_start_time = time.time()
                    elif time.time() - pinch_start_time > 0.4:
                        pyautogui.mouseDown()
                        is_dragging = True
                        status_text = "DRAGGING..."
                cv2.circle(img, (x4, y4), 20, (0, 255, 0), cv2.FILLED)
            else:
                if is_dragging:
                    pyautogui.mouseUp()
                    is_dragging = False
                    status_text = "DROPPED"
                elif pinch_start_time != 0:
                    if time.time() - pinch_start_time < 0.4:
                        pyautogui.click()
                        status_text = "LEFT CLICK"
                pinch_start_time = 0

            # RIGHT CLICK / SCROLL (Index+Middle)
            if dist_ri < 40:
                cv2.circle(img, (x12, y12), 20, (0, 0, 255), cv2.FILLED)
                if prev_scroll_y != 0:
                    scroll_delta = (y12 - prev_scroll_y)
                    if abs(scroll_delta) > 5:
                        pyautogui.scroll(-scroll_delta * 2)
                        status_text = f"SCROLLING {'DOWN' if scroll_delta > 0 else 'UP'}"
                if prev_scroll_y == 0:
                    pyautogui.click(button='right')
                    status_text = "RIGHT CLICK"
                prev_scroll_y = y12
            else:
                prev_scroll_y = 0

        # 4. KEYBOARD CONTROL (Standard Logic)
        else:
            dist_kb = ((x4 - x8)**2 + (y4 - y8)**2)**0.5 # Thumb-Index keyboard pinch
            line_color = (0, 255, 0) if dist_kb < 40 else (0, 0, 255)
            cv2.line(img, (x4, y4), (x8, y8), line_color, 3)

            for button in buttonList:
                bx, by = button.pos
                bw, bh = button.size
                
                if button.text in ["SHIFT", "CTRL", "ALT", "WIN"] and button.text in active_modifiers:
                    button.color = (0, 165, 255)
                else: button.color = (40, 40, 40)

                if bx < x8 < bx + bw and by < y8 < by + bh:
                    button.color = (80, 80, 80)
                    if dist_kb < 40 and time.time() - last_click_time > debounce_time:
                        button.color = (0, 255, 0)
                        key = button.text
                        status_text = f"'{key}' Typed"
                        if key == "Q": # Virtual Exit
                            status_text = "Exiting Application..."
                            # Break the outer loop
                            cap.release()
                            cv2.destroyAllWindows()
                            exit() 
                        
                        if key in ["SHIFT", "CTRL", "ALT", "WIN"]:
                            if key in active_modifiers: active_modifiers.remove(key)
                            else: active_modifiers.add(key)
                        else:
                            type_key(key, modifiers=[m.lower() for m in active_modifiers])
                            active_modifiers.clear()
                        last_click_time = time.time()

    # Status Bar
    cv2.rectangle(img, (0, 0), (w, 60), (30, 30, 30), cv2.FILLED)
    cv2.line(img, (0, 60), (w, 60), (80, 80, 80), 2)
    display_msg = status_text if not active_modifiers else f"MULTI-KEY MODE ON: [{'+'.join(active_modifiers)}] Active. Press next key..."
    draw_text(img, display_msg, 30, 40)
    
    # LIVE STATUS OVERLAY (Duplicate for standalone)
    cv2.rectangle(img, (0, 60), (450, 130), (0, 0, 0), -1)
    cv2.putText(img, f"ACTION: {status_text}", (20, 100), 
                cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 255), 2)
    
    cv2.imshow("AI Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
