import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

class HandTracker:
    def __init__(self, max_hands=1, min_detection_confidence=0.7):
        # Initialize HandLandmarker from the mediapipe tasks API
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_detection_confidence,
            running_mode=vision.RunningMode.VIDEO
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None
        
        # Connections between landmarks afor drawing the hand skeleton
        self.hand_connections = [
            (0, 1), (1, 2), (2, 3), (3, 4), # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8), # Index
            (5, 9), (9, 10), (10, 11), (11, 12), # Middle
            (9, 13), (13, 14), (14, 15), (15, 16), # Ring
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
        ]

    def find_hands(self, img):
        # Convert BGR image to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convert to Mediapipe Image Format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # Get frame timestamp in ms for VIDEO mode
        frame_timestamp_ms = int(time.time() * 1000)
        
        # Perform detection
        self.results = self.detector.detect_for_video(mp_image, frame_timestamp_ms)

        # Draw hand landmarks manually if found
        if self.results and self.results.hand_landmarks:
            for hand_landmarks in self.results.hand_landmarks:
                self.draw_landmarks(img, hand_landmarks)
        return img

    def draw_landmarks(self, img, hand_landmarks):
        h, w, _ = img.shape
        landmarks_px = []
        
        # Plot points
        for lm in hand_landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            landmarks_px.append((cx, cy))
            cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            
        # Draw lines connecting the landmarks
        for connection in self.hand_connections:
            pt1 = landmarks_px[connection[0]]
            pt2 = landmarks_px[connection[1]]
            cv2.line(img, pt1, pt2, (0, 255, 0), 2)

    def get_landmarks(self, hand_index=0):
        """Return normalized landmarks of the hand detected"""
        if self.results and self.results.hand_landmarks:
            if hand_index < len(self.results.hand_landmarks):
                hand = self.results.hand_landmarks[hand_index]
                # Each element is NormalizedLandmark with x, y, (and z if provided)
                return [(lm.x, lm.y, lm.z if hasattr(lm, 'z') else 0.0) for lm in hand]
        return []
