import os
from flask import Flask, render_template, request, jsonify
import base64
import queue
import subprocess
import threading
from queue import Queue
import time
import cv2
from flask_socketio import SocketIO
from flask_cors import CORS
import numpy as np
import Create_Dataset
import Predict_cnnmodel, Predict_randomforest, Predict_svmmodel
import logging


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")


app.config['SECRET_KEY'] = 'secret_key'

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



dataset_thread = None

process = None
recognized_signs = []  # Define recognized_signs globally
recognized_signs_tracker = []



# Define the path where you want to store images locally
local_image_path = 'static\Dataset'  # Replace with your desired directory path


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/save_image', methods=['POST'])
def save_image():
    image_data = request.files['image_data'].read()
    hand = request.form['hand']
    letter = request.form['letter']

    # Create folder structure if it doesn't exist
    folder_path = os.path.join(local_image_path, hand, letter)
    os.makedirs(folder_path, exist_ok=True)

    # Generate a unique filename (e.g., timestamp) for each image
    image_filename = 'image_{}.jpeg'.format(len(os.listdir(folder_path)))

    # Save the image locally as JPEG
    local_image_filepath = os.path.join(folder_path, image_filename)
    with open(local_image_filepath, 'wb') as f:
        f.write(image_data)

    return jsonify({'message': 'Image saved successfully!', 'filename': image_filename})



processing_queue = queue.Queue()
keep_processing = False
processing_lock = threading.Lock()


@socketio.on('send_frame')
def send_frame(data):
    global keep_processing

    # Set keep_processing to True to start processing frames again
    keep_processing = True

    logger.info('Received data from client')

    # Extract frame_data and selectedModel from the received data
    frame_data = data.get('frameData')
    selected_model = data.get('selectedModel')

    nparr = np.frombuffer(base64.b64decode(frame_data.split(',')[1]), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if selected_model == 'RandomForest':
        threading.Thread(target=Predict_randomforest.process_frames_with_sign, args=(frame, socketio,), daemon=True).start()
    elif selected_model == 'CNN':
        num_landmarks = 21
        threading.Thread(target=Predict_cnnmodel.process_frames_with_sign_cnn, args=(frame, num_landmarks, socketio,), daemon=True).start()
    elif selected_model == 'SVM':
        threading.Thread(target=Predict_svmmodel.process_frames_with_sign_svm, args=(frame, socketio,), daemon=True).start()



@socketio.on('recognition_status_request')
def get_recognition_status(data):
    global recognized_signs_tracker
    logger.info('Received Recognition status request from client')
    selected_model = data.get('selectedModel', '')

    # Define a function to get ordered recognized signs and emit recognition status
    def get_ordered_sign_and_emit():
        ordered_sign = []

        if selected_model == 'RandomForest':
            ordered_sign = Predict_randomforest.get_ordered_recognized_sign()
        elif selected_model == 'CNN':
            ordered_sign = Predict_cnnmodel.get_ordered_recognized_signs_cnn()
        elif selected_model == 'SVM':
            ordered_sign = Predict_svmmodel.get_ordered_recognized_signs_svm()  

        if keep_processing:
            if ordered_sign is not None:
                emit_data = {"status": "Recognition in progress...", "ordered_sign": ordered_sign}
            else:
                emit_data = {"status": "No continuous sign detected.", "ordered_sign": None}
        else:
            emit_data = {"status": "Recognition stopped", "ordered_sign": None}

        # Start a new thread for emitting recognition status to the client
        threading.Thread(target=emit_recognition_status, args=(emit_data,), daemon=True).start()

    # Start a new thread for getting ordered signs and emitting recognition status
    threading.Thread(target=get_ordered_sign_and_emit, daemon=True).start()

def emit_recognition_status(emit_data):
    # Emit recognition status to the client
    socketio.emit('recognition_status', emit_data)
    logger.info('Sending Recognition status to client')


@socketio.on('stop_processing')
def stop_processing():
    global keep_processing, processing_lock, recognized_signs_tracker
    logger.info('Received Stop request from client')

    # Acquire the processing lock to prevent concurrent access to keep_processing flag
    with processing_lock:
        # Set keep_processing to False to stop further processing
        keep_processing = False

    # Clear the recognized signs tracker and reset other relevant data
    recognized_signs_tracker.clear()
    Predict_randomforest.reset_data()  # Reset data for random forest
    Predict_cnnmodel.reset_data()  # Reset data for cnn
    Predict_svmmodel.reset_data()  # Reset data for svm

    # Emit a message to indicate that processing has been stopped
    socketio.emit('recognition_status', {"status": "Recognition stopped", "ordered_sign": None})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

