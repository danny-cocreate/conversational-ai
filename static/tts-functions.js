// TTS FUNCTIONS - Updated for database-only lesson system

// Voice descriptions mapping (moved from HTML)
const voiceDescriptions = {
    'Sky': 'A natural-sounding female voice with good expressiveness. Perfect for conversational interactions and storytelling.',
    'Bella': 'American female with reserved personality',
    'Sarah': 'American female, probably an educator; confident',
    'Nicole': 'American female with whisper-like voice, looks casual',
    'Adam': 'American male with confident personality',
    'Michael': 'American male with confident personality',
    'Emma': 'British female',
    'Isabella': 'British female with calm personality',
    'George': 'British male, mature voice',
    'Lewis': 'British male with confident personality'
};

// Test selected voice (moved from HTML)
async function testSelectedVoice() {
    const voiceSelect = document.getElementById('voice_select');
    if (!voiceSelect) {
        console.warn('⚠️ Voice select element not found - cannot test TTS');
        alert('TTS controls are not available on this page');
        return;
    }
    
    const voiceId = voiceSelect.value;
    if (!voiceId) {
        alert('Please select a voice first');
        return;
    }
    
    try {
        const response = await fetch('/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: "Hello! This is a test of the selected voice. How does it sound?",
                voice_id: voiceId,
                speed: document.getElementById('speed')?.value || 1.0,
                temperature: document.getElementById('temperature')?.value || 0.7
            })
        });
        
        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
            
            audio.onerror = (error) => {
                console.error('Audio playback error:', error);
                URL.revokeObjectURL(audioUrl);
                alert('Voice test failed');
            };
            
            await audio.play();
        } else {
            throw new Error('Voice test failed');
        }
    } catch (error) {
        console.error('Voice test error:', error);
        alert('Failed to test voice: ' + error.message);
    }
}

// Script to open the modal (moved from HTML)
function openProfileSettingsModal() {
    console.log('Opening profile settings modal');
    const modalElement = document.getElementById('profileSettingsModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        modal.show();
    }
}

async function loadTTSProviders() {
    try {
        // Check if TTS UI elements exist on this page
        const providerSelect = document.getElementById('provider_select');
        if (!providerSelect) {
            console.log('🎙️ TTS UI not present on this page - skipping TTS provider initialization');
            return;
        }
        
        const response = await fetch('/tts/providers');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}, statusText: ${response.statusText}, url: ${response.url}`);
        }
        const data = await response.json();
        console.log('Received data from /providers:', data);
        
        providerSelect.innerHTML = '';
        
        // Add providers to dropdown
        Object.keys(data.providers).forEach(providerName => {
            const option = document.createElement('option');
            option.value = providerName;
            option.textContent = data.providers[providerName].name;
            if (providerName === data.current_provider) {
                option.selected = true;
            }
            providerSelect.appendChild(option);
        });
        
        // Update provider status
        updateProviderStatus(data.status);
        
        // Update UI based on provider capabilities
        updateProviderCapabilities(data.current_provider);
        
        // Load voices for current provider
        await loadVoices();
        
        console.log('✅ TTS providers loaded successfully');
    } catch (error) {
        console.error('Error loading TTS providers:', error);
        const providerSelectElement = document.getElementById('provider_select');
        if (providerSelectElement) {
            providerSelectElement.innerHTML = '<option>Error loading providers</option>';
        }
    }
}

async function loadVoices() {
    try {
        // Check if voice select element exists
        const voiceSelect = document.getElementById('voice_select');
        if (!voiceSelect) {
            console.log('🎙️ Voice UI not present on this page - skipping voice loading');
            return;
        }
        
        const response = await fetch('/voices');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        voiceSelect.innerHTML = '<option value="" disabled selected>Choose a voice...</option>';
        
        if (data.voices_page && data.voices_page.length > 0) {
            console.log('Voices received from API:', data.voices_page);
            data.voices_page.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.id;
                
                // Extract base name (e.g., 'Sky' from 'Sky (Female)') for description lookup
                const baseVoiceName = voice.name.split(' ')[0].split('(')[0];
                const voiceDescription = voiceDescriptions[baseVoiceName];
                
                console.log(`Looking up description for voice name: ${voice.name}. Found: ${voiceDescription}`);
                
                const displayDescription = voiceDescription || 'No description available.';
                
                // Display voice name and description
                option.textContent = `${voice.name} - ${displayDescription}`;

                voiceSelect.appendChild(option);
            });
            
            // Auto-select first voice if none selected
            if (!voiceSelect.value) {
                voiceSelect.selectedIndex = 1; // Skip the "Choose a voice..." option
            }
            
            console.log(`✅ Loaded ${data.voices_page.length} voices`);
        } else {
            voiceSelect.innerHTML = '<option value="" disabled>No voices available</option>';
            console.warn('⚠️ No voices returned from backend');
        }
    } catch (error) {
        console.error('Error loading voices:', error);
        const voiceSelectElement = document.getElementById('voice_select');
        if (voiceSelectElement) {
            voiceSelectElement.innerHTML = '<option value="" disabled>Error loading voices</option>';
        }
    }
}

function updateProviderCapabilities(currentProvider) {
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    const temperatureNote = document.getElementById('temperatureNote');
    const pitchContainer = document.getElementById('pitchContainer');
    
    // Skip if TTS UI elements don't exist on this page
    if (!temperatureSlider) {
        console.log('🎙️ TTS controls not present - skipping capability update');
        return;
    }
    
    if (currentProvider === 'unrealspeech') {
        // Enable temperature for UnrealSpeech (0.1 to 0.8 range)
        temperatureSlider.disabled = false;
        temperatureSlider.style.opacity = '1';
        temperatureValue.style.opacity = '1';
        temperatureSlider.min = '0.1';
        temperatureSlider.max = '0.8';
        temperatureNote.innerHTML = '✅ Temperature: Lower = stable/deterministic, Higher = expressive/creative (UnrealSpeech: 0.1-0.8)';
        temperatureNote.style.color = '#28a745';
        
        // Show pitch control for UnrealSpeech
        if (pitchContainer) {
            pitchContainer.style.display = 'block';
        }
    } else {
        // Enable temperature for other providers with standard range
        temperatureSlider.disabled = false;
        temperatureSlider.style.opacity = '1';
        temperatureValue.style.opacity = '1';
        temperatureSlider.min = '0.1';
        temperatureSlider.max = '0.8';
        temperatureNote.innerHTML = '✅ Temperature controls speech expressiveness for this provider';
        temperatureNote.style.color = '#28a745';
        
        // Hide pitch control for other providers (they may not support it)
        if (pitchContainer) {
            pitchContainer.style.display = 'none';
        }
    }
}

function updateProviderStatus(status) {
    const statusDiv = document.getElementById('providerStatus');
    
    // Skip if status div doesn't exist on this page
    if (!statusDiv) {
        console.log('🎙️ Provider status UI not present - skipping status update');
        return;
    }
    
    // Ensure status and status.current_provider are defined
    if (!status || typeof status.current_provider === 'undefined') {
        console.error('Error: TTS status or current_provider is undefined.', status);
        statusDiv.innerHTML = '<strong>Error:</strong> TTS status is not available.';
        statusDiv.style.backgroundColor = '#f8d7da';
        statusDiv.style.border = '1px solid #f5c6cb';
        return;
    }

    const currentProvider = status.current_provider;
    let isAvailable = false;
    let apiKeySet = false;

    // Check if available_providers and the specific provider entry exist
    if (status.available_providers && status.available_providers[currentProvider]) {
        console.log(`Provider data for ${currentProvider}:`, status.available_providers[currentProvider]);
        const providerData = status.available_providers[currentProvider];
        
        if (providerData) {
            isAvailable = providerData.available || false;
            apiKeySet = providerData.api_key_set || false;
        } else {
            console.warn(`Warning: Provider data for '${currentProvider}' is null or undefined.`, status);
        }
    } else {
        console.warn(`Warning: Provider '${currentProvider}' not found in available_providers or available_providers is undefined.`, status);
    }
    
    const statusHTML = `
        <strong>Current Provider:</strong> ${currentProvider}<br>
        <strong>Status:</strong> ${isAvailable ? '✅ Available' : '❌ Not Available'}<br>
        <strong>API Key:</strong> ${apiKeySet ? '✅ Set' : '❌ Missing'}
    `;
    
    statusDiv.innerHTML = statusHTML;
    statusDiv.style.backgroundColor = isAvailable ? '#d4edda' : '#f8d7da';
    statusDiv.style.border = `1px solid ${isAvailable ? '#c3e6cb' : '#f5c6cb'}`;
}

async function switchProvider() {
    const providerSelect = document.getElementById('provider_select');
    if (!providerSelect) {
        console.warn('⚠️ Provider select element not found - cannot switch provider');
        alert('Provider controls are not available on this page');
        return;
    }
    
    const selectedProvider = providerSelect.value;
    if (!selectedProvider) {
        alert('Please select a provider');
        return;
    }
    
    try {
        const response = await fetch('/tts/provider', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ provider: selectedProvider })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        alert(`Successfully switched to ${data.provider}`);
        
        // Update UI based on new provider capabilities
        updateProviderCapabilities(data.provider);
        
        // Reload voices for new provider
        await loadVoices();
        
    } catch (error) {
        console.error('Error switching provider:', error);
        alert('Failed to switch provider: ' + error.message);
    }
}

async function testTTS() {
    const voiceSelect = document.getElementById('voice_select');
    if (!voiceSelect) {
        console.warn('⚠️ Voice select element not found - cannot test TTS');
        alert('TTS controls are not available on this page');
        return;
    }
    
    const voiceId = voiceSelect.value;
    if (!voiceId) {
        alert('Please select a voice first');
        return;
    }
    
    try {
        const response = await fetch('/tts/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: 'Hello, this is a test of the text-to-speech system.',
                voice_id: voiceId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        alert(`TTS test successful! Generated ${data.audio_size} bytes of audio with ${data.provider}.`);
        
    } catch (error) {
        console.error('Error testing TTS:', error);
        alert('TTS test failed: ' + error.message);
    }
}

async function testChunking() {
    const voiceSelect = document.getElementById('voice_select');
    if (!voiceSelect) {
        console.warn('⚠️ Voice select element not found - cannot test chunking');
        alert('TTS controls are not available on this page');
        return;
    }
    
    const voiceId = voiceSelect.value;
    if (!voiceId) {
        alert('Please select a voice first');
        return;
    }
    
    const longText = 'This is a very long text that will be used to test the chunking functionality of the text-to-speech system. The system should automatically break this text into smaller chunks that can be processed by the TTS provider without exceeding the maximum character limit.';
    
    try {
        const response = await fetch('/chunk-preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: longText,
                max_chunk_size: 950
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display chunking info
        const chunkingDiv = document.getElementById('chunkingInfo');
        if (chunkingDiv) {
            chunkingDiv.style.display = 'block';
            chunkingDiv.style.backgroundColor = '#e7f3ff';
            chunkingDiv.style.border = '1px solid #b3d9ff';
            chunkingDiv.innerHTML = `
                <strong>Chunking Test Results:</strong><br>
                Original text: ${data.chunking_info.original_length} characters<br>
                Total chunks: ${data.chunking_info.total_chunks}<br>
                Needs chunking: ${data.needs_chunking ? 'Yes' : 'No'}<br>
                <details><summary>Chunk breakdown:</summary>
                ${data.chunking_info.chunks.map(chunk => 
                    `Chunk ${chunk.index + 1}: ${chunk.length} chars ${chunk.is_final ? '(final)' : ''}`
                ).join('<br>')}
                </details>
            `;
        }
        
        console.log('Chunking test completed:', data);
        
    } catch (error) {
        console.error('Error testing chunking:', error);
        alert('Chunking test failed: ' + error.message);
    }
}

async function updateSystemPrompt() {
    const systemPromptElement = document.getElementById('systemPrompt');
    if (!systemPromptElement) {
        console.warn('⚠️ System prompt element not found - cannot update');
        alert('System prompt controls are not available on this page');
        return;
    }
    
    const promptText = systemPromptElement.value.trim();
    if (!promptText) {
        alert('Please enter a system prompt');
        return;
    }
    
    try {
        const response = await fetch('/system-prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: promptText })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        alert('System prompt updated successfully!');
        
        // Save to localStorage
        localStorage.setItem('systemPrompt', promptText);
        
    } catch (error) {
        console.error('Error updating system prompt:', error);
        alert('Failed to update system prompt: ' + error.message);
    }
}

// UPDATED: Removed old document management functions
// The system now uses database lessons as the only knowledge base

async function checkKnowledgeBaseStatus() {
    // Check if we're on a lesson page and show knowledge base status
    if (window.lessonContext && window.lessonContext.lessonId) {
        try {
            const response = await fetch(`/knowledge-base/status?lesson_id=${window.lessonContext.lessonId}`);
            if (response.ok) {
                const data = await response.json();
                console.log('📚 Knowledge base status:', data.status);
                
                // Update UI if there's a knowledge base status element
                const statusElement = document.getElementById('knowledgeBaseStatus');
                if (statusElement) {
                    statusElement.innerHTML = `
                        <strong>Knowledge Base:</strong> Database Lessons<br>
                        <strong>Lesson:</strong> ${data.status.lesson_id}<br>
                        <strong>Slides:</strong> ${data.status.total_slides}
                    `;
                    statusElement.style.backgroundColor = '#d4edda';
                    statusElement.style.border = '1px solid #c3e6cb';
                }
            }
        } catch (error) {
            console.warn('Could not check knowledge base status:', error);
        }
    }
}

async function updateTTSSettings() {
    try {
        // Get all current TTS settings with null checks
        const voiceSelect = document.getElementById('voice_select');
        const speedSlider = document.getElementById('speed');
        const temperatureSlider = document.getElementById('temperature');
        const pitchSlider = document.getElementById('pitch');
        const sensitivitySelect = document.getElementById('sensitivityLevel');
        const providerSelect = document.getElementById('provider_select');
        
        // Check if required elements exist
        if (!voiceSelect || !speedSlider || !temperatureSlider || !sensitivitySelect || !providerSelect) {
            console.warn('⚠️ Some TTS control elements not found - cannot update settings');
            alert('TTS settings controls are not fully available on this page');
            return;
        }
        
        const settings = {
            voice_id: voiceSelect.value || '',
            voice_name: voiceSelect.options[voiceSelect.selectedIndex]?.text || '',
            speed: speedSlider.value || '1.0',
            temperature: temperatureSlider.value || '0.25',
            pitch: pitchSlider ? pitchSlider.value : '1.0',
            sensitivity: sensitivitySelect.value || 'medium',
            provider: providerSelect.value || '',
            timestamp: new Date().toISOString()
        };
        
        // Validate required settings
        if (!settings.voice_id) {
            alert('Please select a voice before updating settings');
            return;
        }
        
        if (!settings.provider) {
            alert('Please select a TTS provider before updating settings');
            return;
        }
        
        // Save to localStorage for persistence
        localStorage.setItem('ttsSettings', JSON.stringify(settings));
        
        console.log('✅ TTS Settings saved:', settings);
        
        // Show success feedback
        const button = event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Settings Updated!';
        button.style.backgroundColor = '#28a745';
        
        // Reset button after 2 seconds
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.backgroundColor = '#007bff';
        }, 2000);
        
    } catch (error) {
        console.error('Error updating TTS settings:', error);
        alert('Failed to update TTS settings: ' + error.message);
    }
}

function loadSavedTTSSettings() {
    try {
        const savedSettings = localStorage.getItem('ttsSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            // Apply saved settings to controls
            const voiceSelect = document.getElementById('voice_select');
            const speedSlider = document.getElementById('speed');
            const temperatureSlider = document.getElementById('temperature');
            const pitchSlider = document.getElementById('pitch');
            const sensitivitySelect = document.getElementById('sensitivityLevel');
            
            if (settings.voice_id && voiceSelect) {
                voiceSelect.value = settings.voice_id;
            }
            
            if (settings.speed && speedSlider) {
                speedSlider.value = settings.speed;
                const speedValue = document.getElementById('speedValue');
                if (speedValue) speedValue.textContent = settings.speed + 'x';
            }
            
            if (settings.temperature && temperatureSlider) {
                temperatureSlider.value = settings.temperature;
                const temperatureValue = document.getElementById('temperatureValue');
                if (temperatureValue) temperatureValue.textContent = settings.temperature;
            }
            
            if (settings.pitch && pitchSlider) {
                pitchSlider.value = settings.pitch;
                const pitchValue = document.getElementById('pitchValue');
                if (pitchValue) pitchValue.textContent = settings.pitch;
            }
            
            if (settings.sensitivity && sensitivitySelect) {
                sensitivitySelect.value = settings.sensitivity;
            }
            
            console.log('✅ TTS settings loaded from localStorage:', settings);
        }
    } catch (error) {
        console.error('Error loading saved TTS settings:', error);
    }
}

function loadSavedSystemPrompt() {
    try {
        const savedPrompt = localStorage.getItem('systemPrompt');
        if (savedPrompt) {
            const systemPromptTextarea = document.getElementById('systemPrompt');
            if (systemPromptTextarea) {
                systemPromptTextarea.value = savedPrompt;
                console.log('✅ System prompt loaded from localStorage');
            }
        }
    } catch (error) {
        console.error('Error loading saved system prompt:', error);
    }
}

// Initialize event listeners for TTS controls
function initializeTTSControls() {
    // Speed slider event listener
    const speedSlider = document.getElementById('speed');
    const speedValue = document.getElementById('speedValue');
    
    if (speedSlider && speedValue) {
        speedSlider.addEventListener('input', function() {
            speedValue.textContent = this.value + 'x';
        });
    }
    
    // Temperature slider event listener
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    
    if (temperatureSlider && temperatureValue) {
        temperatureSlider.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
        });
    }
    
    // Pitch slider event listener
    const pitchSlider = document.getElementById('pitch');
    const pitchValue = document.getElementById('pitchValue');
    
    if (pitchSlider && pitchValue) {
        pitchSlider.addEventListener('input', function() {
            pitchValue.textContent = this.value;
        });
    }
}

// Initialize TTS system
async function initializeTTSSystem() {
    try {
        console.log('🎙️ Initializing TTS system...');
        
        // Check if this page has the full TTS settings UI elements
        const hasFullSettingsUI = document.getElementById('provider_select') !== null;
        const hasVoiceSelectUI = document.getElementById('voice_select') !== null;

        if (hasFullSettingsUI) {
            console.log('🎙️ Full TTS settings UI present - performing full initialization');
            // Load TTS providers and voices
            await loadTTSProviders();
            // Initialize TTS controls
            initializeTTSControls();
            // Load saved TTS settings from localStorage
            setTimeout(() => {
                loadSavedTTSSettings();
                loadSavedSystemPrompt();
            }, 500);

        } else if (hasVoiceSelectUI) {
            console.log('🎙️ Voice select UI present (minimal TTS) - loading voices only');
            await loadVoices();
        } else {
            console.log('🎙️ No primary TTS UI elements found on this page - skipping TTS initialization');
        }

        // Check knowledge base status for lesson pages
        setTimeout(checkKnowledgeBaseStatus, 1000);
        
        console.log('✅ TTS system initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize TTS system:', error);
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTTSSystem);
} else {
    initializeTTSSystem();
}

async function speakText(text, voiceId = null) {
    try {
        // Show visualizer and hide mic button
        if (typeof showVisualizer === 'function') {
            showVisualizer(text);
        }

        const response = await fetch('/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice_id: voiceId || document.getElementById('voice_select')?.value,
                speed: document.getElementById('speed')?.value || 1.0,
                temperature: document.getElementById('temperature')?.value || 0.7
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
            // Hide visualizer and show mic button when audio ends
            if (typeof hideVisualizer === 'function') {
                hideVisualizer();
            }
        };

        audio.onerror = (error) => {
            console.error('Audio playback error:', error);
            URL.revokeObjectURL(audioUrl);
            // Hide visualizer and show mic button on error
            if (typeof hideVisualizer === 'function') {
                hideVisualizer();
            }
            throw error;
        };

        await audio.play();
    } catch (error) {
        console.error('Error in speakText:', error);
        // Hide visualizer and show mic button on error
        if (typeof hideVisualizer === 'function') {
            hideVisualizer();
        }
        throw error;
    }
}
