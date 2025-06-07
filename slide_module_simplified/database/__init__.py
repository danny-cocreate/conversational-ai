# Database module exports
from .models import init_database, get_db_connection
from .lesson_manager import LessonManager, generate_lesson_id
from .session_manager import SessionManager
from .content_parser import ContentParser
from .user_auth import UserAuthManager, get_user_auth_manager

# Check database availability
try:
    import sqlite3
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

__all__ = [
    'DATABASE_AVAILABLE',
    'init_database',
    'get_db_connection', 
    'LessonManager',
    'SessionManager',
    'ContentParser',
    'UserAuthManager',
    'generate_lesson_id',
    'get_user_auth_manager'
]
