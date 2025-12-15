import cv2
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
 from _dlib_pybind11 import
import face_recognition
import numpy as np
from alert_manager import AlertManager
from utils.telegram_alert import TelegramAlert
from object_detector import ObjectDetector   # make sure file name matches

# ---------------- ALERT ----------------
alert = AlertManager(
    sender_email="yourmail@gmail.com",
    app_password="your_app_password"
)

tg = TelegramAlert("BOT_TOKEN", "CHAT_ID")


# ---------------- CONFIG ----------------
CAMERA_INDEX = 0
MIN_MOTION_AREA = 800
FACE_DATA_PATH = "faces"
os.makedirs(FACE_DATA_PATH, exist_ok=True)
# ---------------- CONFIG ----------------
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# ---------------- MAIN ----------------
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        print("❌ Camera not available")
        return

    detector = ObjectDetector(min_area=800)

    print("📹 Object detection started | Press Q to exit")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame, detected = detector.detect(frame)

        # Status text
        cv2.putText(
            frame,
            "OBJECT DETECTED" if detected else "NO OBJECT",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if detected else (0, 0, 255),
            2
        )

        # Timestamp
        cv2.putText(
            frame,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow("Object Detection (No YOLO)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🛑 Object detection stopped")


# ---------------- MOTION DETECTOR ----------------
class MotionDetector:
    def __init__(self):
        self.bg = cv2.createBackgroundSubtractorMOG2()

    def detect(self, frame):
        fg = self.bg.apply(frame)
        fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion = False
        for c in contours:
            if cv2.contourArea(c) < MIN_MOTION_AREA:
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


# ---------------- FACE RECOGNITION ----------------
class FaceRecognizer:
    def __init__(self):
        self.encodings = []
        self.names = []
        self.load_faces()

    def load_faces(self):
        self.encodings.clear()
        self.names.clear()

        for name in os.listdir(FACE_DATA_PATH):
            path = os.path.join(FACE_DATA_PATH, name)
            if not os.path.isdir(path):
                continue

            for img in os.listdir(path):
                image = face_recognition.load_image_file(os.path.join(path, img))
                enc = face_recognition.face_encodings(image)
                if enc:
                    self.encodings.append(enc[0])
                    self.names.append(name)

    def recognize(self, frame):
        small = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for (top,right,bottom,left), enc in zip(locations, encodings):
            name = "Unknown"
            matches = face_recognition.compare_faces(self.encodings, enc)
            if True in matches:
                name = self.names[matches.index(True)]

            top,right,bottom,left = top*4,right*4,bottom*4,left*4
            cv2.rectangle(frame,(left,top),(right,bottom),(255,0,0),2)
            cv2.putText(frame,name,(left,top-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,0,0),2)
        return frame

    def add_person(self, name, samples=20):
        cap = cv2.VideoCapture(CAMERA_INDEX)
        os.makedirs(os.path.join(FACE_DATA_PATH, name), exist_ok=True)

        count = 0
        while count < samples:
            ret, frame = cap.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb)

            for top,right,bottom,left in boxes:
                face = frame[top:bottom, left:right]
                cv2.imwrite(f"{FACE_DATA_PATH}/{name}/{count}.jpg", face)
                count += 1

            cv2.imshow("Collecting Faces", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.load_faces()

# ---------------- GUI APP ----------------
class SurveillanceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Surveillance")
        self.root.geometry("400x300")

        self.running = False
        self.cap = None

        self.motion = MotionDetector()
        self.face = FaceRecognizer()

        tk.Label(self.root, text="AI Surveillance System",
                 font=("Arial",18,"bold")).pack(pady=20)

        self.btn = tk.Button(self.root, text="Start",
                             font=("Arial",14),
                             command=self.toggle)
        self.btn.pack(pady=10)

        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack(pady=10)
        self.name_entry.insert(0, "Person Name")

        tk.Button(self.root, text="Add Person",
                  command=self.add_person).pack(pady=5)

    def toggle(self):
        if not self.running:
            self.running = True
            self.btn.config(text="Stop")
            self.cap = cv2.VideoCapture(CAMERA_INDEX)
            self.loop()
        else:
            self.running = False

    def loop(self):
        if not self.running:
            if self.cap:
                self.cap.release()
                cv2.destroyAllWindows()
            self.btn.config(text="Start")
            return

        ret, frame = self.cap.read()
        if ret:
            frame, motion = self.motion.detect(frame)
            frame = self.face.recognize(frame)

            cv2.putText(frame,
                        datetime.now().strftime("%H:%M:%S"),
                        (10, frame.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255,255,255), 2)

            cv2.imshow("Surveillance", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.running = False

        self.root.after(10, self.loop)  # <-- NO THREADING

    def add_person(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Enter person name")
            return
        self.face.add_person(name)

    def run(self):
        self.root.mainloop()

# ---------------- RUN ----------------
if __name__ == "__main__":
    SurveillanceApp().run()
