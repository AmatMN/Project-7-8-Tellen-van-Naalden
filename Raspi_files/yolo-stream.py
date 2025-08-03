import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from picamera2 import Picamera2
import time
import uvicorn
from ultralytics import YOLO 
from collections import defaultdict
import threading

counts_lock = threading.Lock()
latest_counts = {}

# Load YOLOv8 model
model = YOLO("needles-yv8n.pt")

CLASS_NAMES = ["BV75-4", "C-1", "CT-1", "CT-1 plus", "CTX", "CV-3", "CV-5", "FS-2", "MH plus", "P-3", "UR-6"]

latest_counts.clear()

picam2 = None

def initialize_camera():
    global picam2
    if picam2 is None:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)}))
        picam2.set_controls({"AfMode": 2})
        picam2.start()

# Settings
INFERENCE_SKIP_FRAMES = 4
CONF_THRESH = 0.4
frame_count = 0
last_results = ([], [], [], 0)

def detect_objects(frame):
    start_time = time.time()

    # Run YOLOv8 detection
    results = model(frame)[0]

    boxes, scores, class_ids = [], [], []
    for box in results.boxes:
        if box.conf >= CONF_THRESH:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w = x2 - x1
            h = y2 - y1
            boxes.append([x1, y1, w, h])
            scores.append(float(box.conf))
            class_ids.append(int(box.cls))

    frame_counts = defaultdict(int)
    for cls_id in class_ids:
        frame_counts[cls_id] += 1

    with counts_lock:
        latest_counts.clear()
        latest_counts.update(frame_counts)

    duration_ms = int((time.time() - start_time) * 1000)
    return boxes, scores, class_ids, duration_ms

def draw_boxes(frame, boxes, scores, class_ids, duration_ms):
    for box, score, cls_id in zip(boxes, scores, class_ids):
        x, y, w, h = box
        label = f"{CLASS_NAMES[cls_id]}: {score:.2f}"
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.putText(frame, label, (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    duration_label = f"Inference: {duration_ms}ms"
    cv2.putText(frame, duration_label, (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    return frame

def generate_frames():
    global frame_count, last_results
    initialize_camera()  # <-- Ensure camera is started
    while True:
        frame = picam2.capture_array()
        frame_count += 1

        if frame_count % INFERENCE_SKIP_FRAMES == 0:
            boxes, scores, class_ids, duration_ms = detect_objects(frame)
            last_results = (boxes, scores, class_ids, duration_ms)
        else:
            boxes, scores, class_ids, duration_ms = last_results

        annotated = draw_boxes(frame.copy(), boxes, scores, class_ids, duration_ms)
        _, jpeg = cv2.imencode('.jpg', annotated)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

# FastAPI app
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
    <head><title>Needle Detector</title></head>
    <body>
        <h2>YOLOv8 Needle Detection Stream</h2>
        <img src="/video" width="960" height="1080">
    </body>
    </html>
    """

@app.get("/video")
def video():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/counts", response_class=HTMLResponse)
def counts():
    with counts_lock:
        table_rows = ""
        for cls_id, name in enumerate(CLASS_NAMES):
            count = latest_counts.get(cls_id, 0)
            table_rows += f"<tr><td>{name}</td><td>{count}</td></tr>"

    return f"""
    <html>
    <head>
        <title>Needle Counts</title>
        <meta http-equiv="refresh" content="1">
        <style>
            table {{
                border-collapse: collapse;
                width: 300px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <h2>Detected Needle Counts</h2>
        <table>
            <tr><th>Needle Type</th><th>Count</th></tr>
            {table_rows}
        </table>
        <p>Auto-refresh every 1 seconds</p>
        <p><a href="/">Back to stream</a></p>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("🚀 FastAPI server running at http://localhost:8000")
    uvicorn.run("yolo-stream:app", host="0.0.0.0", port=8000)
