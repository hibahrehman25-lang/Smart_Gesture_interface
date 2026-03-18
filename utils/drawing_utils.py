import cv2

def draw_text(img, text, x, y):
    cv2.putText(img, text, (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

