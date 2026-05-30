from flask import Blueprint, render_template, request, flash, redirect, session
import os
from database.db import get_db, REGISTRY_PATH

# Transactions blueprint to handle all transaction-related routes and logic, allowing for better organization and separation of concerns in the codebase.
# Routes will include viewing, categorizing, and managing transactions for the household.

transactions_bp = Blueprint('transactions', __name__)

# Transactions route to view account, date, amount, description, category, suggested category, api category
# AI note: AI provided the SQL particularly the aliasing and building the where clause correctly

@transactions_bp.route('/transactions', methods=['GET'])
def transactions():
    if 'household_db_path' not in session:
        flash('Please log in to view transactions.', 'danger')
        return redirect('/login')
    db = get_db(session['household_db_path'])

    # Build the where condition from the user input on the transactions search form
    # Now the search is limited to the date then one search criteria. In the future I'd like to expand this capability 
    # to filter any field

    search = request.args.get('search', '').strip()
    field = request.args.get('field', 'all')
    date_to = request.args.get('date_to', '')
    date_from = request.args.get('date_from', '')

    conditions = []
    params = []

    if date_from:
        conditions.append('t.date >= ?')
        params.append(date_from)
    if date_to:
        conditions.append('t.date <= ?')
        params.append(date_to)
    if search:
        if field == "all":
            # logic for all
            conditions.append('(t.description LIKE ? OR t.merchant_name LIKE ? OR c1.name LIKE ? OR c2.name LIKE ? OR t.api_category LIKE ?)')
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
        elif field == "description":
            # logic for description
            conditions.append('t.description LIKE ?')
            params.append(f'%{search}%')
        elif field == "merchant":
            # logic for merchant
            conditions.append('t.merchant_name LIKE ?')
            params.append(f'%{search}%')
        elif field == "category":
            # logic for category
            conditions.append('c1.name LIKE ?')
            params.append(f'%{search}%')
        elif field == "suggested_category":
            # logic for suggested category
            conditions.append('c2.name LIKE ?')
            params.append(f'%{search}%')
        elif field == "api_category":
            # logic for api category
            conditions.append('t.api_category LIKE ?')
            params.append((f'%{search}%'))
    
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)
    else:
        where_clause = ''
    
    sql = f'''SELECT t.date, a.name AS account_name, t.description, t.merchant_name, t.amount,
                    c1.name AS category,
                    c2.name AS suggested_category,
                    t.api_category
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c1 ON t.category_ID = c1.id
                LEFT JOIN categories c2 ON t.suggested_category_id = c2.id
                {where_clause}
                ORDER BY t.date DESC'''
    transactions_display = db.execute(sql, params).fetchall()
    db.close()
    return render_template('transactions.html', transactions_display=transactions_display)