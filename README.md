# Conversational AI with Voice Interface

A web-based conversational AI application that features voice interaction capabilities and knowledge base management. The application supports text-to-speech, speech-to-text, and maintains a dynamic knowledge base for enhanced conversations.

## Features

- Real-time voice conversations with AI
- Text-to-Speech capabilities
- Speech-to-Text input
- Customizable system prompts
- Knowledge base management
- Adjustable speech speed
- Multiple voice options

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install flask openai httpx tqdm
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Project Structure

- `app.py`: Main Flask application
- `conversation.py`: Conversation handling logic
- `document_processor.py`: Knowledge base document processing
- `templates/`: HTML templates
- `knowledge_base/`: Directory for knowledge base documents

## Usage

1. Set up your system prompt for AI behavior customization
2. Upload relevant documents to the knowledge base
3. Start conversations using text or voice input
4. Adjust voice settings as needed

## License

MIT License