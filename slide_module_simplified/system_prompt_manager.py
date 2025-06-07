"""
System Prompt Manager - Centralizes all system prompt handling
"""
from typing import Dict, Optional, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Import database components
try:
    from .database.models import get_db_connection, json_serialize, json_deserialize
    DATABASE_AVAILABLE = True
    logger.info("📊 Database components available for SystemPromptManager")
except ImportError:
    DATABASE_AVAILABLE = False
    get_db_connection = None
    json_serialize = None
    json_deserialize = None
    logger.warning("⚠️ Database components not available for SystemPromptManager")

class SystemPromptManager:
    """Manages system prompts and their modifications across the application"""
    
    def __init__(self):
        self.base_prompt = ""
        self.modifiers = {}  # Store prompt modifiers by context
        self.active_contexts = set()  # Track which contexts are active
        self._load_settings()
        
    def _load_settings(self):
        """Load system settings from the database"""
        if not DATABASE_AVAILABLE:
            raise RuntimeError(
                "Database components are not available. Please ensure the database is properly configured "
                "and the required modules are installed. Contact your system administrator."
            )

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT base_prompt, modifiers FROM system_settings WHERE id = 1
            ''')
            row = cursor.fetchone()

            if row:
                self.base_prompt = row['base_prompt'] or ""
                try:
                    self.modifiers = json_deserialize(row['modifiers']) or {}
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"Failed to parse system prompt modifiers from database: {e}. "
                        "The database may be corrupted. Please contact your system administrator."
                    )

                logger.info("✅ Loaded system settings from database")
                logger.info(f"Loaded base prompt (first 50 chars): {self.base_prompt[:50]}...")
                logger.info(f"Loaded {len(self.modifiers)} modifiers.")
            else:
                # This should not happen if init_database ran, but as a fallback:
                raise RuntimeError(
                    "No system settings found in database. The system has not been properly initialized. "
                    "Please contact your system administrator to run the initialization process."
                )

            conn.close()
        except Exception as e:
            raise RuntimeError(
                f"Failed to load system settings from database: {e}. "
                "Please contact your system administrator to check the database configuration."
            )

    def _get_default_prompt(self) -> str:
        """Get a default system prompt when database is unavailable"""
        if not DATABASE_AVAILABLE:
            raise RuntimeError(
                "Database components are not available. Please ensure the database is properly configured "
                "and the required modules are installed. Contact your system administrator."
            )

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT base_prompt FROM system_settings WHERE id = 1')
            row = cursor.fetchone()
            if row and row['base_prompt']:
                return row['base_prompt']
            raise RuntimeError(
                "No system prompt found in database. The system has not been properly initialized. "
                "Please contact your system administrator to run the initialization process."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load system prompt from database: {e}. "
                "Please contact your system administrator to check the database configuration."
            )
        finally:
            if conn:
                conn.close()
    
    def _save_settings(self):
        """Save system settings to the database"""
        if not DATABASE_AVAILABLE:
            raise RuntimeError(
                "Database components are not available. Cannot save system settings. "
                "Please ensure the database is properly configured and contact your system administrator."
            )

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            modifiers_json = json_serialize(self.modifiers) or "{}"

            cursor.execute('''
                INSERT OR REPLACE INTO system_settings (id, base_prompt, modifiers, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (1, self.base_prompt, modifiers_json, datetime.now()))

            conn.commit()
            conn.close()
            logger.info("💾 Saved system settings to database")
        except Exception as e:
            raise RuntimeError(
                f"Failed to save system settings to database: {e}. "
                "Please contact your system administrator to check the database configuration."
            )
        
    def set_base_prompt(self, prompt: str) -> None:
        """Set the base system prompt and save to DB"""
        self.base_prompt = prompt
        logger.info(f"Base system prompt updated in memory: {len(prompt)} chars")
        logger.info(f"Attempting to save base prompt to DB (first 50 chars): {self.base_prompt[:50]}...")
        self._save_settings() # Save changes to database
        
    def add_modifier(self, context: str, modifier: str) -> None:
        """Add a prompt modifier for a specific context and save to DB"""
        self.modifiers[context] = modifier
        logger.info(f"Added prompt modifier for context: {context} in memory")
        self._save_settings() # Save changes to database
        
    def remove_modifier(self, context: str) -> None:
        """Remove a prompt modifier and save to DB"""
        if context in self.modifiers:
            del self.modifiers[context]
            logger.info(f"Removed prompt modifier for context: {context} from memory")
            self._save_settings() # Save changes to database
            
    def activate_context(self, context: str) -> None:
        """Activate a context's modifier"""
        if context in self.modifiers:
            self.active_contexts.add(context)
            logger.info(f"Activated context: {context}")
            # Activation is only in-memory, no DB save needed
            
    def deactivate_context(self, context: str) -> None:
        """Deactivate a context's modifier"""
        if context in self.active_contexts:
            self.active_contexts.remove(context)
            logger.info(f"Deactivated context: {context}")
            # Deactivation is only in-memory, no DB save needed
            
    def get_full_prompt(self) -> str:
        """Get the complete system prompt with all active modifiers"""
        if not self.base_prompt:
            logger.warning("No base prompt set")
            return ""
            
        # Start with base prompt
        full_prompt = self.base_prompt
        
        # Add active modifiers
        for context in self.active_contexts:
            if context in self.modifiers:
                full_prompt += f"\n\n{self.modifiers[context]}"
                
        return full_prompt
        
    def get_status(self) -> Dict:
        """Get current system prompt status"""
        return {
            'base_prompt_length': len(self.base_prompt) if self.base_prompt else 0,
            'active_contexts': list(self.active_contexts),
            'available_modifiers': list(self.modifiers.keys()),
            'full_prompt_length': len(self.get_full_prompt())
        }

    def initialize_database(self) -> None:
        """Initialize the database with default system prompt and modifiers"""
        if not DATABASE_AVAILABLE:
            logger.warning("Database not available, cannot initialize defaults")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if settings already exist
            logger.info("Checking if system settings already exist...")
            cursor.execute('SELECT id FROM system_settings WHERE id = 1')
            if cursor.fetchone():
                logger.info("System settings already exist in database, skipping initialization.")
                return

            logger.warning("No system settings found in database. Initializing with defaults.")

            # Default base prompt
            default_base_prompt = """You are a helpful and epathetic coach."""

            # Default modifiers
            default_modifiers = {
                'coaching': '''COACHING GUIDELINES:
- Ask one question at a time and wait for the student's response
- Match the student's communication style
- When a student seems confused, acknowledge it first, then ask what specific part is unclear
- Use real-world examples before explaining theory
- Keep responses conversational, not bullet points
- If a student asks "I don't get it", ask them to point to the specific part that's confusing
- Don't overwhelm with information - give small digestible pieces''',
                
                'beginner': '''BEGINNER-FRIENDLY APPROACH:
- Explain technical terms in simple language
- Provide more context and background
- Use analogies and real-world examples
- Check understanding frequently
- Break complex concepts into smaller steps''',
                
                'advanced': '''ADVANCED LEARNER APPROACH:
- Assume familiarity with basic concepts
- Focus on nuances and edge cases
- Discuss implications and advanced applications
- Encourage critical thinking and analysis
- Reference industry best practices'''
            }

            # Insert default settings
            cursor.execute('''
                INSERT INTO system_settings (id, base_prompt, modifiers, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (1, default_base_prompt, json_serialize(default_modifiers), datetime.now()))

            conn.commit()
            logger.info("✅ Initialized database with default system prompt and modifiers")
        except Exception as e:
            logger.error(f"Error initializing database defaults: {e}")
        finally:
            if conn:
                conn.close()

def initialize_default_modifiers(manager: SystemPromptManager) -> None:
    """Initialize default context modifiers if they don't exist"""
    default_modifiers = {
        'coaching': '''COACHING GUIDELINES:
- Ask one question at a time and wait for the student's response
- Match the student's communication style
- When a student seems confused, acknowledge it first, then ask what specific part is unclear
- Use real-world examples before explaining theory
- Keep responses conversational, not bullet points
- If a student asks "I don't get it", ask them to point to the specific part that's confusing
- Don't overwhelm with information - give small digestible pieces''',
        
        'beginner': '''BEGINNER-FRIENDLY APPROACH:
- Explain technical terms in simple language
- Provide more context and background
- Use analogies and real-world examples
- Check understanding frequently
- Break complex concepts into smaller steps''',
        
        'advanced': '''ADVANCED LEARNER APPROACH:
- Assume familiarity with basic concepts
- Focus on nuances and edge cases
- Discuss implications and advanced applications
- Encourage critical thinking and analysis
- Reference industry best practices'''
    }
    
    # Add modifiers that don't already exist
    added_count = 0
    for context, modifier in default_modifiers.items():
        if context not in manager.modifiers:
            manager.add_modifier(context, modifier)
            added_count += 1
            logger.info(f"📝 Added default modifier: {context}")
    
    if added_count > 0:
        logger.info(f"✅ Initialized {added_count} default modifiers")
    else:
        logger.info("ℹ️ All default modifiers already exist")

# Global instance
system_prompt_manager = SystemPromptManager()

# Initialize database with defaults on first run
system_prompt_manager.initialize_database()

# Add logging before initializing default modifiers
logger.info(f"Base prompt before initializing default modifiers (first 50 chars): {system_prompt_manager.base_prompt[:50]}...")

# Initialize default modifiers on first run
initialize_default_modifiers(system_prompt_manager)

def get_system_prompt_manager() -> SystemPromptManager:
    """Get the global system prompt manager instance"""
    return system_prompt_manager 