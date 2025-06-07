"""
Simplified Slide Module
Clean, focused slide system for AI coaching with navigation guidance

Features:
- Slide state tracking (AI knows current position)
- Navigation guidance (AI tells user what to click)  
- Voice intent detection (converts voice to guidance)
- AI coaching with personalization
- Enhanced AI memory and persistent sessions
- Manual navigation support (user clicks UI buttons)
- Clean API endpoints
- No threading complexity

Note: AI provides guidance, user controls navigation via UI buttons
"""

from .slide_controller import SlideController, get_slide_controller
from .voice_interaction import VoiceInteraction, get_voice_interaction, process_voice_input, has_navigation_intent
from .lesson_coaching_manager import LessonCoachingManager
from .slide_content import SlideContent, get_slide_content
from .routes import register_routes, get_blueprint, init_slide_system

__version__ = "1.1.0"
__author__ = "AI Coaching System"

# Try to import database components (optional)
try:
    from .database import init_database, LessonManager, SessionManager, ContentParser, generate_lesson_id
    from .database import UserAuthManager, get_user_auth_manager
    DATABASE_AVAILABLE = True
    print("📊 Database components available")
except ImportError:
    DATABASE_AVAILABLE = False
    init_database = None
    LessonManager = None
    SessionManager = None
    ContentParser = None
    generate_lesson_id = None
    UserAuthManager = None
    get_user_auth_manager = None

# Export main components
__all__ = [
    # Core classes
    'SlideController',
    'VoiceInteraction', 
    'LessonCoachingManager',
    'SlideContent',
    
    # Convenience functions
    'get_slide_controller',
    'get_voice_interaction',
    'get_slide_content',
    'process_voice_input',          # Returns guidance instead of control
    'has_navigation_intent',        # Detects navigation intent
    
    # Flask integration
    'register_routes',
    'get_blueprint',
    'init_slide_system',
    
    # Database components (optional)
    'DATABASE_AVAILABLE',
    'init_database',
    'LessonManager', 
    'SessionManager',
    'ContentParser',
    'generate_lesson_id',
    
    # Authentication components (optional)
    'UserAuthManager',
    'get_user_auth_manager'
]

def setup_slide_system(app=None, enable_database=False):
    """
    Easy setup function for the complete guidance-based slide system
    
    This sets up a system where:
    - AI provides navigation guidance (tells user what to click)
    - User controls slides via UI buttons  
    - AI tracks slide state and provides personalized coaching
    - Enhanced AI memory and personalization (optional)
    
    Args:
        app: Flask app instance (optional)
        enable_database: Whether to initialize database features (optional)
        
    Returns:
        True if setup successful
    """
    try:
        # Initialize the slide system
        success = init_slide_system()
        
        # Initialize database if requested and available
        if enable_database and DATABASE_AVAILABLE:
            db_success = init_database()
            if db_success:
                print("🗄️ Database initialized successfully")
            else:
                print("⚠️ Database initialization failed")
        elif enable_database and not DATABASE_AVAILABLE:
            print("⚠️ Database requested but not available")
        
        if app:
            # Register routes with Flask app
            register_routes(app)
            print("🔗 Slide routes registered with Flask app")
        
        print("✅ Guidance-based slide system ready!")
        print("    - AI provides navigation guidance")
        print("    - User clicks UI buttons to navigate")
        print("    - AI tracks state and provides coaching")
        if enable_database and DATABASE_AVAILABLE:
            print("    - Database features enabled")
        return success
        
    except Exception as e:
        print(f"❌ Failed to setup slide system: {e}")
        return False

# Quick access to global instances
slide_controller = get_slide_controller()
voice_interaction = get_voice_interaction()
slide_content = get_slide_content()

print("📦 Guidance-based slide module loaded")
print("    ✨ AI provides navigation guidance")  
print("    🖱️ User controls via UI buttons")
print("    🎓 Personalized coaching included")
