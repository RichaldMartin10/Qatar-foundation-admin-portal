import os
import uuid
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Admin, Opportunity, PasswordReset

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='sky',
    static_url_path='/sky'
)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'qf-admin-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qf_admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session config — default is browser-session (expires on close)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

CORS(app)
db.init_app(app)

# Create tables on first request
with app.app_context():
    db.create_all()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorator to protect routes — checks for admin_id in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Page route
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Serve the admin portal HTML."""
    return render_template('admin.html')


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------

@app.route('/api/signup', methods=['POST'])
def signup():
    """US-1.1 — Admin Sign Up."""
    data = request.get_json(silent=True) or {}

    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    # --- Validation ---
    errors = {}
    if not full_name:
        errors['full_name'] = 'Full name is required.'
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        errors['email'] = 'A valid email address is required.'
    if not password or len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    if errors:
        return jsonify({'errors': errors}), 400

    # Check duplicate email
    if Admin.query.filter_by(email=email).first():
        return jsonify({'errors': {'email': 'An account with this email already exists.'}}), 409

    # Create admin
    admin = Admin(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(admin)
    db.session.commit()

    logger.info(f'New admin registered: {email}')
    return jsonify({'message': 'Account created successfully.'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """US-1.2 — Admin Login."""
    data = request.get_json(silent=True) or {}

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    remember_me = data.get('remember_me', False)

    if not email or not password:
        return jsonify({'error': 'Invalid email or password.'}), 401

    admin = Admin.query.filter_by(email=email).first()

    if not admin or not check_password_hash(admin.password_hash, password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    # Set session
    session.clear()
    session['admin_id'] = admin.id
    session['admin_name'] = admin.full_name
    session['admin_email'] = admin.email

    if remember_me:
        session.permanent = True   # uses PERMANENT_SESSION_LIFETIME (30 days)
    else:
        session.permanent = False  # expires when browser closes

    logger.info(f'Admin logged in: {email} (remember_me={remember_me})')
    return jsonify({
        'message': 'Login successful.',
        'admin': admin.to_dict()
    }), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    """Clear the session."""
    session.clear()
    return jsonify({'message': 'Logged out successfully.'}), 200


@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """US-1.3 — Forgot Password.
    Always returns the same success message for privacy.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    # Always show same message
    success_msg = 'If an account with that email exists, a reset link has been sent.'

    if not email or '@' not in email:
        return jsonify({'message': success_msg}), 200

    admin = Admin.query.filter_by(email=email).first()
    if admin:
        token = str(uuid.uuid4())
        reset = PasswordReset(
            admin_id=admin.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(reset)
        db.session.commit()
        # Log the reset link internally (no email sent)
        logger.info(f'Password reset token generated for {email}: {token}')

    return jsonify({'message': success_msg}), 200


@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    """Return current logged-in admin info (for session checking on page load)."""
    admin = Admin.query.get(session['admin_id'])
    if not admin:
        session.clear()
        return jsonify({'error': 'Session invalid.'}), 401
    return jsonify({'admin': admin.to_dict()}), 200


# ---------------------------------------------------------------------------
# Opportunity CRUD API
# ---------------------------------------------------------------------------

@app.route('/api/opportunities', methods=['GET'])
@login_required
def list_opportunities():
    """US-2.1 — View all opportunities for the logged-in admin."""
    admin_id = session['admin_id']
    opportunities = Opportunity.query.filter_by(admin_id=admin_id)\
                                     .order_by(Opportunity.created_at.desc())\
                                     .all()
    return jsonify({'opportunities': [o.to_dict() for o in opportunities]}), 200


@app.route('/api/opportunities/<int:opp_id>', methods=['GET'])
@login_required
def get_opportunity(opp_id):
    """Get a single opportunity's full details."""
    admin_id = session['admin_id']
    opp = Opportunity.query.filter_by(id=opp_id, admin_id=admin_id).first()
    if not opp:
        return jsonify({'error': 'Opportunity not found.'}), 404
    return jsonify({'opportunity': opp.to_dict()}), 200


@app.route('/api/opportunities', methods=['POST'])
@login_required
def create_opportunity():
    """US-2.2 — Add a new opportunity."""
    data = request.get_json(silent=True) or {}
    admin_id = session['admin_id']

    # Required fields
    name = (data.get('name') or '').strip()
    duration = (data.get('duration') or '').strip()
    start_date = (data.get('start_date') or '').strip()
    description = (data.get('description') or '').strip()
    skills = (data.get('skills') or '').strip()
    category = (data.get('category') or '').strip()
    future_opportunities = (data.get('future_opportunities') or '').strip()
    max_applicants = data.get('max_applicants')

    errors = {}
    if not name:
        errors['name'] = 'Opportunity name is required.'
    if not duration:
        errors['duration'] = 'Duration is required.'
    if not start_date:
        errors['start_date'] = 'Start date is required.'
    if not description:
        errors['description'] = 'Description is required.'
    if not skills:
        errors['skills'] = 'Skills to gain is required.'
    if not category:
        errors['category'] = 'Category is required.'
    if not future_opportunities:
        errors['future_opportunities'] = 'Future opportunities is required.'

    if errors:
        return jsonify({'errors': errors}), 400

    # Parse max_applicants
    max_app = None
    if max_applicants is not None and str(max_applicants).strip() != '':
        try:
            max_app = int(max_applicants)
        except (ValueError, TypeError):
            pass

    opp = Opportunity(
        admin_id=admin_id,
        name=name,
        duration=duration,
        start_date=start_date,
        description=description,
        skills=skills,
        category=category,
        future_opportunities=future_opportunities,
        max_applicants=max_app
    )
    db.session.add(opp)
    db.session.commit()

    logger.info(f'Opportunity created: {name} (admin_id={admin_id})')
    return jsonify({
        'message': 'Opportunity created successfully.',
        'opportunity': opp.to_dict()
    }), 201


@app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
@login_required
def update_opportunity(opp_id):
    """US-2.5 — Edit an opportunity (ownership validated)."""
    admin_id = session['admin_id']
    opp = Opportunity.query.filter_by(id=opp_id, admin_id=admin_id).first()

    if not opp:
        return jsonify({'error': 'Opportunity not found.'}), 404

    data = request.get_json(silent=True) or {}

    # Required fields
    name = (data.get('name') or '').strip()
    duration = (data.get('duration') or '').strip()
    start_date = (data.get('start_date') or '').strip()
    description = (data.get('description') or '').strip()
    skills = (data.get('skills') or '').strip()
    category = (data.get('category') or '').strip()
    future_opportunities = (data.get('future_opportunities') or '').strip()
    max_applicants = data.get('max_applicants')

    errors = {}
    if not name:
        errors['name'] = 'Opportunity name is required.'
    if not duration:
        errors['duration'] = 'Duration is required.'
    if not start_date:
        errors['start_date'] = 'Start date is required.'
    if not description:
        errors['description'] = 'Description is required.'
    if not skills:
        errors['skills'] = 'Skills to gain is required.'
    if not category:
        errors['category'] = 'Category is required.'
    if not future_opportunities:
        errors['future_opportunities'] = 'Future opportunities is required.'

    if errors:
        return jsonify({'errors': errors}), 400

    # Parse max_applicants
    max_app = None
    if max_applicants is not None and str(max_applicants).strip() != '':
        try:
            max_app = int(max_applicants)
        except (ValueError, TypeError):
            pass

    opp.name = name
    opp.duration = duration
    opp.start_date = start_date
    opp.description = description
    opp.skills = skills
    opp.category = category
    opp.future_opportunities = future_opportunities
    opp.max_applicants = max_app

    db.session.commit()

    logger.info(f'Opportunity updated: {name} (id={opp_id}, admin_id={admin_id})')
    return jsonify({
        'message': 'Opportunity updated successfully.',
        'opportunity': opp.to_dict()
    }), 200


@app.route('/api/opportunities/<int:opp_id>', methods=['DELETE'])
@login_required
def delete_opportunity(opp_id):
    """US-2.6 — Delete an opportunity (ownership validated)."""
    admin_id = session['admin_id']
    opp = Opportunity.query.filter_by(id=opp_id, admin_id=admin_id).first()

    if not opp:
        return jsonify({'error': 'Opportunity not found.'}), 404

    name = opp.name
    db.session.delete(opp)
    db.session.commit()

    logger.info(f'Opportunity deleted: {name} (id={opp_id}, admin_id={admin_id})')
    return jsonify({'message': 'Opportunity deleted successfully.'}), 200


# ---------------------------------------------------------------------------
# Password Reset Verification (bonus — for completeness)
# ---------------------------------------------------------------------------

@app.route('/api/verify-reset-token/<token>', methods=['GET'])
def verify_reset_token(token):
    """Verify if a password reset token is still valid."""
    reset = PasswordReset.query.filter_by(token=token, used=False).first()
    if not reset:
        return jsonify({'error': 'Invalid or expired reset link.'}), 400
    if reset.expires_at < datetime.utcnow():
        return jsonify({'error': 'This reset link has expired. Please request a new one.'}), 400
    return jsonify({'message': 'Token is valid.', 'admin_id': reset.admin_id}), 200


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)
