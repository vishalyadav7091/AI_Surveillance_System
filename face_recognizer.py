import face_recognition
import cv2
import os
import time
import numpy as np
from config.config import Config
from pkg_resources import resource_filename

class FaceRecognizer:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.is_trained = False
        self.load_model()

    def load_model(self):
        print("👤 Loading known faces...")
        self.known_face_encodings = []
        self.known_face_names = []
        self.is_trained = False

        try:
            if not os.path.exists(Config.FACE_DATA_PATH):
                print(f"⚠️ Directory not found: {Config.FACE_DATA_PATH}")
                return

            for person_name in os.listdir(Config.FACE_DATA_PATH):
                person_dir = os.path.join(Config.FACE_DATA_PATH, person_name)
                if os.path.isdir(person_dir):
                    for filename in os.listdir(person_dir):
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            image_path = os.path.join(person_dir, filename)
                            face_image = face_recognition.load_image_file(image_path)
                            if face_image is not None and face_image.size > 0:
                                encodings = face_recognition.face_encodings(face_image)
                                if encodings:
                                    self.known_face_encodings.append(encodings[0])
                                    self.known_face_names.append(person_name)
                                    self.is_trained = True

            if self.is_trained:
                print(f"✅ Known faces loaded: {list(set(self.known_face_names))}")
            else:
                print("⚠️ No faces found. Please collect samples.")

        except Exception as e:
            print(f"❌ Error loading faces: {e}")

    def recognize_faces(self, frame, tolerance=0.55):
        if not self.is_trained or frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return frame

        try:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, known_face_locations=face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance)
                name = "Unknown"

                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]

                top, right, bottom, left = [v * 4 for v in face_location]
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

        except Exception as e:
            print(f"❌ Error during face recognition: {e}")
            cv2.putText(frame, "Recognition Error", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return frame

    def collect_training_data(self, person_name, num_samples=50):
        cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("❌ Could not open camera for sample collection.")
            return

        sample_count = 0
        person_dir = os.path.join(Config.FACE_DATA_PATH, person_name)
        os.makedirs(person_dir, exist_ok=True)
        print(f"📸 Collecting {num_samples} face samples for {person_name}...")

        last_capture_time = time.time()

        while sample_count < num_samples:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                continue

            face_locations = face_recognition.face_locations(frame)

            if face_locations and (time.time() - last_capture_time > 0.5):
                top, right, bottom, left = face_locations[0]
                face_image = frame[top:bottom, left:right]
                if face_image.size > 0:
                    img_path = os.path.join(person_dir, f"{person_name}_{sample_count}.jpg")
                    cv2.imwrite(img_path, face_image)
                    sample_count += 1
                    last_capture_time = time.time()
                    print(f"  - Sample {sample_count}/{num_samples} captured")

            display_frame = frame.copy()
            if face_locations:
                top, right, bottom, left = face_locations[0]
                cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)

            cv2.putText(display_frame, f"Samples: {sample_count}/{num_samples}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press 'q' to stop", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow(f"Collecting Samples for {person_name}", display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print(f"✅ Finished collecting {sample_count} samples for {person_name}.")
        self.load_model()
