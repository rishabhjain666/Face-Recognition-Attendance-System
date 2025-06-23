from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, Response
import os
import shutil
import logging
import csv
import base64
from io import StringIO, BytesIO
from database import init_db, add_student, get_students, mark_attendance, get_attendance, clear_all_data, get_connection
from camera import recognize_faces_from_image, load_known_faces

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.jinja_env.filters['basename'] = os.path.basename  # Add basename filter
init_db()
load_known_faces()  # Preload known faces at startup

@app.route('/')
def home():
    """Render the login page."""
    logging.debug("Rendering login page")
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login requests."""
    username = request.form.get('username')
    password = request.form.get('password')
    logging.debug(f"Login attempt: username={username}")
    if username == 'admin' and password == 'admin':
        logging.info("Login successful")
        return redirect(url_for('dashboard'))
    logging.warning("Invalid login credentials")
    return render_template('login.html', error="Invalid credentials")

@app.route('/dashboard')
def dashboard():
    """Render the dashboard."""
    logging.debug("Rendering dashboard")
    return render_template('dashboard.html')

@app.route('/students')
def students():
    """Render the student list page."""
    conn = get_connection()
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT name, image_path FROM students")
            students = [{'name': row['name'], 'image_path': row['image_path'].replace('\\', '/')} for row in c.fetchall()]
            logging.debug(f"Students fetched: {students}")
    finally:
        conn.close()
    return render_template('students.html', students=students)

@app.route('/dataset/<filename>')
def serve_image(filename):
    """Serve images from the dataset folder."""
    file_path = os.path.join('dataset', filename).replace('\\', '/')
    logging.debug(f"Attempting to serve image: {file_path}")
    if os.path.exists(file_path):
        logging.debug(f"Serving file: {file_path}")
        return send_file(file_path)
    logging.error(f"File not found: {file_path}")
    return jsonify({'error': 'File not found'}), 404

@app.route('/add_student', methods=['POST'])
def add_student_route():
    """Add a new student with their image."""
    try:
        name = request.form.get('name')
        image = request.files.get('image')
        image_data = request.form.get('image_data')  # For live capture
        
        if not name:
            logging.warning("Missing name in add_student")
            return jsonify({'success': False, 'message': 'Name is required'})
        
        # Validate name (alphanumeric, spaces, underscores)
        if not all(c.isalnum() or c in ' _' for c in name):
            logging.warning(f"Invalid name: {name}")
            return jsonify({'success': False, 'message': 'Name must contain only letters, numbers, spaces, or underscores'})
        
        os.makedirs('dataset', exist_ok=True)
        filename = name.replace(" ", "_") + ".jpg"
        path = os.path.join('dataset', filename).replace('\\', '/')
        
        if image:
            # Handle uploaded image
            if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                logging.warning(f"Invalid image format: {image.filename}")
                return jsonify({'success': False, 'message': 'Image must be JPG or PNG'})
            image.save(path)
        elif image_data:
            # Handle live captured image (base64)
            if not image_data.startswith('data:image'):
                logging.warning("Invalid base64 image data")
                return jsonify({'success': False, 'message': 'Invalid image data'})
            image_data = image_data.split(',')[1]
            with open(path, 'wb') as f:
                f.write(base64.b64decode(image_data))
        else:
            logging.warning("No image provided in add_student")
            return jsonify({'success': False, 'message': 'Image is required'})
            
        add_student(name, path)
        logging.debug(f"Added student: {name}, path: {path}")
        # Clear cache to reload new face
        if os.path.exists('known_faces.cache'):
            os.remove('known_faces.cache')
        return jsonify({'success': True, 'message': 'Student added successfully'})
    except Exception as e:
        logging.error(f"Error adding student: {str(e)}")
        return jsonify({'success': False, 'message': f'Error adding student: {str(e)}'})

@app.route('/edit_student/<name>', methods=['POST'])
def edit_student(name):
    """Edit a student's name."""
    try:
        new_name = request.form.get('new_name')
        if not new_name:
            logging.warning("Missing new name in edit_student")
            return jsonify({'success': False, 'message': 'New name is required'})
        
        if not all(c.isalnum() or c in ' _' for c in new_name):
            logging.warning(f"Invalid new name: {new_name}")
            return jsonify({'success': False, 'message': 'New name must contain only letters, numbers, spaces, or underscores'})
        
        conn = get_connection()
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT image_path FROM students WHERE name = ?", (name,))
                row = c.fetchone()
                if not row:
                    logging.warning(f"Student not found: {name}")
                    return jsonify({'success': False, 'message': 'Student not found'})
                
                old_path = row['image_path'].replace('\\', '/')
                new_filename = new_name.replace(" ", "_") + ".jpg"
                new_path = os.path.join('dataset', new_filename).replace('\\', '/')
                
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                else:
                    logging.warning(f"Image file not found: {old_path}")
                
                c.execute("UPDATE students SET name = ?, image_path = ? WHERE name = ?", (new_name, new_path, name))
                logging.debug(f"Edited student: {name} to {new_name}, new path: {new_path}")
        finally:
            conn.close()
        
        if os.path.exists('known_faces.cache'):
            os.remove('known_faces.cache')
        return jsonify({'success': True, 'message': 'Student updated'})
    except Exception as e:
        logging.error(f"Error editing student: {str(e)}")
        return jsonify({'success': False, 'message': f'Error editing student: {str(e)}'})

@app.route('/delete_student/<name>', methods=['POST'])
def delete_student(name):
    """Delete a student and their image."""
    try:
        conn = get_connection()
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT image_path FROM students WHERE name = ?", (name,))
                row = c.fetchone()
                if not row:
                    logging.warning(f"Student not found: {name}")
                    return jsonify({'success': False, 'message': 'Student not found'})
                
                image_path = row['image_path'].replace('\\', '/')
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logging.debug(f"Deleted image: {image_path}")
                
                c.execute("DELETE FROM students WHERE name = ?", (name,))
                c.execute("DELETE FROM attendance WHERE name = ?", (name,))
                logging.debug(f"Deleted student: {name}")
        finally:
            conn.close()
        
        if os.path.exists('known_faces.cache'):
            os.remove('known_faces.cache')
        return jsonify({'success': True, 'message': 'Student deleted'})
    except Exception as e:
        logging.error(f"Error deleting student: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting student: {str(e)}'})

@app.route('/mark_attendance')
def mark_attendance_page():
    """Render the mark attendance page."""
    logging.debug("Rendering mark attendance page")
    return render_template('mark_attendance.html')

@app.route('/mark', methods=['POST'])
def mark():
    """Mark attendance using uploaded image."""
    try:
        if 'image' not in request.files:
            logging.warning("No image uploaded in mark")
            return jsonify({'success': False, 'message': 'No file uploaded'})
            
        img_file = request.files['image']
        name = recognize_faces_from_image(img_file)
        
        if name:
            mark_attendance([name])
            logging.debug(f"Attendance marked for: {name}")
            return jsonify({'success': True, 'message': f'Attendance marked for {name}'})
        else:
            logging.debug("Face not recognized")
            return jsonify({'success': False, 'message': 'Face not recognized'})
    except Exception as e:
        logging.error(f"Error marking attendance: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'})

@app.route('/attendance')
def attendance():
    """Render attendance records page."""
    logging.debug("Rendering attendance page")
    records = get_attendance()
    return render_template('view_attendance.html', records=records)

@app.route('/export_attendance')
def export_attendance():
    """Export attendance records as CSV."""
    try:
        records = get_attendance()
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Name', 'Timestamp'])
        cw.writerows(records)
        output = si.getvalue()
        logging.debug("Exported attendance as CSV")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=attendance.csv"}
        )
    except Exception as e:
        logging.error(f"Error exporting attendance: {str(e)}")
        return jsonify({'error': f'Error exporting attendance: {str(e)}'}), 500

@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear all data from database and dataset."""
    try:
        clear_all_data()
        if os.path.exists('dataset'):
            shutil.rmtree('dataset')
        if os.path.exists('known_faces.cache'):
            os.remove('known_faces.cache')
        logging.debug("All data cleared successfully")
        return jsonify({'success': True, 'message': 'All data cleared'})
    except Exception as e:
        logging.error(f"Error clearing data: {str(e)}")
        return jsonify({'success': False, 'message': f'Error clearing data: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)