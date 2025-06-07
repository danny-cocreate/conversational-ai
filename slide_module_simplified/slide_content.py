"""
Slide Content and Knowledge Base
Contains slide content for AI coaching context
"""

from typing import Dict, Any, List, Optional
from .database.lesson_manager import LessonManager

class SlideContent:
    """
    Slide content and knowledge base for AI coaching
    Provides context about what's on each slide
    """
    
    def __init__(self):
        self.lesson_manager = LessonManager()
        self.current_lesson_id = None
        self.current_lesson = None
        self.current_slides = []
    
    def set_current_lesson(self, lesson_id: str) -> None:
        """Set the current lesson context"""
        self.current_lesson_id = lesson_id
        self.current_lesson = self.lesson_manager.get_lesson(lesson_id)
        if self.current_lesson:
            self.current_slides = self.lesson_manager.get_lesson_slides(lesson_id)
        else:
            self.current_slides = []
    
    def get_slide_content(self, slide_number: int) -> Dict[str, Any]:
        """Get content for a specific slide"""
        if not self.current_lesson or not self.current_slides:
            return self._get_default_slide()
            
        # Find the slide in current slides
        for slide in self.current_slides:
            if slide['slide_number'] == slide_number:
                return {
                    "title": slide['title'],
                    "content": slide['content'],
                    "notes": slide['notes'],
                    "key_concepts": self._extract_key_concepts(slide['content']),
                    "coaching_notes": self._generate_coaching_notes(slide),
                    "questions_to_ask": self._generate_questions(slide)
                }
        
        return self._get_default_slide()
    
    def _get_default_slide(self) -> Dict[str, Any]:
        """Get default slide structure when content is not available"""
        try:
            # Try to get default content from database
            default_content = self.lesson_manager.get_default_slide_content()
            if default_content:
                return default_content
        except Exception as e:
            logger.warning(f"⚠️ Could not get default slide content from database: {e}")
        
        # Fallback to minimal default content
        return {
            "title": "Slide Content",
            "content": ["Content not yet defined"],
            "key_concepts": [],
            "coaching_notes": ["Provide context and explanation"],
            "questions_to_ask": ["How does this relate to your work?"]
        }
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from slide content"""
        try:
            # Try to get key concepts from database
            concepts = self.lesson_manager.extract_key_concepts(content)
            if concepts:
                return concepts
        except Exception as e:
            logger.warning(f"⚠️ Could not extract key concepts from database: {e}")
        
        # Fallback to simple extraction
        if not content:
            return []
            
        concepts = []
        for line in content.split('\n'):
            line = line.strip()
            if line and len(line) > 3:  # Avoid very short lines
                concepts.append(line)
        
        return concepts[:5]  # Limit to top 5 concepts
    
    def _generate_coaching_notes(self, slide: Dict[str, Any]) -> List[str]:
        """Generate coaching notes based on slide content"""
        try:
            # Try to get coaching notes from database
            notes = self.lesson_manager.get_coaching_notes(slide)
            if notes:
                return notes
        except Exception as e:
            logger.warning(f"⚠️ Could not get coaching notes from database: {e}")
        
        # Fallback to basic notes
        notes = []
        
        if slide.get('notes'):
            notes.append(slide['notes'])
        
        if slide.get('content'):
            notes.append("Explain the key points")
            notes.append("Provide relevant examples")
        
        return notes
    
    def _generate_questions(self, slide: Dict[str, Any]) -> List[str]:
        """Generate relevant questions based on slide content"""
        try:
            # Try to get questions from database
            questions = self.lesson_manager.get_suggested_questions(slide)
            if questions:
                return questions
        except Exception as e:
            logger.warning(f"⚠️ Could not get suggested questions from database: {e}")
        
        # Fallback to basic questions
        questions = []
        
        if slide.get('title'):
            questions.append(f"What do you think about {slide['title']}?")
        
        if slide.get('content'):
            questions.append("How would you apply this in your work?")
            questions.append("What questions do you have about this topic?")
        
        return questions
    
    def get_slide_title(self, slide_number: int) -> str:
        """Get title for a specific slide"""
        slide_data = self.get_slide_content(slide_number)
        return slide_data.get("title", f"Slide {slide_number + 1}")
    
    def get_coaching_context(self, slide_number: int) -> Dict[str, Any]:
        """Get coaching context for AI responses"""
        slide_data = self.get_slide_content(slide_number)
        return {
            "slide_number": slide_number,
            "title": slide_data["title"],
            "key_concepts": slide_data["key_concepts"],
            "coaching_notes": slide_data["coaching_notes"],
            "suggested_questions": slide_data["questions_to_ask"]
        }
    
    def get_related_slides(self, slide_number: int) -> Dict[str, int]:
        """Get related slides for navigation suggestions"""
        if not self.current_slides:
            return {}
            
        total_slides = len(self.current_slides)
        related = {}
        
        if slide_number > 0:
            related["previous"] = slide_number - 1
        if slide_number < total_slides - 1:
            related["next"] = slide_number + 1
        
        # Add conceptually related slides based on content
        current_concepts = self.get_slide_content(slide_number)["key_concepts"]
        for slide in self.current_slides:
            if slide['slide_number'] != slide_number:
                slide_concepts = self._extract_key_concepts(slide['content'])
                common_concepts = set(current_concepts) & set(slide_concepts)
                if common_concepts:
                    related[f"related_concept_{slide['slide_number']}"] = slide['slide_number']
        
        return related
    
    def search_content(self, query: str) -> List[Dict[str, Any]]:
        """Search slide content for specific topics"""
        if not self.current_slides:
            return []
            
        query_lower = query.lower()
        results = []
        
        for slide in self.current_slides:
            # Search in title, content, and key concepts
            searchable_text = (
                slide['title'].lower() + " " +
                slide['content'].lower() + " " +
                " ".join(self._extract_key_concepts(slide['content'])).lower()
            )
            
            if query_lower in searchable_text:
                results.append({
                    "slide_number": slide['slide_number'],
                    "title": slide['title'],
                    "relevance": searchable_text.count(query_lower)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results
    
    def get_learning_path(self, user_interests: List[str], experience_level: str) -> List[int]:
        """Generate a personalized learning path based on user profile"""
        if not self.current_slides:
            return []
            
        try:
            # Try to get personalized learning path from database
            path = self.lesson_manager.get_learning_path(user_interests, experience_level)
            if path:
                return path
        except Exception as e:
            logger.warning(f"⚠️ Could not get learning path from database: {e}")
        
        # Fallback to basic path
        all_slides = [slide['slide_number'] for slide in self.current_slides]
        
        # For now, return sequential order
        # In the future, this could be more sophisticated based on interests and level
        if experience_level == "beginner":
            return all_slides  # Cover everything
        elif experience_level == "intermediate":
            return all_slides[::2]  # Every other slide
        else:  # advanced
            return all_slides[::3]  # Every third slide
    
    def get_slide_summary(self, slide_number: int) -> str:
        """Get a brief summary of slide content for AI context"""
        slide_data = self.get_slide_content(slide_number)
        return f"Slide {slide_number + 1}: {slide_data['title']} - {', '.join(slide_data['key_concepts'])}"
    
    def get_total_slides(self) -> int:
        """Get total number of slides with content"""
        return len(self.current_slides) if self.current_slides else 0

# Global instance
slide_content = SlideContent()

def get_slide_content() -> SlideContent:
    """Get the global slide content instance"""
    return slide_content

def get_coaching_context(slide_number: int) -> Dict[str, Any]:
    """Get coaching context for a slide"""
    return slide_content.get_coaching_context(slide_number)

def search_slides(query: str) -> List[Dict[str, Any]]:
    """Search slide content"""
    return slide_content.search_content(query)
