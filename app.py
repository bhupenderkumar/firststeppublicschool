from datetime import datetime
import time
from bson import ObjectId
from flask import Flask, Response, flash, jsonify, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
import os
from flask_login import LoginManager, current_user
from flask_pymongo import PyMongo

from receipt import PDF
app = Flask(__name__)
from gridfs import GridFS
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/school_management')
app.config["MONGO_URI"] = mongo_uri  # replace with your database URI
client = MongoClient(mongo_uri)
db = client.school_management
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
mongo = PyMongo(app)



@login_manager.user_loader
def load_user(user_id):
    return db.students.find_one({'_id': ObjectId(user_id)})

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)


@app.route('/')
def home():
    return render_template('home.html')

def extract_data_from_form(request_form, existing_data=None):
    data = {}
    for key in request_form.keys():
        data[key] = request_form.get(key) or (existing_data[key] if existing_data and key in existing_data else None)
    return data
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        existing_user = db.students.find_one({'username': username})
        if existing_user:
            return render_template('signup.html',  classes=get_classes_from_db(), error="Username already exists!")
        # Extract other data from the form
        form_data = extract_data_from_form(request.form)
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            **form_data,
            'username': username,
            'password': hashed_password,
            'role': role,
            
        }
        db.students.insert_one(user_data)
        return redirect(url_for('login'))
    return render_template('signup.html', classes=get_classes_from_db())

@app.route('/create-student', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        # Ensure the upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        # Extracting data from the form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['dob']  # Assuming you've named the DOB input field as 'dob'
        # Generating username and password
        username = date_of_birth  # Using DOB as the login id
        password = f"{first_name}_{last_name}"  # Using first name and last name separated by an underscore
        child_photo = request.files['child_photo']
        child_aadhar = request.files['child_aadhar']
        child_birth_certificate = request.files['child_birth_certificate']
        father_photo = request.files['father_photo']
        father_aadhar = request.files['father_aadhar']
        mother_photo = request.files['mother_photo']
        mother_aadhar = request.files['mother_aadhar']
        # Save to file system for backup
        filename_child_photo = secure_filename(child_photo.filename)
        child_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_child_photo))

        filename_child_aadhar = secure_filename(child_aadhar.filename)
        child_aadhar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_child_aadhar))

        filename_child_birth_certificate = secure_filename(child_birth_certificate.filename)
        child_birth_certificate.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_child_birth_certificate))

        filename_father_photo = secure_filename(father_photo.filename)
        father_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_father_photo))

        filename_father_aadhar = secure_filename(father_aadhar.filename)
        father_aadhar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_father_aadhar))

        filename_mother_photo = secure_filename(mother_photo.filename)
        mother_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_mother_photo))

        filename_mother_aadhar = secure_filename(mother_aadhar.filename)
        mother_aadhar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_mother_aadhar))

        # Save to MongoDB as BLOB
        child_photo_id = fs.put(child_photo)
        child_aadhar_id = fs.put(child_aadhar)
        child_birth_certificate_id = fs.put(child_birth_certificate)
        father_photo_id = fs.put(father_photo)
        father_aadhar_id = fs.put(father_aadhar)
        mother_photo_id = fs.put(mother_photo)
        mother_aadhar_id = fs.put(mother_aadhar)

        existing_student = db.students.find_one({'username': username})

        if existing_student:
            return render_template('create_student.html', error="Student with this DOB already exists!")

        hashed_password = generate_password_hash(password)
         
        # Store the student data
        student_data = {
            'username': username,
            'password': hashed_password,
            'first_name': first_name,
            'last_name': last_name,
            'gender': request.form['gender'],
            'place_of_birth': request.form['place_of_birth'],
            'father_name': request.form['father_name'],
            'father_mobile': request.form['father_mobile'],
            'father_email': request.form['father_email'],
            'father_qualification': request.form['father_qualification'],
            'father_occupation': request.form['father_occupation'],
            'father_office_name': request.form['father_office_name'],
            'father_office_address': request.form['father_office_address'],
            'mother_name': request.form['mother_name'],
            'mother_address': request.form['mother_address'],
            'mother_mobile': request.form['mother_mobile'],
            'mother_qualification': request.form['mother_qualification'],
            'mother_office_name': request.form['mother_office_name'],
            'mother_office_address': request.form['mother_office_address'],
            'guardian_name': request.form['guardian_name'],
            'guardian_relationship': request.form['guardian_relationship'],
            'guardian_address': request.form['guardian_address'],
            'guardian_mobile': request.form['guardian_mobile'],
            'primary_contact_name': request.form['primary_contact_name'],
            'primary_contact_relationship': request.form['primary_contact_relationship'],
            'primary_contact_mobile': request.form['primary_contact_mobile'],
            'emergency_contact': request.form['emergency_contact'],
            'class_name': request.form['class_name'],
            'previous_school': request.form['previous_school'] if 'previous_school' in request.form else None,
            'allergies': request.form['allergies'] if 'allergies' in request.form else None,
            'precautions': request.form['precautions'] if 'precautions' in request.form else None,
            'child_photo_id': child_photo_id,
            'child_aadhar_id': child_aadhar_id,
            'child_birth_certificate_id': child_birth_certificate_id,
            'father_photo_id': father_photo_id,
            'father_aadhar_id': father_aadhar_id,
            'mother_photo_id': mother_photo_id,
            'mother_aadhar_id': mother_aadhar_id
        }

        db.students.insert_one(student_data)

        return redirect(url_for('dashboard'))

    return render_template('create_student.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.students.find_one({'username': username})
        if user and verify_password(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_role'] = user['role']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))

        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/dashboard')
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

@app.route('/list-media/<folder_name>')
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

@app.route('/media/<folder_name>/<path:filename>')
def serve_media(folder_name, filename):
    return send_from_directory(os.path.join(MEDIA_FOLDER, folder_name), filename)


def get_classes_from_db():
    classes_collection = mongo.db.classes  # Assuming your collection is named 'classes'
    all_classes = classes_collection.find()
    class_names = [cls['name'] for cls in all_classes]
    return class_names


def initialize_classes():
    default_classes = ["Pre School", "Nursery", "L.K.G", "U.K.G", "I", "II", "III", "IV", "V"]    
    # If the classes collection is empty, add the default classes
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

# One-time initialization
initialize_classes()

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# Syllabus page
@app.route('/syllabus')
@login_required
def syllabus():
    return render_template('syllabus.html')

# Holiday Calendar page
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

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/fetch_attendance', methods=['GET'])
def fetch_attendance():
    try:
        user_id = session.get('user_id')  # Use get() to avoid KeyError
        if not user_id:
            flash("User id not found in session", "danger")
            return render_template('error.html', message='User not found'), 404
        user = db.students.find_one({'_id': ObjectId(user_id)})
        if user is None:
            flash("User not found with user id: " + user_id, "danger")
            return render_template('error.html', message='User not found'), 404
        class_name = user.get('class_name')
        
        attendance = db.attendance.find({'class_name': class_name, 'user_id': user_id})
        attendance_data = []
        for entry in attendance:
            attendance_data.append({
                'attendance_date': entry['attendance_date'],
                'status': entry['status']
            })
        student_name = user.get('username')  # Use 'username' instead of 'user_name'
        return render_template('attendance.html', attendance_data=attendance_data, student_name=student_name)
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

# Activities Plan page
@app.route('/activities-plan')
@login_required
def activities_plan():
    return render_template('activities_plan.html')

@app.route('/user/deactivate/<string:user_id>', methods=['POST'])
@login_required
def deactivate_user(user_id):
    # Ensure only admins can access this route
    if session.get('user_role') != 'admin':
        return redirect(url_for('dashboard'), "You don't have permission to access this page!")

    # Update the user's is_active status
    db.students.update_one({"_id": user_id}, {"$set": {"is_active": False}})

    return redirect(url_for('admin_dashboard'), "User has been deactivated!")


@app.route('/user/update-role/<user_id>', methods=['GET', 'POST'])
@login_required
def update_role(user_id):
    # Ensure the current user is an admin
    if current_user.role != 'admin':
        flash('You do not have permission to update user roles.', 'danger')
        return redirect(url_for('dashboard'))

    # If we're accessing the page to render the form
    if request.method == 'GET':
        user = db.students.find_one({"_id": user_id})
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        return render_template('update-role.html', user=user)

    # If we're submitting the form to update the role
    if request.method == 'POST':
        new_role = request.form.get('role')
        db.students.update_one({"_id": user_id}, {"$set": {"role": new_role}})
        flash(f"Role for {user['username']} updated successfully!", 'success')
        return redirect(url_for('dashboard'))

def get_next_sequence(name):
    # First, check if the document exists
    counter_doc = db.counters.find_one({"_id": name})
    if counter_doc:
        return int(int(counter_doc["count"]) + 1)
    else:
        return 1;

@app.route('/downloadfees/<fee_id>')
def download_fee_receipt(fee_id):
    fee_data = db.fees.find_one({"_id": ObjectId(fee_id)})
    if not fee_data:
        return "Fee data not found", 404
    pdf_data = PDF.create_receipt(fee_data)
    with open("fee_receipt.pdf", "rb") as f:
        pdf_data = f.read()
    response = Response(pdf_data, content_type='application/pdf')
    response.headers['Content-Disposition'] = f'inline; filename=fee_receipt_{fee_id}.pdf'
    return response

@app.route('/create_notification', methods=['POST', 'GET'])
@login_required
def create_notification():
    classes = get_classes_from_db()
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        notification_text = request.form.get('notification_text')
        student_id = session.get('user_id')
        # Assuming you have a 'notifications' collection in your database
        db.notifications.insert_one({
            'class_name': class_name,
            'notification_text': notification_text,
            'student_id': student_id,
            'date': datetime.now()
        })
        return redirect(url_for('notifications'))
    else:
        return render_template('create_notification.html', classes=classes)
    
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
    return render_template('404.html'), 404

@app.route('/fees')
@login_required
def fees():
    student_id = session.get('user_id')
    fees_list = []
    student_name = session.get('user_name')
    # If the role is either 'admin' or 'parents'
    fees_list = list(db.fees.find({'student_id': student_id}))
    return render_template('fees.html', fees_list=fees_list, student_name=student_name)

@app.route('/get-students/<class_name>')
def get_students(class_name):
    students = mongo.db.students.find({"class_name": class_name})
    students_list = [
        {"username": student["username"], "_id": str(student["_id"])}
        for student in students
    ]
    return jsonify(students_list)

@app.route("/raise_grievance", methods=["GET", "POST"])
@login_required
def raise_grievance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    grievances = list(db.grievances.find({"user_id": user_id}))
    # Check if user_id is in session
    # Handle the POST request (when a new grievance is raised)
    if request.method == "POST":
        # Extract grievance data from the form
        grievance_text = request.form["grievance_details"]  # replace "grievance_text" with the name attribute of your form field
        # Create a grievance dictionary
        grievance = { 
            'grievance_id':get_next_sequence("grievance"),
            'class_name':request.form['class_name'],
            'school_response':'',
            'user_id':user_id,
            'grievance_text': grievance_text,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')  # Storing the time the grievance was raised
        }
        # Insert the grievance into the MongoDB collection
        db.grievances.insert_one(grievance)
        # Optionally, you can give a flash message to inform the user that their grievance was recorded.
        flash('Your grievance has been recorded!', 'success')
        
        classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
        return render_template('raise_grievance.html', classes=classes,grievances=grievances)

    # Handle the GET request (when the page is initially loaded or refreshed)
    else:
        grievances = list(db.grievances.find({"user_id": user_id}))
        classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
        return render_template('raise_grievance.html', grievances=grievances,  classes=classes)

@app.route('/fees-form')
def fees_form():
    classes = mongo.db.classes.find()  # Assuming you have a collection of classes
    return render_template('update_fees.html', classes=classes, current_date=date.today())


@app.route('/students')
@login_required

def students():
    if session.get('user_role') == 'admin':
        students = db.students.find()
        return render_template('students.html', students=students)
    return redirect(url_for('dashboard'))

@app.route('/teachers')
@login_required

def teachers():
    if session.get('user_role') == 'admin':
        teachers = db.teachers.find()
        return render_template('teachers.html', teachers=teachers)
    return redirect(url_for('dashboard'))

@app.route('/grades')
@login_required

def grades():
    if session.get('user_role') == 'admin':
        grades = db.grades.find()
        return render_template('grades.html', grades=grades)
    return redirect(url_for('dashboard'))


@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = db.students.find_one({'student_id': student_id})

    if request.method == 'POST':
        student_name = request.form['student_name']
        class_id = request.form['class_id']

        db.students.update_one({'student_id': student_id}, {'$set': {
            'student_name': student_name,
            'class_id': class_id
        }})
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug= True)
