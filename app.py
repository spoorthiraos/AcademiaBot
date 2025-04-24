import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import secrets
from werkzeug.utils import secure_filename
import time
from utils import create_embeddings, get_relevant_context, save_upload_file
from classify import classify_use_case
import ollama
from utils import is_clean_text

# App configuration
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt', 'xlsx'}

logging.basicConfig(level=logging.DEBUG) 
logger = logging.getLogger(__name__)

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    logger.info(f"\nCreated upload folder: {app.config['UPLOAD_FOLDER']}\n")


# Simple user database (replace with a real database in production)
users = {
    'admin@amc.edu': {'password': 'admin@123', 'name': 'Admin User'},
    'student@amc.edu': {'password': 'student@123', 'name': 'Student User'},
    'spoorthis@amc.edu': {'password': 'spoorthi@123', 'name': 'Spoorthi S'},
    'charan@amc.edu': {'password': 'charan@123', 'name': 'Charan'},
    'moneshka@123': {'password': 'monesh@123', 'name': 'Monesh K A'},
    'arjundas@amc.edu': {'password': 'arjun@123', 'name': 'Arjun Das'},
    'karanreddy@amc.edu': {'password': 'karan@123', 'name': 'Karan Reddy'},
    'ananyareddy@amc.edu': {'password': 'ananya@123', 'name': 'Ananya Reddy'},
    'ananyakulkarni@amc.edu': {'password': 'ananya@123', 'name': 'Ananya Kulkarni'},
    'meeramehta@amc.edu': {'password': 'meera@123', 'name': 'Meera Mehta'},
    'adityakapoor@amc.edu': {'password': 'aditya@123', 'name': 'Aditya Kapoor'},
    'meerabansal@amc.edu': {'password': 'meera@123', 'name': 'Meera Bansal'},
    'arjunjoshi@amc.edu': {'password': 'arjun@123', 'name': 'Arjun Joshi'},
    'rajtiwari@amc.edu': {'password': 'raj@123', 'name': 'Raj Tiwari'},
    'nikhilpatel@amc.edu': {'password': 'nikhil@123', 'name': 'Nikhil Patel'},
    'kavyajoshi@amc.edu': {'password': 'kavya@123', 'name': 'Kavya Joshi'},
    'simranjoshi@amc.edu': {'password': 'simran@123', 'name': 'Simran Joshi'},
    'priyanair@amc.edu': {'password': 'priya@123', 'name': 'Priya Nair'},
    'karanmenon@amc.edu': {'password': 'karan@123', 'name': 'Karan Menon'},
    'simraniyer@amc.edu': {'password': 'simran@123', 'name': 'Simran Iyer'},
    'priyachatterjee@amc.edu': {'password': 'priya@123', 'name': 'Priya Chatterjee'},
    'divyaiyer@amc.edu': {'password': 'divya@123', 'name': 'Divya Iyer'},
    'sneharao@amc.edu': {'password': 'sneha@123', 'name': 'Sneha Rao'},
    'adityamenon@amc.edu': {'password': 'aditya@123', 'name': 'Aditya Menon'},
    'rahulchatterjee@amc.edu': {'password': 'rahul@123', 'name': 'Rahul Chatterjee'},
    'rohitmishra@amc.edu': {'password': 'rohit@123', 'name': 'Rohit Mishra'},
    'nehatiwari@amc.edu': {'password': 'neha@123', 'name': 'Neha Tiwari'},
    'kavyaghosh@amc.edu': {'password': 'kavya@123', 'name': 'Kavya Ghosh'},
    'kavyapatel@amc.edu': {'password': 'kavya@123', 'name': 'Kavya Patel'},
    'arjunreddy@amc.edu': {'password': 'arjun@123', 'name': 'Arjun Reddy'},
    'adityaverma@amc.edu': {'password': 'aditya@123', 'name': 'Aditya Verma'},
    'priyamenon@amc.edu': {'password': 'priya@123', 'name': 'Priya Menon'},
    'nikhilghosh@amc.edu': {'password': 'nikhil@123', 'name': 'Nikhil Ghosh'},
    'sahilkapoor@amc.edu': {'password': 'sahil@123', 'name': 'Sahil Kapoor'},
    'rahulrao@amc.edu': {'password': 'rahul@123', 'name': 'Rahul Rao'},
    'rahuljoshi@amc.edu': {'password': 'rahul@123', 'name': 'Rahul Joshi'},
    'amitrao@amc.edu': {'password': 'amit@123', 'name': 'Amit Rao'},
    'ananyadas@amc.edu': {'password': 'ananya@123', 'name': 'Ananya Das'},
    'simranmehta@amc.edu': {'password': 'simran@123', 'name': 'Simran Mehta'},
    'simranghosh@amc.edu': {'password': 'simran@123', 'name': 'Simran Ghosh'},
    'nikhilmehta@amc.edu': {'password': 'nikhil@123', 'name': 'Nikhil Mehta'},
    'nehadas@amc.edu': {'password': 'neha@123', 'name': 'Neha Das'},
    'arjunghosh@amc.edu': {'password': 'arjun@123', 'name': 'Arjun Ghosh'},
    'vikrammishra@amc.edu': {'password': 'vikram@123', 'name': 'Vikram Mishra'}
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    if 'user' in session:
        logger.info(f"\nUser {session['user']} redirected to chat page.\n")
        return redirect(url_for('chat'))
    logger.info("\nUser redirected to home page.\n")
    return render_template('home.html')

@app.route('/about')
def about():
    logger.info("\nAbout page accessed.\n")
    return render_template('about.html')

@app.route('/contact')
def contact():
    logger.info("\nContact page accessed.\n")
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        logger.info(f"\nLogin attempt for email: {email}\n")

        if email not in users or users[email]['password'] != password:
            flash('Invalid email or password')
            logger.warning(f"Failed login attempt for email: {email}")
            return redirect(url_for('login'))
        
        if not email.endswith('amc.edu'):
            flash('Only institutional emails (.amc.edu) are allowed')
            logger.warning(f"Login attempt with non-institutional email: {email}")
            return redirect(url_for('login'))
            
        session['user'] = email
        session['name'] = users[email]['name']
        session['chat_history'] = []
        session['document_mode'] = False
        session['uploaded_files'] = []
        logger.info(f"\nUser {email} logged in successfully.\n")
        return redirect(url_for('chat'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        logger.info(f"\nRegistration attempt for email: {email}\n")

        if not email.endswith('amc.edu'):
            flash('Only institutional emails (.amc.edu) are allowed')
            logger.warning(f"Registration attempt with non-institutional email: {email}")
            return redirect(url_for('register'))
            
        if email in users:
            flash('Email already registered')
            logger.warning(f"\nEmail already registered: {email}\n")
            return redirect(url_for('register'))
            
        users[email] = {'password': password, 'name': name}
        flash('Registration successful! Please login')
        logger.info(f"\nUser {email} registered successfully.\n")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        logger.info(f"\nUser {session['user']} logged out.\n")
    session.clear()
    return redirect(url_for('home'))

@app.route('/chat')
def chat():
    if 'user' not in session:
        logger.warning("Unauthorized access attempt to chat.")
        return redirect(url_for('login'))
    logger.info(f"\nUser {session['user']} accessing the chat page.\n")
    return render_template('chat.html', 
                          name=session.get('name', 'User'),
                          document_mode=session.get('document_mode', False),
                          uploaded_files=session.get('uploaded_files', []))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        logger.warning("\nUnauthorized file upload attempt.\n")
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    if 'file' not in request.files:
        logger.warning("\nFile upload request without file part.\n")
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.warning("\nFile upload with empty filename.\n")
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        logger.warning(f"\nAttempted upload of disallowed file type: {file.filename}\n")
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    logger.info(f"\nFile uploaded successfully: {filename}\n")

    # Process the file and add to user_files collection
    try:
        success = save_upload_file(file_path, 'user_files')
        if success:
            if 'uploaded_files' not in session:
                session['uploaded_files'] = []
            session['uploaded_files'].append(filename)
            session.modified = True
            logger.info(f"\nFile processed and added to uploaded files: {filename}\n")
            return jsonify({'success': True, 'filename': filename}), 200
        else:
            logger.error(f"\nFailed to process file: {filename}\n")
            return jsonify({'success': False, 'error': 'Failed to process file'}), 500
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return jsonify({'success': False, 'error': "d"+str(e)}), 500

@app.route('/switch_toggle', methods=['POST'])
def switch_toggle():
    if 'user' not in session:
        return jsonify({'success': False}), 401
    
    data = request.json
    session['document_mode'] = data.get('document_mode', False)
    session.modified = True
    
    return jsonify({'success': True, 'document_mode': session['document_mode']})

@app.route('/ask', methods=['POST'])
def ask():
    if 'user' not in session:
        logger.warning("Unauthorized question submission attempt.")
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.json
    question = data.get('question', '')
    logger.info(f"\nReceived question: {question}\n")
    if not question:
        logger.warning("\nReceived empty question.\n")
        return jsonify({'success': False, 'error': 'Empty question'}), 400
    
    if not is_clean_text(question):
        logger.warning(f"\nProfanity detected in question: {question}\n")
        return jsonify({'success': False, 'error': "Let's keep the conversation respectful. 😊"}), 400


    # Initialize chat history if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Add the user question to chat history
    session['chat_history'].append({'role': 'user', 'content': question})
    
    try:
        # Get the answer based on the current mode
        if session.get('document_mode', False):
            # Document mode - use uploaded files
            if not session.get('uploaded_files', []):
                answer = "Please upload at least one document file first."
            else:
                context = get_relevant_context(question, 'user_files')
                history = [{"role": msg["role"], "content": msg["content"]} 
                           for msg in session['chat_history'][-4:]]
                
                # Call Ollama with context
                prompt = f"Based on the following information:\n\n{context}\n\nAnd considering our conversation so far, please answer this question: {question}"
                response = ollama.chat(model='llama3.2', messages=[
                    {"role": "system", "content": "You are a helpful academic assistant. Answer questions based only on the provided context. If the information is not in the context, say you don't know."},
                    *history,
                    {"role": "user", "content": prompt}
                ])
                answer = response['message']['content']
        else:
            # Standard mode - classify and use appropriate collection
            use_case = classify_use_case(question)
            collection_name = f"{use_case}_docs"
            
            context = get_relevant_context(question, collection_name)
            history = [{"role": msg["role"], "content": msg["content"]} 
                       for msg in session['chat_history'][-4:]]
            
            # Call Ollama with context
            prompt = f"Based on the following information:\n\n{context}\n\nAnd considering our conversation so far, please answer this question: {question}"
            response = ollama.chat(model='llama3.2', messages=[
                {"role": "system", "content": "You are a helpful academic assistant. Answer questions based on the provided context. If you're unsure, say so politely."},
                *history,
                {"role": "user", "content": prompt}
            ])
            answer = response['message']['content']
        
        # Add the bot's answer to chat history
        session['chat_history'].append({'role': 'assistant', 'content': answer})
        session.modified = True
        logger.info(f"\n\nResponse: {answer}\n\n")
        return jsonify({
            'success': True, 
            'answer': answer,
            'document_mode': session.get('document_mode', False)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/history')
def get_history():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    return jsonify({
        'success': True, 
        'history': session.get('chat_history', []),
        'document_mode': session.get('document_mode', False),
        'uploaded_files': session.get('uploaded_files', [])
    })

if __name__ == '__main__':
    app.run(debug=True)