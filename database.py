from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    db = client['career_guidance']
    return db

from flask import Blueprint
from bson import ObjectId
from datetime import datetime

auth = Blueprint('auth', __name__)
from app import mongo  # Adjust this import based on your app structure

@auth.route('/seed_jobs')
def seed_jobs():
    sample_jobs = [
        {
            "title": "Frontend Developer",
            "company": "Techify Inc.",
            "location": "Remote",
            "required_skills": ["HTML", "CSS", "JavaScript", "React"],
            "posted_on": datetime.utcnow()
        },
        {
            "title": "Data Analyst",
            "company": "DataMetrics",
            "location": "Bangalore",
            "required_skills": ["Python", "SQL", "Pandas", "Data Visualization"],
            "posted_on": datetime.utcnow()
        },
        {
            "title": "Backend Developer",
            "company": "CodeCrafters",
            "location": "Hyderabad",
            "required_skills": ["Python", "Flask", "MongoDB", "APIs"],
            "posted_on": datetime.utcnow()
        },
        {
            "title": "Machine Learning Engineer",
            "company": "AI Works",
            "location": "Remote",
            "required_skills": ["Python", "TensorFlow", "Scikit-learn", "Data Preprocessing"],
            "posted_on": datetime.utcnow()
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudCore",
            "location": "Chennai",
            "required_skills": ["Docker", "Kubernetes", "CI/CD", "Linux"],
            "posted_on": datetime.utcnow()
        }
    ]

    result = mongo.db.jobs.insert_many(sample_jobs)
    return f"Inserted {len(result.inserted_ids)} sample jobs!"

