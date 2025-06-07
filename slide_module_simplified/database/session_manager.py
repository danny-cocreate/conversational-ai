"""
Session Manager - User session tracking and AI memory
Handles user sessions, preferences, and coaching interactions
"""
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .models import get_db_connection, json_serialize, json_deserialize

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and AI memory"""
    
    def __init__(self):
        pass
    
    def create_session(self, user_id: str, lesson_id: str) -> str:
        """Create a new user session linked to authenticated user"""
        try:
            session_id = str(uuid.uuid4())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_id, user_id, lesson_id, current_slide)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, lesson_id, 0))
            
            conn.commit()
            conn.close()
            
            logger.info(f"👤 Created session {session_id[:8]}... for user {user_id[:8]}... lesson '{lesson_id}'")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for authenticated user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get session data from new schema
            cursor.execute('''
                SELECT session_id, user_id, lesson_id, current_slide, started_at, last_activity
                FROM user_sessions WHERE session_id = ?
            ''', (session_id,))
            
            session_row = cursor.fetchone()
            if not session_row:
                conn.close()
                return None
            
            session_data = dict(session_row)
            
            # Get user profile data using the user_id
            cursor.execute('''
                SELECT experience_level, learning_style, interests, goals
                FROM user_profiles WHERE user_id = ?
            ''', (session_data['user_id'],))
            
            profile_row = cursor.fetchone()
            if profile_row:
                profile_data = dict(profile_row)
                # Deserialize JSON fields
                profile_data['interests'] = json_deserialize(profile_data['interests']) or []
                profile_data['goals'] = json_deserialize(profile_data['goals']) or []
                session_data['preferences'] = profile_data
            else:
                session_data['preferences'] = {
                    'experience_level': 'beginner',
                    'learning_style': 'visual',
                    'interests': [],
                    'goals': []
                }
            
            conn.close()
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def update_session_activity(self, session_id: str, current_slide: Optional[int] = None) -> bool:
        """Update session's last activity and optionally current slide"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if current_slide is not None:
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = ?, current_slide = ?
                    WHERE session_id = ?
                ''', (datetime.now(), current_slide, session_id))
            else:
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = ?
                    WHERE session_id = ?
                ''', (datetime.now(), session_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False
    
    def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]) -> bool:
        """Update or create user preferences"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Serialize lists to JSON
            interests_json = json_serialize(preferences.get('interests', []))
            goals_json = json_serialize(preferences.get('goals', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (session_id, learning_style, pace_preference, interests, goals, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                preferences.get('learning_style'),
                preferences.get('pace_preference', 'normal'),
                interests_json,
                goals_json,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📝 Updated preferences for session {session_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False
    
    def add_interaction(self, session_id: str, slide_number: int, 
                       user_input: str, ai_response: str, 
                       interaction_type: str = "general") -> bool:
        """Record a coaching interaction"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO coaching_interactions
                (session_id, slide_number, user_input, ai_response, interaction_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, slide_number, user_input, ai_response, interaction_type))
            
            conn.commit()
            conn.close()
            
            # Also update session activity
            self.update_session_activity(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add interaction: {e}")
            return False
    
    def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions for a session"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT slide_number, user_input, ai_response, interaction_type, timestamp
                FROM coaching_interactions
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, limit))
            
            interactions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return interactions
            
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    def get_user_context(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for AI personalization"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            history = self.get_session_history(session_id, limit=5)
            
            # Calculate engagement metrics
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Time spent in session
            cursor.execute('''
                SELECT 
                    julianday(last_activity) - julianday(started_at) as session_duration,
                    COUNT(*) as total_interactions
                FROM user_sessions us
                LEFT JOIN coaching_interactions ci ON us.session_id = ci.session_id
                WHERE us.session_id = ?
                GROUP BY us.session_id
            ''', (session_id,))
            
            metrics_row = cursor.fetchone()
            metrics = dict(metrics_row) if metrics_row else {"session_duration": 0, "total_interactions": 0}
            
            conn.close()
            
            return {
                "session": session,
                "recent_interactions": history,
                "metrics": metrics,
                "personalization": {
                    "user_name": session.get("user_name"),
                    "experience_level": session.get("experience_level", "beginner"),
                    "preferences": session.get("preferences", {}),
                    "current_slide": session.get("current_slide", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return {}
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up sessions older than specified days"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM user_sessions 
                WHERE last_activity < datetime('now', '-{} days')
            '''.format(days_old))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old sessions")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0
    
    def get_lesson_sessions(self, lesson_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific lesson"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, user_name, experience_level, current_slide,
                       started_at, last_activity
                FROM user_sessions
                WHERE lesson_id = ?
                ORDER BY last_activity DESC
            ''', (lesson_id,))
            
            sessions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get lesson sessions: {e}")
            return []
    
    def update_user_profile(self, session_id: str, profile_updates: Dict[str, Any]) -> bool:
        """Update user profile information"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update session table fields
            session_fields = ['user_name', 'experience_level']
            session_updates = {k: v for k, v in profile_updates.items() if k in session_fields}
            
            if session_updates:
                set_clause = ', '.join([f"{k} = ?" for k in session_updates.keys()])
                values = list(session_updates.values()) + [session_id]
                
                cursor.execute(f'''
                    UPDATE user_sessions 
                    SET {set_clause}, last_activity = ?
                    WHERE session_id = ?
                ''', values + [datetime.now()])
            
            # Update preferences
            prefs_fields = ['learning_style', 'pace_preference', 'interests', 'goals']
            prefs_updates = {k: v for k, v in profile_updates.items() if k in prefs_fields}
            
            if prefs_updates:
                # Get current preferences
                current_prefs = self.get_session(session_id).get('preferences', {})
                current_prefs.update(prefs_updates)
                self.update_user_preferences(session_id, current_prefs)
            
            conn.commit()
            conn.close()
            
            logger.info(f"👤 Updated profile for session {session_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False

def get_or_create_session(user_id: str, lesson_id: str, session_id: Optional[str] = None) -> str:
    """Get existing session or create new one for authenticated user"""
    session_manager = SessionManager()
    
    if session_id:
        session = session_manager.get_session(session_id)
        if session and session['user_id'] == user_id and session['lesson_id'] == lesson_id:
            # Update activity
            session_manager.update_session_activity(session_id)
            return session_id
    
    # Create new session for authenticated user
    return session_manager.create_session(user_id, lesson_id)

def create_authenticated_session(user_id: str, lesson_id: str) -> str:
    """Create a new authenticated session"""
    session_manager = SessionManager()
    return session_manager.create_session(user_id, lesson_id)
