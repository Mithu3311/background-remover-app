import os
import io
import requests
import shutil
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import base64
import uuid

app = Flask(__name__)
app.secret_key = 'background_remover_secret_key'

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
RESULT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# API key for remove.bg
API_KEY = "hAkcLnBa8jfuKZEmCzKPAVf5"

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Create symbolic links or copy directories for static access
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_FOLDER, exist_ok=True)

STATIC_UPLOADS = os.path.join(STATIC_FOLDER, 'uploads')
STATIC_RESULTS = os.path.join(STATIC_FOLDER, 'results')

# Create directories in static folder
os.makedirs(STATIC_UPLOADS, exist_ok=True)
os.makedirs(STATIC_RESULTS, exist_ok=True)

# Copy files from uploads and results to static folders
def copy_file_to_static(src_folder, dst_folder, filename):
    src_path = os.path.join(src_folder, filename)
    dst_path = os.path.join(dst_folder, filename)
    shutil.copy2(src_path, dst_path)
    return os.path.join(os.path.basename(dst_folder), filename)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['STATIC_UPLOADS'] = STATIC_UPLOADS
app.config['STATIC_RESULTS'] = STATIC_RESULTS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    # If user doesn't select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the uploaded file
        file.save(file_path)
        
        try:
            # Process the image (remove background)
            result_filename = process_image(file_path)
            
            # Copy files to static directory for serving
            copy_file_to_static(app.config['UPLOAD_FOLDER'], app.config['STATIC_UPLOADS'], filename)
            copy_file_to_static(app.config['RESULT_FOLDER'], app.config['STATIC_RESULTS'], result_filename)
            
            # Use forward slashes for URLs
            original_file = 'uploads/' + filename
            result_file = 'results/' + result_filename
            
            # Return the paths to the template
            return render_template('result.html', 
                                  original_file=original_file,
                                  result_file=result_file,
                                  result_filename=result_filename)
            
        except Exception as e:
            flash(f'Error processing image: {str(e)}')
            return redirect(url_for('index'))
    
    flash('File type not allowed')
    return redirect(url_for('index'))

def process_image(image_path):
    """Process the image using remove.bg API"""
    try:
        # Prepare the API request
        url = "https://api.remove.bg/v1.0/removebg"
        headers = {"X-Api-Key": API_KEY}
        
        with open(image_path, "rb") as image_file:
            files = {"image_file": image_file}
            
            # Make the API request
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                # Generate a unique filename for the result
                result_filename = f"{os.path.basename(image_path).split('_', 1)[0]}_result.png"
                result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
                
                # Save the processed image
                with open(result_path, 'wb') as f:
                    f.write(response.content)
                
                return result_filename
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Processing error: {str(e)}")

@app.route('/download/<filename>')
def download_file(filename):
    """Download the processed image"""
    return send_file(os.path.join(app.config['RESULT_FOLDER'], filename),
                     as_attachment=True)

@app.route('/api/remove-bg', methods=['POST'])
def api_remove_bg():
    """API endpoint for background removal"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the uploaded file
        file.save(file_path)
        
        try:
            # Process the image (remove background)
            result_filename = process_image(file_path)
            
            # Copy files to static directory for serving
            copy_file_to_static(app.config['UPLOAD_FOLDER'], app.config['STATIC_UPLOADS'], filename)
            copy_file_to_static(app.config['RESULT_FOLDER'], app.config['STATIC_RESULTS'], result_filename)
            
            # Return the download URL
            download_url = url_for('download_file', filename=result_filename, _external=True)
            
            return jsonify({
                'success': True,
                'download_url': download_url
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)