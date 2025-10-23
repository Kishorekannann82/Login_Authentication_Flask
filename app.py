from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # CHANGE THIS TO A RANDOM SECRET KEY

# Configuring SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --------------------------
# --- DATABASE MODELS ---
# --------------------------

class User(db.Model):
    """User Model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Video(db.Model):
    """Video Model to store dynamic video content"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    url = db.Column(db.String(500), nullable=False) # Stores the YouTube Embed URL

# --------------------------
# --- ROUTES ---
# --------------------------

@app.route('/')
def home():
    """Displays a Page based on the session of the current user"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Confirms username and password in the database"""
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html', error='Invalid username or password.')

@app.route('/register', methods=['POST'])
def register():
    """Registers a new user"""
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('index.html', error='Username already exists.')
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

# --- UPDATED DASHBOARD ROUTE ---
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        
        # Determine admin status
        is_admin = (username == 'admin@kishorelytics.com')

        # Fetch videos from the database (available to all users)
        # We replace the hardcoded list with a DB query
        videos = Video.query.order_by(Video.id.desc()).all()

        return render_template(
            'dashboard.html', 
            username=username, 
            videos=videos,
            is_admin=is_admin
        )
    
    return redirect(url_for('home'))

# --- NEW ADMIN ROUTE FOR UPLOADING VIDEO ---
@app.route('/add_video', methods=['POST'])
def add_video():
    # 1. Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('home'))
        
    username = session['username']
    
    # 2. Authorization Check: ONLY admin can access this route
    if username != 'admin@kishorelytics.com':
        return redirect(url_for('dashboard'))

    # 3. Process the form data
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        url = request.form.get('url') # This is the YouTube embed URL

        # Basic validation
        if not title or not url:
            # In a real app, use flash messages to inform the admin
            return redirect(url_for('dashboard')) 
        
        # 4. Save to Database
        new_video = Video(title=title, description=description, url=url)
        db.session.add(new_video)
        db.session.commit()

        # 5. Success
        return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))
# In main.py, add this new route after the `add_video` route:

@app.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    # 1. Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('home'))
        
    username = session['username']
    
    # 2. Authorization Check: ONLY admin can delete
    if username != 'admin@kishorelytics.com':
        return redirect(url_for('dashboard'))

    # 3. Find and delete the video
    video_to_delete = Video.query.get_or_404(video_id)
    
    try:
        db.session.delete(video_to_delete)
        db.session.commit()
        # In a real app, you might use flash('Video deleted successfully!')
        return redirect(url_for('dashboard'))
    except Exception as e:
        # Handle case where deletion fails
        print(f"Error deleting video: {e}")
        db.session.rollback()
        return "An error occurred during deletion.", 500
# In main.py, add this new route:

@app.route('/admin_users')
def admin_users():
    # 1. Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('home'))

    # 2. Authorization Check: ONLY admin can view this page
    if session['username'] != 'admin@kishorelytics.com':
        return redirect(url_for('dashboard'))

    # 3. Fetch all users from the database
    users = User.query.all()

    # 4. Render the new admin template
    return render_template('admin_users.html', users=users)

if __name__ in '__main__':
    # Create ALL tables (User and Video)
    with app.app_context():
        db.create_all()
    app.run(debug=True)