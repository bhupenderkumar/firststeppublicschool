from flask import Blueprint, render_template, jsonify, request, flash, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
from utils import login_required, verify_password
import os
from db_operations import * 
shared_bp = Blueprint('shared_bp', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MEDIA_FOLDER = './media'

# Utility Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_data_from_request(request_obj, exclude_keys=None):
    return {
        key: request_obj.form[key]
        for key in request_obj.form.keys()
        if not exclude_keys or key not in exclude_keys
    }

def handle_file_uploads(request_files, existing_data=None):
    file_data = {}
    for field in request_files.keys():
        uploaded_file = request_files.get(field)
        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(os.path.join("uploads", filename))
            file_id = filename 
        else:
            file_id = existing_data[f"{field}_id"] if existing_data and f"{field}_id" in existing_data else None
        file_data[f"{field}_id"] = file_id

    return file_data


MEDIA_FOLDER = './media'  # Assuming your folder name is 'media' in the current directory
from flask import send_from_directory



@shared_bp.route('/holiday-calendar')
@login_required
def holiday_calendar():
    return render_template('holiday_calendar.html')

def extract_data_from_form(request_form, existing_data=None):
    return {
        key: request_form.get(key)
        or (
            existing_data[key]
            if existing_data and key in existing_data
            else None
        )
        for key in request_form.keys()
    }


    

@shared_bp.route('/login', methods=['GET', 'POST'])
def login():
    initialize_classes()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_student_from_db_username(username)
        if user and verify_password(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['role'] = user['role']
            session['username'] = user['username']
            flash(f'{str(user)} ' + str(user['_id']), 'danger')
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')


@shared_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method != 'POST':
        return render_template('signup.html', classes=get_classes_from_db())
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    if existing_user := db.students.find_one({'username': username}):
        return render_template('signup.html', error="Username already exists!")
    # Extract other data from the form
    form_data = extract_data_from_form(request.form)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_data = {
        'username': username,
        'password': hashed_password,
        'role': role,
        **form_data
    }
    db.students.insert_one(user_data)
    return redirect(url_for('login'))



@shared_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('shared_bp.home'))

@shared_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = db.users.find_one({'username': session['username']})  # Assuming you store admin's username in the session
    if request.method == 'POST':
        form_data = extract_data_from_form(request.form, user)
        file_data = handle_file_uploads(request.files, user)
        form_data.update(file_data)
        db.users.update_one({'username': session['username']}, {'$set': form_data},  upsert=True)
        return render_template('home.html')
    return render_template('edit_profile.html', admin=user)
def get_next_sequence(name):
    if counter_doc := db.counters.find_one({"_id": name}):
        db.counters.update_one({"_id": name}, {"$inc": {"count": 1}})
        return int(int(counter_doc["count"]) + 1)
    else:
        return 1;

def respond_with_error(message, status_code):
    return message, status_code

def gather_updated_student_data(form, files, existing_student):
    form_data = extract_data_from_form(form, existing_student)
    file_data = handle_file_uploads(files, existing_student)
    form_data.update(file_data)
    return form_data

@shared_bp.route('/')
def home():
    return render_template('home.html')


@shared_bp.route('/media-page')
def media_page():
    return render_template('media.html')

@shared_bp.route('/list-media-folders')
def list_media_folders():
    # List all folders in the MEDIA_FOLDER
    folders = [f for f in os.listdir(MEDIA_FOLDER) if os.path.isdir(os.path.join(MEDIA_FOLDER, f))]
    return jsonify({'folders': folders})


# Holiday Calendar page


# Activities Plan page
@shared_bp.route('/activities-plan')
@login_required
def activities_plan():
    return render_template('activities_plan.html')


# Syllabus page
@shared_bp.route('/syllabus')
@login_required
def syllabus():
    return render_template('syllabus.html')

@shared_bp.route('/list-media/<folder_name>')
def list_media_in_folder(folder_name):
    folder_path = os.path.join(MEDIA_FOLDER, folder_name)
    
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404

    # List all files in the specified folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Separate images and videos based on file extensions. 
    images = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
    videos = [f for f in files if f.endswith(('.mp4', '.avi', '.mkv'))]

    return jsonify({'images': images, 'videos': videos})

@shared_bp.route('/media/<folder_name>/<path:filename>')
def serve_media(folder_name, filename):
    return send_from_directory(os.path.join(MEDIA_FOLDER, folder_name), filename)

@shared_bp.route('/grades')
@login_required
def grades():
    if session.get('role') == 'admin':
        grades = db.grades.find()
        return render_template('grades.html', grades=grades)
    return redirect(url_for('dashboard'))