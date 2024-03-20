import io
import time
from bson import ObjectId
from flask import Flask, Response, flash, jsonify, render_template, request, redirect, url_for, session
from flask import  make_response
from fpdf import FPDF
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
mongo_uri = os.environ.get('MONGODB_URI')
# mongo_uri = 'localhost:27017'
app.config["MONGODB_URI"] = mongo_uri  # replace with your database URI
client = MongoClient(mongo_uri)
db = client.school
fs = GridFS(db)
from functools import wraps
from werkzeug.utils import secure_filename
filename = ".././etc/passwd"
safe_filename = secure_filename(filename)
from werkzeug.security import generate_password_hash
from flask import  send_file
UPLOAD_FOLDER = 'uploads'  # Create a folder in your project directory named 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required_with_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return render_template('404.html')

            user_id = session.get('user_id')
            user = db.students.find_one({'_id': ObjectId(user_id)})
            if not user or 'role' not in user or user['role'] != required_role:
                return render_template('404.html')

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return login_required_with_role('admin')(f)

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


@app.route("/transfer_certificates", methods=["GET", "POST"])
def transfer_certificates():
    return render_template('transfer_certificates.html')

@app.route("/regular_feedback", methods=["GET", "POST"])
@login_required
def regular_feedback():
    return render_template('regular_feedback.html')


@app.route("/holi", methods=["GET", "POST"])
def holi():
    classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
    if request.method == "GET":
        return render_template('holi.html', classes=classes)
    
    holi_data = extract_data_from_form(request.form)
    
    # Handle file upload
    if 'child_photo' in request.files:
        file = request.files['child_photo']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            with open(file_path, 'rb') as f:
                from bson import Binary
                holi_data['child_photo'] = Binary(f.read())
            os.remove(file_path)  # Remove the file after reading its content
    db.holi.insert_one(holi_data)
    flash("Child is Registered Successfully. Registered Child Name is " + holi_data.get('children_attending', ''), 'success')
    return redirect(url_for("holi"))

@app.route("/report_card", methods=["GET", "POST"])
def report_card():
    return render_template('report_card.html')
                                            


@app.route("/create_fees", methods=["GET", "POST"])
@login_required
@admin_required
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
    print(provided_password.encode('utf-8'))
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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        if db.students.find_one({'username': username}):
            return render_template('signup.html',  classes=get_classes_from_db(), error="Username already exists!")
        
        form_data = extract_data_from_form(request.form)
        hashed_password = hash_password(password)
        user_data = {
            **form_data,
            'username': username,
            'password': hashed_password,
            'role': role,
        }
        db.students.insert_one(user_data)
        
        return redirect(url_for('login'))
    
    return render_template('signup.html', classes=get_classes_from_db())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.students.find_one({'username': username})
        if user and verify_password(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['role'] = user['role']
            session['username'] = user['username']
            session['class_name'] = user['class_name']
            return redirect(url_for('home'))
        else:
            flash(f"Invalid username or password", 'danger')
        return render_template('login.html', error="Invalid username or password")
    
    if request.method == 'GET' and session.get('user_id') is not None:
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/home')
@login_required
def dashboard():
    user = load_user(session.get('user_id'))
    role = user['role']
    template_map = {
        'teacher': 'teacher_dashboard.html',
        'admin': 'admin_dashboard.html',
        'parents': 'parents_dashboard.html'
    }
    return render_template(template_map.get(role, 'dashboard.html'), username=user['username'])

MEDIA_FOLDER = './media'

@app.route('/media-page')
@login_required
def media_page():
    return render_template('media.html')


@app.route('/activities-plan')
@login_required
def activities_plan():
    return render_template('activities_plan.html')

@app.route('/list-media/<folder_name>')
@login_required
def list_media_in_folder(folder_name):
    folder_path = os.path.join(MEDIA_FOLDER, folder_name)
    
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    images = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
    videos = [f for f in files if f.endswith(('.mp4', '.avi', '.mkv'))]
    
    return jsonify({'images': images, 'videos': videos})


def get_classes_from_db():
    classes_collection = mongo.db.classes  # Assuming your collection is named 'classes'
    all_classes = classes_collection.find()
    return [cls['name'] for cls in all_classes]


def initialize_classes():
    default_classes = ["Pre Nursery", "Nursery", "L.K.G", "U.K.G", "I", "II", "III", "IV", "V"]    
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
    if not db.counters.find_one({"_id":"tc_id"}):
        db.counters.insert_one({"_id": "tc_id","count":1000})
    else:
        print("counter for tc already exists")
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
@admin_required
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
        flash(f"Error please check the request or contact admin dept  ", 'danger')
        return jsonify({'message': 'No attendance record found for the given ID'})


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

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = db.students.find_one({'username': session['username']})  
    if request.method == 'POST':
        # updateing as i want only few fields to be updated
        
        form_data = extract_data_from_form(request.form, user)
        file_data = handle_file_uploads(request.files, user)
        form_data.update(file_data)
        password = form_data['password']
        if not verify_password(user['password'], password):
            hashed_password = hash_password(password)
            form_data['password'] = hashed_password
        
        db.students.update_one({'username': session['username']}, {'$set': form_data},  upsert=True)
        return render_template('home.html')
    return render_template('edit_profile.html', admin=user)

def send_notification():
    # send the whats app notiication to admin first before send the notificatioin to parents
    admin = db.student.find({'role': 'admin'})
    for admin in admin:
        print(admin.phone_number)

@app.route("/answer_grievance", methods=["GET"])
@login_required
@admin_required
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

@app.route('/create_notification', methods=['POST','GET'])
@login_required
def create_notification():
    if session.get('role') != 'admin':
        return render_template('create_notification.html',classes=get_classes_from_db());
    if session.get('role') == 'admin':
        notifications = db.notifications.find()
    if request.method == 'GET':
        return render_template('create_notification.html',classes=get_classes_from_db(),notifications =notifications);
    elif request.method == 'POST':
        class_name = request.form.get('class_name')
        notification_text = request.form.get('notification_text') 
        raised_by = student_name = session.get('user_name')# Get multiple selected student IDs
        date = datetime.now()
        remaining_fields = extract_data_from_form(request_form=request.form)
        db.notifications.insert_one({
            **remaining_fields,
            'class_name': class_name,
            'raised_by': raised_by,
            'notification_text': notification_text,
            'date': date,
            'status': 'PENDING'
        })
        send_notification()
        flash("Records inserted successfully", 'success')
        notifications = list(db.notifications.find())
        return render_template('create_notification.html',classes=get_classes_from_db(),notifications =notifications);
    
    return render_template('create_notification.html',classes=get_classes_from_db(),notifications =notifications);

@app.route('/create_attendance', methods=['GET', 'POST'])
@login_required
@admin_required
def insert_attendance():
    if request.method == 'GET':
        return render_template('create_attendance.html', classes=get_classes_from_db())
    elif request.method == 'POST':
        try:
            class_name = request.form.get('class_name')
            student_ids = request.form.getlist('student_list[]')  # Get multiple selected student IDs
            date = datetime.now().date().strftime('%Y-%m-%d')
            print(class_name)
            print(student_ids)
            status = 'PRESENT'
            available = db.attendance.find({'class_name': class_name,'date': date})
            if available and available.count() > 0:
                 flash(f"Already attendance avaialble for {class_name} for  date {date} ", 'danger')
            else:   
                db.attendance.insert_one({
                    'class_name': class_name,
                    'student_ids': student_ids,
                    'date': date,
                    'status': status
                })
                flash("Records inserted successfully", 'success')
            return render_template('create_attendance.html', classes=get_classes_from_db())
        except Exception as e:
            flash("Error inserting records: " + str(e), 'danger')
            return render_template('create_attendance.html', classes=get_classes_from_db())
from datetime import datetime, date, time


from bson import ObjectId

@app.route('/fetch_attendance', methods=['GET', 'POST'])
@login_required
def fetch_attendance():
    admin = session.get('role')
    class_name = session.get('class_name')
    combined_data = []
    all_students = []
    date = request.form.get('date')
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        if admin == 'admin':
            attendance_list = list(db.attendance.find({'class_name': class_name, 'date': date}))
            for attendance in attendance_list:
                student_ids = attendance.get('student_ids', [])
                object_ids = [ObjectId(student_id) for student_id in student_ids]
                students = db.students.find({'_id': {'$in': object_ids}})
                for student in students:
                    student['attendance_data'] = attendance
                combined_data.extend(students)
        else:
            # For non-admin users
            attendance_list = db.attendance.find({'class_name': class_name, 'date': date})
            student_ids = [str(session.get('user_id'))]  # Assuming user_id is a string
            object_ids = [ObjectId(student_id) for student_id in student_ids]
            all_students = db.students.find({'_id': {'$in': object_ids}})
            combined_data.extend(all_students)
    else:
        current_user_id = str(session.get('user_id'))
        object_id = ObjectId(current_user_id)
        attendance_record = db.attendance.find_one({'student_ids': current_user_id})
        if attendance_record:
            student_details = db.students.find_one({'_id': object_id})
        combined_data = {**attendance_record, **student_details}
    
    return render_template('attendance.html', classes=get_classes_from_db(), attendance_list=combined_data, all_students=all_students, date=date)


def get_next_sequence(name):
    # First, check if the document exists
    counter_doc = db.counters.find_one({"_id": name})
    if counter_doc:
        db.counters.update_one({'_id':name}, {'$inc': {'count': 1}})
        return int(int(counter_doc["count"]) + 1)
    else:
        return 1;
    

@app.route('/fees')
@login_required
def fees():
    student_id = session.get('user_id')
    student_name = session.get('user_name')
    fees_list = []
    if session.get('role') == 'admin':
        fees_list = list(db.fees.find())
    else:
        fees_list = list(db.fees.find({'student_id': student_id}))
    return render_template('fees.html', fees_list=fees_list, student_name=student_name)

from flask import request


@app.route('/tcdetails/<tc_id>', methods=['GET'])
def tcdetails(tc_id):
    tc_record = db.tc.find_one({'_id':int(tc_id)})
    return render_template('tc_detail.html', tc_detail= tc_record);
    

@app.route('/tc_list', methods=['GET'])
@login_required
def get_tc_list():
    tc_list = db.tc.find()
    return render_template('tc_list.html',tc_list= tc_list)

@app.route('/create_tc', methods=['POST','GET'])
def create_tc():
    classes = get_classes_from_db()
    if request.method == 'GET':
        return render_template('create_tc.html', classes=classes)
    else:
        student_class = request.form.get('class_name')
        student_id = request.form.get('student_id')
        form_request = extract_data_from_request(request)
        student_data = db.students.find_one({'_id': ObjectId(student_id), 'class_name': student_class})
        if student_data:
            tc_id = get_next_sequence('tc_id')
            db.students.update_one({'_id': ObjectId(student_id)}, {'$set': {'inactive': True}})
            form_request["_id"] = tc_id
            form_request["student_name"] = student_data["username"]
            db.tc.insert_one(form_request)
        return render_template('create_tc.html', classes=classes)


@app.route("/raise_grievance", methods=["GET", "POST"])
@login_required
def raise_grievance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    if session.get('role') == 'admin':
        grievances = list(db.grievances.find())
    else:
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
        grievances = list(db.grievances.find({"user_id": user_id}))
        flash('Your grievance has been recorded!', 'success')
        classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
        return render_template('raise_grievance.html', classes=classes,grievances=grievances)
    else:
        grievances = list(db.grievances.find({"user_id": user_id}))
        classes = get_classes_from_db()  # Implement this function to fetch class names from MongoDB
        return render_template('raise_grievance.html', grievances=grievances,  classes=classes)

@app.route('/downloadfees/<fee_id>')
@login_required
def download_fee_receipt(fee_id):
    fee_data = db.fees.find_one({"_id": ObjectId(fee_id)})
    if not fee_data:
        return "Fee data not found", 404
    pdf = PDF()
    pdf_data= pdf.create_receipt(fee_data)
    pdf_bytes = pdf_data.output(dest='S').encode('ISO-8859-1')
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename="generated_pdf.pdf"'
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
    students = db.students.find({"$and": [{"class_name": class_name}, {"$or": [{"inactive": False}, {"inactive": {"$exists": False}}]}]})
    students_list = [
        {"username": student["username"],"fathername":student['fathername'],'class_name':student['class_name'], "_id": str(student["_id"])}
        for student in students
    ]
    return jsonify(students_list)

@app.route('/students')
@login_required
def students():
    if session.get('role') == 'admin':
        students = db.students.find()
        return render_template('students.html', students=students)
    return redirect(url_for('dashboard'))

@app.route('/grades')
@login_required
def grades():
    if session.get('role') == 'admin':
        grades = db.grades.find()
        return render_template('grades.html', grades=grades)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
