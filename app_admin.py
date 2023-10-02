import json
import re
from flask_login import login_user, logout_user, current_user
from datetime import date
import time
from bson import ObjectId
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, session
from gridfs import GridFS
from pymongo import MongoClient
import bcrypt
import os
from flask_login import LoginManager, current_user
from flask_pymongo import PyMongo
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/school_management')
app.config["MONGO_URI"] = mongo_uri  # replace with your database URI
client = MongoClient(mongo_uri)
db = client.school_management
fs = GridFS(db)

from functools import wraps
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'  # Create a folder in your project directory named 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

login_manager = LoginManager(app)
mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template('home.html')

def get_classes_from_db():
    """
    Gets all the classes from the database.

    Returns:
        A list of dictionaries, where each dictionary represents a class.
    """
    classes_collection = db.classes  # Assuming you have a collection named 'classes' in your database
    all_classes = classes_collection.find()
    classes = []
    for class_doc in all_classes:
        class_data = {
            "class_name": class_doc["name"]
        }
        classes.append(class_data)

    return classes

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
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
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Combine data for insertion into the database
    user_data = {
        'username': username,
        'password': hashed_password,
        'role': role,
        **form_data
    }
    db.students.insert_one(user_data)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.students.find_one({'username': username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid username or password!")

    return render_template('login.html', classes=get_classes_from_db())





app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')

def extract_data_from_form(request_form, existing_data=None):
    data = {}
    for key in request_form.keys():
        # Check if the field contains multiple values (i.e., multi-select)
        values = request_form.getlist(key)
        if len(values) > 1:
            data[key] = values
        else:
            data[key] = request_form.get(key) or (existing_data[key] if existing_data and key in existing_data else None)
    return data


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

@app.route("/answer_grievance", methods=["GET"])
@login_required
def answer_grievance():
    if 'user_id' not in session:
        return redirect(url_for('login')) 
    grievances = list(db.grievances.find())
    return render_template('answer_grievance.html', grievances=grievances)
 
def extract_data_from_request(request_obj, exclude_keys=None):
    return {
        key: request_obj.form[key]
        for key in request_obj.form.keys()
        if not exclude_keys or key not in exclude_keys
    }

@app.route("/fees", methods=["GET", "POST"])
@login_required
def create_fee():
    classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
    if request.method == "GET":
        return render_template('create_fee.html', classes=classes)
    fee_data = extract_data_from_request(request)
    fee_data["collected_by"] = session["username"]
    db.fees.insert_one(fee_data)
    return redirect(url_for("create_fee"))

@app.route('/')
def home():
    return render_template('home.html')


def get_next_sequence(name):
    if counter_doc := db.counters.find_one({"_id": name}):
        db.counters.update_one({"_id": name}, {"$inc": {"count": 1}})
        return int(int(counter_doc["count"]) + 1)
    else:
        return 1;
@app.route("/raise_grievance", methods=["GET", "POST"])
@login_required
def raise_grievance():
    classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
    if request.method == "GET":
        return render_template('raise_grievance.html', classes=classes)
    grievance_data = extract_data_from_request(request)
    grievance_data["grievance_id"] = get_next_sequence("grievance")
    grievance_data["school_response"] = ""
    grievance_data["user_name"] = session["user_name"]
    grievance_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    db.grievances.insert_one(grievance_data)
    flash('Your grievance has been recorded!', 'success')
    return render_template('raise_grievance.html', classes=classes)

@app.route("/create_notification", methods=["GET", "POST"])
@login_required
def create_notification():
    classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
    if request.method == "GET":
        all_notification = db.notifications.find();
        return render_template('create_notification.html', classes=classes, all_notification=all_notification)
    notification_data = extract_data_from_request(request)
    notification_data["notification_id"] = get_next_sequence("notification")
    notification_data["user_id"] = session["user_id"]
    notification_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    db.notifications.insert_one(notification_data)
    all_notification = db.notifications.find();
    flash('Your notification has been created!', 'success')
    return render_template('create_notification.html', classes=classes,all_notification=all_notification)


@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    user = db.users.find_one({'username': session['username']})  # Assuming you store the admin's username in the session
    if request.method == 'POST':
        form_data = extract_data_from_form(request.form, user)
        file_data = handle_file_uploads(request.files, user)
        form_data.update(file_data)
        db.users.update_one({'username': session['username']}, {'$set': form_data},  upsert=True)
        return render_template('home.html')
    return render_template('edit_profile.html', admin=user)

def remove_special_characters(input_string):
    return re.sub(r'[^a-zA-Z0-9 ]', '', input_string)

@app.route('/get-students/<class_name>')
def get_students(class_name):
    students = mongo.db.students.find({"class_name": class_name})
    students_list = [
        {"username": student["username"], "_id": str(student["_id"])}
        for student in students
    ]
    return jsonify(students_list)


def fetch_students_from_db(class_name):
    students_query = db.students.find({'class_name': class_name})
    return [
        {"username": student["username"], "_id": str(student["_id"])}
        for student in students_query
    ]
@app.route("/respond_grievance/<int:grievance_id>", methods=["POST"])
@login_required
def respond_grievance(grievance_id):
    if not has_permission_to_respond(session.get("user_id")):
        return redirect_with_flash('raise_grievance', "Permission denied!", "danger")

    response_text = request.form["school_response"]
    if record_response(grievance_id, response_text):
        return redirect_with_flash('raise_grievance', 'Response recorded!', 'success')
    else:
        return redirect_with_flash('raise_grievance', 'Failed to record response!', 'danger')


def has_permission_to_respond(user_id):
    # This is just a placeholder, implement your own logic for permission check
    return is_admin(user_id)

def record_response(grievance_id, response_text):
    result = db.grievances.update_one(
        {"grievance_id": grievance_id},
        {"$set": {"school_response": response_text}}
    )
    return result.matched_count > 0

def redirect_with_flash(endpoint, message, category):
    flash(message, category)
    return redirect(url_for(endpoint))

def is_admin(user_id):
    # Dummy function, implement your own logic to check if a user is admin
   return True

@app.route('/edit-student', methods=['GET', 'POST'])
def edit_student():
    classes = get_classes_from_db()

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        student = get_student_from_db(student_id)

        if not student:
            return respond_with_error("Student not found", 404)

        updated_data = gather_updated_student_data(request.form, request.files, student)
        save_updated_student_data(student_id, updated_data)

        return redirect(url_for('dashboard'))

    return render_template('edit_student.html', student=None, classes=classes)

def get_student_from_db(student_id):
    return db.students.find_one({'_id': student_id})

def gather_updated_student_data(form, files, existing_student):
    form_data = extract_data_from_form(form, existing_student)
    file_data = handle_file_uploads(files, existing_student)
    form_data.update(file_data)
    return form_data


def save_updated_student_data(student_id, updated_data):
    db.students.update_one({'_id': student_id}, {'$set': updated_data})


def respond_with_error(message, status_code):
    return message, status_code

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002,debug= True)