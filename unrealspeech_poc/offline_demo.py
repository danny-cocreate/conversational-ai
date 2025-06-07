"""
Unreal Speech Offline Demo
Shows the expected user experience without requiring an API key
"""

from flask import Flask, render_template_string, jsonify, request
import time
import random
import json

app = Flask(__name__)

DEMO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Unreal Speech Demo (Offline Mode)</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f7fa;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.08);
        }
        h1 {
            color: #1a202c;
            text-align: center;
            margin-bottom: 10px;
        }
        .badge {
            background: #ff6b6b;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            text-align: center;
            display: inline-block;
            margin: 0 auto 30px;
            display: block;
            width: fit-content;
        }
        .demo-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }
        .demo-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }
        textarea, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        textarea:focus, select:focus {
            outline: none;
            border-color: #4299e1;
        }
        .voice-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 10px;
        }
        .voice-card {
            background: white;
            padding: 10px;
            border-radius: 6px;
            border: 2px solid transparent;
            cursor: pointer;
            transition: all 0.3s;
        }
        .voice-card:hover {
            border-color: #4299e1;
            transform: translateY(-2px);
        }
        .voice-card.selected {
            border-color: #4299e1;
            background: #ebf8ff;
        }
        button {
            background: #4299e1;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
        }
        button:hover {
            background: #3182ce;
            transform: translateY(-1px);
        }
        button:active {
            transform: translateY(0);
        }
        .metrics {
            background: #1a202c;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #2d3748;
        }
        .metric-row:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .metric-label {
            color: #a0aec0;
        }
        .metric-value {
            color: #48bb78;
            font-weight: bold;
        }
        .streaming-indicator {
            display: none;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
            padding: 15px;
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            border-radius: 6px;
            color: #276749;
        }
        .streaming-indicator.active {
            display: flex;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #48bb78;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .comparison-table th,
        .comparison-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        .comparison-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .comparison-table tr:last-child td {
            border-bottom: none;
        }
        .word-highlight {
            background: #fef3c7;
            padding: 2px 4px;
            border-radius: 3px;
            transition: background 0.3s;
        }
        .word-highlight.active {
            background: #fbbf24;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Unreal Speech Demo</h1>
        <div class="badge">OFFLINE MODE - No API Key Required</div>
        
        <div class="demo-grid">
            <div>
                <div class="demo-section">
                    <h3>Text Input</h3>
                    <div class="form-group">
                        <textarea id="text" rows="4" placeholder="Enter text to synthesize...">Hello! This is a demonstration of Unreal Speech's text-to-speech capabilities with ultra-low latency streaming.</textarea>
                    </div>
                    
                    <h3>Voice Selection</h3>
                    <div class="voice-grid">
                        <div class="voice-card selected" data-voice="af_sky">
                            <strong>Sky</strong><br>
                            <small>Young Female</small>
                        </div>
                        <div class="voice-card" data-voice="af_bella">
                            <strong>Bella</strong><br>
                            <small>Warm Female</small>
                        </div>
                        <div class="voice-card" data-voice="am_michael">
                            <strong>Michael</strong><br>
                            <small>Deep Male</small>
                        </div>
                        <div class="voice-card" data-voice="bm_george">
                            <strong>George</strong><br>
                            <small>British Male</small>
                        </div>
                    </div>
                    
                    <button onclick="simulateStreaming()" style="margin-top: 20px;">
                        🚀 Simulate Streaming
                    </button>
                </div>
                
                <div class="streaming-indicator" id="streamingIndicator">
                    <div class="pulse-dot"></div>
                    <span>Streaming audio chunks...</span>
                </div>
                
                <div class="demo-section" style="margin-top: 20px;">
                    <h3>Word-Level Highlighting Demo</h3>
                    <p id="wordHighlightDemo" style="line-height: 1.8;">
                        <!-- Words will be added here -->
                    </p>
                </div>
            </div>
            
            <div>
                <div class="demo-section">
                    <h3>Performance Metrics</h3>
                    <div class="metrics" id="metrics">
                        <div class="metric-row">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value">Ready</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Time to First Byte:</span>
                            <span class="metric-value">-</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Total Time:</span>
                            <span class="metric-value">-</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Chunks Received:</span>
                            <span class="metric-value">-</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Audio Size:</span>
                            <span class="metric-value">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="demo-section" style="margin-top: 20px;">
                    <h3>Unreal Speech vs Hume AI</h3>
                    <table class="comparison-table">
                        <tr>
                            <th>Feature</th>
                            <th>Unreal Speech</th>
                            <th>Hume AI</th>
                        </tr>
                        <tr>
                            <td>Latency</td>
                            <td style="color: #48bb78;">~300ms</td>
                            <td>~500ms+</td>
                        </tr>
                        <tr>
                            <td>Streaming</td>
                            <td style="color: #48bb78;">✅ Native</td>
                            <td>⚠️ Limited</td>
                        </tr>
                        <tr>
                            <td>Word Timestamps</td>
                            <td style="color: #48bb78;">✅ Yes</td>
                            <td>❌ No</td>
                        </tr>
                        <tr>
                            <td>Voices</td>
                            <td style="color: #48bb78;">48 voices</td>
                            <td>Limited</td>
                        </tr>
                        <tr>
                            <td>Cost (per 1M chars)</td>
                            <td style="color: #48bb78;">$8</td>
                            <td>~$240</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Voice selection
        document.querySelectorAll('.voice-card').forEach(card => {
            card.addEventListener('click', () => {
                document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
            });
        });
        
        async function simulateStreaming() {
            const text = document.getElementById('text').value;
            const voice = document.querySelector('.voice-card.selected').dataset.voice;
            const metrics = document.getElementById('metrics');
            const indicator = document.getElementById('streamingIndicator');
            
            // Reset metrics
            updateMetric('Status:', 'Connecting...');
            updateMetric('Time to First Byte:', '-');
            updateMetric('Total Time:', '-');
            updateMetric('Chunks Received:', '0');
            updateMetric('Audio Size:', '0 KB');
            
            // Show streaming indicator
            indicator.classList.add('active');
            
            try {
                const response = await fetch('/simulate-stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, voice })
                });
                
                const reader = response.body.getReader();
                const startTime = performance.now();
                let firstByteTime = null;
                let totalBytes = 0;
                let chunkCount = 0;
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    if (firstByteTime === null) {
                        firstByteTime = performance.now() - startTime;
                        updateMetric('Status:', 'Streaming...');
                        updateMetric('Time to First Byte:', `${firstByteTime.toFixed(0)}ms`);
                    }
                    
                    chunkCount++;
                    totalBytes += value.length;
                    
                    updateMetric('Chunks Received:', chunkCount.toString());
                    updateMetric('Audio Size:', `${(totalBytes / 1024).toFixed(1)} KB`);
                    
                    // Simulate chunk processing delay
                    await new Promise(resolve => setTimeout(resolve, 50));
                }
                
                const totalTime = performance.now() - startTime;
                updateMetric('Status:', 'Complete ✓');
                updateMetric('Total Time:', `${(totalTime / 1000).toFixed(2)}s`);
                
                // Simulate word highlighting
                await simulateWordHighlighting(text);
                
            } catch (error) {
                updateMetric('Status:', 'Error: ' + error.message);
            } finally {
                indicator.classList.remove('active');
            }
        }
        
        function updateMetric(label, value) {
            const metrics = document.getElementById('metrics');
            const rows = metrics.querySelectorAll('.metric-row');
            rows.forEach(row => {
                if (row.querySelector('.metric-label').textContent === label) {
                    row.querySelector('.metric-value').textContent = value;
                }
            });
        }
        
        async function simulateWordHighlighting(text) {
            const container = document.getElementById('wordHighlightDemo');
            const words = text.split(' ');
            
            // Clear and add words
            container.innerHTML = '';
            words.forEach(word => {
                const span = document.createElement('span');
                span.className = 'word-highlight';
                span.textContent = word + ' ';
                container.appendChild(span);
            });
            
            // Highlight words sequentially
            const spans = container.querySelectorAll('.word-highlight');
            for (let i = 0; i < spans.length; i++) {
                spans[i].classList.add('active');
                await new Promise(resolve => setTimeout(resolve, 200));
                if (i > 0) spans[i-1].classList.remove('active');
            }
            spans[spans.length - 1].classList.remove('active');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DEMO_HTML)

@app.route('/simulate-stream', methods=['POST'])
def simulate_stream():
    """Simulate streaming response"""
    data = request.json
    text = data.get('text', '')
    
    def generate():
        # Simulate initial latency
        time.sleep(0.3)  # 300ms latency
        
        # Calculate chunks based on text length
        total_size = len(text) * 150  # Rough estimate
        chunk_size = 1024
        num_chunks = max(5, total_size // chunk_size)
        
        for i in range(num_chunks):
            # Simulate chunk data
            chunk_data = b'x' * min(chunk_size, total_size - (i * chunk_size))
            yield chunk_data
            
            # Simulate network delay between chunks
            time.sleep(random.uniform(0.01, 0.05))
    
    return app.response_class(generate(), mimetype='application/octet-stream')

if __name__ == '__main__':
    print("🚀 Starting Unreal Speech Offline Demo")
    print("This demo simulates the expected behavior without requiring an API key")
    print("Open http://localhost:5004 to see the demo")
    app.run(debug=True, host='0.0.0.0', port=5004)
