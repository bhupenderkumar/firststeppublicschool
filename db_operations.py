# db_operations.py

from bson import ObjectId
from flask import app 
from flask_pymongo import PyMongo
from pymongo import MongoClient
from gridfs import GridFS
import os
import bcrypt
INIT =False;
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/school_management')
client = MongoClient(mongo_uri)
db = client.school_management
fs = GridFS(db)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')
mongo_uri = os.environ.get('MONGO_URI')
app.config["MONGO_URI"] = mongo_uri
mongo = PyMongo(app)

# Utility Functions

def find_user(username):
   return db.users.find_one({'username': username})

def update_grievance_response(grievance_id, response_text):
    result = db.grievances.update_one(
        {"grievance_id": grievance_id},
        {"$set": {"school_response": response_text}}
    )
    return result.matched_count > 0
def get_classes_from_db():
   classes_collection = db.classes
   all_classes = classes_collection.find()
   return [cls['name'] for cls in all_classes]

def add_grievance(grievance):
    db.grievances.insert_one(grievance)

def find_grievance_by_user_id(user_id):
    return db.grievances.find({"user_id": user_id});

def edit_profile(form_data,username):
    return db.users.update_one({'username': username}, {'$set': form_data},  upsert=True)
def add_fees(fee_data):
    db.fees.insert_one(fee_data)

def find_all_grievance(user_id):
    return db.grievances.find({"user_id": user_id});

def get_student_from_db(student_id):
    return db.students.find_one({'_id': student_id})

def load_user_from_db(user_id):
    return db.students.find_one({'_id': ObjectId(user_id)})

def get_all_fees():
    return db.fees.find();

def find_fees_by_student_id(student_id):
    return list(db.fees.find({'student_id': student_id}))

def get_student_from_db_username(student_id):
    return db.students.find_one({'username': student_id})

def save_updated_student_data(student_id, updated_data):
    db.students.update_one({'_id': student_id}, {'$set': updated_data})

def fetch_students_from_db(class_name):
   students_query = db.students.find({'class_name': class_name}, {'username': 1, "_id": 1, 'fathername': 1})
   return [{
       "username": student["username"],
       "_id": str(student["_id"]),
       'fathername': student['fathername'],
   } for student in students_query]

def initialize_classes():
    # If the classes collection is empty, add the default classes
   if db.classes.count_documents({}) == 0:
      default_classes = ["Pre School", "Nursery", "L.K.G", "U.K.G", "I", "II", "III", "IV", "V"]
      for cls in default_classes:
          db.classes.insert_one({"name": cls})
   if not db.counters.find_one({"_id": "grievance"}):
       db.counters.insert_one({
           "_id": "grievance",
           "count": 0
       })
   else:
       print("Counter for 'grievance' already exists.")

