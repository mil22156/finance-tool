import os
from core.auth import hash_password, verify_password
from dotenv import load_dotenv
from database.db import init_registry, init_db, get_db
from flask import Flask, render_template, request, flash, redirect, session
import uuid

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

REGISTRY_PATH = os.path.join('data', 'registry.db')
os.makedirs("data", exist_ok=True)
init_registry(REGISTRY_PATH)

@app.route('/')
def index():
    return render_template('index.html')

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
        email = request.form.get('email') 
                
        # validate fields
        if not household_name or not email or not password or not username or not confirm_password:
            flash('All fields are required.', 'danger')
            return redirect('/household/new')
        
        # verify email format
        if '@' not in email or '.' not in email:
            flash('Invalid email format.', 'danger')
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
            'INSERT INTO users (username, email, password_hash, rights) VALUES (?, ?, ?, ?)', (username, email, hash_password(password), 'admin'))
        household_conn.commit()
        household_conn.close()
        
        # register household in the registry
        conn.execute('INSERT INTO households (name, database_path) VALUES (?, ?)', (household_name, db_path))
        conn.commit()
        conn.close()
                

        flash('Household created successfully. Please log in.', 'success')
        return redirect('/login')

    return render_template('household_new.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        household_id = request.form.get('household_id')
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate credentials (simplified for demonstration)
        if not username or not password or not household_id:
            flash('Username, password, and household are required.', 'danger')
            return redirect('/login')

        # Here you would typically check the credentials against the database
        # get the database path for the selected household
        conn = get_db(REGISTRY_PATH)
        household = conn.execute('SELECT database_path FROM households WHERE id = ?', (household_id,)).fetchone()
        conn.close()

        if not household:
            flash('Invalid household.', 'danger')
            return redirect('/login')

        # Check that the username is associated with the household and that the password is correct
        household_conn = get_db(household[0])
        user = household_conn.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,)).fetchone()
        household_conn.close()

        if not user or not verify_password(password, user[1]):
            flash('Invalid username, password, or household.', 'danger')
            return redirect('/login')

        # For demonstration purposes, we'll assume valid credentials
        session['user_id'] = user[0]
        session['household_db_path'] = household[0]


        flash('Login successful.', 'success')
        return redirect('/')

    else:
        # Fetch households for the dropdown
        conn = get_db(REGISTRY_PATH)
        households = conn.execute('SELECT id, name FROM households').fetchall()
        conn.close()
        return render_template('login.html', households=households)


#  if __name__ == '__main__': — Python sets a special variable called __name__ on every file it loads. When   
#  you run a file directly (e.g. python app.py), Python sets __name__ to '__main__'. When a file is imported
#  by another file, __name__ is set to the module name instead. So this condition is just asking "was this    
#  file run directly, or imported?" — and only starts the server in the direct-run case.

#  app.run(debug=True) — starts Flask's built-in development server. debug=True enables two things: automatic 
#  reloading when you save a file, and the interactive debugger in the browser if an error occurs.
                                                                                                             
#  You'd remove debug=True (or set it to False) before any real deployment — it exposes a debug console that  
#  would be a security risk on a public server.

if __name__ == '__main__':
    app.run(debug=True)

