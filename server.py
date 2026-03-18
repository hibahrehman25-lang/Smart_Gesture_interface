import cv2
import time
import threading
import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import numpy as np
import pyautogui

from modules.hand_tracker import HandTracker
from modules.mouse_control import move_mouse
from modules.keyboard_control import type_key, Button, draw_keyboard

app = FastAPI()

# Configuration
W_WIDTH, W_HEIGHT = 1280, 720
active_modifiers = set()
debounce_time = 0.4
status_text = "System Initialized"
current_mode = "MENU" # MENU, KEYBOARD, MOUSE
last_click_time = 0
is_dragging = False
pinch_start_time = 0
prev_scroll_y = 0 
main_loop = None

# Keyboard Layout Configuration
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
    kb_y_start = (height - kb_height) // 2 + 50 
    kb_width = width - (2 * margin_x) - 100 
    
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

# Hand Tracking Logic State
class AIState:
    def __init__(self):
        self.running = True
        self.hand_data = {}
        self.status = "System Ready"
        self.active_modifiers = []
        self.volume = 0.5

ai_state = AIState()

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

def ai_engine():
    global last_click_time, status_text, current_mode, active_modifiers, is_dragging, pinch_start_time
    cap = None
    tracker = None
    kb_buttons = []

    while ai_state.running:
        if current_mode != "MENU":
            # Initialize Camera and Tracker if not already active
            if cap is None:
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, W_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, W_HEIGHT)
                tracker = HandTracker(max_hands=1, min_detection_confidence=0.7)
                kb_buttons = create_buttons(W_WIDTH, W_HEIGHT)
                status_text = f"Mode {current_mode} Active"

            success, img = cap.read()
            if not success: 
                time.sleep(0.1)
                continue
                
            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            
            img = tracker.find_hands(img)
            landmarks = tracker.get_landmarks()
            
            # Logic based on mode
            if current_mode == "KEYBOARD":
                img = draw_keyboard(img, kb_buttons)
                if landmarks:
                    h, w, _ = img.shape
                    # Landmarks: 4 (Thumb), 8 (Index)
                    x4, y4 = int(landmarks[4][0] * w), int(landmarks[4][1] * h)
                    x8, y8 = int(landmarks[8][0] * w), int(landmarks[8][1] * h)
                    dist_kb = ((x4 - x8)**2 + (y4 - y8)**2)**0.5
                    
                    # Visual feedback line
                    line_color = (0, 255, 0) if dist_kb < 40 else (0, 0, 255)
                    cv2.line(img, (x4, y4), (x8, y8), line_color, 3)
                    
                    for button in kb_buttons:
                        bx, by = button.pos
                        bw, bh = button.size
                        
                        # Set colors based on state (LEGACY Logic)
                        if button.text in ["SHIFT", "CTRL", "ALT", "WIN"] and button.text in active_modifiers:
                            button.color = (0, 165, 255) # Orange (BGR: 255,165,0 in RGB is 0,165,255 in BGR)
                        else:
                            button.color = (40, 40, 40) # Default Gray/Black

                        if bx < x8 < bx + bw and by < y8 < by + bh:
                            button.color = (80, 80, 80) # Hover
                            if dist_kb < 40 and time.time() - last_click_time > debounce_time:
                                button.color = (0, 255, 0) # Click Green
                                key = button.text
                                if key == "Q": 
                                    current_mode = "MENU"
                                    status_text = "Closed via Keyboard 'Q'"
                                elif key in ["SHIFT", "CTRL", "ALT", "WIN"]:
                                    if key in active_modifiers: active_modifiers.remove(key)
                                    else: active_modifiers.add(key)
                                else:
                                    type_key(key, modifiers=[m.lower() for m in active_modifiers])
                                    active_modifiers.clear()
                                status_text = f"Typed: {key}"
                                last_click_time = time.time()

            elif current_mode == "MOUSE":
                if landmarks:
                    h, w, _ = img.shape
                    # Landmarks: 4 (Thumb), 8 (Index), 12 (Middle)
                    x4, y4 = int(landmarks[4][0] * w), int(landmarks[4][1] * h)
                    x8, y8 = int(landmarks[8][0] * w), int(landmarks[8][1] * h)
                    x12, y12 = int(landmarks[12][0] * w), int(landmarks[12][1] * h)
                    
                    dist_li = ((x4 - x8)**2 + (y4 - y8)**2)**0.5 # Left Click / Drag (Thumb-Index)
                    dist_ri = ((x8 - x12)**2 + (y8 - y12)**2)**0.5 # Right Click / Scroll (Index-Middle)
                    
                    # 1. PRECISION MOVEMENT (Index Tip)
                    norm_x = (landmarks[8][0] - 0.2) / 0.6
                    norm_y = (landmarks[8][1] - 0.2) / 0.6
                    move_mouse(max(0, min(1, norm_x)), max(0, min(1, norm_y)))
                    cv2.circle(img, (x8, y8), 10, (0, 255, 255), cv2.FILLED)
                    
                    # 2. LEFT CLICK / DRAG (Thumb+Index)
                    if dist_li < 40:
                        if not is_dragging:
                            if pinch_start_time == 0:
                                pinch_start_time = time.time()
                            elif time.time() - pinch_start_time > 0.4:
                                pyautogui.mouseDown()
                                is_dragging = True
                                status_text = "DRAGGING..."
                        cv2.circle(img, (x4, y4), 20, (0, 255, 0), cv2.FILLED) # Green for action
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
                        
                    # 3. RIGHT CLICK / SCROLL (Index+Middle)
                    if dist_ri < 40:
                        cv2.circle(img, (x12, y12), 20, (0, 0, 255), cv2.FILLED) # Red for action
                        # Use y-movement for scrolling
                        if prev_scroll_y != 0:
                            scroll_delta = (y12 - prev_scroll_y)
                            if abs(scroll_delta) > 5:
                                # Sensitivity adjustment
                                pyautogui.scroll(-scroll_delta * 2) 
                                status_text = f"SCROLLING {'DOWN' if scroll_delta > 0 else 'UP'}"
                        
                        # To detect a Right Click tap, we could use a similar timer, 
                        # but "Two finger tap or hold" can mean simple pinch for tap.
                        # For now, let's treat quick pinch as Right Click if movement is small.
                        if prev_scroll_y == 0:
                            pyautogui.click(button='right')
                            status_text = "RIGHT CLICK"
                        
                        prev_scroll_y = y12
                    else:
                        prev_scroll_y = 0
            
            # LIVE STATUS OVERLAY ON VIDEO
            # Add semi-transparent background for text
            cv2.rectangle(img, (0, 0), (450, 70), (0, 0, 0), -1)
            cv2.putText(img, f"MODE: {current_mode}", (20, 30), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 2)
            cv2.putText(img, f"ACTION: {status_text}", (20, 60), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 255), 2)
            
            # SHOW WINDOW & STAY ON TOP (NORMAL for resizability)
            cv2.namedWindow("AI Control Stream", cv2.WINDOW_NORMAL)
            cv2.imshow("AI Control Stream", img)
            cv2.setWindowProperty("AI Control Stream", cv2.WND_PROP_TOPMOST, 1)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        else:
            # MENU MODE - Release Camera to turn off light
            if cap is not None:
                cap.release()
                cap = None
                cv2.destroyAllWindows()
                tracker = None
                status_text = "Menu Active - Camera Off"
            
        try:
            message = json.dumps({
                'type': 'status',
                'message': status_text,
                'mode': current_mode,
                'modifiers': list(active_modifiers)
            })
            if main_loop:
                asyncio.run_coroutine_threadsafe(manager.broadcast(message), main_loop)
        except:
            pass
        
        time.sleep(0.01)

    if cap is not None: cap.release()
    cv2.destroyAllWindows()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_mode
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg['type'] == 'mode_change':
                current_mode = msg['data']
    except WebSocketDisconnect:
        current_mode = "MENU"
        manager.disconnect(websocket)

# Start AI Engine in Background
# Startup logic
@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    thread = threading.Thread(target=ai_engine, daemon=True)
    thread.start()

# Mount Frontend Build AT THE END to prevent WebSocket conflict
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
