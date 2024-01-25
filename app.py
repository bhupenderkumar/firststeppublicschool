from datetime import datetime
import time
from bson import ObjectId
from flask import Flask, Response, flash, jsonify, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
import os
from flask_login import LoginManager, current_user
from flask_pymongo import PyMongo
import pymongo
from receipt import PDF
app = Flask(__name__)
from gridfs import GridFS
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')
db_url = os.environ.get('MONGODB_URI')
# mongo_uri = 'mongodb+srv://vercel-admin-user:XQUP69T1QwIRD3yJ@cluster0.gstjaja.mongodb.net/?retryWrites=true&w=majority'
mongo_uri = 'localhost:27017'
app.config["MONGODB_URI"] = mongo_uri  # replace with your database URI
client = MongoClient(mongo_uri)
db = client.school
fs = GridFS(db)
from functools import wraps
from werkzeug.utils import secure_filename
filename = ".././etc/passwd"
safe_filename = secure_filename(filename)
from werkzeug.security import generate_password_hash

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
mongo = pymongo.MongoClient(mongo_uri)
print('initialized mongo instance')
print(mongo.db)

@app.route("/create_fees", methods=["GET", "POST"])
@login_required
def create_fee():
    classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
    if request.method == "GET":
        return render_template('create_fee.html', classes=classes)
    fee_data = extract_data_from_request(request)
    fee_data['fee_type'] = request.form.getlist('fee_type[]')
    fee_data["collected_by"] = session["username"]
    db.fees.insert_one(fee_data)
    return redirect(url_for("create_fee"))

@login_manager.user_loader
def load_user(user_id):
    return db.students.find_one({'_id': ObjectId(user_id)})

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_password, provided_password):
    print(stored_password)
    print(provided_password)
    print(bcrypt.checkpw(provided_password.encode('utf-8'), stored_password))
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)


@app.route('/')
def home():
    return render_template('home.html')

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

def extract_data_from_request(request_obj, exclude_keys=None):
    return {
        key: request_obj.form[key]
        for key in request_obj.form.keys()
        if not exclude_keys or key not in exclude_keys
    }

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method != 'POST':
        return render_template('signup.html', classes=get_classes_from_db())
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    if existing_user := db.students.find_one({'username': username}):
        return render_template('signup.html',  classes=get_classes_from_db(), error="Username already exists!")
    # Extract other data from the form
    form_data = extract_data_from_form(request.form)
    if 'confirm_password' in form_data:
        form_data.pop('confirm_password')
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_data = {
        **form_data,
        'username': username,
        'password': hashed_password,
        'role': role,

    }
    db.students.insert_one(user_data)
    return redirect(url_for('login'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.students.find_one({'username': username})
        print(user)
        print(db.students.find_one({'username': username}))
        if user and verify_password(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_role'] = user['role']
            session['username'] = user['username']
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid username or password")
    if request.method == 'GET' and session.get('user_id') is not None:
        return render_template(url_for('home'))

    return render_template('login.html')

@app.route('/home')
@login_required
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = load_user(session['user_id'])
    role = user['role']
    template_map = {
        'teacher': 'teacher_dashboard.html',
        'admin': 'admin_dashboard.html',
        'parents': 'parents_dashboard.html'
    }
    return render_template(template_map.get(role, 'dashboard.html'), username=user['username'])


MEDIA_FOLDER = './media'  # Assuming your folder name is 'media' in the current directory
from flask import send_from_directory

@app.route('/media-page')
def media_page():
    return render_template('media.html')

@app.route('/list-media-folders')
def list_media_folders():
    # List all folders in the MEDIA_FOLDER
    folders = [f for f in os.listdir(MEDIA_FOLDER) if os.path.isdir(os.path.join(MEDIA_FOLDER, f))]
    return jsonify({'folders': folders})
# Activities Plan page

@app.route('/activities-plan')
@login_required
def activities_plan():
    return render_template('activities_plan.html')

@app.route('/list-media/<folder_name>')
def list_media_in_folder(folder_name):
    folder_path = os.path.join(MEDIA_FOLDER, folder_name)
    
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    images = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
    videos = [f for f in files if f.endswith(('.mp4', '.avi', '.mkv'))]
    return jsonify({'images': images, 'videos': videos})

@app.route('/media/<folder_name>/<path:filename>')
def serve_media(folder_name, filename):
    return send_from_directory(os.path.join(MEDIA_FOLDER, folder_name), filename)


def get_classes_from_db():
    classes_collection = mongo.db.classes  # Assuming your collection is named 'classes'
    all_classes = classes_collection.find()
    return [cls['name'] for cls in all_classes]


def initialize_classes():
    default_classes = ["Pre Nursery", "Nursery/Prep 1", "L.K.G/Prep II", "U.K.G/Prep II", "I", "II", "III", "IV", "V"]    
    if mongo.db.classes.count_documents({}) == 0:
        for cls in default_classes:
            mongo.db.classes.insert_one({"name": cls})
    if not db.counters.find_one({"_id": "grievance"}):
        db.counters.insert_one({
            "_id": "grievance",
            "count": 0
        })
    else:
        print("Counter for 'grievance' already exists.")
initialize_classes()

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/syllabus')
@login_required
def syllabus():
    return render_template('syllabus.html')


@app.route('/holiday-calendar')
@login_required
def holiday_calendar():
    return render_template('holiday_calendar.html')

@app.route('/update_attendance/<attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    data = request.json  # Assuming the data is sent as JSON in the request body
    new_status = data.get('new_status')
    updated_result = db.attendance.update_one(
        {'_id': ObjectId(attendance_id)},
        {'$set': {'status': new_status}}
    )
    if updated_result.modified_count > 0:
        flash(f"Record updated succesfully ", 'success')
        return jsonify({'message': 'Attendance record updated successfully'})
    else:
        flash(f"Error please check the request or contact admin dept  ", 'dangeer')
        return jsonify({'message': 'No attendance record found for the given ID'})


@app.route('/create_attendance', methods=['GET', 'POST'])
def insert_attendance():
    if request.method == 'GET':
        return render_template('create_attendance.html', classes=get_classes_from_db())
    elif request.method == 'POST':
        try:
            class_name = request.form.get('class_name')
            student_ids = request.form.getlist('student_id[]')  # Get multiple selected student IDs
            date = request.form.get('date')
            status = request.form.get('status')
            remaining_fields = extract_data_from_form(request_form=request.form)
            for student_id in student_ids:
                db.attendance.insert_one({
                    **remaining_fields,
                    'class_name': class_name,
                    'student_id': student_id,
                    'user_id': student_id,
                    'date': date,
                    'status': status
                })
            flash("Records inserted successfully", 'success')
            return render_template('create_attendance.html', classes=get_classes_from_db())
        except Exception as e:
            flash("Error inserting records: " + str(e), 'error')
            return render_template('create_attendance.html', classes=get_classes_from_db())


@app.route('/fetch_attendance', methods=['GET'])
def fetch_attendance():
    try:
        user_id = session.get('user_id')  # Use get() to avoid KeyError
        if not user_id:
            flash("User id not found in session", "danger")
            return render_template('error.html', message='User not found'), 404
        user = db.students.find_one({'_id': ObjectId(user_id)})
        if user is None:
            flash(f"User not found with user id: {user_id}", "danger")
            return render_template('error.html', message='User not found'), 404
        class_name = user.get('class_name')

        attendance = db.attendance.find({'class_name': class_name, 'user_id': user_id})
        attendance_data = [
            {
                'attendance_date': entry['attendance_date'],
                'status': entry['status'],
            }
            for entry in attendance
        ]
        student_name = user.get('username')  # Use 'username' instead of 'user_name'
        return render_template('attendance.html', attendance_data=attendance_data, student_name=student_name)
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

def get_next_sequence(name):
    # First, check if the document exists
    counter_doc = db.counters.find_one({"_id": name})
    if counter_doc:
        return int(int(counter_doc["count"]) + 1)
    else:
        return 1;

@app.route('/fees')
@login_required
def fees():
    student_id = session.get('user_id')
    fees_list = []
    student_name = session.get('user_name')
    # If the role is either 'admin' or 'parents'
    fees_list = list(db.fees.find({'student_id': student_id}))
    return render_template('fees.html', fees_list=fees_list, student_name=student_name)

@app.route("/raise_grievance", methods=["GET", "POST"])
@login_required
def raise_grievance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    grievances = list(db.grievances.find({"user_id": user_id}))
    if request.method == "POST":
        grievance_text = request.form["grievance_details"]  # replace "grievance_text" with the name attribute of your form field
        grievance = { 
            'grievance_id':get_next_sequence("grievance"),
            'class_name':request.form['class_name'],
            'school_response':'',
            'user_id':user_id,
            'grievance_text': grievance_text,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')  # Storing the time the grievance was raised
        }
        db.grievances.insert_one(grievance)
        flash('Your grievance has been recorded!', 'success')
        classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
        return render_template('raise_grievance.html', classes=classes,grievances=grievances)
    else:
        grievances = list(db.grievances.find({"user_id": user_id}))
        classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
        return render_template('raise_grievance.html', grievances=grievances,  classes=classes)


@app.route('/downloadfees/<fee_id>')
def download_fee_receipt(fee_id):
    fee_data = db.fees.find_one({"_id": ObjectId(fee_id)})
    fee_data['student_id'] =  fee_data['student_id']
    if not fee_data:
        return "Fee data not found", 404
    pdf_data = PDF.create_receipt(fee_data)
    with open("fee_receipt.pdf", "rb") as f:
        pdf_data = f.read()
    response = Response(pdf_data, content_type='application/pdf')
    response.headers['Content-Disposition'] = f'inline; filename=fee_receipt_{fee_id}.pdf'
    return response

@app.route('/notifications')
@login_required
def notifications():
    student_id = session.get('user_id')
    student_name = session.get('user_name')
    # Fetch the class name associated with the student from the database
    student_data = db.students.find_one({'_id': ObjectId(student_id)})
    class_name = student_data.get('class_name') if student_data else None
    notifications_list = []
    if class_name:
        # Fetch all notifications related to the class
        notifications_list = list(db.notifications.find({'class_name': class_name}))
    return render_template('notifications.html', notifications_list=notifications_list, student_name=student_name)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html'), 404


@app.route('/get-students/<class_name>')
def get_students(class_name):
    students = db.students.find({"class_name": class_name})
    print(students.count())
    students_list = [
        {"username": student["username"], "_id": str(student["_id"])}
        for student in students
    ]
    return jsonify(students_list)

@app.route('/students')
@login_required
def students():
    if session.get('user_role') == 'admin':
        students = db.students.find()
        return render_template('students.html', students=students)
    return redirect(url_for('dashboard'))

@app.route('/grades')
@login_required
def grades():
    if session.get('user_role') == 'admin':
        grades = db.grades.find()
        return render_template('grades.html', grades=grades)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
