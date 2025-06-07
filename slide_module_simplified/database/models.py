"""
SQLite Database Models and Schema
Handles lesson management and user session data
"""
import sqlite3
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Database file path - relative to project root
DB_PATH = "lessons.db"

def get_db_connection() -> sqlite3.Connection:
    """Get database connection with proper configuration"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def init_database() -> bool:
    """Initialize database with all required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create lessons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                content_file TEXT,
                slide_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_published BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create lesson slides table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lesson_slides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id TEXT NOT NULL,
                slide_number INTEGER NOT NULL,
                title TEXT,
                content TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                UNIQUE(lesson_id, slide_number)
            )
        ''')
        
        # Create user sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                lesson_id TEXT,
                user_name TEXT,
                experience_level TEXT DEFAULT 'beginner',
                current_slide INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lesson_id) REFERENCES lessons(id)
            )
        ''')
        
        # Create coaching interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coaching_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                slide_number INTEGER,
                user_input TEXT,
                ai_response TEXT,
                interaction_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
            )
        ''')
        
        # Create user preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                session_id TEXT PRIMARY KEY,
                learning_style TEXT,
                pace_preference TEXT DEFAULT 'normal',
                interests TEXT,  -- JSON array
                goals TEXT,      -- JSON array
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
            )
        ''')
        
        # Create system settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1), -- Ensure only one row
                base_prompt TEXT,
                modifiers TEXT, -- Store modifiers as JSON
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default settings if table is empty
        cursor.execute('SELECT COUNT(*) FROM system_settings')
        if cursor.fetchone()[0] == 0:
            from slide_content_knowledge import AI_COACH_PERSONALITY
            default_modifiers = {} # Start with no default modifiers
            cursor.execute('''
                INSERT INTO system_settings (id, base_prompt, modifiers)
                VALUES (?, ?, ?)
            ''', (1, AI_COACH_PERSONALITY, json.dumps(default_modifiers)))
            logger.info("📝 Inserted default system settings")

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lessons_published ON lessons(is_published)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_slides_lesson ON lesson_slides(lesson_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_lesson ON user_sessions(lesson_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_session ON coaching_interactions(session_id)')
        
        conn.commit()
        conn.close()
        
        logger.info("🗄️ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and basic stats"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table counts
        cursor.execute("SELECT COUNT(*) FROM lessons")
        lesson_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        session_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM coaching_interactions")
        interaction_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "healthy",
            "database_file": DB_PATH,
            "tables": {
                "lessons": lesson_count,
                "sessions": session_count,
                "interactions": interaction_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Utility functions for JSON handling
def json_serialize(data: Any) -> str:
    """Safely serialize data to JSON string"""
    if data is None:
        return None
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return None

def json_deserialize(json_str: str) -> Any:
    """Safely deserialize JSON string to data"""
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to deserialize JSON: {e}")
        return None
