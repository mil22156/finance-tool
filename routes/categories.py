from flask import Blueprint, render_template, request, flash, redirect, session
import os
from database.db import get_db, REGISTRY_PATH

categories_bp = Blueprint('categories', __name__)

# Categories blueprint to handle all category related routes
# Routes include /categories, /categories/new, /categories/edit
# Categories/delete
# Route to add to the categorization rules

# Populate the database with the default categories if they don't exist. This will be called when the user first creates a household. It will check if the categories table is empty and if so it will populate it with the default categories. This is a one time operation per household and will not be called on every login or page load.
def populate_default_categories(household_db_path):
    conn = get_db(household_db_path)
    existing_categories = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    if existing_categories == 0:
        default_categories = [
            ('SHOPPING', None),
            ('GROCERIES', None),
            ('RESTAURANTS', None),
            ('TRAVEL', None),
            ('WORK EXPENSES', None),
            ('ENTERTAINMENT', None),
            ('ALCOHOL', None),
            ('UTILITIES', None),
            ('CHARITY', None),
            ('HOME IMPROVEMENT', None),
            ('PERSONAL CARE', None),
            ('TAXES', None),
            ('CARS/GAS', None),
            ('WIFE PHONE', None),
            ('CASH', None),
            ('SMOKE', None),
            ('HOUSEHOLD SHOPPING', None),
            ('HUSBAND PHONE', None),
            ('UNCATEGORIZED', None),
            ('PARKING/UBERS', None),
            ('RENT', None),
            ('TRANSPORTATION', None),
            ('DINING OUT', None),
            ('HEALTHCARE', None),
            ('EDUCATION', None),
            ('CLOTHING', None),
            ('MISCELLANEOUS', None),
        ]
        conn.executemany('INSERT INTO categories (name, parent_id) VALUES (?, ?)', default_categories)
        conn.commit()
    conn.close()

# Categories route loads categories from the database and serves them to the categories page
@categories_bp.route('/categories')
def categories():
    if 'household_db_path' not in session:
        flash('Please log in.', 'danger')
        return redirect('/login')
    household_conn = get_db(session['household_db_path'])
    categories_list = household_conn.execute('''SELECT categories.id, categories.name, parent.name as parent_name 
                                             FROM categories
                                             LEFT JOIN categories parent ON categories.parent_id = parent.id''').fetchall()
    household_conn.close()
    # Confirm ID is used to identify when a user is trying to delete something confirm ID allows for a 
    # confirmation of delete by the user before the record is actually deleted
    confirm_id = request.args.get('confirm_id', type = int)
    return render_template('categories.html', categories_list=categories_list, confirm_id=confirm_id)

# New Categories route adds the route from the categories page to the database. category_name and parent_category_id are passed
@categories_bp.route('/categories/new', methods=['GET', 'POST'])
def add_category():
    if 'household_db_path' not in session:
        flash('Please log in.', 'danger')
        return redirect('/login')    
    household_conn = get_db(session['household_db_path'])
    categories_list = household_conn.execute('''SELECT categories.id, categories.name, parent.name as parent_name 
                                             FROM categories
                                             LEFT JOIN categories parent ON categories.parent_id = parent.id''').fetchall()
    if request.method == 'POST':
        category_name = request.form.get('name').upper()
        parent_category_id = request.form.get('parent_id') or None  # Convert empty string to None
        if not category_name:
            flash('Category Name Required','danger')
            household_conn.close()
            return redirect('/categories/new')
        household_conn.execute('INSERT INTO categories (name, parent_id) VALUES (?, ?)', (category_name, parent_category_id))
        household_conn.commit()
        household_conn.close()
        flash('Category added successfully.', 'success')
        return redirect('/categories')    
    household_conn.close()
    return render_template('category_form.html', categories_list=categories_list)

# Edit Categories
@categories_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if 'household_db_path' not in session:
        flash('Please log in.', 'danger')
        return redirect('/login')
    household_conn = get_db(session['household_db_path'])
    category = household_conn.execute('SELECT id, name, parent_id FROM categories where id = ?', (category_id,)).fetchone()
    
    categories_list = household_conn.execute('''SELECT categories.id, categories.name, parent.name as parent_name 
                                             FROM categories
                                             LEFT JOIN categories parent ON categories.parent_id = parent.id''').fetchall()
    if request.method == 'POST':
        category_name = request.form.get('name').upper()
        parent_category_id = request.form.get('parent_id') or None  # Convert empty string to None
        if not category_name:
            flash('Category Name Required')
            household_conn.close()
            return redirect(f'/categories/edit/{category_id}')
        household_conn.execute('UPDATE categories SET name = ?, parent_ID = ? where id = ?', (category_name, parent_category_id, category_id))
        household_conn.commit()
        household_conn.close()
        flash('Category Updated.', 'success')
        return redirect('/categories')
    household_conn.close()
    return render_template('category_form.html', category=category, categories_list=categories_list)
    

# Delete Categories 

@categories_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    household_conn = get_db(session['household_db_path'])
    category = household_conn.execute('SELECT id FROM categories WHERE id = ?', (category_id,)).fetchone()
    if not category:
        flash('Category not found.', 'danger')
        household_conn.close()
        return redirect('/categories')
    household_conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    household_conn.commit()
    household_conn.close()
    flash('Category deleted successfully.', 'success')
    return redirect('/categories')

