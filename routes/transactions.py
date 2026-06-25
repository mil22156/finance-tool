from flask import Blueprint, render_template, request, flash, redirect, session
import os
from database.db import get_db, REGISTRY_PATH
from core.categorizer import category_rule_check

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
    categorize_category = request.args.get('categorize_category')

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
        if filter_category == '__uncategorized__':
            conditions.append('c1.name IS NULL')
        else:
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
                    t.api_category,
                    t.id
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
                           amount_max = amount_max, categorize_category=categorize_category, record_count = record_count, total_amount = total_amount, categories_list=categories_list)

# Edit Transactions opens the transactions_form.html which allows for the edit of the category only
# Future versions may include further editing and transaction creation bot not now

@transactions_bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    if 'household_db_path' not in session:
        flash('Please log in to edit transactions.', 'danger')
        return redirect('/login')
    db = get_db(session['household_db_path'])
    if request.method == 'POST':
        new_category = request.form.get('category')
        row = db.execute('SELECT id FROM categories WHERE name = ?', (new_category,)).fetchone()
        if row is None:
            db.close()
            flash('Category not found.', 'danger')
            return redirect(f'/transactions/edit/{transaction_id}')
        new_category_id = row[0]
        # Check whether this description already has a category
        description = db.execute('SELECT description FROM transactions WHERE id = ?',(transaction_id,)).fetchone()[0]
        try:
            category = category_rule_check(db, description, new_category_id, overwrite=False)
        except ValueError as e:
            db.close()
            flash(str(e), 'danger')
            return redirect(f'/transactions/edit/{transaction_id}')
        if category != new_category_id:
            pass # To Do - write the code and update the page to give the user the choice of overwriting the 
                 # existing rule or keeping the old one

        db.execute('''UPDATE transactions SET category_id = ? 
                    WHERE id = ?''', (new_category_id, transaction_id))
        db.commit()
        db.close()
        flash('Transaction updated successfully.', 'success')
        return redirect('/transactions')
    else:
        transaction = db.execute('''SELECT t.id, t.date, a.name AS account_name, t.description, t.merchant_name, t.amount,
                                            c1.name AS category,
                                            c2.name AS suggested_category,
                                            t.api_category
                                        FROM transactions t
                                        JOIN accounts a ON t.account_id = a.id
                                        LEFT JOIN categories c1 ON t.category_ID = c1.id
                                        LEFT JOIN categories c2 ON t.suggested_category_id = c2.id
                                        WHERE t.id = ?''', (transaction_id,)).fetchone()
        categories_list = db.execute('''SELECT categories.id, categories.name, parent.name as parent_name 
                                                 FROM categories
                                                 LEFT JOIN categories parent ON categories.parent_id = parent.id''').fetchall()
        db.close()
        if transaction is None:
            flash('Transaction not found.', 'danger')
            return redirect('/transactions')
        return render_template('transactions_form.html', transaction=transaction, categories_list=categories_list)

# Function to categorize all of the transactions filtered on the transactions form
@transactions_bp.route('/transactions/bulk_categorize', methods=['POST'])
def bulk_categorize():
    if 'household_db_path' not in session:
        flash('Please log in to categorize transactions.', 'danger')
        return redirect('/login')
    
    
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
    categorize_category = request.args.get('categorize_category')

    if not categorize_category:
        flash('No category selected for bulk categorization.', 'danger')
        return redirect('/transactions')

    db = get_db(session['household_db_path'])

    # Update query to update the category id of all the transactions currently filtered on the 
    # transactions page to that matching categorize category
    conditions = []
    params = []
    if date_from:
        conditions.append('date >= ?')
        params.append(date_from)
    if date_to:
        conditions.append('date <= ?')
        params.append(date_to)
    if filter_account:
        conditions.append('account_id IN (SELECT id FROM accounts WHERE name LIKE ?)')
        params.append(f'%{filter_account}%')
    if filter_description:
        conditions.append('description LIKE ?')
        params.append(f'%{filter_description}%')
    if filter_merchant:
        conditions.append('merchant_name LIKE ?')
        params.append(f'%{filter_merchant}%')
    if filter_category:
        conditions.append('category_id IN (SELECT id FROM categories WHERE name LIKE ?)')
        params.append(f'%{filter_category}%')
    if filter_suggested_category:
        conditions.append('suggested_category_id IN (SELECT id FROM categories WHERE name LIKE ?)')
        params.append(f'%{filter_suggested_category}%')
    if filter_api_category:
        conditions.append('api_category LIKE ?')
        params.append(f'%{filter_api_category}%')
    if amount_min:
        try:
            conditions.append('amount >= ?')
            params.append(float(amount_min))
        except ValueError:
            pass
    if amount_max:
        try:
            conditions.append('amount <= ?')
            params.append(float(amount_max))
        except ValueError:
            pass
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)
    else:        where_clause = ''
    sql = f'''UPDATE transactions 
                SET category_id = (SELECT id FROM categories WHERE name = ?)
                {where_clause}'''
    db.execute(sql, (categorize_category, *params))
    db.commit()
    db.close()
    flash('Transactions categorized successfully.', 'success')
    return redirect('/transactions')
    
