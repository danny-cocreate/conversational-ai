// Audio Playback Fix - Run this in browser console
console.log('🔧 Applying audio playback fix...');

// 1. Show the audio player for debugging
function showAudioPlayerForDebugging() {
    const audioPlayer = document.getElementById('audioPlayer');
    if (audioPlayer) {
        audioPlayer.style.display = 'block';
        audioPlayer.style.position = 'fixed';
        audioPlayer.style.bottom = '100px';
        audioPlayer.style.left = '20px';
        audioPlayer.style.zIndex = '10000';
        audioPlayer.controls = true;
        audioPlayer.volume = 1.0;
        audioPlayer.muted = false;
        console.log('✅ Audio player is now visible');
        return audioPlayer;
    }
    return null;
}

// 2. Test basic audio playback
async function testBasicAudioPlayback() {
    try {
        const audioPlayer = document.getElementById('audioPlayer');
        if (!audioPlayer) {
            console.error('❌ Audio player not found');
            return false;
        }
        
        console.log('🎵 Testing basic audio playback...');
        
        // Try to play current source if available
        if (audioPlayer.src && audioPlayer.src !== window.location.href) {
            try {
                await audioPlayer.play();
                console.log('✅ Audio is playing successfully!');
                return true;
            } catch (playError) {
                console.log('⚠️ Play failed, trying to reload source...');
                audioPlayer.load();
                await audioPlayer.play();
                console.log('✅ Audio playing after reload!');
                return true;
            }
        } else {
            console.log('⚠️ No audio source available to test');
            return false;
        }
    } catch (error) {
        console.error('❌ Audio test failed:', error);
        return false;
    }
}

// 3. Enhanced MediaSource playback fix
function patchMediaSourcePlayback() {
    console.log('🔧 Patching MediaSource playback...');
    
    // Override the handleVoiceModeResponse to add forced playback
    if (window.ChatModule && window.ChatModule.handleVoiceModeResponse) {
        const originalHandleVoiceMode = window.ChatModule.handleVoiceModeResponse;
        
        window.ChatModule.handleVoiceModeResponse = async function(text) {
            console.log('🎵 Enhanced voice mode response with forced playback');
            
            // Call original function
            await originalHandleVoiceMode.call(this, text);
            
            // Add forced playback after a delay
            setTimeout(async () => {
                const audioPlayer = document.getElementById('audioPlayer');
                if (audioPlayer && audioPlayer.src && audioPlayer.paused) {
                    console.log('🎵 Force-starting audio playback...');
                    try {
                        await audioPlayer.play();
                        console.log('✅ Forced audio playback successful!');
                    } catch (error) {
                        console.log('⚠️ Forced playback failed, showing controls:', error);
                        showAudioPlayerForDebugging();
                    }
                }
            }, 1000);
        };
        
        console.log('✅ MediaSource playback patched');
    }
}

// 4. Add event listeners for better audio debugging
function addAudioEventListeners() {
    const audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) return;
    
    console.log('🔧 Adding enhanced audio event listeners...');
    
    audioPlayer.addEventListener('canplay', () => {
        console.log('🎵 Audio can play - attempting automatic playback...');
        audioPlayer.play().catch(error => {
            console.log('⚠️ Automatic playbook failed, manual controls available:', error);
        });
    });
    
    audioPlayer.addEventListener('loadeddata', () => {
        console.log('🎵 Audio data loaded, trying to play...');
        audioPlayer.play().catch(error => {
            console.log('⚠️ Play on loadeddata failed:', error);
        });
    });
    
    audioPlayer.addEventListener('progress', () => {
        console.log(`🎵 Audio loading progress: ${audioPlayer.buffered.length} ranges buffered`);
    });
    
    audioPlayer.addEventListener('error', (event) => {
        console.error('❌ Audio element error:', event);
        console.error('Audio error details:', {
            error: audioPlayer.error,
            networkState: audioPlayer.networkState,
            readyState: audioPlayer.readyState
        });
    });
    
    console.log('✅ Enhanced audio event listeners added');
}

// 5. Simple fallback TTS function
window.simpleTTSPlayback = async function(text = "This is a test of simple TTS playback") {
    console.log('🎵 Using simple TTS playback...');
    
    try {
        const response = await fetch('/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice_id: 'Sky',
                speed: '1.0'
            })
        });
        
        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            const audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.src = audioUrl;
            audioPlayer.style.display = 'block';
            audioPlayer.controls = true;
            
            await audioPlayer.play();
            console.log('✅ Simple TTS playback successful!');
            
            audioPlayer.addEventListener('ended', () => {
                URL.revokeObjectURL(audioUrl);
                console.log('🔇 Simple TTS playback finished');
            }, { once: true });
            
        } else {
            throw new Error(`TTS failed: ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Simple TTS failed:', error);
    }
};

// Apply all fixes
async function applyAllFixes() {
    console.log('🔧 Applying all audio fixes...');
    
    // Show audio player
    showAudioPlayerForDebugging();
    
    // Add event listeners
    addAudioEventListeners();
    
    // Patch MediaSource
    patchMediaSourcePlayback();
    
    // Test current audio
    await testBasicAudioPlayback();
    
    console.log('✅ All audio fixes applied!');
    console.log('💡 To test TTS: run simpleTTSPlayback()');
    console.log('💡 To test current audio: testBasicAudioPlayback()');
}

// Auto-apply fixes if this script is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyAllFixes);
} else {
    applyAllFixes();
}

// Make functions globally available
window.showAudioPlayerForDebugging = showAudioPlayerForDebugging;
window.testBasicAudioPlayback = testBasicAudioPlayback;
window.applyAllFixes = applyAllFixes;

console.log('✅ Audio fix script loaded - audio player should now be visible');
