from flask import Blueprint, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
import os
from database.db import get_db, REGISTRY_PATH

upload_bp = Blueprint('upload', __name__)

# Define allowed file extensions for upload
ALLOWED_EXTENSIONS = {'csv', 'ofx', 'qfx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for handling file uploads
@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        #Handle file upload logic here
        # file-level validation (e.g., check file type, size, non-empty, OFX header check)
        # AI note. I needed a lot of AI help on this file manipation logic.

        if 'file' not in request.files:
            flash('No file provided', 'danger')
            return redirect('/upload')
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect('/upload')      
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)
        else:
            flash('Invalid file type. Only CSV and OFX files are allowed.', 'danger')
            return redirect('/upload') 
        

        
            
        # column mapping logic (e.g., allow user to specify which columns correspond to date, description, amount)  
        # Column Validation (e.g., check that date column contains valid dates, amount column contains valid numbers)   
        # Transaction parsing logic (e.g., read the file, parse transactions, and prepare them for insertion into the database)
        # Database insertion logic (e.g., insert parsed transactions into the appropriate household database)
        pass       
    return render_template('upload.html')