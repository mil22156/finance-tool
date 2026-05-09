from flask import Blueprint, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
import os
from database.db import get_db, REGISTRY_PATH

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle file upload logic here
        pass       
    return render_template('upload.html')