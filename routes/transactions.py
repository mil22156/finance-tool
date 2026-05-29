from flask import Blueprint, render_template, request, flash, redirect, session
import os
from database.db import get_db, REGISTRY_PATH

# Transactions blueprint to handle all transaction-related routes and logic, allowing for better organization and separation of concerns in the codebase.
# Routes will include viewing, categorizing, and managing transactions for the household.

transactions_bp = Blueprint('transactions', __name__)

# Transactions route to view account, date, amount, description, category, suggested category, api category

@transactions_bp.route('/transactions', methods=['GET'])
def transactions():
    if 'household_db_path' not in session:
        flash('Please log in to view transactions.', 'danger')
        return redirect('/login')
    db = get_db(session['household_db_path'])
    transactions_display = db.execute('''SELECT t.date, a.name, t.description, t.merchant_name, t.amount,
                                    c1.name AS category,
                                    c2.name AS suggested_category,
                                    t.api_category
                                FROM transactions t
                                JOIN accounts a ON t.account_id = a.id
                                LEFT JOIN categories c1 ON t.category_ID = c1.id
                                LEFT JOIN categories c2 ON t.suggested_category_id = c2.id
                                ORDER BY t.date DESC''').fetchall()
    db.close()
    return render_template('transactions.html', transactions_display=transactions_display)