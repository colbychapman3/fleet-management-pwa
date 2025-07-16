"""
Authentication routes for login, logout, and user management
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import structlog
from datetime import datetime

def get_app_db():
    import app
    return app.db

from models.models.user import User
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

auth_bp = Blueprint('auth', __name__)

# First register function removed - duplicate route


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.main'))
        return render_template('auth/login.html')
    
    # Handle POST request
    try:
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            remember = data.get('remember', False)
        else:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)
        
        # Validate input
        if not email or not password:
            error_msg = 'Email and password are required'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            logger.warning(f"Failed login attempt for email: {email}")
            error_msg = 'Invalid email or password'
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 401
        
        if not user.is_active:
            error_msg = 'Account is disabled'
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 401
        
        # Login successful
        login_user(user, remember=remember)
        user.update_last_login()
        
        logger.info(f"User logged in: {user.email}")
        
        if request.is_json:
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict(),
                'redirect_url': url_for('dashboard.main')
            })
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.main'))
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        error_msg = 'An error occurred during login'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/login.html'), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """User logout endpoint"""
    user_email = current_user.email if current_user.is_authenticated else 'unknown'
    logout_user()
    session.clear()
    
    logger.info(f"User logged out: {user_email}")
    
    if request.is_json:
        return jsonify({'message': 'Logout successful'})
    
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint (for managers to create worker accounts)"""
    if request.method == 'GET':
        if not current_user.is_authenticated or not current_user.is_manager():
            flash('Access denied', 'error')
            return redirect(url_for('auth.login'))
        return render_template('auth/register.html')
    
    # Handle POST request
    if not current_user.is_authenticated or not current_user.is_manager():
        if request.is_json:
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['email', 'username', 'password', 'role']
        for field in required_fields:
            if not data.get(field, '').strip():
                error_msg = f'{field.title()} is required'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('auth/register.html'), 400
        
        email = data['email'].strip().lower()
        username = data['username'].strip()
        password = data['password']
        role = data['role'].strip()
        
        # Validate role
        if role not in ['manager', 'worker']:
            error_msg = 'Invalid role specified'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html'), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            error_msg = 'Email already registered'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html'), 400
        
        if User.query.filter_by(username=username).first():
            error_msg = 'Username already taken'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html'), 400
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            phone=data.get('phone', '').strip(),
            vessel_id=data.get('vessel_id') if data.get('vessel_id') else None
        )
        
        db = get_app_db()
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {email} by {current_user.email}")
        
        if request.is_json:
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict()
            }), 201
        
        flash('User registered successfully', 'success')
        return redirect(url_for('dashboard.users'))
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        error_msg = 'An error occurred during registration'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/register.html'), 500

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'GET':
        if request.is_json:
            return jsonify(current_user.to_dict())
        return render_template('auth/profile.html', user=current_user)
    
    # Handle POST request (profile update)
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            current_user.last_name = data['last_name'].strip()
        if 'phone' in data:
            current_user.phone = data['phone'].strip()
        
        # Only managers can update vessel assignment and role
        if current_user.is_manager():
            if 'vessel_id' in data:
                current_user.vessel_id = data['vessel_id'] if data['vessel_id'] else None
        
        db = get_app_db()
        db.session.commit()
        
        logger.info(f"Profile updated for user: {current_user.email}")
        
        if request.is_json:
            return jsonify({
                'message': 'Profile updated successfully',
                'user': current_user.to_dict()
            })
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Profile update error: {e}")
        error_msg = 'An error occurred while updating profile'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/profile.html', user=current_user), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            error_msg = 'All password fields are required'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        if not current_user.check_password(current_password):
            error_msg = 'Current password is incorrect'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        if new_password != confirm_password:
            error_msg = 'New passwords do not match'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        if len(new_password) < 6:
            error_msg = 'Password must be at least 6 characters long'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db = get_app_db()
        db.session.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        if request.is_json:
            return jsonify({'message': 'Password changed successfully'})
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('auth.profile'))
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Password change error: {e}")
        error_msg = 'An error occurred while changing password'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('auth.profile'))

@auth_bp.route('/sync-status')
@login_required
def sync_status():
    """Get user's sync status"""
    try:
        sync_stats = SyncLog.get_sync_statistics(current_user.id)
        pending_syncs = SyncLog.get_pending_syncs(current_user.id)
        
        return jsonify({
            'statistics': sync_stats,
            'pending_syncs': [sync.to_dict() for sync in pending_syncs[:10]],  # Last 10
            'last_sync': current_user.last_sync.isoformat() if current_user.last_sync else None
        })
        
    except Exception as e:
        logger.error(f"Sync status error: {e}")
        return jsonify({'error': 'Failed to get sync status'}), 500