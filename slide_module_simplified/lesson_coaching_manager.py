import logging
import os
import re # Added re for name extraction
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .slide_controller import get_slide_controller # Keep for navigation info
from .voice_interaction import get_voice_interaction # Keep for intent detection
from conversation import ConversationManager # Might still be useful for basic non-lesson chat
from .system_prompt_manager import get_system_prompt_manager
from .database.lesson_manager import LessonManager # Direct access to database manager
from config import Config # Import Config for OpenAI key
from openai import OpenAI # Import OpenAI client
import traceback # Import traceback for logging errors

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile for personalization"""
    name: Optional[str] = None
    experience_level: str = "beginner"  # beginner, intermediate, advanced
    interests: List[str] = field(default_factory=list)
    learning_style: str = "visual"  # visual, auditory, hands-on
    goals: List[str] = field(default_factory=list)
    previous_interactions: List[Dict] = field(default_factory=list)

@dataclass
class CoachingContext:
    """Current coaching session context"""
    slide_number: int = 0
    user_questions: List[str] = field(default_factory=list)
    engagement_level: str = "neutral"  # low, neutral, high
    time_on_slide: float = 0.0
    personalization_notes: List[str] = field(default_factory=list)
    current_lesson_id: str = "" # Track current lesson ID

class LessonCoachingManager:
    """
    Combined Lesson Coaching and Conversation Manager
    Handles user input, context, slide content, and LLM interaction for a specific lesson.
    """

    def __init__(self, lesson_id: str):
        self.lesson_id = lesson_id
        self.slide_controller = get_slide_controller() # Keep as it provides navigation info
        self.voice_interaction = get_voice_interaction() # Keep for intent detection
        self.lesson_manager = LessonManager() # Direct access to database manager
        self.user_profile = UserProfile() # Keep user profile
        self.coaching_context = CoachingContext(current_lesson_id=lesson_id) # Keep coaching context

        # Initialize LLM client and history management directly
        self._client = None # Lazy initialization of OpenAI client
        self.conversation_history = [] # Manage history directly
        self.model = "gpt-4" # Using reliable model

        # Load base prompts and potentially user profile data on initialization
        self.coaching_prompts = self._load_coaching_prompts()

        logger.info(f"🎓 LessonCoachingManager initialized for lesson: {self.lesson_id}")

    def _load_coaching_prompts(self) -> Dict[str, Any]:
        """Load coaching prompts from database"""
        try:
            # Assuming LessonManager has get_coaching_prompts method
            prompts = self.lesson_manager.get_coaching_prompts()
            if prompts:
                return prompts
        except Exception as e:
            logger.warning(f"⚠️ Could not load coaching prompts from database: {e}")

        # Return minimal default prompts if database fails
        # These should ideally be in the database for production
        return {
            "slide_intro": {
                "beginner": "Let me walk you through this concept step by step.",
                "intermediate": "You might find this builds on what you already know about...",
                "advanced": "This concept connects to some advanced topics you're likely familiar with."
            },
            "engagement": {
                "low": "I notice you might need a moment. Would you like me to explain this differently?",
                "neutral": "How are you feeling about this concept so far?",
                "high": "Great! I can see you're engaged. Let's dive deeper."
            },
            "navigation_encouragement": {
                "general": "Take your time to absorb this information. When you're ready to continue, just click the 'Next' button.",
                "ready_to_move": "It sounds like you're ready to move forward! Go ahead and click 'Next' when you want to continue.",
                "review_suggestion": "If you'd like to review the previous slide, click the 'Previous' button. Otherwise, click 'Next' to continue.",
                "location_help": "You can see which slide we're on in the navigation area at the top of the screen."
            },
             "personalized_welcome": {
                "returning_user": "Welcome back, {name}! I remember you're interested in {interests} and have {experience_level} experience. Ready to continue where we left off?",
                "new_user": "Hello {name}! Thanks for telling me about your {experience_level} experience level and interest in {interests}. I'll personalize our learning journey accordingly."
            }
        }

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            api_key = Config.OPENAI_API_KEY
            if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
                raise ValueError(
                    "❌ OpenAI API key not set or invalid.\n"
                    "🔑 Get a new key from: https://platform.openai.com/api-keys\n"
                    "📝 Update OPENAI_API_KEY in config.py or set as environment variable"
                )
            self._client = OpenAI(api_key=api_key)
        return self._client

    def update_user_profile(self, updates: Dict[str, Any]) -> None:
        """Update user profile in memory"""
        for key, value in updates.items():
            if hasattr(self.user_profile, key):
                setattr(self.user_profile, key, value)
        logger.info(f"👤 User profile updated: {updates}")
        # Note: Persistent storage of user profile would be handled elsewhere

    def process_user_input(self, user_input: str, current_slide: int, input_type: str = "text", conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process user input, get slide context, and generate personalized coaching response.
        """
        self.coaching_context.slide_number = current_slide # Update current slide in context
        user_input_lower = user_input.lower()

        # NEW: Update conversation history if provided
        if conversation_history:
            logger.info(f"📚 Received {len(conversation_history)} messages in conversation history")
            # Clear existing history and use the provided one
            self.conversation_history = conversation_history
            # Add current user input if not already the last message
            if not self.conversation_history or self.conversation_history[-1].get("content") != user_input:
                self.conversation_history.append({"role": "user", "content": user_input})
        else:
            # If no history provided, just add current input
            self.add_message("user", user_input)

        # Define keywords for learning intents (questions about content) and location intents
        learning_keywords = ["explain", "tell me about", "what is", "why is", "how does", "define", "describe", "clarify", "understand", "meaning", "relevance"]
        location_keywords = ["which slide", "what slide", "current slide", "we are on"] # Add keywords related to slide location

        # Check for learning intent keywords
        has_learning_intent_keywords = any(keyword in user_input_lower for keyword in learning_keywords)

        # Check for location intent keywords
        has_location_intent_keywords = any(keyword in user_input_lower for keyword in location_keywords)

        # Check for navigation intent (handled externally, but could check here for logging/info)
        # is_navigation_intent = self.voice_interaction.has_navigation_intent(user_input)

        # Determine interaction type for logging/handling
        if has_learning_intent_keywords or has_location_intent_keywords:
            logger.info(f"📚 Learning or location interaction detected. Getting slide context.")
            # Directly generate response instead of calling _handle_learning_interaction
            coaching_response = self._generate_personalized_response(user_input)
            return {
                 "type": "learning",
                 "success": True,
                 "coaching_response": coaching_response,
                 "personalization_applied": True,
                 "slide_info": self.slide_controller.get_navigation_info()
            }
        else:
            logger.info(f"💬 General interaction detected. Getting slide context for response.")
            # Directly generate response for general interactions too
            coaching_response = self._generate_personalized_response(user_input)
            return {
                "type": "general",
                "success": True,
                "coaching_response": coaching_response,
                "personalization_applied": True,
                "slide_info": self.slide_controller.get_navigation_info()
            }

    # Removed _handle_learning_interaction as logic is now combined

    def _analyze_user_input(self, user_input: str) -> None:
        """Analyze user input to update personalization"""
        # This logic remains largely the same
        input_lower = user_input.lower()
        profile_changed = False # Keep track if profile fields changed

        # Detect experience level indicators
        if any(word in input_lower for word in ["confused", "don't understand", "what is", "explain", "help"]):
            if self.user_profile.experience_level == "advanced":
                self.user_profile.experience_level = "intermediate"
                profile_changed = True
            elif self.user_profile.experience_level == "intermediate":
                self.user_profile.experience_level = "beginner"
                profile_changed = True

        elif any(word in input_lower for word in ["already know", "familiar", "experienced", "advanced"]):
            if self.user_profile.experience_level == "beginner":
                self.user_profile.experience_level = "intermediate"
                profile_changed = True
            elif self.user_profile.experience_level == "intermediate":
                self.user_profile.experience_level = "advanced"
                profile_changed = True

        # Detect interests
        ai_keywords = ["machine learning", "ai", "artificial intelligence", "neural networks", "automation"]
        ux_keywords = ["user experience", "design", "interface", "usability", "user research"]
        research_keywords = ["research", "testing", "analytics", "data", "insights"]

        if any(keyword in input_lower for keyword in ai_keywords):
            if "AI/ML" not in self.user_profile.interests:
                self.user_profile.interests.append("AI/ML")
                profile_changed = True

        if any(keyword in input_lower for keyword in ux_keywords):
            if "UX Design" not in self.user_profile.interests:
                self.user_profile.interests.append("UX Design")
                profile_changed = True

        if any(keyword in input_lower for keyword in research_keywords):
            if "User Research" not in self.user_profile.interests:
                self.user_profile.interests.append("User Research")
                profile_changed = True

        # Update engagement level
        engagement_indicators = {
            "high": ["interesting", "great", "love", "excited", "more", "awesome", "amazing"],
            "low": ["boring", "confused", "lost", "difficult", "skip", "hard"],
            "neutral": ["ok", "fine", "continue", "next", "sure"]
        }

        for level, indicators in engagement_indicators.items():
            if any(indicator in input_lower for indicator in indicators):
                self.coaching_context.engagement_level = level
                break

        # Extract name if mentioned (simplified)
        name_match = re.search(r"(?:my name is|i'm)\s+([a-zA-Z]+)", input_lower)
        if name_match:
             potential_name = name_match.group(1).capitalize()
             if potential_name not in ["A", "An", "The", "Interested", "Learning", "About", "I"]: # Avoid common words and 'I'
                 self.user_profile.name = potential_name
                 profile_changed = True

        # Note: Persistent storage of profile changes would be handled elsewhere


    def _generate_personalized_response(self, user_input: str) -> str:
        """Generate coaching response using the LLM with combined logic"""
        # 1. Get slide context from the database (using 1-based index)
        try:
            slide_context_str = self._get_slide_context_from_db(self.coaching_context.slide_number, self.lesson_id)
        except Exception as e:
             logger.error(f"❌ Error fetching slide context in _generate_personalized_response: {e}")
             slide_context_str = f"Could not retrieve specific content for this slide due to an internal error. ({e})"

        # 2. Gather other context for the LLM
        context = {
            "slide_number": self.coaching_context.slide_number,
            "experience_level": self.user_profile.experience_level,
            "interests": self.user_profile.interests,
            "learning_style": self.user_profile.learning_style,
            "recent_questions": self.coaching_context.user_questions[-3:], # Last 3 questions
            "name": self.user_profile.name,
            "engagement_level": self.coaching_context.engagement_level,
        }

        # 3. Get the system prompt with active modifiers
        try:
            from .system_prompt_manager import get_system_prompt_manager
            prompt_manager = get_system_prompt_manager()
            
            # Activate relevant contexts based on user profile
            prompt_manager.activate_context('coaching')
            if self.user_profile.experience_level == 'beginner':
                prompt_manager.activate_context('beginner')
            elif self.user_profile.experience_level == 'advanced':
                prompt_manager.activate_context('advanced')

            # Get the full prompt with all active modifiers
            base_prompt = prompt_manager.get_full_prompt()
            if not base_prompt:
                base_prompt = "You are a helpful AI assistant specialized in UX design and AI tools."
                logger.warning("⚠️ Centralized system prompt not available, using default.")

        except Exception as e:
            logger.warning(f"⚠️ Error with centralized prompt manager: {e}")
            base_prompt = "You are a helpful AI assistant specialized in UX design and AI tools."

        # 4. Compose final system prompt for the LLM API call
        system_prompt = f"""{base_prompt}

## CURRENT CONTEXT:
- You are on Slide {self.coaching_context.slide_number + 1} of the workshop
- Slide Content: {slide_context_str}

## USER CONTEXT:
- Experience Level: {context['experience_level']}
- Learning Style: {context['learning_style']}
- Name: {context['name'] if context['name'] else 'Not provided'}
- Engagement: {context['engagement_level']}
- Recent Questions: {', '.join(context['recent_questions']) if context['recent_questions'] else 'None'}

## RESPONSE GUIDELINES:
- Keep responses focused on the current slide content
- Maintain a conversational and encouraging tone
- Ask relevant questions to check understanding
- Adapt your explanation style to the user's experience level
- Do not mention technical terms like "database" or "markdown file"
"""

        # 5. Prepare messages for the LLM API
        messages = []
        messages.append({"role": "system", "content": system_prompt})

        # Add recent conversation history
        history_limit = 10
        messages.extend(self.conversation_history[max(0, len(self.conversation_history) - history_limit):])

        # Ensure the last message is the current user input
        if messages and (messages[-1].get("role") != "user" or messages[-1].get("content") != user_input):
            if messages and messages[-1].get("role") == "user":
                messages.pop()
            messages.append({"role": "user", "content": user_input})
        elif not messages:
            messages.append({"role": "user", "content": user_input})

        logger.debug(f"Prepared {len(messages)} messages for API call. System prompt length: {len(system_prompt)}")

        # 6. Call the OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            ai_response = response.choices[0].message.content
            logger.info("✅ Received response from LLM")

        except Exception as e:
            logger.error(f"❌ Error calling LLM API: {e}")
            ai_response = "I apologize, but I encountered an error trying to generate a response. Please try again!"
            import traceback
            logger.error(traceback.format_exc())

        # 7. Store the interaction in history
        self.add_message("user", user_input)
        self.add_message("assistant", ai_response)

        return ai_response


    def _get_slide_context_from_db(self, slide_number: int, lesson_id: str) -> str:
        """Get slide content from database for AI responses"""
        # Adjust slide_number to be 1-based for database lookup
        db_slide_number = slide_number + 1
        logger.info(f"Attempting to get slide context for slide {slide_number + 1} (DB: {db_slide_number}) from database for lesson {lesson_id}")
        try:
            # lesson_manager is already initialized in __init__
            slide_data = self.lesson_manager.get_slide_content(lesson_id=lesson_id, slide_number=db_slide_number)

            if not slide_data:
                logger.warning(f"⚠️ No slide content found in database for slide {slide_number + 1} (DB: {db_slide_number}), lesson {lesson_id}")
                # If no data found, return a specific message for the AI
                return f"No specific content found for Slide {slide_number + 1} in the database."


            # Build context string from database content
            content_list = slide_data.get('content', [])
            content_text = '\n'.join([f"- {item}" for item in content_list])

            key_concepts = slide_data.get('key_concepts', [])
            concepts_text = ', '.join(key_concepts) if key_concepts else 'None specified'

            coaching_notes = slide_data.get('coaching_notes', [])
            notes_text = '\n'.join([f"- {note}" for note in coaching_notes]) if coaching_notes else 'No coaching notes available'

            questions = slide_data.get('questions_to_ask', [])
            questions_text = '\n'.join([f"- {q}" for q in questions]) if questions else 'No suggested questions'

            # Get lesson context from database - assuming LessonManager has this method
            try:
                # Assuming LessonManager has get_lesson_context method
                lesson_context = self.lesson_manager.get_lesson_context(lesson_id)
                logger.debug(f"Retrieved lesson context for lesson {lesson_id}")
            except AttributeError:
                logger.warning("LessonManager has no get_lesson_context method. Using default.")
                lesson_context = "Interactive workshop focused on practical application and hands-on learning. Emphasis on real-world examples and hands-on practice."
            except Exception as e:
                 logger.warning(f"Error getting lesson context: {e}. Using default.")
                 lesson_context = "Interactive workshop focused on practical application and hands-on learning. Emphasis on real-world examples and hands-on practice."


            # Use a regular f-string and double braces for literal curly braces
            # Correcting the nested f-string syntax for the title fallback
            slide_title = slide_data.get('title', f'Slide {slide_number + 1}')
            context_string = f"""Slide Title: {slide_title}
Content:
{content_text}

Key Concepts: {concepts_text}
Coaching Notes (for AI reference):
{notes_text}

Suggested Discussion Questions:
{questions_text}

General Workshop Context: {lesson_context}
"""


            logger.info(f"✅ Using database content for slide {slide_number + 1}")
            logger.debug(f"Database context string preview:\n{context_string[:500]}...")
            return context_string

        except Exception as e:
            # If database access fails, log the error and return a minimal context string
            logger.error(f"❌ Error getting slide context from database: {e}")
            return f"Could not retrieve specific content for Slide {slide_number + 1} due to an error: {e}"


    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        # Simple history management
        self.conversation_history.append({"role": role, "content": content})
        # Optional: Limit history length to manage memory/token usage
        self.conversation_history = self.conversation_history[-20:] # Keep last 20 messages


    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("🗑️ Conversation history cleared")

    def generate_lesson_greeting(self, current_slide: int = 0, lesson_context: Dict = None) -> str:
        """Generate a personalized lesson greeting"""
        try:
            # Get lesson info from database
            lesson = self.lesson_manager.get_lesson(self.lesson_id)
            if not lesson:
                raise Exception(f"Lesson {self.lesson_id} not found")
            
            lesson_title = lesson.get('title', 'this lesson')
            total_slides = len(self.lesson_manager.get_lesson_slides(self.lesson_id))
            
            # Get first slide info
            first_slide = None
            try:
                first_slide_data = self.lesson_manager.get_slide_content(self.lesson_id, 1)
                first_slide = first_slide_data.get('title', 'Introduction') if first_slide_data else 'Introduction'
            except:
                first_slide = 'Introduction'
            
            # Generate personalized greeting based on user profile
            if self.user_profile.name:
                greeting_start = f"Hello {self.user_profile.name}! "
            else:
                greeting_start = "Hello! "
            
            # Customize based on experience level
            if self.user_profile.experience_level == "beginner":
                approach = "I'll guide you through each concept step by step, making sure you understand everything before we move on."
            elif self.user_profile.experience_level == "advanced":
                approach = "I'll focus on the advanced applications and how these concepts connect to your existing knowledge."
            else:
                approach = "I'll adapt my explanations to match your learning pace and interests."
            
            # Build the greeting
            greeting = f"""{greeting_start}Welcome to "{lesson_title}"! I'm your AI coach, and I'm excited to learn alongside you today.
            
We have {total_slides} slides to explore together, starting with "{first_slide}". {approach}
            
I'm here to answer questions, explain concepts, and help you get the most out of this material. You can ask me anything about what you see on screen, request examples, or even ask me to explain things differently if something isn't clear.
            
Feel free to interact with me naturally - just speak or type your questions. When you're ready to move to the next slide, simply click the 'Next' button.
            
Shall we dive in?"""
            
            logger.info(f"🎉 Generated personalized greeting for lesson {self.lesson_id}")
            return greeting
            
        except Exception as e:
            logger.error(f"❌ Error generating lesson greeting: {e}")
            # Fallback greeting
            return f"Welcome to this lesson! I'm your AI coach and I'm here to help you learn. We're starting with slide {current_slide + 1}. Feel free to ask me questions about anything you see here!"
    
    def get_status(self):
        """Get current status of the LessonCoachingManager"""
        return {
            'lesson_id': self.lesson_id,
            'current_slide': self.coaching_context.slide_number,
            'conversation_history_length': len(self.conversation_history),
            'user_experience_level': self.user_profile.experience_level,
            'user_interests': self.user_profile.interests,
            'engagement_level': self.coaching_context.engagement_level,
            # Add other relevant status info
        }

    # Potentially add methods for navigation handling if needed here,
    # but for now, assume navigation updates self.coaching_context.slide_number externally.


# We will need to instantiate this class per lesson session.
# The app.py or a session manager will handle creating instances.
# For now, we can keep a simple global instance for basic testing if needed,
# but the proper implementation would be per-session.

# Global instance for basic testing/access (consider removing in production per-session model)
# lesson_coaching_manager_instance = LessonCoachingManager("default-lesson-id") # Need a valid default lesson or handle dynamically

# def get_lesson_coaching_manager(lesson_id: str) -> LessonCoachingManager:
#     """Get or create LessonCoachingManager instance for a lesson ID"""
#     # This would need a proper session management mechanism
#     # For now, just a placeholder
#     global lesson_coaching_manager_instance
#     if lesson_coaching_manager_instance.lesson_id != lesson_id:
#          logger.warning(f"Creating new LessonCoachingManager instance for lesson: {lesson_id}")
#          lesson_coaching_manager_instance = LessonCoachingManager(lesson_id)
#     return lesson_coaching_manager_instance 