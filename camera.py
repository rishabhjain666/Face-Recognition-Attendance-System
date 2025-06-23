import face_recognition
import numpy as np
import os
import cv2
from io import BytesIO
import pickle
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Cache file for known encodings
CACHE_FILE = 'known_faces.cache'

def load_known_faces(dataset_path='dataset'):
    """Load known faces from dataset directory with caching."""
    logging.debug(f"Loading known faces from {dataset_path}")
    if os.path.exists(CACHE_FILE):
        logging.debug(f"Loading cached encodings from {CACHE_FILE}")
        try:
            with open(CACHE_FILE, 'rb') as f:
                known_encodings, known_names = pickle.load(f)
            logging.debug(f"Loaded {len(known_encodings)} encodings from cache")
            return known_encodings, known_names
        except Exception as e:
            logging.error(f"Error loading cache: {str(e)}")
    
    known_encodings = []
    known_names = []
    
    os.makedirs(dataset_path, exist_ok=True)
    for file in os.listdir(dataset_path):
        if file.lower().endswith(('.jpg', '.png')):
            image_path = os.path.join(dataset_path, file).replace('\\', '/')
            logging.debug(f"Processing image: {image_path}")
            try:
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image, num_jitters=1)  # Reduced jitters
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(os.path.splitext(file)[0])
                    logging.debug(f"Added encoding for {os.path.splitext(file)[0]}")
                else:
                    logging.warning(f"No face found in {image_path}")
            except Exception as e:
                logging.error(f"Error processing {image_path}: {str(e)}")
                continue
    
    # Cache the encodings
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump((known_encodings, known_names), f)
        logging.debug(f"Cached {len(known_encodings)} encodings to {CACHE_FILE}")
    except Exception as e:
        logging.error(f"Error caching encodings: {str(e)}")
    
    return known_encodings, known_names

def recognize_faces_from_image(uploaded_image):
    """Recognize faces from uploaded image file."""
    try:
        logging.debug("Processing uploaded image for face recognition")
        # Read and resize image
        image_data = uploaded_image.read()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logging.error("Failed to decode image")
            return None
        
        # Resize image for faster processing (max width 480px)
        height, width = image.shape[:2]
        if width > 480:
            scale = 480 / width
            image = cv2.resize(image, (480, int(height * scale)), interpolation=cv2.INTER_AREA)
            logging.debug(f"Resized image to width {480}")
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        known_encodings, known_names = load_known_faces()
        
        # Find faces and their encodings with fewer jitters
        face_locations = face_recognition.face_locations(rgb_image, model='hog')  # Use HOG for speed
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations, num_jitters=1)
        logging.debug(f"Found {len(face_encodings)} faces in image")
        
        for encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.6)
            if True in matches:
                matched_idx = matches.index(True)
                logging.debug(f"Recognized face: {known_names[matched_idx]}")
                return known_names[matched_idx]
        
        logging.debug("No recognized faces")
        return None
    except Exception as e:
        logging.error(f"Error in face recognition: {str(e)}")
        return None