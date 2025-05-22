import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ConversationManager:
    def __init__(self):
        self.conversation_history = []
        self.model = "gpt-4.1-nano"
        self.system_prompt = ""
        self.knowledge_base = {}
        
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the conversation."""
        self.system_prompt = prompt
        # Clear existing history when system prompt changes
        self.clear_history()
    
    def add_message(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_response(self, user_input):
        """Get a response from the GPT model."""
        try:
            # Add user input to conversation history
            self.add_message("user", user_input)
            
            # Prepare messages with system prompt and knowledge context
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            
            # Add relevant knowledge base context
            if self.knowledge_base:
                context = "Available knowledge base information:\n" + "\n".join(self.knowledge_base.values())
                messages.append({"role": "system", "content": context})
            
            # Add conversation history
            messages.extend(self.conversation_history)
            
            # Get response from GPT
            response = client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            # Extract and store assistant's response
            assistant_response = response.choices[0].message.content
            self.add_message("assistant", assistant_response)
            
            return assistant_response
        
        except Exception as e:
            raise Exception(f"Error getting GPT response: {str(e)}")
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []