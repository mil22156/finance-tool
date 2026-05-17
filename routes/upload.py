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
    
    # Check that each record has a valid date. AI suggested using df.iloc and df.itterrows to loop through the rows and validate the date format. 
    # AI also suggested how to set up the error message
    df = pd.read_csv(file_path)  # Read the entire file for processing
    # Claude suggested how to get the column index for the date and description columns based on the mapping provided by the user. This allows us to validate the correct columns for dates and descriptions.
    date_col = next((int(k) for k, v in mapping.items() if v in ['date', 'transaction_date', 'post_date']), None    )
    desc_col = next((int(k) for k, v in mapping.items() if v == 'description'), None)

    for column_index, column_type in mapping.items():
        if column_type in ['date', 'transaction_date', 'post_date']:
            for row_num, row in df.iterrows():
                value = row.iloc[int(column_index)]  # Get the value from the date column
                try:
                    pd.to_datetime(value)  # Try to convert to datetime
                except ValueError:
                    col_name = df.columns[int(column_index)]
                    flash(f'Invalid date "{value}" in column "{col_name}" at row {row_num + 2}. '
                          f'Date: {row.iloc[date_col] if date_col is not None else "unknown"}, '
                          f'Description: {row.iloc[desc_col] if desc_col is not None else "unknown"}', 'danger')
                    return redirect('/upload')
                

    # Check that each record has a valid amount (either in the amount column or in the debit/credit columns)
    for column_index, column_type in mapping.items():
        if column_type in ['amount']:
            for row_num, row in df.iterrows():
                value = row.iloc[int(column_index)]  # Get the value from the amount column
                try:
                    float(value)  # Try to convert to float
                except ValueError:
                    col_name = df.columns[int(column_index)]
                    flash(f'Invalid amount "{value}" in column "{col_name}" at row {row_num + 2}. '
                          f'Date: {row.iloc[date_col] if date_col is not None else "unknown"}, '
                          f'Description: {row.iloc[desc_col] if desc_col is not None else "unknown"}', 'danger')
                    return redirect('/upload')
        elif column_type in ['debit', 'credit']:
            for row_num, row in df.iterrows():
                value = row.iloc[int(column_index)]  # Get the value from the debit/credit column
                if pd.isna(value):
                    continue  # Skip empty values, we'll check that at least one of debit/credit is filled in later
                try:
                    float(value)  # Try to convert to float
                except ValueError:
                    col_name = df.columns[int(column_index)]
                    flash(f'Invalid amount "{value}" in column "{col_name}" at row {row_num + 2}. '
                          f'Date: {row.iloc[date_col] if date_col is not None else "unknown"}, '
                          f'Description: {row.iloc[desc_col] if desc_col is not None else "unknown"}', 'danger')
                    return redirect('/upload')
            
            


    # rename the columns in the dataframe based on the mapping provided by the user, so that we have consistent column names to work with for the rest of the processing steps. This will make it easier to handle the data in a standardized way regardless of how the user mapped their columns.
    df = df.rename(columns={df.columns[int(k)]: v for k, v in mapping.items()})
    
    # Normalize — clean up the data: convert amounts to signed floats (combine debit/credit if needed), parse dates to a consistent
    # format, strip whitespace from descriptions

    # Deduplication logic (e.g., check if a transaction with the same date, description, and amount already exists in the database to avoid duplicates)

    # Categorization logic (e.g., use the description to suggest a category for the transaction, either through simple keyword matching or an AI model)

    # Review and confirmation step (e.g., show the user a preview of the parsed transactions with the assigned categories and allow them to make any necessary adjustments before finalizing the import)

    # Commit the transactions to the database after confirmation, ensuring that all necessary fields are populated and valid. This may involve inserting into multiple tables (e.g., transactions, categories) and handling any relationships between them.


           
