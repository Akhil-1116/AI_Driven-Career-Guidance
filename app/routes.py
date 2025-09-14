from flask import Blueprint, render_template, request, redirect, session, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from app import mongo
import pdfkit
import os
import re
from werkzeug.utils import secure_filename
import logging
from flask import Flask


app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Or any other level you want

# Now you can log like this
app.logger.info('App started.')

auth = Blueprint('auth', __name__)


@auth.route('/')
def home():
    return render_template('index.html')  # with login/signup links


# ========== User Registration ==========
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        users_collection = mongo.db.users
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return "User already exists"

        hashed_pw = generate_password_hash(password)
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_pw,
            "role": role
        })
        return redirect('/login')
    
    return render_template('register.html')


# ========== User Login ==========
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = mongo.db.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'student':
                return redirect('/student/dashboard')
            else:
                return redirect('/jobseeker/dashboard')

        return "Invalid credentials"
    return render_template('login.html')


# ========== Logout ==========
@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ========== Student Dashboard ==========

@auth.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/login')
    return render_template('student_dashboard.html', username=session['username'])


@auth.route('/jobseeker/dashboard')
def jobseeker_dashboard():
    if 'user_id' not in session or session.get('role') != 'job_seeker':
        return redirect('/login')

    user_id = session['user_id']
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    # Get user data to pass to the template
    username = user['username']

    return render_template('jobseeker_dashboard.html', username=session['username'])

@auth.route('/student/career_roadmap', methods=['GET', 'POST'])
def career_roadmap():
    roadmap = None
    if request.method == 'POST':
        ambition = request.form['ambition'].strip().lower()

        career_data = {
    'ias': {
        'steps': [
            'Complete 10+2 in any stream',
            "Pursue a Bachelor's degree in any discipline",
            'Prepare for and crack the UPSC Civil Services Examination',
            'Undergo training at Lal Bahadur Shastri National Academy of Administration',
            'Serve as an IAS officer in administrative roles'
        ],
        'education': '''In Intermediate (10+2): Any stream.<br>
            Degree: Bachelor's degree in any discipline (3–4 years)<br>
            Exam: <a href="https://upsc.gov.in" class="text-blue-600 underline">UPSC Civil Services Exam</a><br>
            • Preliminary Exam<br>• Mains<br>• Interview''',
        'training': 'Selected candidates train at the Lal Bahadur Shastri National Academy of Administration.',
        'image': 'ias.jpg'  # store in static folder
    },
    'data scientist': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor's in Computer Science/Stats/IT",
            'Learn Python, SQL, Machine Learning, Data Analysis',
            'Build a strong portfolio with projects',
            'Apply for roles or pursue a Master’s in Data Science'
        ],
        'education': 'Maths + CS in 10+2, Bachelor’s in CS/Stats/IT. Optional: M.Sc. in Data Science.',
        'training': 'Use platforms like Coursera, edX, Kaggle to build skills.',
        'image': 'tech.jpg'
    },
    'ips': {
        'steps': [
            'Complete 10+2 in any stream',
            "Pursue a Bachelor's degree in any discipline",
            'Prepare for and crack the UPSC IPS Examination',
            'Undergo training at the Sardar Vallabhbhai Patel National Police Academy',
            'Serve as an IPS officer in law enforcement and administrative roles'
        ],
        'education': '''In Intermediate (10+2): Any stream.<br>
            Degree: Bachelor's degree in any discipline (3–4 years)<br>
            Exam: <a href="https://upsc.gov.in" class="text-blue-600 underline">UPSC Civil Services Exam (IPS)</a><br>
            • Preliminary Exam<br>• Mains<br>• Interview''',
        'training': 'Selected candidates train at the Sardar Vallabhbhai Patel National Police Academy.',
        'image': 'ias.jpg'
    },
    'ifs': {
        'steps': [
            'Complete 10+2 in Science (preferably)',
            "Pursue a Bachelor's degree in any discipline",
            'Prepare for and crack the UPSC IFS Examination',
            'Undergo training at the Indira Gandhi National Forest Academy',
            'Serve as an IFS officer in environmental conservation roles'
        ],
        'education': '''In Intermediate (10+2): Science stream.<br>
            Degree: Bachelor's degree in any discipline (3–4 years)<br>
            Exam: <a href="https://upsc.gov.in" class="text-blue-600 underline">UPSC Civil Services Exam (IFS)</a><br>
            • Preliminary Exam<br>• Mains<br>• Interview''',
        'training': 'Selected candidates train at the Indira Gandhi National Forest Academy.',
        'image': 'ias.jpg'
    },
    'doctor': {
        'steps': [
            'Complete 10+2 with Physics, Chemistry, Biology',
            "Pursue an MBBS degree (5 years)",
            'Internship and gain clinical experience',
            'Prepare for Post-Graduate entrance exams (optional)',
            'Specialize in a field or practice as a general physician'
        ],
        'education': '''In Intermediate (10+2): Physics, Chemistry, Biology.<br>
            Degree: MBBS (5 years). Optional: Post-Graduation (MD/MS).<br>
            Exam: <a href="https://neet.nta.nic.in" class="text-blue-600 underline">NEET</a> (National Eligibility cum Entrance Test)<br> 
            • NEET UG Exam<br>• NEET PG (for Post-Graduation)''',
        'training': 'Internship at a medical college, hands-on clinical experience.',
        'image': 'tech2.webp'
    },
    'lawyer': {
        'steps': [
            'Complete 10+2 in any stream',
            "Pursue a 5-year LLB degree or 3-year LLB after graduation",
            'Prepare for and crack the Common Law Admission Test (CLAT) or Law School Admission Test (LSAT)',
            'Complete internship in law firms or courts',
            'Enroll in Bar Council and start practicing law'
        ],
        'education': '''In Intermediate (10+2): Any stream.<br>
            Degree: 5-year integrated LLB or 3-year LLB (after graduation).<br>
            Exam: <a href="https://clat.ac.in" class="text-blue-600 underline">CLAT</a> or <a href="https://www.lsac.org" class="text-blue-600 underline">LSAT</a><br> 
            • CLAT/LSAT Exam<br>• LLB degree (5/3 years)''',
        'training': 'Internship with lawyers or at courts for hands-on experience.',
        'image': 'ias.jpg'
    },
    'entrepreneur': {
        'steps': [
            'Complete 10+2 in any stream',
            "Pursue a Bachelor's degree in Business/Commerce (optional)",
            'Identify and develop a business idea',
            'Create a business plan, secure funding, and launch your business',
            'Scale your business and manage operations'
        ],
        'education': '''In Intermediate (10+2): Any stream.<br>
            Degree: Optional, business or commerce background helps.<br>
            Focus: Entrepreneurship and business management.<br>
            Resources: Online entrepreneurship courses, startup mentors.''',
        'training': 'Join business incubators, startup programs, or mentorship networks.',
        'image': 'tech2.webp'
    },
    'scientist': {
        'steps': [
            'Complete 10+2 with Science stream (Physics/Chemistry/Biology)',
            "Pursue a B.Sc. in your field of interest",
            'Specialize through a Master’s or Ph.D.',
            'Join research institutions or universities',
            'Publish research papers and contribute to scientific advancements'
        ],
        'education': '''In Intermediate (10+2): Science stream (Physics/Chemistry/Biology).<br>
            Degree: B.Sc. (3 years), M.Sc./Ph.D. (optional, but important for research).<br>
            Focus: Research, innovation, and advanced learning.''',
        'training': 'Work in laboratories, research institutes, or universities for hands-on experience.',
        'image': 'ias.jpg'
    },
    'software engineer': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, IT, or related field",
            'Learn programming languages (Java, C++, Python, etc.)',
            'Build a strong portfolio with personal or open-source projects',
            'Apply for software engineering roles in tech companies'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/IT (4 years).<br>
            Focus: Programming languages, Algorithms, Data Structures.''',
        'training': 'Take coding bootcamps, internships, and online courses (e.g., Coursera, edX).',
        'image': 'tech2.webp'
    },
    'web developer': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, Web Development, or related field",
            'Learn front-end and back-end development (HTML, CSS, JavaScript, Node.js, etc.)',
            'Build a portfolio with projects, including responsive websites and web apps',
            'Apply for web developer roles in companies or freelance'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/IT (4 years), or Web Development bootcamp.<br>
            Focus: Front-end, back-end, databases, and web technologies.''',
        'training': 'Internships, online coding challenges, and projects on GitHub.',
        'image': 'tech.jpg'
    },
    'mobile app developer': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, IT, or related field",
            'Learn programming languages (Swift, Kotlin, Java, React Native)',
            'Build a portfolio with mobile app projects for iOS/Android',
            'Apply for mobile app developer roles or freelance'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/IT (4 years).<br>
            Focus: Mobile app development, frameworks, UI/UX design.''',
        'training': 'Internships, app development bootcamps, and real-world projects.',
        'image': 'tech2.webp'
    },
    'data analyst': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor's degree in Computer Science, Statistics, or related field",
            'Learn data analysis tools like Excel, SQL, Python, R, and visualization tools',
            'Build a portfolio with data analysis projects and Kaggle competitions',
            'Apply for data analyst roles in companies'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/Statistics (3–4 years).<br>
            Focus: Data collection, cleaning, analysis, and visualization tools.''',
        'training': 'Use platforms like Coursera, DataCamp, or Kaggle for hands-on learning.',
        'image': 'tech.jpg'
    },
    'ux/ui designer': {
        'steps': [
            'Complete 10+2 with any stream',
            "Pursue a Bachelor’s degree in Design, Computer Science, or related field",
            'Learn design principles, wireframing, prototyping tools (Figma, Sketch, Adobe XD)',
            'Build a portfolio with design projects, wireframes, and prototypes',
            'Apply for UX/UI designer roles or freelance'
        ],
        'education': '''In Intermediate (10+2): Any stream.<br>
            Degree: B.Des., B.Tech. (with a specialization in UI/UX), or Design bootcamp.<br>
            Focus: User experience, user interface design, prototyping, and wireframing.''',
        'training': 'Join design workshops, UX bootcamps, or online design communities.',
        'image': 'tech.jpg'
    },
    'network engineer': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, Network Engineering, or related field",
            'Learn networking concepts, protocols, and tools (CCNA, TCP/IP, DNS, etc.)',
            'Get certified in network management (CCNA, CompTIA Network+)',
            'Apply for network engineer roles or internships'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/IT/Networking (4 years).<br>
            Focus: Network management, security, and troubleshooting.''',
        'training': 'Obtain certifications like CCNA or CompTIA, and work on real network setups.',
        'image': 'tech2.webp'
    },
    'cybersecurity analyst': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, Information Security, or related field",
            'Learn cybersecurity concepts, ethical hacking, firewalls, encryption, etc.',
            'Obtain cybersecurity certifications (e.g., CEH, CISSP, CompTIA Security+)',
            'Apply for cybersecurity analyst roles'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/Information Security (4 years).<br>
            Focus: Ethical hacking, network security, encryption.''',
        'training': 'Gain hands-on experience with cybersecurity labs, penetration testing tools.',
        'image': 'tech.jpg'
    },
    'cloud architect': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, IT, or related field",
            'Learn cloud platforms (AWS, Azure, Google Cloud) and architecture design',
            'Obtain cloud certifications (e.g., AWS Certified Solutions Architect)',
            'Apply for cloud architect roles'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/IT (4 years).<br>
            Focus: Cloud computing, architecture design, and cloud management platforms.''',
        'training': 'Obtain cloud certifications and work on cloud-related projects.',
        'image': 'tech.jpg'
    },
    'police': {
    'steps': [
        'Complete 10+2 in any stream',
        'Clear state-level or national police recruitment exams (like SSC, UPSC CAPF, or state PSC exams)',
        'Pass physical fitness tests and medical examinations',
        'Undergo police training at a designated academy',
        'Join the police force as a Sub-Inspector, Constable, or other officer, depending on qualification and rank'
    ],
    'education': '''In Intermediate (10+2): Any stream.<br>
        Degree: Optional but preferred for higher positions.<br>
        Exam: <ul>
            <li><a href="https://ssc.nic.in" class="text-blue-600 underline">SSC CPO (for Sub-Inspector)</a></li>
            <li><a href="https://upsc.gov.in" class="text-blue-600 underline">UPSC CAPF</a></li>
            <li>State-level Police Constable or SI exams</li>
        </ul>''',
    'training': 'Recruits undergo rigorous physical and tactical training at a police training academy.',
    'image': 'ias.jpg'  # You can use a relevant image name here, or fetch dynamically
},
    'artificial intelligence engineer': {
        'steps': [
            'Complete 10+2 with Math and Computer Science',
            "Pursue a Bachelor’s degree in Computer Science, AI, or related field",
            'Learn AI concepts, machine learning algorithms, deep learning frameworks (TensorFlow, PyTorch)',
            'Build a portfolio with AI-based projects',
            'Apply for AI engineer roles or pursue a Master’s in AI or Machine Learning'
        ],
        'education': '''In Intermediate (10+2): Maths + Computer Science.<br>
            Degree: B.Tech./B.Sc. in Computer Science/AI (4 years).<br>
            Focus: AI algorithms, machine learning, neural networks, deep learning.''',
        'training': 'Work on Kaggle competitions, AI research, and participate in AI-related communities.',
        'image': 'tech2.webp'
    }
}


        roadmap = career_data.get(ambition, {
            'steps': ['Career roadmap not found. Please try a different ambition.'],
            'education': '',
            'training': '',
            'image': 'default.jpg'
        })

    return render_template('career_roadmap.html', roadmap=roadmap)

from flask import render_template, request, Blueprint

# Assuming 'auth' is your Blueprint name
@auth.route('/student/skill_builder', methods=['GET', 'POST'])
def skill_builder():
    skills_data = {
        'computer_science': [
            {"name": "Python", "level": "Intermediate"},
            {"name": "JavaScript", "level": "Beginner"},
            {"name": "Machine Learning", "level": "Advanced"}
        ],
        'mechanical': [
            {"name": "Thermodynamics", "level": "Intermediate"},
            {"name": "Fluid Mechanics", "level": "Advanced"},
            {"name": "Strength of Materials", "level": "Beginner"}
        ],
        'civil': [
            {"name": "AutoCAD Civil 3D", "level": "Intermediate"},
            {"name": "STAAD.Pro", "level": "Advanced"},
            {"name": "Surveying", "level": "Beginner"}
        ],
        'electrical': [
            {"name": "Circuit Analysis", "level": "Intermediate"},
            {"name": "Power Systems", "level": "Advanced"},
            {"name": "Embedded Systems", "level": "Beginner"}
        ],
        'electronics': [
            {"name": "VLSI Design", "level": "Intermediate"},
            {"name": "PCB Design", "level": "Advanced"},
            {"name": "Signal Processing", "level": "Beginner"}
        ],
        'it': [
            {"name": "Networking", "level": "Intermediate"},
            {"name": "Cloud Computing", "level": "Advanced"},
            {"name": "Cybersecurity", "level": "Beginner"}
        ],
        'chemical': [
            {"name": "Process Simulation", "level": "Intermediate"},
            {"name": "Thermodynamics", "level": "Advanced"},
            {"name": "Heat Transfer", "level": "Beginner"}
        ]
    }

    if request.method == 'POST':
        field = request.form['field']
        # Check if field is present in the skills data
        skills = skills_data.get(field, [])
        return render_template('skill_builder.html', skills=skills)

    return render_template('skill_builder.html', skills=[])

# ========== Resume Builder ==========
@auth.route('/student/resume_builder', methods=['GET', 'POST'])
def resume_builder():
    if request.method == 'POST':
        user_id = session.get('user_id')
        users_collection = mongo.db.users

        # Collecting form data (excluding photo)
        data = {
            "name": request.form['name'],
            "email": request.form['email'],
            "phone": request.form['phone'],
            "address": request.form['address'],
            "linkedin": request.form['linkedin'],
            "github": request.form['github'],
            "activity_title": request.form['activity_title'],
            "activity_description": request.form['activity_description'],
            "education": {
                "degree": request.form['degree'],
                "college": request.form['college'],
                "year": request.form['year'],
                "GPA": request.form['GPA']
            },
            "skills": [skill.strip() for skill in request.form['skills'].split(',') if skill.strip()],
            "projects": [{
                "project_title": request.form.get('project_title', ''),
                "project_description": request.form.get('project_description', ''),
                "project_technologies": [tech.strip() for tech in request.form.get('project_technologies', '').split(',') if tech.strip()],
                "project_date": request.form.get('project_date', '')
            }],
            "certifications": [cert.strip() for cert in request.form.get('certifications', '').split(',') if cert.strip()],
        }

        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"profile": data}}
        )

        return redirect('/student/dashboard')

    return render_template('resume_builder.html')


# PDFKit config for Windows
PDFKIT_CONFIG = pdfkit.configuration()
PDFKIT_OPTIONS = {
    'enable-local-file-access': True,
    'encoding': 'UTF-8',
    'page-size': 'A4',
    'no-outline': True,
    'disable-smart-shrinking': True,
    'load-error-handling': 'ignore'
}

from flask import current_app  # Import current_app

@auth.route('/student/view_resume', methods=['GET', 'POST'])
def view_resume():
    user_id = session.get('user_id')
    if not user_id:
        return "Unauthorized access. Please log in.", 401

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return "User not found.", 404

    resume_data = user.get('profile', {})
    if not resume_data:
        return "Resume data not found.", 404

    # Handle PDF generation logic
    safe_filename = re.sub(r'[\\/*?:"<>|]', "_", user.get('username', 'resume'))
    pdf_filename = f"{safe_filename}_resume.pdf"
    
    # Use Flask's static folder for storing the generated PDF
    static_dir = os.path.join(os.getcwd(), 'app', 'static')
    pdf_path = os.path.join(static_dir, pdf_filename)
    os.makedirs(static_dir, exist_ok=True)

    if request.method == 'POST':
        try:
            rendered_html = render_template('resume_template.html', resume=resume_data)
    # Generate PDF and get command line (for debugging)
            pdfkit.from_string(rendered_html, pdf_path, configuration=PDFKIT_CONFIG, options=PDFKIT_OPTIONS)
        except Exception as e:
            current_app.logger.error(f"PDF generation failed: {e}")
            return f"PDF generation failed: {e}", 500

        # Check if the PDF was created successfully
        if not os.path.exists(pdf_path):
            return "PDF generation failed: File not created.", 500

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )

    # Handle GET request to display resume
    return render_template('view_resume.html', resume=resume_data)
# === Flask Route for Project Ideas ===

import json
from flask import render_template, request, session, redirect, url_for

# Sample list of 50 project ideas (you can expand to 100+ later)
ALL_PROJECT_IDEAS = [
    {"title": "Smart Attendance System", "category": "AI/ML", "difficulty": "Intermediate", "description": "Mark attendance using facial recognition."},
    {"title": "Flask Chat App", "category": "Web Dev", "difficulty": "Intermediate", "description": "Live chat app with Flask and Socket.IO."},
    {"title": "Expense Tracker", "category": "Data Science", "difficulty": "Beginner", "description": "Track and visualize personal expenses."},
    {"title": "Voice Assistant", "category": "AI/ML", "difficulty": "Advanced", "description": "Build your own voice-controlled virtual assistant."},
    {"title": "Blog Platform", "category": "Web Dev", "difficulty": "Intermediate", "description": "A full-stack blog app with Flask and MongoDB."},
    {"title": "Portfolio Website", "category": "Web Dev", "difficulty": "Beginner", "description": "Personal portfolio using HTML/CSS/JS."},
    {"title": "Resume Parser", "category": "AI/ML", "difficulty": "Advanced", "description": "Extract structured info from resumes using NLP."},
    {"title": "To-Do App with Drag & Drop", "category": "Web Dev", "difficulty": "Intermediate", "description": "Kanban-style to-do list with drag-and-drop UI."},
    {"title": "Weather Dashboard", "category": "Web Dev", "difficulty": "Beginner", "description": "Weather forecast app using OpenWeatherMap API."},
    {"title": "Online Quiz App", "category": "Web Dev", "difficulty": "Beginner", "description": "MCQ-based quiz system with timer."},
    # Add the next 100+ ideas below...
    {"title": "Netflix Data Analysis", "category": "Data Science", "difficulty": "Beginner", "description": "Analyze Netflix data for viewer trends."},
    {"title": "COVID-19 Tracker", "category": "Data Science", "difficulty": "Intermediate", "description": "Real-time COVID stats with visualizations."},
    {"title": "Crime Rate Prediction", "category": "Data Science", "difficulty": "Advanced", "description": "Predict crime trends using regression models."},
    {"title": "E-commerce Sales Dashboard", "category": "Data Science", "difficulty": "Intermediate", "description": "Analyze sales and customer data for trends."},
    {"title": "Air Quality Index Monitor", "category": "Data Science", "difficulty": "Intermediate", "description": "Visualize air quality data using APIs."},
    {"title": "Customer Segmentation", "category": "Data Science", "difficulty": "Advanced", "description": "Cluster users based on shopping behavior."},
    {"title": "IPL Score Analyzer", "category": "Data Science", "difficulty": "Beginner", "description": "Plot and analyze IPL cricket match scores."},
    {"title": "Stock Market Visualizer", "category": "Data Science", "difficulty": "Intermediate", "description": "Display trends and patterns from stock data."},
    {"title": "Global Temperature Trends", "category": "Data Science", "difficulty": "Intermediate", "description": "Study climate change using global datasets."},
    {"title": "Road Accident Visualizer", "category": "Data Science", "difficulty": "Advanced", "description": "Analyze accident hotspots from traffic data."},
    {"title": "Smart Home Automation", "category": "IoT", "difficulty": "Advanced", "description": "Control appliances using IoT and sensors."},
    {"title": "Smart Parking System", "category": "IoT", "difficulty": "Intermediate", "description": "Find and reserve parking spaces automatically."},
    {"title": "Home Security System", "category": "IoT", "difficulty": "Advanced", "description": "Motion-detecting alert and camera system."},
    {"title": "Voice-Controlled Lights", "category": "IoT", "difficulty": "Beginner", "description": "Use voice commands to control lighting."},
    {"title": "IoT Weather Station", "category": "IoT", "difficulty": "Intermediate", "description": "Monitor temperature, humidity and air pressure."},
    {"title": "Fitness Band Interface", "category": "IoT", "difficulty": "Advanced", "description": "Simulate a fitness band UI and backend."},
    {"title": "Water Level Monitor", "category": "IoT", "difficulty": "Beginner", "description": "Track water tank levels with sensors."},
    {"title": "Smart Farming System", "category": "IoT", "difficulty": "Advanced", "description": "Soil moisture-based irrigation control."},
    {"title": "Car Accident Alert System", "category": "IoT", "difficulty": "Intermediate", "description": "Notify emergency services during crashes."},
    {"title": "IoT Pet Feeder", "category": "IoT", "difficulty": "Intermediate", "description": "Feed pets remotely using a mobile app."},
    {"title": "Password Strength Checker", "category": "Cybersecurity", "difficulty": "Beginner", "description": "Evaluate password strength and provide feedback."},
    {"title": "Keylogger Detection Tool", "category": "Cybersecurity", "difficulty": "Advanced", "description": "Detect malicious keylogging programs on a system."},
    {"title": "Secure File Sharing App", "category": "Cybersecurity", "difficulty": "Intermediate", "description": "Encrypt and share files securely between users."},
    {"title": "Firewall Simulator", "category": "Cybersecurity", "difficulty": "Intermediate", "description": "Simulate a firewall system for packet filtering."},
    {"title": "Phishing Website Detector", "category": "Cybersecurity", "difficulty": "Advanced", "description": "Detect and warn users about fake websites."},
    {"title": "Encrypted Chat App", "category": "Cybersecurity", "difficulty": "Intermediate", "description": "Chat with end-to-end encryption."},
    {"title": "Data Breach Visualizer", "category": "Cybersecurity", "difficulty": "Beginner", "description": "Show historical data breaches with visuals."},
    {"title": "Secure Login System", "category": "Cybersecurity", "difficulty": "Intermediate", "description": "Implement 2FA and hashing for secure logins."},
    {"title": "Network Packet Sniffer", "category": "Cybersecurity", "difficulty": "Advanced", "description": "Monitor and analyze network traffic."},
    {"title": "Cybersecurity Awareness Quiz", "category": "Cybersecurity", "difficulty": "Beginner", "description": "Interactive quiz to educate about threats."},
    {"title": "Daily Habit Tracker", "category": "Android Dev", "difficulty": "Beginner", "description": "Android app to track and build daily habits."},
    {"title": "Health & Fitness App", "category": "Android Dev", "difficulty": "Intermediate", "description": "Workout and meal tracker mobile app."},
    {"title": "Expense Splitter App", "category": "Android Dev", "difficulty": "Intermediate", "description": "Split bills and manage group expenses."},
    {"title": "Event Reminder App", "category": "Android Dev", "difficulty": "Beginner", "description": "Notify users of tasks or events."},
    {"title": "Offline Notes App", "category": "Android Dev", "difficulty": "Beginner", "description": "Create and store notes offline."},
    {"title": "Food Delivery UI Clone", "category": "Android Dev", "difficulty": "Intermediate", "description": "Replicate UI of Zomato or Swiggy."},
    {"title": "Student Attendance App", "category": "Android Dev", "difficulty": "Intermediate", "description": "Manage student attendance records."},
    {"title": "E-book Reader App", "category": "Android Dev", "difficulty": "Advanced", "description": "Android reader for EPUB/PDF books."},
    {"title": "QR Code Scanner", "category": "Android Dev", "difficulty": "Beginner", "description": "Scan and generate QR codes."},
    {"title": "Bluetooth File Transfer", "category": "Android Dev", "difficulty": "Advanced", "description": "Transfer files using Bluetooth."},
    {"title": "Simple Blockchain Simulator", "category": "Blockchain", "difficulty": "Intermediate", "description": "Understand blockchain by simulating blocks."},
    {"title": "Voting System on Blockchain", "category": "Blockchain", "difficulty": "Advanced", "description": "Transparent voting using Ethereum."},
    {"title": "Crypto Wallet UI", "category": "Blockchain", "difficulty": "Intermediate", "description": "Design frontend of a crypto wallet."},
    {"title": "Smart Contract for Certificate", "category": "Blockchain", "difficulty": "Advanced", "description": "Issue and verify digital certificates."},
    {"title": "NFT Gallery App", "category": "Blockchain", "difficulty": "Intermediate", "description": "Display and track NFTs for a wallet."},
    {"title": "Decentralized Chat App", "category": "Blockchain", "difficulty": "Advanced", "description": "Chat using decentralized protocols."},
    {"title": "Token Airdrop Platform", "category": "Blockchain", "difficulty": "Intermediate", "description": "Simulate crypto token distribution."},
    {"title": "Crowdfunding with Smart Contracts", "category": "Blockchain", "difficulty": "Advanced", "description": "Fundraising DApp using Ethereum."},
    {"title": "Land Registry System", "category": "Blockchain", "difficulty": "Advanced", "description": "Secure land records using blockchain."},
    {"title": "Decentralized Voting Poll", "category": "Blockchain", "difficulty": "Intermediate", "description": "Anonymous voting using smart contracts."},
    {"title": "AR Measuring Tape", "category": "AR/VR", "difficulty": "Intermediate", "description": "Measure real-world objects using AR."},
    {"title": "Virtual Campus Tour", "category": "AR/VR", "difficulty": "Advanced", "description": "Explore college via a virtual reality app."},
    {"title": "AR Chemistry Lab", "category": "AR/VR", "difficulty": "Advanced", "description": "Visualize molecules and reactions in AR."},
    {"title": "3D Room Planner", "category": "AR/VR", "difficulty": "Intermediate", "description": "Design interior layouts in virtual space."},
    {"title": "AR Flashcards for Learning", "category": "AR/VR", "difficulty": "Beginner", "description": "Educational cards that show 3D models."},
    {"title": "Virtual Art Gallery", "category": "AR/VR", "difficulty": "Advanced", "description": "Tour a 3D gallery of artwork."},
    {"title": "AR Solar System Explorer", "category": "AR/VR", "difficulty": "Beginner", "description": "Visualize planets using augmented reality."},
    {"title": "VR Meditation Space", "category": "AR/VR", "difficulty": "Intermediate", "description": "Immersive environment for meditation."},
    {"title": "AR Business Card", "category": "AR/VR", "difficulty": "Intermediate", "description": "Scan card to view 3D profile or intro."},
    {"title": "Historical Site VR Tour", "category": "AR/VR", "difficulty": "Advanced", "description": "Experience ancient sites in virtual reality."}
]


@auth.route('/student/project_ideas', methods=['GET', 'POST'])
def project_ideas():
    user_id = session.get('user_id')
    users_collection = mongo.db.users

    category_filter = request.args.get('category', '').lower()
    difficulty_filter = request.args.get('difficulty', '').lower()

    filtered_ideas = [idea for idea in ALL_PROJECT_IDEAS if
                      (category_filter in idea['category'].lower() if category_filter else True) and
                      (difficulty_filter in idea['difficulty'].lower() if difficulty_filter else True)]

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    saved = user.get("saved_ideas", []) if user else []

    # Extract unique categories and difficulties for filters
    all_categories = sorted(set(idea['category'] for idea in ALL_PROJECT_IDEAS))
    all_difficulties = sorted(set(idea['difficulty'] for idea in ALL_PROJECT_IDEAS))

    return render_template('project_ideas.html', ideas=filtered_ideas, saved_ideas=saved,
                           all_categories=all_categories, all_difficulties=all_difficulties)

@auth.route('/student/save_idea', methods=['POST'])
def save_idea():
    user_id = session.get('user_id')
    idea_title = request.form.get('title')
    users_collection = mongo.db.users

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"saved_ideas": idea_title}}  # avoid duplicates
    )

    return redirect(url_for('auth.project_ideas'))

@auth.route('/student/remove_idea', methods=['POST'])
def remove_idea():
    user_id = session.get('user_id')
    idea_title = request.form.get('title')
    users_collection = mongo.db.users

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"saved_ideas": idea_title}}  # Remove from saved list
    )

    return redirect(url_for('auth.project_ideas'))

# ========== Resume Builder ==========
@auth.route('/jobseeker/resume_builderj', methods=['GET', 'POST'])
def resume_builderj():
    if request.method == 'POST':
        user_id = session.get('user_id')
        users_collection = mongo.db.users

        # Collecting form data (excluding photo)
        data = {
            "name": request.form['name'],
            "email": request.form['email'],
            "phone": request.form['phone'],
            "address": request.form['address'],
            "linkedin": request.form['linkedin'],
            "github": request.form['github'],
            "activity_title": request.form['activity_title'],
            "activity_description": request.form['activity_description'],
            "education": {
                "degree": request.form['degree'],
                "college": request.form['college'],
                "year": request.form['year'],
                "GPA": request.form['GPA']
            },
            "skills": [skill.strip() for skill in request.form['skills'].split(',') if skill.strip()],
            "projects": [{
                "project_title": request.form.get('project_title', ''),
                "project_description": request.form.get('project_description', ''),
                "project_technologies": [tech.strip() for tech in request.form.get('project_technologies', '').split(',') if tech.strip()],
                "project_date": request.form.get('project_date', '')
            }],
            "certifications": [cert.strip() for cert in request.form.get('certifications', '').split(',') if cert.strip()],
        }

        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"profile": data}}
        )

        return redirect('/jobseeker/dashboard')

    return render_template('resume_builderj.html')


import shutil

wkhtmltopdf_path = shutil.which("wkhtmltopdf")
if wkhtmltopdf_path is None:
    raise RuntimeError("wkhtmltopdf is not installed or not in PATH.")

PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

PDFKIT_OPTIONS = {
    'enable-local-file-access': True,
    'encoding': 'UTF-8',
    'page-size': 'A4',
    'no-outline': True,
    'disable-smart-shrinking': True,
    'load-error-handling': 'ignore'
}

from flask import current_app  # Import current_app

@auth.route('/jobseeker/view_resumej', methods=['GET', 'POST'])
def view_resumej():
    user_id = session.get('user_id')
    if not user_id:
        return "Unauthorized access. Please log in.", 401

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return "User not found.", 404

    resume_data = user.get('profile', {})
    if not resume_data:
        return "Resume data not found.", 404

    # Handle PDF generation logic
    safe_filename = re.sub(r'[\\/*?:"<>|]', "_", user.get('username', 'resume'))
    pdf_filename = f"{safe_filename}_resume.pdf"
    
    # Use Flask's static folder for storing the generated PDF
    static_dir = os.path.join(os.getcwd(), 'app', 'static')
    pdf_path = os.path.join(static_dir, pdf_filename)
    os.makedirs(static_dir, exist_ok=True)

    if request.method == 'POST':
        try:
            rendered_html = render_template('resume_template.html', resume=resume_data)
    # Generate PDF and get command line (for debugging)
            pdfkit.from_string(rendered_html, pdf_path, configuration=PDFKIT_CONFIG, options=PDFKIT_OPTIONS)
        except Exception as e:
            current_app.logger.error(f"PDF generation failed: {e}")
            return f"PDF generation failed: {e}", 500

        # Check if the PDF was created successfully
        if not os.path.exists(pdf_path):
            return "PDF generation failed: File not created.", 500

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )

    # Handle GET request to display resume
    return render_template('view_resumej.html', resume=resume_data)



from flask import render_template, request, send_file
from fpdf import FPDF
import os


@auth.route('/interview_prep')
def interview_preparation():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('interview_preparation.html')


@auth.route('/jobseeker/profile_settings', methods=['GET', 'POST'])
def profile_settings():
    # Ensure the user is logged in
    if 'user_id' not in session or session.get('role') != 'job_seeker':
        return redirect('/login')

    user_id = session['user_id']
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if request.method == 'POST':
        # Handle profile information update (email, phone, address, etc.)
        updated_data = {}
        
        if 'name' in request.form:
            updated_data["profile.name"] = request.form['name']
        if 'email' in request.form:
            updated_data["profile.email"] = request.form['email']
        if 'phone' in request.form:
            updated_data["profile.phone"] = request.form['phone']
        if 'address' in request.form:
            updated_data["profile.address"] = request.form['address']
        
        # Handle password change (if provided)
        if 'password' in request.form and request.form['password']:
            password_hash = generate_password_hash(request.form['password'])
            updated_data["password"] = password_hash
        
        # Update the user's profile in the database
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updated_data}
        )

        return redirect('/jobseeker/dashboard')

    # Prepopulate the form with the current profile data
    profile_data = user.get('profile', {})
    return render_template('profile_settings.html', profile=profile_data)


@auth.route('/jobseeker/profile', methods=['GET', 'POST'])
def jobseeker_profile():
    if 'user_id' not in session or session.get('role') != 'job_seeker':
        return redirect('/login')

    user_id = ObjectId(session['user_id'])
    profile_collection = mongo.db.job_seekers
    existing_profile = profile_collection.find_one({"user_id": user_id})

    if request.method == 'POST':
        data = {
            "user_id": user_id,
            "full_name": request.form.get('full_name'),
            "phone": request.form.get('phone'),
            "location": request.form.get('location'),
            "bio": request.form.get('bio'),
            "skills": request.form.get('skills').split(','),
            "education": [{
                "degree": request.form.get('degree'),
                "institution": request.form.get('institution'),
                "year": request.form.get('year')
            }],
            "experience": [{
                "title": request.form.get('job_title'),
                "company": request.form.get('company'),
                "duration": request.form.get('duration'),
                "description": request.form.get('job_description')
            }],
            "certifications": request.form.get('certifications').split(',')
        }

        if existing_profile:
            profile_collection.update_one({"user_id": user_id}, {"$set": data})
        else:
            profile_collection.insert_one(data)

        return redirect('/jobseeker/profile')

    return render_template('jobseeker_profile.html', profile=existing_profile)
from flask import Blueprint, render_template, request
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import matplotlib.pyplot as plt
import numpy as np
import os


# Utility functions integrated here

def extract_skills_from_resume(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()

    skill_keywords = ['python', 'java', 'sql', 'html', 'css', 'javascript',
                      'machine learning', 'deep learning', 'data analysis', 
                      'communication', 'leadership', 'django', 'flask', 
                      'tensorflow', 'pandas', 'numpy', 'react', 'git']

    found_skills = [skill for skill in skill_keywords if skill in text.lower()]
    return list(set(found_skills))

def get_required_skills_for_role(role):
    skill_map = {
        'data scientist': ['python', 'pandas', 'numpy', 'machine learning', 'deep learning', 'sql', 'data analysis'],
        'web developer': ['html', 'css', 'javascript', 'react', 'django', 'flask', 'git'],
        'software engineer': ['python', 'java', 'git', 'communication', 'sql', 'leadership'],
        'ai engineer': ['python', 'tensorflow', 'deep learning', 'machine learning', 'numpy'],
    }
    if role is None:
        return []
    return skill_map.get(role.lower(), [])

def generate_pie_chart(user_skills_count, required_skills_count, save_path):
    # Validate inputs
    if user_skills_count is None or (isinstance(user_skills_count, float) and np.isnan(user_skills_count)):
        user_skills_count = 0
    if required_skills_count is None or (isinstance(required_skills_count, float) and np.isnan(required_skills_count)):
        required_skills_count = 0

    user_skills_count = max(0, int(user_skills_count))
    required_skills_count = max(0, int(required_skills_count))

    total_skills = user_skills_count + required_skills_count
    if total_skills == 0:
        # No chart to generate if no skills
        return False

    labels = ['Skills You Have', 'Skills To Learn']
    sizes = [user_skills_count, required_skills_count]
    colors = ['#66b3ff', '#ff9999']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    return True

@auth.route('/jobseeker/skill_suggestions', methods=['GET', 'POST'])
def skill_suggestions():
    if request.method == 'POST':
        role = request.form.get('desired_role')  # Match form field name
        resume = request.files.get('resume')

        if not resume or not role:
            return render_template('skill_suggestions.html', error="Please upload a resume and enter a role.")

        filename = secure_filename(resume.filename)
        upload_folder = os.path.join('app', 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        resume_path = os.path.join(upload_folder, filename)
        resume.save(resume_path)

        resume_skills = extract_skills_from_resume(resume_path)
        required_skills = get_required_skills_for_role(role)

        common_skills = set(resume_skills).intersection(set(required_skills))
        missing_skills = set(required_skills) - set(resume_skills)

        chart_filename = f'skill_pie_{filename}.png'  # Unique filename per upload
        chart_path = os.path.join(upload_folder, chart_filename)

        chart_generated = generate_pie_chart(len(common_skills), len(missing_skills), chart_path)

        return render_template('skill_suggestions.html',
                               role=role,
                               matched_skills=common_skills,
                               missing_skills=missing_skills,
                               chart_filename=chart_filename if chart_generated else None)
    return render_template('skill_suggestions.html')



