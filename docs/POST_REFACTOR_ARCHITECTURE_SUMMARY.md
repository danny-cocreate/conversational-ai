# Post-Refactoring Architecture Summary: Guidance-Based AI Coaching System

This document describes the system architecture following the refactoring efforts that consolidated coaching and conversation management into the `LessonCoachingManager` and solidified the database as a core requirement.

## Key Architectural Changes

1.  **Consolidation of Coaching Logic:** The separate `coaching_agent.py` and `conversation_manager.py` files have been removed. Their core functionalities for handling user input, maintaining conversation history, integrating context (like slide content), and managing lesson-specific data have been merged into the **`LessonCoachingManager` class** within the `slide_module_simplified` package.
2.  **Database as a Core Dependency:** The system now fundamentally relies on the database for essential functions. Features such as loading lesson content, retrieving the lesson-specific system prompt, managing user sessions, storing user preferences, tracking interaction history (for enhanced memory), and managing the knowledge base documents are all handled through the database components integrated within the `slide_module_simplified` package. The previous notion of the database being "optional" is no longer accurate for the intended functionality of the system.
3.  **Lesson-Scoped Management:** The `LessonCoachingManager` operates on a per-lesson basis. An instance of this manager is typically created or retrieved for each active lesson session, ensuring that conversations, system prompts, and knowledge base documents are correctly scoped to the specific lesson the user is interacting with.
4.  **Streamlined Backend Endpoints:** Backend endpoints in `app.py` related to lesson interactions, system prompts, and knowledge base management (`/lesson/<lesson_id>/chat`, `/system-prompt`, `/documents`, `/knowledge-base/status`, etc.) have been updated to route requests through the appropriate `LessonCoachingManager` instance, requiring the `lesson_id` as part of the request. Outdated endpoints related to the old "Router Pattern" or global conversation management have been removed.
5.  **Updated Imports and Dependencies:** Imports across the codebase, particularly in `app.py` and `slide_module_simplified/__init__.py`, have been updated to reflect the removal of the old files and the new structure where functions like `start_enhanced_session` and variables like `DATABASE_AVAILABLE` are accessed via the `slide_module_simplified.database` module or are handled internally within the new manager.

## Current System Flow (Lesson Interaction)

1.  The user accesses a specific lesson page (e.g., `/lesson/<lesson_id>`). The frontend identifies the `lesson_id`.
2.  The frontend sends user input (text/voice) to the `/lesson/<lesson_id>/chat` endpoint, including the user's message, the `lesson_id`, and the current slide number.
3.  The backend (`app.py`) receives the request and retrieves the `LessonCoachingManager` instance associated with that `lesson_id`. If one doesn't exist for the current session, it creates a new one.
4.  The `LessonCoachingManager` uses the `lesson_id` and `current_slide` to access the relevant lesson content and potentially retrieve session history, user preferences, and the lesson's specific system prompt from the database.
5.  The manager processes the user's input using this context and generates a coaching response.
6.  The response is sent back to the frontend, where it is displayed or synthesized into speech.

## Key Components

-   **`LessonCoachingManager`**: Manages the conversation state, knowledge base, system prompt, and interaction logic for a specific lesson, integrating with the database.
-   **Database Components**: Handle persistent storage for all lesson content, user data, and session information, enabling enhanced memory and personalization.
-   **Frontend (JavaScript)**: Manages the user interface, captures input, displays output, and ensures that `lesson_id` is included in relevant backend requests.
-   **Flask Endpoints**: Route frontend requests to the correct `LessonCoachingManager` instance and other backend services.

This refactoring has resulted in a more focused and maintainable architecture where lesson-specific logic and data management are centralized, and the database plays a critical, integrated role. 