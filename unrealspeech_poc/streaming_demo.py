"""
Unreal Speech Streaming Flask Demo
Demonstrates real-time streaming TTS in a web application
"""

from flask import Flask, Response, request, jsonify, render_template_string
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
UNREALSPEECH_API_KEY = os.getenv("UNREALSPEECH_API_KEY", "YOUR_API_KEY_HERE")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Unreal Speech Streaming Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        textarea, select, input[type="range"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        #status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        audio {
            width: 100%;
            margin-top: 20px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        .metric {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Unreal Speech Streaming Demo</h1>
        
        <div class="form-group">
            <label for="text">Text to synthesize:</label>
            <textarea id="text" placeholder="Enter your text here...">Hello! This is a test of Unreal Speech streaming text-to-speech. Notice how quickly the audio starts playing!</textarea>
        </div>
        
        <div class="form-group">
            <label for="voice">Voice:</label>
            <select id="voice">
                <optgroup label="Female Voices">
                    <option value="af_sky" selected>Sky (Female)</option>
                    <option value="af_bella">Bella (Female)</option>
                    <option value="af_sarah">Sarah (Female)</option>
                    <option value="af_nicole">Nicole (Female)</option>
                    <option value="bf_emma">Emma (British Female)</option>
                    <option value="bf_isabella">Isabella (British Female)</option>
                </optgroup>
                <optgroup label="Male Voices">
                    <option value="am_adam">Adam (Male)</option>
                    <option value="am_michael">Michael (Male)</option>
                    <option value="bm_george">George (British Male)</option>
                    <option value="bm_lewis">Lewis (British Male)</option>
                </optgroup>
            </select>
        </div>
        
        <div class="form-group">
            <label for="speed">Speed: <span id="speedValue">1.0x</span></label>
            <input type="range" id="speed" min="-1" max="1" step="0.1" value="0">
        </div>
        
        <div class="form-group">
            <label for="pitch">Pitch: <span id="pitchValue">1.0</span></label>
            <input type="range" id="pitch" min="0.5" max="1.5" step="0.1" value="1">
        </div>
        
        <button onclick="synthesize()">Generate Speech</button>
        <button onclick="testStreaming()">Test Streaming</button>
        <button onclick="clearAudio()">Clear</button>
        
        <div id="status"></div>
        
        <audio id="audioPlayer" controls style="display: none;"></audio>
        
        <div class="metrics" id="metrics" style="display: none;">
            <div class="metric">
                <div class="metric-value" id="ttfb">-</div>
                <div class="metric-label">Time to First Byte</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="totalTime">-</div>
                <div class="metric-label">Total Time</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="dataSize">-</div>
                <div class="metric-label">Audio Size</div>
            </div>
        </div>
    </div>

    <script>
        // Update slider values
        document.getElementById('speed').addEventListener('input', (e) => {
            document.getElementById('speedValue').textContent = 
                e.target.value > 0 ? `${1 + parseFloat(e.target.value)}x` : 
                e.target.value < 0 ? `${1 + parseFloat(e.target.value)}x` : '1.0x';
        });
        
        document.getElementById('pitch').addEventListener('input', (e) => {
            document.getElementById('pitchValue').textContent = e.target.value;
        });

        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = type;
            status.style.display = 'block';
            
            if (type === 'success' || type === 'error') {
                setTimeout(() => {
                    status.style.display = 'none';
                }, 5000);
            }
        }

        function clearAudio() {
            const audio = document.getElementById('audioPlayer');
            audio.style.display = 'none';
            audio.src = '';
            document.getElementById('metrics').style.display = 'none';
            showStatus('Cleared', 'info');
            setTimeout(() => {
                document.getElementById('status').style.display = 'none';
            }, 1000);
        }

        async function synthesize() {
            const text = document.getElementById('text').value;
            const voice = document.getElementById('voice').value;
            const speed = document.getElementById('speed').value;
            const pitch = document.getElementById('pitch').value;
            
            if (!text) {
                showStatus('Please enter some text', 'error');
                return;
            }
            
            if (text.length > 1000) {
                showStatus('Text too long! Maximum 1,000 characters for streaming.', 'error');
                return;
            }
            
            showStatus('Generating speech...', 'info');
            const startTime = performance.now();
            
            try {
                const response = await fetch('/synthesize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        voice_id: voice,
                        speed: speed,
                        pitch: pitch
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Synthesis failed');
                }
                
                const blob = await response.blob();
                const audioUrl = URL.createObjectURL(blob);
                const audio = document.getElementById('audioPlayer');
                
                audio.src = audioUrl;
                audio.style.display = 'block';
                
                const totalTime = performance.now() - startTime;
                
                // Update metrics
                document.getElementById('metrics').style.display = 'grid';
                document.getElementById('ttfb').textContent = 'N/A';
                document.getElementById('totalTime').textContent = `${(totalTime/1000).toFixed(2)}s`;
                document.getElementById('dataSize').textContent = `${(blob.size/1024).toFixed(1)}KB`;
                
                showStatus('Speech generated successfully!', 'success');
                
            } catch (error) {
                showStatus(`Error: ${error.message}`, 'error');
            }
        }

        async function testStreaming() {
            const text = document.getElementById('text').value;
            const voice = document.getElementById('voice').value;
            const speed = document.getElementById('speed').value;
            const pitch = document.getElementById('pitch').value;
            
            if (!text) {
                showStatus('Please enter some text', 'error');
                return;
            }
            
            showStatus('Starting streaming...', 'info');
            
            const startTime = performance.now();
            let firstByteTime = null;
            const chunks = [];
            
            try {
                const response = await fetch('/stream', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        voice_id: voice,
                        speed: speed,
                        pitch: pitch
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Streaming failed');
                }
                
                const reader = response.body.getReader();
                
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) break;
                    
                    if (firstByteTime === null) {
                        firstByteTime = performance.now() - startTime;
                    }
                    
                    chunks.push(value);
                }
                
                // Combine chunks into a single blob
                const blob = new Blob(chunks, { type: 'audio/mpeg' });
                const audioUrl = URL.createObjectURL(blob);
                const audio = document.getElementById('audioPlayer');
                
                audio.src = audioUrl;
                audio.style.display = 'block';
                
                const totalTime = performance.now() - startTime;
                
                // Update metrics
                document.getElementById('metrics').style.display = 'grid';
                document.getElementById('ttfb').textContent = `${firstByteTime.toFixed(0)}ms`;
                document.getElementById('totalTime').textContent = `${(totalTime/1000).toFixed(2)}s`;
                document.getElementById('dataSize').textContent = `${(blob.size/1024).toFixed(1)}KB`;
                
                showStatus('Streaming completed!', 'success');
                
            } catch (error) {
                showStatus(`Error: ${error.message}`, 'error');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Standard synthesis endpoint"""
    try:
        data = request.json
        text = data.get('text', '')
        voice_id = data.get('voice_id', 'af_sky')
        speed = data.get('speed', '0')
        pitch = data.get('pitch', '1')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if len(text) > 1000:
            return jsonify({'error': 'Text too long (max 1000 chars)'}), 400
        
        # Call Unreal Speech API
        response = requests.post(
            'https://api.v8.unrealspeech.com/stream',
            headers={
                'Authorization': f'Bearer {UNREALSPEECH_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'Text': text,
                'VoiceId': voice_id,
                'Bitrate': '192k',
                'Speed': speed,
                'Pitch': pitch,
                'Codec': 'libmp3lame'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'API error: {response.text}'}), response.status_code
        
        return Response(
            response.content,
            mimetype='audio/mpeg',
            headers={
                'Content-Type': 'audio/mpeg',
                'Content-Disposition': 'inline; filename="speech.mp3"'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream', methods=['POST'])
def stream():
    """Streaming synthesis endpoint"""
    try:
        data = request.json
        text = data.get('text', '')
        voice_id = data.get('voice_id', 'af_sky')
        speed = data.get('speed', '0')
        pitch = data.get('pitch', '1')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if len(text) > 1000:
            return jsonify({'error': 'Text too long (max 1000 chars)'}), 400
        
        def generate():
            # Make streaming request to Unreal Speech
            response = requests.post(
                'https://api.v8.unrealspeech.com/stream',
                headers={
                    'Authorization': f'Bearer {UNREALSPEECH_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'Text': text,
                    'VoiceId': voice_id,
                    'Bitrate': '192k',
                    'Speed': speed,
                    'Pitch': pitch,
                    'Codec': 'libmp3lame'
                },
                stream=True  # Enable streaming
            )
            
            if response.status_code != 200:
                yield b''  # Empty response on error
                return
            
            # Stream chunks as they arrive
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        
        return Response(
            generate(),
            mimetype='audio/mpeg',
            headers={
                'Content-Type': 'audio/mpeg',
                'Cache-Control': 'no-cache',
                'Transfer-Encoding': 'chunked',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Unreal Speech Demo Server...")
    print(f"API Key: {'Set' if UNREALSPEECH_API_KEY != 'YOUR_API_KEY_HERE' else 'Not Set'}")
    
    if UNREALSPEECH_API_KEY == 'YOUR_API_KEY_HERE':
        print("\n⚠️  Please set your API key:")
        print("export UNREALSPEECH_API_KEY='your_actual_key'")
    
    app.run(debug=True, host='0.0.0.0', port=5003)
