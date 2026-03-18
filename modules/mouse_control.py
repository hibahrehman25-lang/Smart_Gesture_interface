import pyautogui

pyautogui.FAILSAFE = False


def move_mouse(x, y):
    """
    Move the mouse based on normalized coordinates (0 to 1).
    x, y are normalized coordinates from hand detection.
    """
    screen_w, screen_h = pyautogui.size()
    # Safely calculate target coordinates
    target_x = int(x * screen_w)
    target_y = int(y * screen_h)
    
    # Constrain to screen boundaries
    mouse_x = max(10, min(screen_w - 10, target_x))
    mouse_y = max(10, min(screen_h - 10, target_y))

    pyautogui.moveTo(mouse_x, mouse_y)

