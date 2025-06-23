console.log('script.js loaded');

let stream = null;
let currentStudentName = null;

// Show Toast Notification
function showToast(message, type = 'success') {
    console.log(`Showing toast: ${message}, type: ${type}`);
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
}

// Image Source Modal
function openImageSourceModal() {
    console.log('Opening image source modal');
    const modal = document.getElementById('image-source-modal');
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error('Image source modal not found');
    }
}

function closeImageSourceModal() {
    console.log('Closing image source modal');
    const modal = document.getElementById('image-source-modal');
    if (modal) {
        modal.style.display = 'none';
        stopCamera();
    }
}

function triggerFileInput() {
    console.log('Triggering file input');
    const fileInput = document.getElementById('image');
    if (fileInput) {
        fileInput.click();
        closeImageSourceModal();
    } else {
        console.error('File input not found');
    }
}

async function openCameraModal() {
    console.log('Opening camera modal');
    const cameraModal = document.getElementById('camera-modal');
    if (cameraModal) {
        cameraModal.style.display = 'block';
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.getElementById('video');
            if (video) {
                video.srcObject = stream;
                console.log('Camera stream started');
            } else {
                console.error('Video element not found');
            }
        } catch (err) {
            console.error('Error accessing camera:', err);
            showToast('Unable to access camera. Please allow camera permissions.', 'error');
        }
    } else {
        console.error('Camera modal not found');
    }
}

function captureImage() {
    console.log('Capturing image');
    const video = document.getElementById('video');
    if (!video) {
        console.error('Video element not found');
        return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg');
    const imageDataInput = document.getElementById('image_data');
    if (imageDataInput) {
        imageDataInput.value = imageData;
        console.log('Image captured and set to image_data');
    }
    stopCamera();
    closeImageSourceModal();
    showToast('Image captured successfully', 'success');
}

function stopCamera() {
    console.log('Stopping camera');
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
        console.log('Camera stream stopped');
    }
    const cameraModal = document.getElementById('camera-modal');
    if (cameraModal) {
        cameraModal.style.display = 'none';
    }
}

// Clear Data Modal
function openClearDataModal() {
    console.log('Opening clear data modal');
    const modal = document.getElementById('clear-data-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeClearDataModal() {
    console.log('Closing clear data modal');
    const modal = document.getElementById('clear-data-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function clearData() {
    console.log('Clearing all data');
    try {
        const response = await fetch('/clear_data', { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            showToast('All data cleared successfully', 'success');
            window.location.reload();
        } else {
            showToast(result.message, 'error');
        }
    } catch (err) {
        console.error('Error clearing data:', err);
        showToast('Error clearing data: ' + err.message, 'error');
    }
    closeClearDataModal();
}

// Edit Student Modal
function openEditModal(name) {
    console.log('Opening edit modal for:', name);
    currentStudentName = name;
    const form = document.getElementById('edit-student-form');
    if (form) {
        form.action = `/edit_student/${name}`;
        document.getElementById('new_name').value = name;
        document.getElementById('edit-student-modal').style.display = 'flex';
    }
}

function closeEditModal() {
    console.log('Closing edit modal');
    document.getElementById('edit-student-modal').style.display = 'none';
}

// Delete Student Modal
function openDeleteModal(name) {
    console.log('Opening delete modal for:', name);
    currentStudentName = name;
    document.getElementById('delete-student-modal').style.display = 'flex';
}

function closeDeleteModal() {
    console.log('Closing delete modal');
    document.getElementById('delete-student-modal').style.display = 'none';
}

async function deleteStudent() {
    console.log('Deleting student:', currentStudentName);
    try {
        const response = await fetch(`/delete_student/${currentStudentName}`, { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            showToast('Student deleted successfully', 'success');
            window.location.reload();
        } else {
            showToast(result.message, 'error');
        }
    } catch (err) {
        console.error('Error deleting student:', err);
        showToast('Error deleting student: ' + err.message, 'error');
    }
    closeDeleteModal();
}

// Camera for Mark Attendance
async function startCamera() {
    console.log('Starting camera for mark attendance');
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById('video');
        if (video) {
            video.srcObject = stream;
            console.log('Camera stream started for mark attendance');
        } else {
            console.error('Video element not found');
        }
    } catch (err) {
        console.error('Error accessing camera:', err);
        showToast('Unable to access camera. Please allow camera permissions.', 'error');
    }
}

async function captureAttendance() {
    console.log('Capturing attendance');
    const video = document.getElementById('video');
    if (!video) {
        console.error('Video element not found');
        return;
    }
    const spinner = document.getElementById('capture-spinner');
    if (spinner) spinner.style.display = 'inline-block';

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
    const formData = new FormData();
    formData.append('image', blob, 'capture.jpg');
    try {
        const response = await fetch('/mark', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        console.log('Attendance capture result:', result);
        if (spinner) spinner.style.display = 'none';
        if (result.success) {
            showToast(result.message, 'success');
            window.location.href = '/attendance';
        } else {
            showToast(result.message, 'error');
            window.location.reload();
        }
    } catch (err) {
        console.error('Error marking attendance:', err);
        if (spinner) spinner.style.display = 'none';
        showToast('Error marking attendance: ' + err.message, 'error');
        window.location.reload();
    }
    stopCamera();
}

// Initialize camera on mark attendance page
if (window.location.pathname === '/mark_attendance') {
    console.log('Initializing camera for mark attendance page');
    startCamera();
}