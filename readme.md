# 🧿 3rd Eye – Raspberry Pi Head-Tracking Assistive Camera

**DurHack 2025 – Assistive Technology & Robotics**

3rd Eye is an assistive-vision prototype designed to give visually impaired users a remote "second camera" that automatically follows their head movement. The system streams live video from a Raspberry Pi to a PC while using real-time face landmark tracking (Mediapipe) to rotate a servo-mounted camera.

Originally, the team aimed to use eye-gaze tracking, but due to time constraints and model limitations, we pivoted to a more robust nose-landmark head-tracking approach.

---

## 🎯 Motivation

Blind and visually-impaired people often struggle to explore their surroundings independently. **3rd Eye** acts as a remote controllable viewpoint:

- The Raspberry Pi camera acts as an **external vision device**
- Your **head movements** control where it looks
- The PC receives **live video + provides UI feedback**

This allows the user to scan and explore spaces that they cannot physically reach.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Face Tracking** | Mediapipe Face Landmarker v2 |
| **Communication** | ZeroMQ (PUSH/PULL), ImageZMQ |
| **Camera** | Raspberry Pi Camera Module (Picamera2) |
| **Servo Motor** | AngularServo (GPIOZero) |
| **UI / Display** | OpenCV on PC |
| **Language** | Python 3 (both PC + Raspberry Pi) |

> **Note:** No Node.js, web, or browser components were used in this implementation.

---

## ⚙️ System Overview

```
┌──────────────────────────┐
│      PC (Python)         │
│  ─ Head Tracking (MP)    │
│  ─ UI + Servo Angle Calc │
│  ─ Receives Pi Camera    │
└──────────┬───────────────┘
           │ ZMQ (angles)
           ▼
┌──────────────────────────┐
│    Raspberry Pi          │
│  ─ Camera Streaming      │
│  ─ Receives Servo Angles │
│  ─ Controls Servo Motor  │
└──────────────────────────┘
```

The Pi continuously streams frames → PC, while the PC continuously sends angles → Pi.

---

## 📁 Project Structure

```
DurhackX/
│
├── camera_servo_zmq.py                           # PC-side tracker + display
├── rpi_control.py                                # Pi-side camera + servo control
├── face_landmarker_v2_with_blendshapes.task      # Mediapipe model
└── README.md
```

---

## 🧠 How the Tracking Works

### 1. Real-Time Face Landmark Detection
Using **Mediapipe Tasks API**:
- Landmark #1 (nose tip) is extracted
- Nose horizontal position = head direction

### 2. Mapping Head Movement → Servo Angle
```python
offset = nose_x - calibrated_center
angle_change = (offset / (screen_width / 4)) * sensitivity
servo_angle = clamp(90 + angle_change)
```
This gives smooth left-right pan control from **0° → 180°**.

### 3. Sending the Angle to Raspberry Pi
- PC → ZMQ PUSH → Pi (port 5556)

### 4. Streaming Camera Feed Back to PC
- Pi → ImageZMQ → PC (port 5555)
- The received frame is shown in the corner of the PC UI.

---

## 🛠️ Requirements & Installation

### 🖥️ PC Setup

**Install dependencies:**
```bash
pip install opencv-python mediapipe numpy pyzmq imagezmq
```

**Place the Mediapipe model:**
- `face_landmarker_v2_with_blendshapes.task`

---

### 🍓 Raspberry Pi Setup

**Enable camera:**
```bash
sudo raspi-config
```

**Install dependencies:**
```bash
sudo apt update
sudo apt install python3-picamera2
pip install gpiozero pyzmq imagezmq numpy
```

---

## ▶️ How to Run

### 🚀 1. Start Raspberry Pi Controller

**Edit PC IP in `rpi_control.py`:**
```python
PC_IP = "your_pc_ip_here"
```

**Run:**
```bash
python3 rpi_control.py
```

This starts:
- Camera streaming
- Servo listener

---

### 🚀 2. Start PC Tracking System

**Edit RPi IP:**
```python
RPI_IP = "your_rpi_ip_here"
```

**Run:**
```bash
python3 camera_servo_zmq.py
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `c` | Recalibrate head center |
| `q` | Quit system |

---

## 🌟 What Was Planned (Eye Tracking)

The original idea was:
- Detect **pupil movement** → turn servo
- Track **gaze direction** → move camera

While this worked partially, gaze tracking was:
- ❌ Too noisy
- ❌ Required lighting calibration
- ❌ Hard to stabilize within the hackathon time

Thus the pivot to:
- ✔ Robust face landmark tracking
- ✔ Fast + stable
- ✔ Same user-intention (direction control)

---

## 📌 Results

- ✅ Real-time head-controlled camera movement
- ✅ Smooth servo panning with <50ms latency
- ✅ Seamless Pi → PC video streaming
- ✅ Robust performance even with partial occlusion

---

## 🧭 Future Enhancements

- [ ] Switch back to eye-gaze tracking when time allows
- [ ] Add object detection + audio feedback
- [ ] Pan–tilt dual-servo rig
- [ ] Battery-powered wearable version
- [ ] Mobile app + Bluetooth control

---

## 👥 Team

Built at **DurHack 2025** for the Assistive Technology & Robotics track.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- **Mediapipe** for face landmark detection
- **Google** for Gemini apis
- **Raspberry Pi Foundation** for hardware support
- **DurHack 2025** organizers and mentors
