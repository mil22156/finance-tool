import os
from core.auth import hash_password
from dotenv import load_dotenv
from database.db import init_registry, init_db, get_db
from flask import Flask, render_template, request, flash, redirect, session
import uuid

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

REGISTRY_PATH = os.path.join('data', 'registry.db')
init_registry(REGISTRY_PATH)

@app.route('/')
def index():
    return 'Finance Tool is running.'

# Household creation route
@app.route('/household/new', methods=['GET', 'POST'])
def household_new():
    if request.method == 'POST':
        # get form fields: name, creation code, username, password, confirm password
        household_name = request.form.get('household_name')

        # validate creation code
        creation_code = request.form.get('creation_code')
        if creation_code != os.getenv('CREATION_CODE'):
            flash('Invalid creation code.', 'danger')
            return redirect('/household/new')

        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
                
        # validate fields
        if not household_name or not password or not username or not confirm_password:
            flash('All fields are required.', 'danger')
            return redirect('/household/new')
        
        # verify password length
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect('/household/new')

        # validate password match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect('/household/new')

        # validate household name uniqueness
        conn= get_db(REGISTRY_PATH)
        existing = conn.execute('SELECT id FROM households WHERE name = ?', (household_name,)).fetchone()
        if existing:
            flash('Household name already exists. Please choose a different name.', 'danger')
            conn.close()
            return redirect('/household/new')
        
        # Creation block
        # generate a unigue household ID
        household_id = uuid.uuid4().hex

        # define household database path
        db_path = os.path.join('data', household_id, f'{household_id}.db')

        # create household database
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        init_db(db_path)

        # insert admin user into the household database
        household_conn = get_db(db_path)
        household_conn.execute(
            'INSERT INTO users (username, password_hash, rights) VALUES (?, ?, ?)', (username, hash_password(password), 'admin'))
        household_conn.commit()
        household_conn.close()
        
        # register household in the registry
        conn.execute('INSERT INTO households (name, database_path) VALUES (?, ?)', (household_name, db_path))
        conn.commit()
        conn.close()
                

        flash('Household created successfully. Please log in.', 'success')
        return redirect('/login')

    return render_template('household_new.html')

if __name__ == '__main__':
    app.run(debug=True)

