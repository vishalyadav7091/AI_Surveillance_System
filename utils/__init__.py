import cv2
import numpy as np
from datetime import datetime

class MotionDetector:
    def __init__(self, min_area=500, sensitivity=25):
        self.min_area = min_area
        self.sensitivity = sensitivity
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.motion_detected = False
        
    def detect_motion(self, frame):
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return frame, False

        fg_mask = self.background_subtractor.apply(frame)
        fg_mask = cv2.threshold(fg_mask, self.sensitivity, 255, cv2.THRESH_BINARY)[1]
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue
            self.motion_detected = True
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Motion Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        status_text = "MOTION DETECTED" if self.motion_detected else "NO MOTION"
        color = (0, 255, 0) if self.motion_detected else (0, 0, 255)
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        return frame, self.motion_detected
    
    def reset_background(self):
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )
        self.motion_detected = False
        print("Background model reset")

