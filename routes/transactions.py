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
    categories_list = db.execute('''SELECT categories.id, categories.name, parent.name as parent_name 
                                             FROM categories
                                             LEFT JOIN categories parent ON categories.parent_id = parent.id''').fetchall()

    # Build the where condition from the user input on the transactions search form
    # Now the search is limited to the date then one search criteria. In the future I'd like to expand this capability 
    # to filter any field

    date_to = request.args.get('date_to', '')
    date_from = request.args.get('date_from', '')
    filter_account = request.args.get('filter_account', '')
    filter_description = request.args.get('filter_description', '')
    filter_merchant = request.args.get('filter_merchant', '')
    filter_category = request.args.get('filter_category', '')
    filter_suggested_category = request.args.get('filter_suggested_category', '')
    filter_api_category = request.args.get('filter_api_category', '')
    sort = request.args.get('sort', '')
    direction = request.args.get('direction', 'DESC')
    amount_min = request.args.get('amount_min', '')
    amount_max = request.args.get('amount_max', '')

    conditions = []
    params = []

    # Ensure that min max are valid numbers
    if amount_min:
        try:
            conditions.append('t.amount >= ?')
            params.append(float(amount_min))
        except ValueError:
            pass
    
    if amount_max:
        try:
            conditions.append('t.amount <= ?')
            params.append(float(amount_max))
        except ValueError:
            pass

    
    # White list direction to avoid malicious SQL injection
    if direction not in ['ASC', 'DESC']:
        direction = 'DESC' 
    
    # Build the where condition for the transactions query from the user input on the form
    
    if date_from:
        conditions.append('t.date >= ?')
        params.append(date_from)
    if date_to:
        conditions.append('t.date <= ?')
        params.append(date_to)
    if filter_account:
        conditions.append('a.name LIKE ?')
        params.append(f'%{filter_account}%')
    if filter_description:
        conditions.append('t.description LIKE ?')
        params.append(f'%{filter_description}%')
    if filter_merchant:
        conditions.append('t.merchant_name LIKE ?')
        params.append(f'%{filter_merchant}%')
    if filter_category:
        conditions.append('c1.name LIKE ?')
        params.append(f'%{filter_category}%')
    if filter_suggested_category:
        conditions.append('c2.name LIKE ?')
        params.append(f'%{filter_suggested_category}%')
    if filter_api_category:
        conditions.append('t.api_category LIKE ?')
        params.append(f'%{filter_api_category}%')
    
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)
    else:
        where_clause = ''
    
    # build the sort clause for transactions from the user input on the form
    if sort == 'date':
        sort_clause = f't.date {direction}'
    elif sort == 'account':
        sort_clause = f'a.name {direction}'
    elif sort == 'description':
        sort_clause = f't.description {direction}'
    elif sort == 'merchant':
        sort_clause = f't.merchant_name {direction}'
    elif sort == 'category':
        sort_clause = f'c1.name {direction}'
    elif sort == 'suggested_category':
        sort_clause = f'c2.name {direction}'
    elif sort == 'api_category':
        sort_clause = f't.api_category {direction}'
    elif sort == 'amount':
        sort_clause = f't.amount {direction}'
    else:
        sort_clause = 't.date DESC'
    
    # query transactions to send to the transactions form for display
    sql = f'''SELECT t.date, a.name AS account_name, t.description, t.merchant_name, t.amount,
                    c1.name AS category,
                    c2.name AS suggested_category,
                    t.api_category
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c1 ON t.category_ID = c1.id
                LEFT JOIN categories c2 ON t.suggested_category_id = c2.id
                {where_clause}
                ORDER BY {sort_clause}'''
    transactions_display = db.execute(sql, params).fetchall()
    record_count = len(transactions_display)
    total_amount = sum(t['amount'] for t in transactions_display)
    db.close()

    # render transaction page sending the data and the current filter and sort criteria
    return render_template('transactions.html', transactions_display=transactions_display, date_to = date_to, date_from = date_from,
                           filter_account = filter_account, filter_description = filter_description, filter_merchant = filter_merchant, 
                           filter_category = filter_category, filter_suggested_category = filter_suggested_category, 
                           filter_api_category = filter_api_category, sort = sort, direction = direction, amount_min = amount_min, 
                           amount_max = amount_max, record_count = record_count, total_amount = total_amount, categories_list=categories_list)