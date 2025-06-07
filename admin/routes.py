"""
Admin Routes - Lesson Management Interface
Provides admin endpoints for uploading, managing, and publishing lessons
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from slide_module_simplified.system_prompt_manager import get_system_prompt_manager

logger = logging.getLogger(__name__)

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', 
                    template_folder='templates')

# Simple session-based authentication
ADMIN_PASSWORD = "admin123"  # Change this in production!

def check_admin_auth():
    """Check if user is authenticated as admin"""
    from flask import session
    return session.get('admin_authenticated', False)

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_admin_auth():
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@require_admin_auth
def dashboard():
    """Admin dashboard - lesson overview"""
    try:
        from slide_module_simplified import LessonManager, DATABASE_AVAILABLE
        
        if not DATABASE_AVAILABLE:
            return render_template('admin_error.html', 
                                 error="Database not available", 
                                 message="Enable database features to use admin interface")
        
        lesson_manager = LessonManager()
        lessons = lesson_manager.list_lessons()
        
        # Get stats for each lesson
        lesson_stats = []
        total_sessions = 0
        total_interactions = 0
        for lesson in lessons:
            stats = lesson_manager.get_lesson_stats(lesson['id'])
            lesson_stats.append({
                **lesson,
                'stats': stats
            })
            # Safely add session and interaction counts
            if stats and 'error' not in stats:
                total_sessions += stats.get('session_count', 0)
                total_interactions += stats.get('interaction_count', 0)
        
        return render_template('admin_dashboard.html', 
                             lessons=lesson_stats,
                             total_lessons=len(lessons),
                             total_sessions=total_sessions,
                             total_interactions=total_interactions)
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return render_template('admin_error.html', 
                             error="Dashboard Error", 
                             message=str(e))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            from flask import session
            session['admin_authenticated'] = True
            flash('Logged in successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid password', 'error')
    
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    from flask import session
    session.pop('admin_authenticated', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/lessons')
@require_admin_auth
def lesson_list():
    """List all lessons with management options"""
    try:
        from slide_module_simplified import LessonManager, DATABASE_AVAILABLE
        
        if not DATABASE_AVAILABLE:
            return render_template('admin_error.html', 
                                 error="Database not available")
        
        lesson_manager = LessonManager()
        lessons = lesson_manager.list_lessons()
        
        return render_template('lesson_list.html', lessons=lessons)
        
    except Exception as e:
        logger.error(f"Lesson list error: {e}")
        flash(f'Error loading lessons: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/lessons/upload', methods=['GET', 'POST'])
@require_admin_auth  
def upload_lesson():
    """Upload new lesson from text file"""
    if request.method == 'POST':
        try:
            from slide_module_simplified import LessonManager, generate_lesson_id
            
            # Get form data
            lesson_title = request.form.get('lesson_title', '').strip()
            lesson_id = request.form.get('lesson_id', '').strip()
            
            # Always publish immediately (draft option removed)
            publish_immediately = True
            
            # Handle file upload
            if 'lesson_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)
            
            file = request.files['lesson_file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Read file content
            content = file.read().decode('utf-8')
            
            # Generate lesson ID if not provided
            if not lesson_id:
                lesson_id = generate_lesson_id(lesson_title) if lesson_title else generate_lesson_id(file.filename)
            
            # Create lesson
            lesson_manager = LessonManager()
            result = lesson_manager.create_lesson_from_file(
                lesson_id=lesson_id,
                file_content=content,
                publish=publish_immediately  # Always True now
            )
            
            if result['success']:
                flash(f'Lesson "{result["title"]}" uploaded and published successfully with {result["slide_count"]} slides! Students can now access it.', 'success')
                return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))
            else:
                flash(f'Failed to create lesson: {result.get("error", "Unknown error")}', 'error')
                return render_template('lesson_upload.html', 
                                     form_data=request.form,
                                     error=result.get('details'))
        
        except Exception as e:
            logger.error(f"Lesson upload error: {e}")
            flash(f'Upload error: {str(e)}', 'error')
            return render_template('lesson_upload.html', form_data=request.form)
    
    return render_template('lesson_upload.html')

@admin_bp.route('/lessons/<lesson_id>')
@require_admin_auth
def lesson_detail(lesson_id):
    """View lesson details and management options"""
    try:
        from slide_module_simplified import LessonManager, SessionManager
        
        lesson_manager = LessonManager()
        lesson = lesson_manager.get_lesson(lesson_id)
        
        if not lesson:
            flash('Lesson not found', 'error')
            return redirect(url_for('admin.lesson_list'))
        
        # Get lesson statistics
        stats = lesson_manager.get_lesson_stats(lesson_id)
        
        # Get recent sessions
        session_manager = SessionManager()
        recent_sessions = session_manager.get_lesson_sessions(lesson_id)
        
        return render_template('lesson_detail.html', 
                             lesson=lesson,
                             stats=stats,
                             recent_sessions=recent_sessions[:10])  # Show latest 10
        
    except Exception as e:
        logger.error(f"Lesson detail error: {e}")
        flash(f'Error loading lesson: {str(e)}', 'error')
        return redirect(url_for('admin.lesson_list'))

@admin_bp.route('/lessons/<lesson_id>/preview')
@require_admin_auth
def lesson_preview(lesson_id):
    """Preview lesson content before publishing"""
    try:
        from slide_module_simplified import LessonManager
        
        lesson_manager = LessonManager()
        lesson = lesson_manager.get_lesson(lesson_id)
        
        if not lesson:
            flash('Lesson not found', 'error')
            return redirect(url_for('admin.lesson_list'))
        
        return render_template('lesson_preview.html', lesson=lesson)
        
    except Exception as e:
        logger.error(f"Lesson preview error: {e}")
        flash(f'Error previewing lesson: {str(e)}', 'error')
        return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))

@admin_bp.route('/lessons/<lesson_id>/publish', methods=['POST'])
@require_admin_auth
def toggle_lesson_publish(lesson_id):
    """Toggle lesson published status"""
    try:
        from slide_module_simplified import LessonManager
        
        publish = request.form.get('publish') == 'true'
        
        lesson_manager = LessonManager()
        success = lesson_manager.update_lesson_status(lesson_id, publish)
        
        if success:
            status = "published" if publish else "unpublished"
            flash(f'Lesson {status} successfully', 'success')
        else:
            flash('Failed to update lesson status', 'error')
        
        return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))
        
    except Exception as e:
        logger.error(f"Lesson publish toggle error: {e}")
        flash(f'Error updating lesson: {str(e)}', 'error')
        return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))

@admin_bp.route('/lessons/<lesson_id>/delete', methods=['POST'])
@require_admin_auth
def delete_lesson(lesson_id):
    """Delete a lesson (with confirmation)"""
    try:
        from slide_module_simplified import LessonManager
        
        confirm = request.form.get('confirm') == 'true'
        
        if not confirm:
            flash('Deletion not confirmed', 'error')
            return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))
        
        lesson_manager = LessonManager()
        success = lesson_manager.delete_lesson(lesson_id)
        
        if success:
            flash(f'Lesson "{lesson_id}" deleted successfully', 'success')
            return redirect(url_for('admin.lesson_list'))
        else:
            flash('Failed to delete lesson', 'error')
            return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))
        
    except Exception as e:
        logger.error(f"Lesson delete error: {e}")
        flash(f'Error deleting lesson: {str(e)}', 'error')
        return redirect(url_for('admin.lesson_detail', lesson_id=lesson_id))

@admin_bp.route('/api/lessons/<lesson_id>/stats')
@require_admin_auth
def api_lesson_stats(lesson_id):
    """API endpoint for lesson statistics"""
    try:
        from slide_module_simplified import LessonManager
        
        lesson_manager = LessonManager()
        stats = lesson_manager.get_lesson_stats(lesson_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"API lesson stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/lessons/search')
@require_admin_auth
def api_lesson_search():
    """API endpoint for searching lessons"""
    try:
        from slide_module_simplified import LessonManager
        
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query required'
            }), 400
        
        lesson_manager = LessonManager()
        results = lesson_manager.search_lessons(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"API lesson search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/settings')
@require_admin_auth
def settings():
    """Admin settings page"""
    try:
        return render_template('admin_settings.html')
        
    except Exception as e:
        logger.error(f"Settings page error: {e}")
        flash(f'Settings error: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/system-prompt-ui')
@require_admin_auth
def system_prompt_ui():
    """Render the system prompt management UI page"""
    try:
        return render_template('admin_system_prompt.html')
    except Exception as e:
        logger.error(f"System prompt UI render error: {e}")
        flash(f'Error loading system prompt page: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/analytics')
@require_admin_auth
def analytics():
    """Analytics dashboard"""
    try:
        from slide_module_simplified import LessonManager, SessionManager
        from slide_module_simplified.database import check_database_health
        
        # Get overall statistics
        lesson_manager = LessonManager()
        lessons = lesson_manager.list_lessons()
        
        session_manager = SessionManager()
        
        # Calculate analytics
        total_lessons = len(lessons)
        published_lessons = len([l for l in lessons if l['is_published']])
        
        # Get database health
        db_health = check_database_health()
        
        analytics_data = {
            'lessons': {
                'total': total_lessons,
                'published': published_lessons,
                'unpublished': total_lessons - published_lessons
            },
            'database': db_health,
            'recent_lessons': lessons[:5]  # Latest 5 lessons
        }
        
        return render_template('admin_analytics.html', 
                             analytics=analytics_data)
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        flash(f'Analytics error: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/test')
@require_admin_auth
def test_admin():
    """Test admin functionality"""
    try:
        from slide_module_simplified import DATABASE_AVAILABLE
        from slide_module_simplified.database import check_database_health
        
        if not DATABASE_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            })
        
        # Check database health
        health = check_database_health()
        
        # Test lesson manager
        from slide_module_simplified import LessonManager
        lesson_manager = LessonManager()
        lessons = lesson_manager.list_lessons()
        
        return jsonify({
            'success': True,
            'database_available': DATABASE_AVAILABLE,
            'database_health': health,
            'total_lessons': len(lessons),
            'admin_routes': 'working'
        })
        
    except Exception as e:
        logger.error(f"Admin test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/settings/system-prompt', methods=['GET', 'POST'])
@require_admin_auth
def manage_system_prompt():
    """Manage system prompt and its modifiers"""
    try:
        prompt_manager = get_system_prompt_manager()
        
        if request.method == 'POST':
            data = request.get_json()
            action = data.get('action')
            
            if action == 'update_base':
                # Update base prompt
                prompt = data.get('prompt', '').strip()
                if not prompt:
                    return jsonify({'error': 'Prompt cannot be empty'}), 400
                    
                prompt_manager.set_base_prompt(prompt)
                return jsonify({
                    'status': 'success',
                    'message': 'Base prompt updated',
                    'prompt_length': len(prompt)
                })
                
            elif action == 'add_modifier':
                # Add a new modifier
                context = data.get('context')
                modifier = data.get('modifier')
                if not context or not modifier:
                    return jsonify({'error': 'Context and modifier required'}), 400
                    
                prompt_manager.add_modifier(context, modifier)
                return jsonify({
                    'status': 'success',
                    'message': f'Added modifier for {context}'
                })
                
            elif action == 'remove_modifier':
                # Remove a modifier
                context = data.get('context')
                if not context:
                    return jsonify({'error': 'Context required'}), 400
                    
                prompt_manager.remove_modifier(context)
                return jsonify({
                    'status': 'success',
                    'message': f'Removed modifier for {context}'
                })
                
            elif action == 'toggle_context':
                # Toggle a context's active state
                context = data.get('context')
                activate = data.get('activate', True)
                if not context:
                    return jsonify({'error': 'Context required'}), 400
                    
                if activate:
                    prompt_manager.activate_context(context)
                else:
                    prompt_manager.deactivate_context(context)
                    
                return jsonify({
                    'status': 'success',
                    'message': f'Context {context} {"activated" if activate else "deactivated"}'
                })
                
            else:
                return jsonify({'error': 'Invalid action'}), 400
                
        else:  # GET request
            status = prompt_manager.get_status()
            return jsonify({
                'status': 'success',
                'data': {
                    'base_prompt': prompt_manager.base_prompt,
                    'modifiers': prompt_manager.modifiers,
                    'active_contexts': list(prompt_manager.active_contexts),
                    'full_prompt': prompt_manager.get_full_prompt(),
                    'status': status
                }
            })
            
    except Exception as e:
        logger.error(f"System prompt management error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings/token', methods=['GET', 'POST'])
@require_admin_auth
def manage_token_settings():
    """Manage token optimization settings"""
    try:
        # Import the shared db instance and models
        from database import db
        from models import TokenSettings
        
        if request.method == 'GET':
            # Get current settings
            settings = TokenSettings.query.first()
            if not settings:
                settings = TokenSettings()  # Use defaults
                db.session.add(settings)
                db.session.commit()
            
            # Get token usage statistics
            stats = get_token_usage_stats()
            
            return jsonify({
                'status': 'success',
                'settings': {
                    'token_optimization_level': settings.token_optimization_level,
                    'max_conversation_history': settings.max_conversation_history,
                    'max_system_prompt_length': settings.max_system_prompt_length,
                    'max_emotional_states': settings.max_emotional_states,
                    'enable_context_pruning': settings.enable_context_pruning,
                    'enable_context_summarization': settings.enable_context_summarization
                },
                'stats': stats
            })
            
        elif request.method == 'POST':
            # Update settings
            data = request.get_json()
            settings = TokenSettings.query.first()
            if not settings:
                settings = TokenSettings()
                db.session.add(settings)
            
            # Update settings from request data
            settings.token_optimization_level = data.get('token_optimization_level', settings.token_optimization_level)
            settings.max_conversation_history = data.get('max_conversation_history', settings.max_conversation_history)
            settings.max_system_prompt_length = data.get('max_system_prompt_length', settings.max_system_prompt_length)
            settings.max_emotional_states = data.get('max_emotional_states', settings.max_emotional_states)
            settings.enable_context_pruning = data.get('enable_context_pruning', settings.enable_context_pruning)
            settings.enable_context_summarization = data.get('enable_context_summarization', settings.enable_context_summarization)
            
            db.session.commit()
            
            # Get updated token usage statistics
            stats = get_token_usage_stats()
            
            return jsonify({
                'status': 'success',
                'message': 'Token settings updated',
                'stats': stats
            })
            
    except Exception as e:
        logger.error(f"Token settings error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

def get_token_usage_stats():
    """Get current token usage statistics"""
    try:
        from database import db
        from models import TokenSettings
        from slide_module_simplified import ConversationManager, get_system_prompt_manager
        
        # Get conversation manager instance
        conv_manager = ConversationManager()
        
        # Count tokens in conversation history
        conversation_tokens = sum(len(msg['content']) // 4 for msg in conv_manager.conversation_history)
        
        # Count tokens in system prompt
        prompt_manager = get_system_prompt_manager()
        system_prompt_tokens = len(prompt_manager.base_prompt) // 4 if prompt_manager.base_prompt else 0
        
        # Calculate total tokens
        total_tokens = conversation_tokens + system_prompt_tokens
        
        # Calculate savings (if any)
        pruning_savings = 0
        summarization_savings = 0
        
        # Get settings
        settings = TokenSettings.query.first()
        
        if settings and settings.enable_context_pruning:
            # Estimate pruning savings (difference between max and current history)
            max_possible = settings.max_conversation_history * 100  # Rough estimate
            pruning_savings = max(0, max_possible - conversation_tokens)
            
        if settings and settings.enable_context_summarization:
            # Estimate summarization savings
            summarization_savings = conversation_tokens // 2  # Rough estimate
        
        total_savings = pruning_savings + summarization_savings
        
        return {
            'conversation_tokens': conversation_tokens,
            'system_prompt_tokens': system_prompt_tokens,
            'total_tokens': total_tokens,
            'pruning_savings': pruning_savings,
            'summarization_savings': summarization_savings,
            'total_savings': total_savings
        }
        
    except Exception as e:
        logger.error(f"Error getting token stats: {e}")
        return None

def init_admin_routes(app):
    """Initialize admin routes with the Flask app"""
    try:
        # Import the shared db instance from the database module
        from database import db
        
        # Register the admin blueprint
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        print("✅ Admin routes initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Admin routes initialization failed: {e}")
        return False

# Add template filters
@admin_bp.app_template_filter('datetime_format')
def datetime_format(value):
    """Format datetime for display"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return value

@admin_bp.app_template_filter('file_size')
def file_size_format(value):
    """Format file size for display"""
    try:
        size = int(value)
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"
    except:
        return value
