from database import db

# Persistent TTS Settings Model
class TTSSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(64), default='hume_evi3')
    voice_id = db.Column(db.String(128), default='ee966436-01ab-4810-a880-9e0a532e03b8')
    speed = db.Column(db.String(16), default='1.0')
    temperature = db.Column(db.String(16), default='0.7')

# Token Optimization Settings
class TokenSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    max_conversation_history = db.Column(db.Integer, default=5)  # Number of messages to keep
    max_system_prompt_length = db.Column(db.Integer, default=1000)  # Max chars in system prompt
    enable_context_pruning = db.Column(db.Boolean, default=True)  # Whether to prune old context
    enable_context_summarization = db.Column(db.Boolean, default=True)  # Whether to summarize old context
    max_emotional_states = db.Column(db.Integer, default=5)  # Number of emotional states to keep
    token_optimization_level = db.Column(db.String(16), default='balanced')  # aggressive, balanced, or minimal 