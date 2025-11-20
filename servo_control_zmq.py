import cv2
import mediapipe as mp
import numpy as np
import zmq
import time

# --- Configuration ---
RPI_IP = "10.232.170.146"  # <-- Double-check this is still your Raspberry Pi's IP
MODEL_PATH = "face_landmarker_v2_with_blendshapes.task" # <-- Make sure this file is in the same folder

# CHANGED: Reduced sensitivity.
# This value controls how much the servo turns relative to your head movement.
# A smaller value (e.g., 60) is less sensitive and smoother.
# A larger value (e.g., 150) is more sensitive and "twitchy".
angle_scale = 60
# ---------------------

# ZMQ setup
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(f"tcp://{RPI_IP}:5556")
print(f"[PC] Connecting to tcp://{RPI_IP}:5556")

# MediaPipe setup
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

try:
    base_options = BaseOptions(model_asset_path=MODEL_PATH)
    options = FaceLandmarkerOptions(base_options=base_options, num_faces=1)
    detector = FaceLandmarker.create_from_options(options)
except Exception as e:
    print(f"Error loading model '{MODEL_PATH}'.")
    print(f"Please make sure the file is in the same directory as the script.")
    print(f"Error: {e}")
    exit()

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

center_x = None  # Will be set on first frame or by pressing 'c'
w = int(cap.get(3)) # Get actual width (640)
h = int(cap.get(4)) # Get actual height (480)

print("[PC] Starting head tracking... Press 'c' to calibrate center, 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[PC] Error: Can't receive frame. Exiting...")
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    # Detect face landmarks
    result = detector.detect(mp_image)
    
    if result.face_landmarks:
        landmarks = result.face_landmarks[0]
        
        # Use nose tip (landmark index 1) as head position reference
        nose_x_normalized = landmarks[1].x
        nose_y_normalized = landmarks[1].y
        
        x_pixel = int(nose_x_normalized * w)
        y_pixel = int(nose_y_normalized * h)

        # Calibrate center_x on the first frame
        if center_x is None:
            center_x = x_pixel
            print(f"[PC] Calibrated center X to: {center_x}")

        # Calculate horizontal offset from center
        offset = x_pixel - center_x

        # Calculate servo angle
        # We divide offset by a portion of the screen width (w / 4)
        # to normalize the movement, then multiply by our sensitivity (angle_scale)
        angle_change = (offset / (w / 4)) * angle_scale
        servo_angle = 90 + int(angle_change) # Start from 90 (center)
        
        # Clamp the angle between 0 and 180
        servo_angle = max(0, min(180, servo_angle))

        # Send servo angle to Raspberry Pi
        try:
            socket.send_string(str(servo_angle), zmq.DONTWAIT)
            print(f"[PC] Nose: {x_pixel}, Offset: {offset}, Servo Angle: {servo_angle}   ", end='\r')
        except zmq.Again:
            # This can happen if the RPi is not connected or lagging
            print("[PC] Warning: Could not send data (RPi not ready?)")
            pass

        # Visualization
        cv2.circle(frame, (x_pixel, y_pixel), 5, (0, 0, 255), -1) # Red dot on nose
        cv2.line(frame, (center_x, 0), (center_x, h), (255, 255, 255), 1) # White center line
        cv2.putText(frame, f"Servo: {servo_angle}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Head Tracking (PC)", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("\n[PC] Quitting...")
        break
    elif key == ord('c'):
        center_x = None # Flag for recalibration on the next frame
        print("\n[PC] Recalibrating center position...")

cap.release()
cv2.destroyAllWindows()
socket.close()
context.term()