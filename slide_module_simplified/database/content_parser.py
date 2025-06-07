"""
Content Parser for Lesson Text Files
Parses structured text files and converts them to database format
"""
import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ParsedSlide:
    """Represents a single parsed slide"""
    slide_number: int
    title: str
    content: str
    notes: str = ""

@dataclass 
class ParsedLesson:
    """Represents a complete parsed lesson"""
    title: str
    description: str
    slides: List[ParsedSlide]
    total_slides: int = field(init=False)
    
    def __post_init__(self):
        self.total_slides = len(self.slides)

class ContentParser:
    """Parses lesson content from text files"""
    
    def __init__(self):
        self.slide_pattern = r'^## Slide (\d+):'
        self.title_pattern = r'^\*\*Title:\*\* (.+)$'
        self.subtitle_pattern = r'^\*\*Subtitle:\*\* (.+)$'
        
    def parse_lesson_file(self, file_content: str) -> ParsedLesson:
        """Parse a complete lesson file into structured data"""
        try:
            lines = file_content.split('\n')
            
            # Extract lesson title and description
            lesson_title, lesson_description = self._extract_lesson_metadata(lines)
            
            # Parse individual slides
            slides = self._parse_slides(lines)
            
            # Ensure we have at least some slides
            if not slides:
                logger.warning("No slides found in lesson content")
                # Create a default slide if none found
                slides = [ParsedSlide(
                    slide_number=1,
                    title="Welcome",
                    content="This lesson content needs to be formatted with proper slide markers.",
                    notes="Please check the lesson format."
                )]
            
            logger.info(f"📖 Parsed lesson: '{lesson_title}' with {len(slides)} slides")
            
            parsed_lesson = ParsedLesson(
                title=lesson_title,
                description=lesson_description,
                slides=slides
            )
            
            # Verify total_slides is set correctly
            if parsed_lesson.total_slides != len(slides):
                logger.warning(f"Total slides mismatch: expected {len(slides)}, got {parsed_lesson.total_slides}")
                parsed_lesson.total_slides = len(slides)
            
            return parsed_lesson
            
        except Exception as e:
            logger.error(f"Failed to parse lesson file: {e}")
            logger.error(f"File content preview: {file_content[:200]}...")
            raise
    
    def _extract_lesson_metadata(self, lines: List[str]) -> Tuple[str, str]:
        """Extract lesson title and description from file header"""
        title = "Untitled Lesson"
        description = ""
        
        for i, line in enumerate(lines[:15]):  # Check first 15 lines
            line = line.strip()
            if line.startswith('#') and not line.startswith('##'):
                # Main title line - extract everything after the first #
                title = line.lstrip('# ').strip()
                if title:  # Only use if not empty
                    # Look for description in next few lines
                    for j in range(i+1, min(i+8, len(lines))):
                        desc_line = lines[j].strip()
                        if desc_line and not desc_line.startswith('#') and not desc_line.startswith('---'):
                            description = desc_line
                            break
                    break
        
        # Fallback title extraction if main method fails
        if title == "Untitled Lesson" or not title:
            for line in lines[:10]:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('---'):
                    title = line[:50]  # Use first meaningful line as title
                    break
        
        return title, description
    
    def _parse_slides(self, lines: List[str]) -> List[ParsedSlide]:
        """Parse all slides from the content"""
        slides = []
        current_slide = None
        current_content = []
        current_notes = []
        in_notes_section = False
        
        logger.debug(f"Parsing {len(lines)} lines for slides")
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for slide header
            slide_match = re.match(self.slide_pattern, line_stripped)
            if slide_match:
                # Save previous slide if exists
                if current_slide is not None:
                    slide = self._create_slide(current_slide, current_content, current_notes)
                    slides.append(slide)
                    logger.debug(f"Created slide {slide.slide_number}: '{slide.title}'")
                
                # Start new slide
                slide_number = int(slide_match.group(1))
                current_slide = {"number": slide_number, "title": ""}
                current_content = []
                current_notes = []
                in_notes_section = False
                logger.debug(f"Found slide header: Slide {slide_number} at line {line_num + 1}")
                continue
            
            # Skip if no current slide
            if current_slide is None:
                continue
            
            # Extract slide title
            title_match = re.match(self.title_pattern, line_stripped)
            if title_match:
                current_slide["title"] = title_match.group(1)
                logger.debug(f"Found title: '{current_slide['title']}'")
                continue
            
            # Check for notes section
            if line_stripped.startswith("**Notes:**"):
                in_notes_section = True
                continue
            elif line_stripped.startswith("**Visual Description:**"):
                in_notes_section = False
                continue
            elif line_stripped.startswith("---"):
                # End of slide
                in_notes_section = False
                continue
            elif line_stripped.startswith("**Overall Presentation Notes:**"):
                # End of slides, start of overall notes
                logger.debug("Found overall notes section, stopping slide parsing")
                break
            
            # Add content to appropriate section
            if in_notes_section:
                if line_stripped:  # Skip empty lines in notes
                    current_notes.append(line)
            else:
                current_content.append(line)
        
        # Don't forget the last slide
        if current_slide is not None:
            slide = self._create_slide(current_slide, current_content, current_notes)
            slides.append(slide)
            logger.debug(f"Created final slide {slide.slide_number}: '{slide.title}'")
        
        # Ensure slides are sorted by slide number
        slides.sort(key=lambda x: x.slide_number)
        
        logger.info(f"Parsed {len(slides)} slides total")
        return slides
    
    def _create_slide(self, slide_info: Dict, content_lines: List[str], notes_lines: List[str]) -> ParsedSlide:
        """Create a ParsedSlide object from collected data"""
        
        # Clean and join content
        content = self._clean_content('\n'.join(content_lines))
        notes = self._clean_content('\n'.join(notes_lines))
        
        return ParsedSlide(
            slide_number=slide_info["number"],
            title=slide_info.get("title", f"Slide {slide_info['number']}"),
            content=content,
            notes=notes
        )
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content text"""
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Max 2 newlines
        content = content.strip()
        
        # Remove markdown artifacts that might confuse the AI
        content = re.sub(r'^\*\*(Content|Visual Description|Notes):\*\*\s*$', '', content, flags=re.MULTILINE)
        
        return content

    def validate_parsed_lesson(self, lesson: ParsedLesson) -> Dict[str, Any]:
        """Validate parsed lesson data"""
        issues = []
        warnings = []
        
        # Check lesson metadata
        if not lesson.title or lesson.title == "Untitled Lesson":
            issues.append("Lesson title is missing or generic")
        
        if not lesson.description:
            warnings.append("Lesson description is empty")
        
        # Check slides
        if len(lesson.slides) == 0:
            issues.append("No slides found in lesson")
        
        slide_numbers = [slide.slide_number for slide in lesson.slides]
        
        # Check for missing slides
        expected_range = range(1, max(slide_numbers) + 1) if slide_numbers else []
        missing_slides = [n for n in expected_range if n not in slide_numbers]
        if missing_slides:
            issues.append(f"Missing slides: {missing_slides}")
        
        # Check for duplicate slides
        duplicates = [n for n in slide_numbers if slide_numbers.count(n) > 1]
        if duplicates:
            issues.append(f"Duplicate slides: {set(duplicates)}")
        
        # Check slide content
        for slide in lesson.slides:
            if not slide.title.strip():
                warnings.append(f"Slide {slide.slide_number} has no title")
            if not slide.content.strip():
                warnings.append(f"Slide {slide.slide_number} has no content")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "slide_count": len(lesson.slides),
            "slide_range": f"{min(slide_numbers)}-{max(slide_numbers)}" if slide_numbers else "None"
        }

# Example usage and testing
if __name__ == "__main__":
    # Test with sample content
    sample_content = """
# AI-Powered UX Design Workshop Presentation Content

## Slide 1: Title Slide
**Title:** Intro to AI-Powered UX Design  
**Subtitle:** Workshop for UX Professionals

**Content:**
- Presenter: Danny Setiawan
- Job titles: Coach and Instructor at CoCreate

**Notes:** 60-minute workshop duration

---

## Slide 2: About the Instructor
**Title:** About the Instructor

**Content:**
Professional background information here.

**Notes:** Establishes credibility
"""
    
    parser = ContentParser()
    try:
        lesson = parser.parse_lesson_file(sample_content)
        validation = parser.validate_parsed_lesson(lesson)
        print(f"Parsed: {lesson.title}")
        print(f"Slides: {lesson.total_slides}")
        print(f"Valid: {validation['valid']}")
        if validation['issues']:
            print(f"Issues: {validation['issues']}")
    except Exception as e:
        print(f"Parse error: {e}")
