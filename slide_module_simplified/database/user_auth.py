"""
User Authentication Manager
Handles user registration, login, and profile management
"""

import logging
import sqlite3
import hashlib
import secrets
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

from .models import get_db_connection

logger = logging.getLogger(__name__)

class UserAuthManager:
    """Manages user authentication and profile creation"""
    
    def __init__(self):
        self._init_auth_tables()
    
    def _init_auth_tables(self):
        """Initialize authentication tables"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Users table for authentication
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    email_verified BOOLEAN DEFAULT 0,
                    profile_complete BOOLEAN DEFAULT 0
                )
            ''')
            
            # User profiles table for learning preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    experience_level TEXT DEFAULT 'beginner',
                    learning_style TEXT DEFAULT 'visual',
                    interests TEXT,  -- JSON array
                    goals TEXT,      -- JSON array
                    timezone TEXT DEFAULT 'UTC',
                    language TEXT DEFAULT 'en',
                    profile_picture_url TEXT,
                    bio TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Update user_sessions table to link to users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions_new (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    current_slide INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_data TEXT,  -- JSON for additional session info
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Check if we need to migrate existing sessions
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'")
            existing_table = cursor.fetchone()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions_old'")
            old_table_exists = cursor.fetchone()
            
            if existing_table and old_table_exists:
                # Migration already happened, clean up
                cursor.execute("DROP TABLE IF EXISTS user_sessions_new")
                logger.info("🔄 Migration already completed, cleaned up temporary table")
            elif existing_table:
                # Need to migrate - old table exists but no backup
                cursor.execute("SELECT COUNT(*) FROM user_sessions")
                existing_sessions = cursor.fetchone()[0]
                
                if existing_sessions > 0:
                    logger.info(f"Migrating {existing_sessions} existing sessions...")
                
                # Rename old table and use new one
                cursor.execute("ALTER TABLE user_sessions RENAME TO user_sessions_old")
                cursor.execute("ALTER TABLE user_sessions_new RENAME TO user_sessions")
            else:
                # No existing table, just rename new one
                cursor.execute("ALTER TABLE user_sessions_new RENAME TO user_sessions")
            
            # Authentication tokens for session management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("🔐 Authentication tables initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing auth tables: {e}")
            raise
    
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for password hashing
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100k iterations
        ).hex()
        
        return password_hash, salt
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if len(password) > 128:
            return False, "Password too long (max 128 characters)"
        
        # Optional: Add more strength requirements
        # has_upper = any(c.isupper() for c in password)
        # has_lower = any(c.islower() for c in password)
        # has_digit = any(c.isdigit() for c in password)
        
        return True, "Password is valid"
    
    def register_user(self, email: str, password: str, first_name: str = None, 
                     last_name: str = None) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Validate inputs
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email format"}
            
            password_valid, password_error = self._validate_password(password)
            if not password_valid:
                return {"success": False, "error": password_error}
            
            # Check if user already exists
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email.lower(),))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "error": "User with this email already exists"}
            
            # Create new user
            user_id = str(uuid.uuid4())
            password_hash, salt = self._hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (user_id, email, password_hash, salt, first_name, last_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, email.lower(), password_hash, salt, first_name, last_name))
            
            # Create default profile
            cursor.execute('''
                INSERT INTO user_profiles (user_id, experience_level, learning_style, interests, goals)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, 'beginner', 'visual', '[]', '[]'))
            
            conn.commit()
            conn.close()
            
            logger.info(f"👤 New user registered: {email}")
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "User registered successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return {"success": False, "error": "Registration failed"}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user data
            cursor.execute('''
                SELECT user_id, password_hash, salt, first_name, last_name, is_active
                FROM users WHERE email = ?
            ''', (email.lower(),))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return {"success": False, "error": "Invalid email or password"}
            
            user_id, stored_hash, salt, first_name, last_name, is_active = user_data
            
            if not is_active:
                conn.close()
                return {"success": False, "error": "Account is deactivated"}
            
            # Verify password
            password_hash, _ = self._hash_password(password, salt)
            
            if password_hash != stored_hash:
                conn.close()
                return {"success": False, "error": "Invalid email or password"}
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE user_id = ?
            ''', (datetime.now(), user_id))
            
            # Generate authentication token
            token = self._generate_auth_token(user_id, cursor)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ User authenticated: {email}")
            
            return {
                "success": True,
                "user_id": user_id,
                "token": token,
                "user": {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    def _generate_auth_token(self, user_id: str, cursor) -> str:
        """Generate authentication token"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=30)  # 30 day expiration
        
        cursor.execute('''
            INSERT INTO auth_tokens (token_id, user_id, token_hash, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), user_id, token_hash, expires_at))
        
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify authentication token and return user_id"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id FROM auth_tokens 
                WHERE token_hash = ? AND expires_at > ? AND is_active = 1
            ''', (token_hash, datetime.now()))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"❌ Token verification error: {e}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user basic info
            cursor.execute('''
                SELECT email, first_name, last_name, created_at, last_login
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return None
            
            # Get profile data
            cursor.execute('''
                SELECT experience_level, learning_style, interests, goals, 
                       timezone, language, bio, updated_at
                FROM user_profiles WHERE user_id = ?
            ''', (user_id,))
            
            profile_data = cursor.fetchone()
            
            conn.close()
            
            if user_data and profile_data:
                from .models import json_deserialize
                
                return {
                    "user_id": user_id,
                    "email": user_data[0],
                    "first_name": user_data[1],
                    "last_name": user_data[2],
                    "created_at": user_data[3],
                    "last_login": user_data[4],
                    "experience_level": profile_data[0],
                    "learning_style": profile_data[1],
                    "interests": json_deserialize(profile_data[2]) or [],
                    "goals": json_deserialize(profile_data[3]) or [],
                    "timezone": profile_data[4],
                    "language": profile_data[5],
                    "bio": profile_data[6],
                    "updated_at": profile_data[7]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Separate user table updates from profile table updates
            user_fields = ['first_name', 'last_name']
            profile_fields = ['experience_level', 'learning_style', 'interests', 
                            'goals', 'timezone', 'language', 'bio']
            
            # Update user table
            user_updates = {k: v for k, v in updates.items() if k in user_fields}
            if user_updates:
                set_clause = ', '.join([f"{k} = ?" for k in user_updates.keys()])
                values = list(user_updates.values()) + [user_id]
                
                cursor.execute(f'''
                    UPDATE users SET {set_clause} WHERE user_id = ?
                ''', values)
            
            # Update profile table
            profile_updates = {k: v for k, v in updates.items() if k in profile_fields}
            if profile_updates:
                from .models import json_serialize
                
                # Serialize lists
                if 'interests' in profile_updates:
                    profile_updates['interests'] = json_serialize(profile_updates['interests'])
                if 'goals' in profile_updates:
                    profile_updates['goals'] = json_serialize(profile_updates['goals'])
                
                profile_updates['updated_at'] = datetime.now()
                
                set_clause = ', '.join([f"{k} = ?" for k in profile_updates.keys()])
                values = list(profile_updates.values()) + [user_id]
                
                cursor.execute(f'''
                    UPDATE user_profiles SET {set_clause} WHERE user_id = ?
                ''', values)
            
            conn.commit()
            conn.close()
            
            logger.info(f"👤 Profile updated for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating profile: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        try:
            # Validate new password
            password_valid, password_error = self._validate_password(new_password)
            if not password_valid:
                return {"success": False, "error": password_error}
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify old password
            cursor.execute('''
                SELECT password_hash, salt FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"success": False, "error": "User not found"}
            
            stored_hash, salt = result
            old_password_hash, _ = self._hash_password(old_password, salt)
            
            if old_password_hash != stored_hash:
                conn.close()
                return {"success": False, "error": "Current password is incorrect"}
            
            # Set new password
            new_password_hash, new_salt = self._hash_password(new_password)
            
            cursor.execute('''
                UPDATE users SET password_hash = ?, salt = ? WHERE user_id = ?
            ''', (new_password_hash, new_salt, user_id))
            
            # Invalidate all existing tokens (force re-login)
            cursor.execute('''
                UPDATE auth_tokens SET is_active = 0 WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🔒 Password changed for user: {user_id}")
            
            return {"success": True, "message": "Password changed successfully"}
            
        except Exception as e:
            logger.error(f"❌ Password change error: {e}")
            return {"success": False, "error": "Password change failed"}
    
    def logout_user(self, token: str) -> bool:
        """Logout user by invalidating token"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE auth_tokens SET is_active = 0 WHERE token_hash = ?
            ''', (token_hash,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Logout error: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, lesson_id, current_slide, started_at, last_activity
                FROM user_sessions WHERE user_id = ?
                ORDER BY last_activity DESC
            ''', (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "lesson_id": row[1],
                    "current_slide": row[2],
                    "started_at": row[3],
                    "last_activity": row[4]
                })
            
            conn.close()
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Error getting user sessions: {e}")
            return []

# Global instance
user_auth_manager = UserAuthManager()

def get_user_auth_manager() -> UserAuthManager:
    """Get the global user auth manager instance"""
    return user_auth_manager
