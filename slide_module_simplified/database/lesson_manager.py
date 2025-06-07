"""
Lesson Manager - CRUD operations for lessons and slides
Handles lesson storage, retrieval, and management
"""
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from .models import get_db_connection, json_serialize, json_deserialize
from .content_parser import ContentParser, ParsedLesson

logger = logging.getLogger(__name__)

def generate_lesson_id(title: str) -> str:
    """Generate URL-friendly lesson ID from title"""
    import re
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    lesson_id = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    lesson_id = re.sub(r'\s+', '-', lesson_id)
    lesson_id = re.sub(r'-+', '-', lesson_id)  # Remove multiple consecutive hyphens
    lesson_id = lesson_id.strip('-')  # Remove leading/trailing hyphens
    
    # Ensure it's not empty
    if not lesson_id:
        from datetime import datetime
        lesson_id = f"lesson-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    return lesson_id

class LessonManager:
    """Manages lesson data in the database"""
    
    def __init__(self):
        self.parser = ContentParser()
    
    def create_lesson_from_file(self, lesson_id: str, file_content: str, 
                              publish: bool = False) -> Dict[str, Any]:
        """Create a new lesson from uploaded text content"""
        try:
            # Parse the content
            parsed_lesson = self.parser.parse_lesson_file(file_content)
            
            # Validate the parsed content
            validation = self.parser.validate_parsed_lesson(parsed_lesson)
            if not validation['valid']:
                return {
                    "success": False,
                    "error": "Invalid lesson content",
                    "details": validation
                }
            
            # Store in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Insert lesson record
                cursor.execute('''
                    INSERT OR REPLACE INTO lessons 
                    (id, title, description, slide_count, is_published, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    lesson_id,
                    parsed_lesson.title,
                    parsed_lesson.description,
                    parsed_lesson.total_slides,
                    publish,
                    datetime.now()
                ))
                
                # Delete existing slides for this lesson
                cursor.execute('DELETE FROM lesson_slides WHERE lesson_id = ?', (lesson_id,))
                
                # Insert slide records
                for slide in parsed_lesson.slides:
                    cursor.execute('''
                        INSERT INTO lesson_slides 
                        (lesson_id, slide_number, title, content, notes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        lesson_id,
                        slide.slide_number,
                        slide.title,
                        slide.content,
                        slide.notes
                    ))
                
                conn.commit()
                logger.info(f"📚 Created lesson '{lesson_id}' with {parsed_lesson.total_slides} slides")
                
                return {
                    "success": True,
                    "lesson_id": lesson_id,
                    "title": parsed_lesson.title,
                    "slide_count": parsed_lesson.total_slides,
                    "validation": validation,
                    "published": publish
                }
                
            except sqlite3.Error as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to create lesson from file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Get lesson metadata and slides"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get lesson metadata
            cursor.execute('''
                SELECT id, title, description, slide_count, created_at, 
                       updated_at, is_published
                FROM lessons WHERE id = ?
            ''', (lesson_id,))
            
            lesson_row = cursor.fetchone()
            if not lesson_row:
                return None
            
            lesson_data = dict(lesson_row)
            
            # Get slides
            cursor.execute('''
                SELECT slide_number, title, content, notes
                FROM lesson_slides 
                WHERE lesson_id = ?
                ORDER BY slide_number
            ''', (lesson_id,))
            
            slides = [dict(row) for row in cursor.fetchall()]
            lesson_data['slides'] = slides
            
            conn.close()
            return lesson_data
            
        except Exception as e:
            logger.error(f"Failed to get lesson {lesson_id}: {e}")
            return None
    
    def list_lessons(self, published_only: bool = False) -> List[Dict[str, Any]]:
        """List all lessons with metadata"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, title, description, slide_count, created_at, 
                       updated_at, is_published
                FROM lessons
            '''
            params = []
            
            if published_only:
                query += ' WHERE is_published = 1'
            
            query += ' ORDER BY updated_at DESC'
            
            cursor.execute(query, params)
            lessons = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return lessons
            
        except Exception as e:
            logger.error(f"Failed to list lessons: {e}")
            return []
    
    def update_lesson_status(self, lesson_id: str, published: bool) -> bool:
        """Update lesson published status"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE lessons 
                SET is_published = ?, updated_at = ?
                WHERE id = ?
            ''', (published, datetime.now(), lesson_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                status = "published" if published else "unpublished"
                logger.info(f"📝 Lesson '{lesson_id}' {status}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update lesson status: {e}")
            return False
    
    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete a lesson and all its slides"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Delete lesson (slides will be deleted by CASCADE)
            cursor.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"🗑️ Deleted lesson '{lesson_id}'")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete lesson: {e}")
            return False
    
    def get_lesson_slides(self, lesson_id: str) -> List[Dict[str, Any]]:
        """Get all slides for a lesson"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT slide_number, title, content, notes
                FROM lesson_slides
                WHERE lesson_id = ?
                ORDER BY slide_number
            ''', (lesson_id,))

            slides = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return slides

        except Exception as e:
            logger.error(f"Failed to get slides for lesson {lesson_id}: {e}")
            return []

    def get_slide_content(self, lesson_id: str, slide_number: int) -> Optional[Dict[str, Any]]:
        """Get specific slide content"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT slide_number, title, content, notes
                FROM lesson_slides
                WHERE lesson_id = ? AND slide_number = ?
            ''', (lesson_id, slide_number))

            slide_row = cursor.fetchone()
            conn.close()

            return dict(slide_row) if slide_row else None

        except Exception as e:
            logger.error(f"Failed to get slide {slide_number} for lesson {lesson_id}: {e}")
            return None
    
    def search_lessons(self, query: str) -> List[Dict[str, Any]]:
        """Search lessons by title, description, or content"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            
            cursor.execute('''
                SELECT DISTINCT l.id, l.title, l.description, l.slide_count, 
                       l.created_at, l.updated_at, l.is_published
                FROM lessons l
                LEFT JOIN lesson_slides s ON l.id = s.lesson_id
                WHERE l.title LIKE ? 
                   OR l.description LIKE ?
                   OR s.title LIKE ?
                   OR s.content LIKE ?
                ORDER BY l.updated_at DESC
            ''', (search_term, search_term, search_term, search_term))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search lessons: {e}")
            return []
    
    def get_lesson_stats(self, lesson_id: str) -> Dict[str, Any]:
        """Get lesson statistics and metadata"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get lesson info
            lesson = self.get_lesson(lesson_id)
            if not lesson:
                return {"error": "Lesson not found"}
            
            # Get session count for this lesson
            cursor.execute('''
                SELECT COUNT(*) as session_count,
                       COUNT(DISTINCT user_name) as unique_users
                FROM user_sessions 
                WHERE lesson_id = ?
            ''', (lesson_id,))
            
            session_stats = dict(cursor.fetchone())
            
            # Get interaction count
            cursor.execute('''
                SELECT COUNT(*) as interaction_count
                FROM coaching_interactions ci
                JOIN user_sessions us ON ci.session_id = us.session_id
                WHERE us.lesson_id = ?
            ''', (lesson_id,))
            
            interaction_stats = dict(cursor.fetchone())
            
            conn.close()
            
            return {
                "lesson_id": lesson_id,
                "title": lesson["title"],
                "slide_count": lesson["slide_count"],
                "is_published": lesson["is_published"],
                "created_at": lesson["created_at"],
                "updated_at": lesson["updated_at"],
                **session_stats,
                **interaction_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get lesson stats: {e}")
            return {"error": str(e)}

# End of LessonManager class
