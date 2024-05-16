from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json

app = Flask(__name__, template_folder='pages')
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

def load_users():
    with open('users.json', 'r') as f:
        data = json.load(f)
    return [User(user['id'], user['username'], user['password'], user['role']) for user in data['users']]

users = load_users()

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == user_id:
            return user
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user in users:
            if user.username == username and user.password == password:
                login_user(user)
                return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    video_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
    videos = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.webm', '.ogg'))]
    return render_template('index.html', videos=videos)

@app.route('/videos/<path:filename>')
@login_required
def download_file(filename):
    video_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
    return send_from_directory(video_folder, filename)

@app.route('/play', methods=['POST'])
@login_required
def play_video():
    video_name = request.form.get('video_name')
    return video_name

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Access denied: Admins only!')
        return redirect(url_for('index'))
    return render_template('admin.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if current_user.role != 'admin':
        flash('Access denied: Admins only!')
        return redirect(url_for('home'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/')
@login_required
def home():
    return render_template('index.html', current_user=current_user)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
