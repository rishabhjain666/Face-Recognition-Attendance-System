# Face Recognition Attendance System (Full Stack)

## 🔧 Features
- Face detection and recognition with OpenCV
- Flask web dashboard
- Add students with image
- Mark attendance using webcam
- View attendance records with timestamp

## 📁 Project Structure
- `app.py` – Flask server
- `camera.py` – Face recognition logic
- `database.py` – SQLite3 DB functions
- `templates/` – HTML files
- `static/` – CSS, images
- `dataset/` – Face image storage

## 🚀 How to Run
1. Install requirements: `pip install -r requirements.txt`
2. Run Flask app: `python app.py`
3. Go to `localhost:5000` in browser
4. Login with: **admin / admin**

## 📌 Notes
- Press `q` to exit webcam window
- You can add CSV export or email features easily
