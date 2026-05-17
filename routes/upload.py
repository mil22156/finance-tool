from flask import Blueprint, render_template, request, flash, redirect, session
from werkzeug.utils import secure_filename
import os
from database.db import get_db, REGISTRY_PATH
import pandas as pd


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
        session['uploaded_file'] = file_path
        
        has_headers = 'has_headers' in request.form

        df = pd.read_csv(file_path, nrows=5, header=0 if has_headers else None  )  # Read only the first 5 rows for preview
        #AI note: this was a autocomplete suggestion
        headers = [str(col) for col in df.columns] if has_headers else [f'Column {i}' for i in range(len(df.columns))]
        sample_rows = df.values.tolist()

        return render_template('confirm.html', headers=headers, sample_rows=sample_rows)

    return render_template('upload.html')

@upload_bp.route('/upload/confirm', methods=['POST'])
def upload_confirm():
    # Get the uploaded file path from the session
    file_path = session.get('uploaded_file')
    if not file_path:
        flash('Session expired, please upload the file again.', 'danger')
        return redirect('/upload')

    # Read the mapping from the form AI Note. This was claudes suggestion for how to handle the mapping of columns. 
    mapping = {}
    for key, value in request.form.items():
        if key.startswith('mapping_'):
            column_index = int(key.split('_')[1])   
            mapping[column_index] = value
    
    #Validate the required columns were assigned
    if 'date' not in mapping.values() and 'transaction_date' not in mapping.values():
        flash('You must assign a date column.', 'danger')
        return redirect('/upload')
    if 'amount' not in mapping.values() and not ('debit' in mapping.values() or 'credit' in mapping.values()):
        flash('You must assign an amount column, or both a debit and credit column.', 'danger')
        return redirect('/upload')
    
    # Store the mapping in the session for use in the final processing step
    session['column_mapping'] = mapping

    # Process the file and mapping to prepare for database insertion
    return redirect('/upload')

    # Handle confirmation logic here
    # Column Validation (e.g., check that date column contains valid dates, amount column contains valid numbers)
@upload_bp.route('/upload/process', methods=['POST'])
def upload_process():
     # Get the uploaded file path and column mapping from the session
    file_path = session.get('uploaded_file')
    mapping = session.get('column_mapping')
    if not file_path or not mapping:
        flash('Session expired, please upload the file again.', 'danger')
        return redirect('/upload')  
    
    # Check that each record has a valid date
    df = pd.read_csv(file_path)  # Read the entire file for processing

    for column_index, column_type in mapping.items():
        if column_type in ['date', 'transaction_date', 'post_date']:            
            for row_num, value in enumerate(df.iloc[:, int(column_index)], start=2):  # Start at 2 to account for header row
                try:
                    pd.to_datetime(value)
                except ValueError:
                    flash(f'Invalid date at row {row_num} column "{column_index}";{value}', 'danger')
                    return redirect('/upload')
                

    # Check that each record has a valid amount (either in the amount column or in the debit/credit columns)
    for column_index, column_type in mapping.items():
        if column_type == 'amount':
            
            for row_num, value in enumerate(df.iloc[:, int(column_index)], start=2):
                try:
                    float(value)
                except ValueError:
                    flash(f'Invalid amount at row {row_num} column "{column_index}";{value}', 'danger')
                    return redirect('/upload')
        elif column_type in ['debit', 'credit']:
            
            for row_num, value in enumerate(df.iloc[:, int(column_index)], start=2):
                try:
                    float(value)
                except ValueError:
                    flash(f'Invalid {column_type} at row {row_num} column "{column_index}";{value}', 'danger')
                    return redirect('/upload')  


    # Transaction parsing logic (e.g., read the file, parse transactions, and prepare them for insertion into the database)
    # Database insertion logic 
           
