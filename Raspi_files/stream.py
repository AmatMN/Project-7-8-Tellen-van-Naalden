import cv2
from flask import Flask, Response

from picamera2 import Picamera2
import numpy as np

import os
from datetime import datetime

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (1920, 1080)}))
picam2.set_controls({"AfMode": 2})
picam2.start()

SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)

app = Flask(__name__)

def generate_frames():
    while True:
        frame = picam2.capture_array()

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/capture')
def capture_image():
    frame = picam2.capture_array()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SAVE_DIR, f"capture_{timestamp}.jpg")
    cv2.imwrite(filename, frame)
    return "Image Captured!"

@app.route('/video')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def view_page():
    return '''
    <html>
    <head>
        <title>YOLOv11 Stream</title>
    </head>
    <body>
        <h2>Live Stream from Raspberry Pi</h2>
        <img src="/video" width="640" height="480"><br><br>
        <button onclick="fetch('/capture').then(() => alert('Image Captured!'));">Take Picture</button>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
