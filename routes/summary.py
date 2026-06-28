from flask import Blueprint, render_template, request, flash, redirect, session
import os
from database.db import get_db, REGISTRY_PATH

summary_bp = Blueprint('summary', __name__)

# summary blueprint to provide summarized report data to the summary page

# summary route

@summary_bp.route('/summary', methods=['GET'])
def summary():
    # Confirm a user is logged in
    if 'household_db_path' not in session:
        flash('Please log in.', 'danger')
        return redirect('/login')
    
    # import db from household db. create lists for categories and accounts to use in the filter
    db = get_db(session['household_db_path'])
    categories_list = db.execute('''SELECT categories.id, categories.name, parent.name as parent_name
                                             FROM categories
                                             LEFT JOIN categories parent ON categories.parent_id = parent.id''').fetchall()
    account_list = db.execute('''SELECT name FROM accounts''').fetchall()

    # load the page arguments into variables to build the query

    date_to = request.args.get('date_to', '')
    date_from = request.args.get('date_from', '')
    filter_account = request.args.get('filter_account', '')
    filter_category = request.args.get('filter_category', '')

    conditions = []
    params = []
    # build the where condition from the filter on the summary page
    # similar to how the transactions page works
    # filters to include date, account, category

    if date_from:
        conditions.append('t.date >= ?')
        params.append(date_from)
    if date_to:
        conditions.append('t.date <= ?')
        params.append(date_to)
    if filter_account:
        conditions.append('a.name = ?')
        params.append(filter_account)
    if filter_category:
        if filter_category == '__uncategorized__':
            conditions.append('c1.name IS NULL')
        else:
            conditions.append('c1.name LIKE ?')
            params.append(f'%{filter_category}%')

    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)
    else:
        where_clause = ''
    
    # query transactions for the summery. SQL came from Claude AI
    sql = f'''SELECT c1.name AS category,
                    SUM(t.amount) AS total,
                    COUNT(*) AS cnt
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c1 ON t.category_id = c1.id
            {where_clause}
            GROUP BY c1.name
            ORDER BY total'''

    summary_display = db.execute(sql, params).fetchall()
    total_amount = sum(c['total'] for c in summary_display)
    db.close()
    # render summary page

    return render_template('summary.html', categories_list=categories_list, account_list=account_list, 
                           date_to=date_to, date_from=date_from, filter_account=filter_account, 
                           filter_category=filter_category, summary_display=summary_display, 
                           total_amount=total_amount)
