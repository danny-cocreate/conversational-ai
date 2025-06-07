"""
Simplified Slide State Tracker
Tracks slide state for AI coaching - AI provides guidance, user clicks buttons
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SlideState:
    """Current state of the slide presentation"""
    current_slide: int = 0
    total_slides: int = 18
    presentation_id: str = "ai_ux_deck"
    last_updated: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SlideController:
    """
    Slide state tracker for AI coaching
    
    Features:
    - State tracking (AI knows current position)
    - Manual navigation updates (when user clicks buttons)
    - Navigation guidance (AI tells user what to click)
    
    Note: AI provides guidance, user controls navigation via UI buttons
    """
    
    def __init__(self, total_slides: int = 18, presentation_id: str = "ai_ux_deck"):
        self.state = SlideState(
            current_slide=0,
            total_slides=total_slides,
            presentation_id=presentation_id,
            last_updated=time.time()
        )
        print(f"🎬 SlideController initialized: {total_slides} slides")
    
    # === MANUAL NAVIGATION METHODS (Called by UI when user clicks buttons) ===
    
    def update_slide_position(self, new_slide: int) -> Dict[str, Any]:
        """Update slide position when user manually navigates (via UI buttons)"""
        if 0 <= new_slide < self.state.total_slides:
            old_slide = self.state.current_slide
            self.state.current_slide = new_slide
            self.state.last_updated = time.time()
            
            return {
                "success": True,
                "previous_slide": old_slide,
                "current_slide": self.state.current_slide,
                "message": f"Slide updated to {self.state.current_slide + 1}/{self.state.total_slides}",
                **self.get_navigation_info()
            }
        else:
            return {
                "success": False,
                "current_slide": self.state.current_slide,
                "message": f"Invalid slide {new_slide + 1}. Must be between 1 and {self.state.total_slides}",
                **self.get_navigation_info()
            }
    
    def manual_next(self) -> Dict[str, Any]:
        """Called when user clicks 'Next' button in UI"""
        return self.update_slide_position(self.state.current_slide + 1)
    
    def manual_previous(self) -> Dict[str, Any]:
        """Called when user clicks 'Previous' button in UI"""
        return self.update_slide_position(self.state.current_slide - 1)
    
    def manual_goto(self, slide_index: int) -> Dict[str, Any]:
        """Called when user navigates to specific slide via UI"""
        return self.update_slide_position(slide_index)
    
    # === NAVIGATION GUIDANCE METHODS (For AI responses) ===
    
    def get_navigation_guidance(self, desired_action: str) -> str:
        """Get guidance text for AI to tell user what button to click"""
        guidance = {
            "next": "When you're ready to continue, go ahead and click the 'Next' button at the top right of the screen.",
            "previous": "To go back to the previous slide, click the 'Previous' button at the top left.",
            "first": "To start from the beginning, click the 'Previous' button repeatedly to get back to slide 1, or refresh the page.",
            "last": f"To jump to the end, click the 'Next' button repeatedly to reach slide {self.state.total_slides}.",
            "current": f"We're currently on slide {self.state.current_slide + 1} of {self.state.total_slides}.",
            "general": "You can use the navigation buttons at the top of the screen to move between slides."
        }
        return guidance.get(desired_action, guidance["general"])
    
    def get_contextual_guidance(self) -> str:
        """Get contextual navigation guidance based on current position"""
        current = self.state.current_slide + 1
        total = self.state.total_slides
        
        if self.state.current_slide == 0:
            return f"We're on slide {current} of {total}. When you're ready to move forward, click the 'Next' button."
        elif self.state.current_slide == self.state.total_slides - 1:
            return f"We're on the last slide ({current} of {total}). You can click 'Previous' to review earlier slides."
        else:
            return f"We're on slide {current} of {total}. Use the 'Next' and 'Previous' buttons to navigate."
    
    # === STATE INFORMATION METHODS ===
    
    def get_current_slide(self) -> int:
        """Get current slide index (0-based)"""
        return self.state.current_slide
    
    def get_total_slides(self) -> int:
        """Get total number of slides"""
        return self.state.total_slides
    
    def get_navigation_info(self) -> Dict[str, Any]:
        """Get comprehensive navigation information"""
        return {
            "current_slide": self.state.current_slide,
            "current_slide_human": self.state.current_slide + 1,  # 1-based for humans
            "total_slides": self.state.total_slides,
            "can_go_next": self.state.current_slide < self.state.total_slides - 1,
            "can_go_previous": self.state.current_slide > 0,
            "is_first_slide": self.state.current_slide == 0,
            "is_last_slide": self.state.current_slide == self.state.total_slides - 1,
            "progress_percentage": round((self.state.current_slide / max(self.state.total_slides - 1, 1)) * 100, 1),
            "presentation_id": self.state.presentation_id,
            "last_updated": self.state.last_updated
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current slide state"""
        return self.state.to_dict()

# Global instance
slide_controller = SlideController()

def get_slide_controller() -> SlideController:
    """Get the global slide controller"""
    return slide_controller
