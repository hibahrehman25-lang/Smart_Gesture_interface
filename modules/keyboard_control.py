import pyautogui
import cv2
import numpy as np

class Button():
    def __init__(self, pos, text, size=[65, 65]): # Reduced default size for more keys
        self.pos = pos
        self.size = size
        self.text = text
        self.color = (60, 60, 60) # Darker gray default for better visibility
        self.text_color = (255, 255, 255)

def type_key(letter, modifiers=None):
    """Simulate pressing a key with optional modifiers."""
    if modifiers is None:
        modifiers = []

    # Mapping special display text to pyautogui keys
    key_map = {
        "SPACE": "space",
        "BACK": "backspace",
        "ENTER": "enter",
        "TAB": "tab",
        "CAPS": "capslock",
        "SHIFT": "shift",
        "CTRL": "ctrl",
        "ALT": "alt",
        "WIN": "win",
        "DEL": "delete",
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "HOME": "home",
        "END": "end",
        "PGUP": "pageup",
        "PGDN": "pagedown",
        "MENU": "menu",
        "~": "`",
    }

    key_to_press = key_map.get(letter.upper(), letter.lower() if len(letter) == 1 else letter)

    # Use hold() for multiple modifiers
    if modifiers:
        with pyautogui.hold(modifiers):
            pyautogui.press(key_to_press)
    else:
        pyautogui.press(key_to_press)

def draw_keyboard(img, buttonList):
    """Draw all buttons on the image with higher contrast."""
    imgNew = np.zeros_like(img, np.uint8)
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        # Draw button background
        cv2.rectangle(img, button.pos, (x + w, y + h), button.color, cv2.FILLED)
        # Draw border
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 255, 255), 2)
        
        # Calculate text position (roughly center)
        font_scale = 1.2 if len(button.text) > 1 else 2
        thickness = 2
        (tw, th), _ = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_PLAIN, font_scale, thickness)
        tx = x + (w - tw) // 2
        ty = y + (h + th) // 2
        
        cv2.putText(img, button.text, (tx, ty),
                    cv2.FONT_HERSHEY_PLAIN, font_scale, button.text_color, thickness)

    return img
