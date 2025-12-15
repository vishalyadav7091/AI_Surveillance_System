import cv2
import numpy as np
from datetime import datetime

class MotionDetector:
    def __init__(self, min_area=600, sensitivity=25):
        self.min_area = min_area
        self.sensitivity = sensitivity
        self.bg = cv2.createBackgroundSubtractorMOG2(
            history=400, varThreshold=16, detectShadows=False
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    def detect(self, frame):
        if frame is None or frame.size == 0:
            return frame, False

        mask = self.bg.apply(frame)
        mask = cv2.threshold(mask, self.sensitivity, 255, cv2.THRESH_BINARY)[1]
        mask = cv2.dilate(mask, self.kernel, iterations=2)

        motion = False
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            if cv2.contourArea(c) < self.min_area:
                continue
            motion = True
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.putText(frame,
                    "MOTION" if motion else "NO MOTION",
                    (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0) if motion else (0,0,255),
                    2)
        return frame, motion

    def reset(self):
        self.bg = cv2.createBackgroundSubtractorMOG2()
        print("Background reset")
