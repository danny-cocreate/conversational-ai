// Audio Debugging and Fixing Script
console.log('🔧 Loading audio debugging fixes...');

// Audio troubleshooting functions
window.AudioDebugger = {
    // Test basic audio playback capability
    async testBasicAudio() {
        console.log('🧪 Testing basic audio playback...');
        
        try {
            // Create a simple test audio
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Play a simple beep
            oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            
            console.log('✅ Basic audio test completed - you should hear a beep');
            return true;
        } catch (error) {
            console.error('❌ Basic audio test failed:', error);
            return false;
        }
    },
    
    // Check audio element state
    checkAudioElement() {
        const audioPlayer = document.getElementById('audioPlayer');
        if (!audioPlayer) {
            console.error('❌ Audio player element not found');
            return false;
        }
        
        console.log('🔍 Audio element state:', {
            paused: audioPlayer.paused,
            currentTime: audioPlayer.currentTime,
            duration: audioPlayer.duration,
            volume: audioPlayer.volume,
            muted: audioPlayer.muted,
            readyState: audioPlayer.readyState,
            networkState: audioPlayer.networkState,
            src: audioPlayer.src.substring(0, 50) + '...'
        });
        
        return true;
    },
    
    // Force audio playback with user interaction
    async forceAudioTest() {
        console.log('🎵 Testing forced audio playback...');
        
        const audioPlayer = document.getElementById('audioPlayer');
        if (!audioPlayer) {
            console.error('❌ Audio player not found');
            return false;
        }
        
        try {
            // Try to play the current audio source
            if (audioPlayer.src) {
                console.log('🎵 Attempting to play current audio source...');
                await audioPlayer.play();
                console.log('✅ Audio is playing!');
                return true;
            } else {
                console.log('⚠️ No audio source set');
                return false;
            }
        } catch (error) {
            console.error('❌ Forced audio playback failed:', error);
            return false;
        }
    },
    
    // Show audio player for debugging
    showAudioPlayer() {
        const audioPlayer = document.getElementById('audioPlayer');
        if (audioPlayer) {
            audioPlayer.style.display = 'block';
            audioPlayer.controls = true;
            console.log('👁️ Audio player is now visible for debugging');
        }
    },
    
    // Hide audio player
    hideAudioPlayer() {
        const audioPlayer = document.getElementById('audioPlayer');
        if (audioPlayer) {
            audioPlayer.style.display = 'none';
            console.log('🙈 Audio player hidden');
        }
    },
    
    // Get detailed audio diagnosis
    async runFullDiagnosis() {
        console.log('🩺 Running full audio diagnosis...');
        
        const results = {
            basicAudio: await this.testBasicAudio(),
            audioElement: this.checkAudioElement(),
            userInteraction: false
        };
        
        // Test user interaction requirement
        try {
            const audioPlayer = document.getElementById('audioPlayer');
            if (audioPlayer && audioPlayer.src) {
                await audioPlayer.play();
                results.userInteraction = true;
                audioPlayer.pause();
            }
        } catch (error) {
            console.log('⚠️ User interaction required for audio playback');
            results.userInteraction = false;
        }
        
        console.log('📊 Audio diagnosis results:', results);
        return results;
    }
};

// Enhanced audio event logging
function setupAudioEventLogging() {
    const audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) {
        console.warn('⚠️ Audio player not found - skipping event logging setup');
        return;
    }
    
    // Log all audio events
    const events = [
        'loadstart', 'progress', 'loadeddata', 'loadedmetadata', 
        'canplay', 'canplaythrough', 'play', 'playing', 'pause', 
        'ended', 'error', 'stalled', 'waiting', 'seeking', 'seeked'
    ];
    
    events.forEach(eventType => {
        audioPlayer.addEventListener(eventType, (event) => {
            console.log(`🎵 Audio event: ${eventType}`, {
                currentTime: audioPlayer.currentTime,
                duration: audioPlayer.duration,
                paused: audioPlayer.paused,
                volume: audioPlayer.volume,
                readyState: audioPlayer.readyState
            });
        });
    });
    
    console.log('✅ Audio event logging setup complete');
}

// Enhanced MediaSource debugging
function patchMediaSourceForDebugging() {
    const originalCreateMediaSource = window.MediaSource;
    
    if (!originalCreateMediaSource) {
        console.warn('⚠️ MediaSource not supported in this browser');
        return;
    }
    
    console.log('🔧 Patching MediaSource for debugging...');
    
    // Store reference to original
    window.OriginalMediaSource = originalCreateMediaSource;
    
    // Log MediaSource events
    const originalAddEventListener = originalCreateMediaSource.prototype.addEventListener;
    originalCreateMediaSource.prototype.addEventListener = function(type, listener, options) {
        console.log(`📡 MediaSource addEventListener: ${type}`);
        return originalAddEventListener.call(this, type, (...args) => {
            console.log(`📡 MediaSource event fired: ${type}`, args);
            return listener.apply(this, args);
        }, options);
    };
    
    console.log('✅ MediaSource debugging patches applied');
}

// Simple audio playback fallback
window.simpleAudioPlayback = async function(audioBlob) {
    console.log('🎵 Using simple audio playback fallback...');
    
    const audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) {
        console.error('❌ Audio player element not found');
        return false;
    }
    
    try {
        // Stop any current playback
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        
        // Set new source
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayer.src = audioUrl;
        
        // Show audio player for debugging
        audioPlayer.style.display = 'block';
        audioPlayer.controls = true;
        
        // Try to play
        await audioPlayer.play();
        
        console.log('✅ Simple audio playback started successfully');
        
        // Clean up when finished
        audioPlayer.addEventListener('ended', () => {
            URL.revokeObjectURL(audioUrl);
            audioPlayer.style.display = 'none';
            console.log('🔇 Simple audio playback finished');
        }, { once: true });
        
        return true;
    } catch (error) {
        console.error('❌ Simple audio playback failed:', error);
        return false;
    }
};

// Quick audio fix for current issue
window.quickAudioFix = function() {
    console.log('⚡ Applying quick audio fix...');
    
    const audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) {
        console.error('❌ Audio player not found');
        return;
    }
    
    // Make audio player visible and accessible
    audioPlayer.style.display = 'block';
    audioPlayer.style.position = 'fixed';
    audioPlayer.style.bottom = '100px';
    audioPlayer.style.left = '20px';
    audioPlayer.style.zIndex = '10000';
    audioPlayer.controls = true;
    audioPlayer.volume = 1.0;
    audioPlayer.muted = false;
    
    console.log('✅ Audio player is now visible and ready');
    console.log('🎯 Try triggering TTS again - you should see and hear the audio player');
};

// Auto-fix audio on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Setting up audio debugging on page load...');
    
    // Small delay to let everything load
    setTimeout(() => {
        setupAudioEventLogging();
        patchMediaSourceForDebugging();
        
        // Run diagnosis after user interaction
        document.addEventListener('click', async function() {
            console.log('👆 User clicked - running audio diagnosis...');
            await AudioDebugger.runFullDiagnosis();
        }, { once: true });
        
        console.log('✅ Audio debugging setup complete');
        console.log('💡 To debug audio issues, run: AudioDebugger.runFullDiagnosis()');
        console.log('💡 To see audio player, run: quickAudioFix()');
    }, 1000);
});

console.log('✅ Audio debugging script loaded');
