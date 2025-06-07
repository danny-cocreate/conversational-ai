/**
 * TTSVisualizer - Audio visualization for AI speech
 * Creates realistic audio-like visualization based on text analysis
 */

class TTSVisualizer {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.options = {
            style: options.style || 'bars', // 'bars', 'wave', 'dots', 'hybrid'
            colorScheme: options.colorScheme || 'ai', // 'ai', 'rainbow', 'monochrome', 'warm', 'cool'
            barWidth: options.barWidth || 3,
            barGap: options.barGap || 1,
            height: options.height || 0.8, // Relative to canvas height
            speed: options.speed || 1.0,
            ...options
        };
        
        this.isActive = false;
        this.animationFrame = null;
        this.lastFrameTime = 0;
        this.phase = 0;
        
        // Initialize canvas size
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        // Get dimensions from the parent div using getBoundingClientRect
        const parent = this.canvas.parentElement;
        if (!parent) {
            console.error('TTSVisualizer: Parent element not found for canvas.');
            return;
        }
        
        const rect = parent.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        console.log(`TTSVisualizer: Parent getBoundingClientRect dimensions: ${width}x${height}`);
        
        if (width > 0 && height > 0) {
            this.canvas.width = width;
            this.canvas.height = height;
            console.log(`TTSVisualizer: Canvas drawing dimensions set to ${this.canvas.width}x${this.canvas.height}`);
            
            // ** DEBUG DRAWING **
            // Remove or comment out debug drawing after confirming dimensions are correct
            // this.ctx.fillStyle = 'rgba(0, 255, 0, 0.5)'; // Semi-transparent green
            // this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);\n            // console.log(\'TTSVisualizer: Filled canvas with green rectangle.\');\n            // ** END DEBUG DRAWING **\n            \n        } else {\n            console.warn(`TTSVisualizer: Parent has zero dimensions (${width}x${height}) based on getBoundingClientRect, cannot resize canvas.`);
        }
    }
    
    start(text) {
        if (this.isActive) return;
        
        console.log('TTSVisualizer: Starting with text:', text);
        
        // Analyze text for visualization patterns
        this.textAnalysis = this.analyzeText(text);
        this.isActive = true;
        this.lastFrameTime = performance.now();
        this.animate();
    }
    
    stop() {
        this.isActive = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    analyzeText(text) {
        // Simple text analysis for visualization patterns
        const words = text.split(/\s+/);
        const patterns = [];
        
        words.forEach(word => {
            // Generate pattern based on word length and complexity
            const length = word.length;
            const hasPunctuation = /[.,!?]/.test(word);
            const isQuestion = word.includes('?');
            const isExclamation = word.includes('!');
            
            patterns.push({
                amplitude: Math.min(1, length / 10), // Normalize amplitude
                frequency: 1 + (length / 5), // Longer words = higher frequency
                emphasis: isExclamation ? 1.5 : isQuestion ? 1.2 : 1,
                pause: hasPunctuation ? 0.5 : 0
            });
        });
        
        return patterns;
    }
    
    animate() {
        if (!this.isActive) return;
        
        // console.log('TTSVisualizer: Animating...'); // Log less frequently for performance
        
        const now = performance.now();
        const deltaTime = (now - this.lastFrameTime) / 1000;
        this.lastFrameTime = now;
        
        this.phase += deltaTime * this.options.speed;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw visualization based on style
        switch (this.options.style) {
            case 'bars':
                // console.log('TTSVisualizer: Drawing bars...'); // Log less frequently for performance
                this.drawBars();
                break;
            case 'wave':
                // console.log('TTSVisualizer: Drawing wave...'); // Log less frequently for performance
                this.drawWave();
                break;
            case 'dots':
                // console.log('TTSVisualizer: Drawing dots...'); // Log less frequently for performance
                this.drawDots();
                break;
            case 'hybrid':
                // console.log('TTSVisualizer: Drawing hybrid...'); // Log less frequently for performance
                this.drawHybrid();
                break;
        }
        
        this.animationFrame = requestAnimationFrame(() => this.animate());
    }
    
    drawBars() {
        const { width, height } = this.canvas;
        const barCount = Math.floor(width / (this.options.barWidth + this.options.barGap));
        const centerY = height / 2;
        
        for (let i = 0; i < barCount; i++) {
            const x = i * (this.options.barWidth + this.options.barGap);
            const patternIndex = Math.floor(i / barCount * this.textAnalysis.length);
            const pattern = this.textAnalysis[patternIndex] || this.textAnalysis[0];
            
            const amplitude = pattern.amplitude * Math.sin(this.phase * pattern.frequency);
            const barHeight = Math.abs(amplitude) * height * this.options.height * pattern.emphasis;
            
            this.ctx.fillStyle = this.getColor(amplitude);
            this.ctx.fillRect(x, centerY - barHeight/2, this.options.barWidth, barHeight);
        }
    }
    
    drawWave() {
        const { width, height } = this.canvas;
        const centerY = height / 2;
        
        this.ctx.beginPath();
        this.ctx.moveTo(0, centerY);
        
        for (let x = 0; x < width; x += 2) {
            const patternIndex = Math.floor(x / width * this.textAnalysis.length);
            const pattern = this.textAnalysis[patternIndex] || this.textAnalysis[0];
            
            const amplitude = pattern.amplitude * Math.sin(this.phase * pattern.frequency + x * 0.01);
            const y = centerY + amplitude * height * this.options.height * pattern.emphasis;
            
            this.ctx.lineTo(x, y);
        }
        
        this.ctx.strokeStyle = this.getColor(1);
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }
    
    drawDots() {
        const { width, height } = this.canvas;
        const dotCount = Math.floor(width / 10);
        const centerY = height / 2;
        
        for (let i = 0; i < dotCount; i++) {
            const x = i * 10;
            const patternIndex = Math.floor(i / dotCount * this.textAnalysis.length);
            const pattern = this.textAnalysis[patternIndex] || this.textAnalysis[0];
            
            const amplitude = pattern.amplitude * Math.sin(this.phase * pattern.frequency);
            const y = centerY + amplitude * height * this.options.height * pattern.emphasis;
            
            this.ctx.beginPath();
            this.ctx.arc(x, y, 2, 0, Math.PI * 2);
            this.ctx.fillStyle = this.getColor(amplitude);
            this.ctx.fill();
        }
    }
    
    drawHybrid() {
        this.drawWave();
        this.drawDots();
    }
    
    getColor(amplitude) {
        const absAmplitude = Math.abs(amplitude);
        
        switch (this.options.colorScheme) {
            case 'ai':
                return `rgba(33, 150, 243, ${0.3 + absAmplitude * 0.7})`; // Blue theme
            case 'rainbow':
                const hue = (this.phase * 50 + absAmplitude * 180) % 360;
                return `hsla(${hue}, 70%, 50%, ${0.3 + absAmplitude * 0.7})`;
            case 'monochrome':
                return `rgba(0, 0, 0, ${0.3 + absAmplitude * 0.7})`;
            case 'warm':
                return `rgba(255, ${Math.floor(165 * (1 - absAmplitude))}, 0, ${0.3 + absAmplitude * 0.7})`;
            case 'cool':
                return `rgba(0, ${Math.floor(191 * absAmplitude)}, 255, ${0.3 + absAmplitude * 0.7})`;
            default:
                return `rgba(33, 150, 243, ${0.3 + absAmplitude * 0.7})`;
        }
    }
    
    setStyle(style) {
        this.options.style = style;
    }
    
    setColorScheme(scheme) {
        this.options.colorScheme = scheme;
    }
    
    setSpeed(speed) {
        this.options.speed = speed;
    }
} 