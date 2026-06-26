from flask import Blueprint, render_template, request, flash, redirect, session
from werkzeug.utils import secure_filename
import os
from database.db import get_db, REGISTRY_PATH
import pandas as pd
import hashlib
import uuid


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
        # AI note. I needed a lot of AI help on this file manipation logic.

        # clear all data from the staging_transactions table for this household before processing the new upload, to avoid confusion with any old data that may be in there from a previous upload that was not completed. We will repopulate the staging_transactions table with the new upload data after we process and normalize the new upload file.
        db = get_db(session['household_db_path'])
        db.execute('DELETE FROM staging_transactions')
        db.commit()
        db.close()

        # Validate that a file was provided in the request and that it has an allowed file extension
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
            
        
        # validate that an account was selected
        account_id = request.form.get('account_id')
        if not account_id:
            flash('No account selected', 'danger')
            return redirect('/upload')

        # column mapping logic (e.g., allow user to specify which columns correspond to date, description, amount)  
        session['uploaded_file'] = file_path
        session['account_id'] = account_id

                        
        has_headers = 'has_headers' in request.form

        df = pd.read_csv(file_path, nrows=5, header=0 if has_headers else None  )  # Read only the first 5 rows for preview
        #AI note: this was a autocomplete suggestion
        headers = [str(col) for col in df.columns] if has_headers else [f'Column {i}' for i in range(len(df.columns))]
        sample_rows = df.values.tolist()

        return render_template('confirm.html', headers=headers, sample_rows=sample_rows)

    else:
        db = get_db(session['household_db_path'])
        accounts = db.execute('SELECT id, name, institution FROM accounts').fetchall()
        db.close()
        return render_template('upload.html', accounts=accounts)
    
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
    return redirect('/upload/process')
    
@upload_bp.route('/upload/process', methods=['GET', 'POST'])
def upload_process():
     # Get the uploaded file path and column mapping from the session
    file_path = session.get('uploaded_file')
    mapping = session.get('column_mapping')
    account_id = session.get('account_id')  
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
            
            


    # AI suggested this. I would have probably done something more clunky: rename the columns in the dataframe based on the mapping provided by the user, so that we have consistent column names to work with for the rest of the processing steps. This will make it easier to handle the data in a standardized way regardless of how the user mapped their columns.
    df = df.rename(columns={df.columns[int(k)]: v for k, v in mapping.items()})
    
    # Normalize — clean up the data: convert amounts to signed floats (combine debit/credit if needed), parse dates to a consistent
    # format. rename category to api_category. 
    # drop ignored columns.
    df = df.drop(columns=['ignore'], errors='ignore')

    # Normalize the transaction amount columns by stripping any currency symbols or commas or spaces and converting to float
    for col in ['amount', 'debit', 'credit']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('[$, ]', '', regex=True)
            df[col] = pd.to_numeric(df[col])  # Convert to numeric


    # If there are separate debit and credit columns, combine them into a single amount column with positive values for credits and negative values for debits
    if 'debit' in df.columns and 'credit' in df.columns:
        df['amount'] = df.apply(lambda row: -row['debit'] if not pd.isna(row['debit']) else (row['credit'] if not pd.isna(row['credit']) else 0), axis=1)
        df = df.drop(columns=['debit', 'credit'])
    
    
    # Parse dates to a consistent format including time if available(e.g., ISO format)
    # If there is a "date" column, no further processing after formatting.
    # If there is not already a "date" column and there is a transaction_date then copy the transaction_date into the date column.
    # If there is no transaction_date but there is a post_date, copy the post_date into the date column. This way we have a consistent "date" column to work with for the rest of the processing, regardless of how the user mapped their columns.
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')  # Convert to datetime and format as string
    elif 'transaction_date' in df.columns:
        df['date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')
    elif 'post_date' in df.columns:
        df['date'] = pd.to_datetime(df['post_date']).dt.strftime('%Y-%m-%d')    
    if 'transaction_date' in df.columns:
        df = df.drop(columns=['transaction_date'])
    if 'post_date' in df.columns:
        df = df.drop(columns=['post_date'])
    
    # Rename category column to api_category to avoid confusion with the categories in our database
    if 'category' in df.columns:
        df = df.rename(columns={'category': 'api_category'})    
    
    # Deduplication logic (e.g., check if a transaction with the same date, description, and amount already exists in the database to avoid duplicates)
    
    # Create dedupe hashes for the upload transactions
    def make_dedup_hash(account_id, date, description, amount):
        value = f"{account_id}|{date}|{amount}|{description.strip().lower()}"
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    df['dedup_hash'] = df.apply(lambda row: make_dedup_hash(account_id, row['date'], row['description'], row['amount']), axis=1)

    # Check for duplicates in the database based on the dedup_hash
    db = get_db(session['household_db_path'])
    existing_hashes = set(row[0] for row in db.execute('SELECT dedup_hash FROM transactions').fetchall())
    db.close()
    df['is_duplicate'] = df['dedup_hash'].apply(lambda x: x in existing_hashes)

    # Remove duplicatesFor now we will just drop duplicates, but in the future we may want to keep them and allow the user to review and decide whether to keep or discard each potential duplicate.
    duplicate_count = df['is_duplicate'].sum()
    if duplicate_count > 0:
        flash(f'{duplicate_count} duplicate transactions were found and will be skipped.', 'warning')

    df = df[~df['is_duplicate']]

    # apply categories from the category rules table.
    # get the categorization_rules and look up each transaction description and write any 
    # matching categorization rule to the the suggested_category_id column
    # I got AI help for this. particularly the for loop. I would not have had something so dense
    db = get_db(session['household_db_path'])
    rules = dict(db.execute('''SELECT description_pattern, category_ID
                            FROM categorization_rules''').fetchall())
    db.close()
    for index, row in df.iterrows():
        df.at[index, 'suggested_category_id'] = rules.get(row['description'])



    # Drop the is_duplicate column before displaying the review page, since it's not needed for the user to see and may cause confusion.
    df = df.drop(columns=['is_duplicate'])

    # copy the df to the staging_transactions table before rendering the review page. This way we have a record of the uploaded transactions in the database and can use that for the review page and final commit to the transactions table after the user reviews and confirms.
    # We will need to add a household_id column to the staging_transactions table to associate the uploaded transactions with the correct household, since multiple users may be uploading transactions at the same time. We can get the household_id from the session since it's stored there when the user logs in.
    # AI Note: I got this code from Claude.
    session_id = uuid.uuid4().hex  # Generate a unique session ID for this upload
    session['upload_session_id'] = session_id  # Store the session ID in the session

    db = get_db(session['household_db_path'])
    db.execute('DELETE FROM staging_transactions')  # Clear any existing staging transactions for this session
    for _, row in df.iterrows():
        db.execute('''INSERT INTO staging_transactions 
            (session_id, account_id, date, amount, description, api_category, suggested_category_id, dedup_hash, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (session_id, account_id, row['date'], row['amount'], row['description'], 
             row.get('api_category'), row.get('suggested_category_id'), row['dedup_hash'], 'csv'))
    db.commit()
    db.close()

    # Show the user the data that will be imported before the user commits the data to the database
    session['duplicate_count'] = int(duplicate_count)
    return redirect('/upload/review')

# Review Route for the user to review the transactions that were uploaded before committing to the database. This allows the user to catch any potential issues with the data before it gets imported into the main transactions table.    
# staging_transactions table will be loaded to df to pass to the review.html template for display to the user. The user can then choose to confirm and commit the transactions to the main transactions table, or cancel and discard the uploaded transactions. We will identify the staging transactions for this upload based on the unique session_id that we generated and stored in the session when we processed the upload. This way we can ensure that each user's uploaded transactions are kept separate and there is no confusion between multiple users uploading at the same time.
@upload_bp.route('/upload/review', methods=['POST', 'GET'])
def upload_review():   
    if request.method == 'POST':
        # User confirmed the upload, so we will move the transactions from the staging_transactions table to the main transactions table and then clear the staging_transactions for this session.
        session_id = session.get('upload_session_id')
        if not session_id:
            flash('Session expired, please upload the file again.', 'danger')
            return redirect('/upload')
        db = get_db(session['household_db_path'])
        # Move transactions from staging to transaction
        result = db.execute('''INSERT INTO  transactions (account_id, date, amount, description, api_category, suggested_category_id, dedup_hash, source)
                            SELECT account_id, date, amount, description, api_category, suggested_category_id, dedup_hash, source
                            FROM staging_transactions
                            WHERE session_id = ?''', (session_id,))        
        db.execute('DELETE FROM staging_transactions WHERE session_id = ?', (session_id,))  # Clear the staging transactions for this session after committing to the main transactions table
        db.commit()
        db.close()        
        flash(f'{result.rowcount} transactions have been successfully uploaded.', 'success')
        return redirect('/transactions')  # Redirect to the transactions page after successful upload

    else:
        # User is just viewing the review page, so we will load the transactions from the staging_transactions table for this session and display them for review.
        # I had some AI assistance on the SQL
        session_id = session.get('upload_session_id')
        if not session_id:
            flash('Session expired, please upload the file again.', 'danger')
            return redirect('/upload')
        db = get_db(session['household_db_path'])
        df = pd.read_sql_query('''SELECT s.*, c.name AS suggested_category 
                               FROM staging_transactions s
                               LEFT JOIN categories c ON s.suggested_category_id = c.id
                               WHERE s.session_id = ?''', db, params=(session_id,))        
        db.close()
        df=df.drop(columns=['session_id', 'suggested_category_id', 'account_id', 'dedup_hash', 'source', 'import_date', 'statement_id', 'pending'])  # Drop columns that are not needed for the review display
        duplicate_count = session.get('duplicate_count', 0)
        return render_template('review.html', df=df, duplicate_count=duplicate_count)   
