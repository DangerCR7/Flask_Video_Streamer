from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time

app = Flask(__name__)
camera = None
recording = False
out = None

def initialize_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)  # Reinitialize camera

def generate_frames():
    global camera, recording, out
    while True:
        if camera is None or not camera.isOpened():
            initialize_camera()  # Ensure camera is initialized

        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Save video if recording
            if recording and out is not None:
                out.write(frame)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace;boundary=frame')

@app.route('/start', methods=['POST'])
def start():
    global camera
    initialize_camera()
    return jsonify({"status": "started"})

# Capture Screenshot
@app.route('/capture', methods=['POST'])
def capture():
    success, frame = camera.read()
    if success:
        filename = f"static/screenshot_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)
        return jsonify({"status": "captured", "image_url": filename})
    return jsonify({"status": "failed"})

@app.route('/stop', methods=['POST'])
def stop():
    global camera
    if camera is not None and camera.isOpened():
        camera.release()
    return jsonify({"status": "stopped"})

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording, out
    if not recording:
        initialize_camera()  # Ensure camera is active
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter("static/recording.mp4", fourcc, 20.0, (640, 480))
        recording = True
    return jsonify({"status": "recording started"})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, out
    if recording:
        recording = False
        if out is not None:
            out.release()
            out = None
    return jsonify({"status": "recording stopped"})

if __name__ == "__main__":
    app.run(debug=True)
