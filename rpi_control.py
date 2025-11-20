import time
import zmq
import socket
import threading
from picamera2 import Picamera2
import imagezmq
from gpiozero import AngularServo  # Using modern library from your first script

# --- CONFIGURATION ---
# Set your PC's IP address here (where the receiver is running)
PC_IP = "10.232.170.71"   

# --- GPIO setup ---
SERVO_PIN = 2  # This is BCM pin 2 (which is physical pin 3)

# Setup servo using gpiozero (from your first script)
# We calculate pulse widths from your second script's logic:
# 50Hz = 20ms period
# 2% duty cycle (angle 0) = 0.4ms
# 12% duty cycle (angle 180) = 2.4ms
servo = AngularServo(
    SERVO_PIN,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.4/1000,  # 0.4ms
    max_pulse_width=2.4/1000   # 2.4ms
)
servo.angle = 90  # Start at neutral (90 degrees)

# =====================
# SERVO CONTROL THREAD
# =====================
def servo_listener():
    """Receive angles from PC and move the servo."""
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind("tcp://*:5556")
    print("[RPI] Servo listener started on port 5556...")
    print("[RPI] Waiting for angles from PC...")

    def set_angle(angle):
        """Sets the servo angle, clamped between 0 and 180."""
        # Clamp angle to valid range
        angle = max(0, min(180, angle))
        servo.angle = angle
        print(f"[RPI] Angle: {angle:.1f}°   ", end="\r")

    try:
        while True:
            msg = socket.recv_string()
            try:
                angle = float(msg)
                set_angle(angle)
            except ValueError:
                print(f"\n[RPI] Invalid value received: {msg}")
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[RPI] Stopping servo...")
        servo.close()  # Cleanly shut down the servo
        socket.close()
        context.term()
        print("[RPI] Servo listener stopped.")

# =====================
# CAMERA STREAM THREAD
# =====================
def camera_sender():
    """Continuously send camera feed to PC."""
    sender = imagezmq.ImageSender(connect_to=f'tcp://{PC_IP}:5555')
    rpi_name = socket.gethostname()
    print(f"[RPI] Streaming camera feed as '{rpi_name}' to {PC_IP}:5555 ...")

    picam = Picamera2()
    picam.configure(picam.create_preview_configuration(main={"size": (640, 480)}))
    picam.start()
    time.sleep(2)  # Allow camera to warm up

    try:
        while True:
            # capture_array() returns an RGB numpy array
            frame = picam.capture_array()
            # Send the raw RGB frame; the PC client can handle conversion
            sender.send_image(rpi_name, frame)
    except Exception as e:
        # Catch exceptions if the main thread closes
        print(f"\n[RPI] Camera error: {e}")
    finally:
        print("\n[RPI] Stopping camera...")
        picam.stop()
        sender.close()
        print("[RPI] Camera streaming stopped.")

# =====================
# MAIN EXECUTION
# =====================
if __name__ == "__main__":
    print("[RPI] Starting ZMQ camera + servo system...")

    # Run camera in a separate, daemonic thread
    # It will exit automatically when the main thread (servo_listener) stops
    cam_thread = threading.Thread(target=camera_sender, daemon=True)
    cam_thread.start()

    # Run the servo listener in the main thread
    # This allows us to catch KeyboardInterrupt (Ctrl+C) properly
    servo_listener()

    print("[RPI] System shut down.")
