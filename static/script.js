// ============================================================================
// CoCreate AI Coach - Main Script
// ============================================================================
// This script contains all the JavaScript functionality for the voice chat bot
// application organized into modular components.

'use strict';

// ============================================================================
// Global State Management
// ============================================================================
const AppState = {
    // UI State
    chatExpanded: false,
    settingsExpanded: false,
    
    // Audio State
    isAISpeaking: false,
    audioInitialized: false,
    currentAudioElement: null,
    
    // Speech Recognition State
    isRecording: false,
    isTextMode: false,
    
    // Visualization State
    visualizer: null,
    
    // TTS State
    currentProvider: null,
    currentVoice: null,
    
    // Request cancellation support
    currentTTSController: null,
    isInterrupted: false,
    
    // Enhanced State Management
    conversationState: 'ready', // 'ready', 'thinking', 'generating-speech', 'speaking', 'listening'
    currentStatusMessage: null,
    lastUserInput: null,
    responseTimeout: null,
    hasGreeted: false,
    currentTopic: null,
    topicTransitionPending: false,
    slidesPresented: new Set(), // Track which slides have been presented

    // Enhanced Topic Management
    topicState: {
        currentTopic: null,
        topicStartTime: null,
        topicsCovered: new Set(),
        lastTransitionTime: null,
        transitionPending: false,
        userConfirmedUnderstanding: false
    },

    // NEW: Centralized Conversation Memory
    conversationMemory: {
        messages: [], // Array of {role: 'user'|'assistant', content: string, timestamp: number}
        context: {
            lessonId: null,
            currentSlide: null,
            lastInteraction: null,
            currentTopic: null,
            topicStartTime: null,
            slideContentPresented: new Set(),
            topicsCovered: new Set(),
            lastTransitionTime: null,
            userConfirmedUnderstanding: false
        },
        metadata: {
            startTime: null,
            mode: 'text', // 'text' or 'voice'
            totalTurns: 0,
            topicsCovered: [],
            contextWindowSize: 10
        }
    }
};

// ============================================================================
// UI Control Module
// ============================================================================
const UIControls = {
    // Toggle settings sidebar
    toggleSettingsSidebar() {
        const sidebar = document.getElementById('settingsSidebar');
        sidebar.classList.toggle('collapsed');
        AppState.settingsExpanded = !AppState.settingsExpanded;
    },
    
    // Toggle chat window
    toggleChatWindow() {
        const chatContainer = document.getElementById('chatContainer');
        const audioPlayer = document.getElementById('audioPlayer');
        const expandIcon = document.getElementById('chatExpandIcon');
        
        chatContainer.classList.toggle('expanded');
        AppState.chatExpanded = chatContainer.classList.contains('expanded');
        
        // Update accordion icon
        expandIcon.textContent = AppState.chatExpanded ? '▼' : '▲';
        
        // Handle mode switching
        if (AppState.chatExpanded) {
            // Expanded = TEXT MODE
            console.log('📝 Switching to TEXT MODE');
            
            // Stop any ongoing conversation mode (user switched modes)
            if (SpeechModule.conversationMode) {
                console.log('🔇 Pausing voice mode due to mode switch');
                SpeechModule.stopListening();
                // Don't stop conversation mode, just pause listening
            }
            
            // Hide audio player when in text mode
            if (audioPlayer.style.display !== 'none') {
                audioPlayer.style.display = 'none';
            }
            
            // Focus the text input for immediate typing
            const textInput = document.getElementById('text');
            setTimeout(() => {
                textInput.focus();
            }, 100);
            
        } else {
            // Collapsed = VOICE MODE
            console.log('🎤 Switching to VOICE MODE');
            
            // Clear text input when switching back to voice mode
            const textInput = document.getElementById('text');
            textInput.value = '';
            textInput.blur();
            
            // Check if we're in lesson mode
            const isLessonMode = window.lessonContext && window.lessonContext.isLessonMode;
            
            // Auto-start conversation mode in voice mode
            if (!SpeechModule.conversationMode) {
                if (isLessonMode) {
                    console.log('🎓 In lesson mode - starting voice without generic greeting');
                    // For lessons, just start listening without triggering greeting
                    SpeechModule.conversationMode = true;
                    SpeechModule.startListening();
                } else {
                    console.log('🎤 Auto-starting voice conversation mode');
                    SpeechModule.startConversation();
                }
            } else {
                console.log('🎤 Resuming voice mode');
                SpeechModule.startListening();
            }
        }
        
        // Update button state to reflect new mode
        UIControls.updateButtonState();
    },
    
    // Update button states
    updateButtonState() {
        const micButton = document.getElementById('micButton');
        const interruptButton = document.getElementById('interruptButton');
        const chatContainer = document.getElementById('chatContainer');
        const isVoiceMode = !chatContainer.classList.contains('expanded');
        
        if (!micButton) return;
        
        // Update mic button based on current state
        if (AppState.isAISpeaking) {
            // AI is speaking - show visualizer instead of button
            micButton.style.display = 'none';
            const visualizer = document.getElementById('ttsVisualizer');
            if (visualizer) {
                visualizer.style.display = 'block';
            }
            // Show interrupt button
            if (interruptButton) {
                interruptButton.style.display = 'inline-flex';
            }
        } else {
            // Hide visualizer and show mic button when AI is not speaking
            micButton.style.display = 'block';
            const visualizer = document.getElementById('ttsVisualizer');
            if (visualizer) {
                visualizer.style.display = 'none';
            }
            // Hide interrupt button when AI not speaking
            if (interruptButton) {
                interruptButton.style.display = 'none';
            }
            
            if (isVoiceMode) {
                // Voice mode - show appropriate state
                if (AppState.isRecording && SpeechModule.isListening) {
                    // Actually listening for speech
                    micButton.className = 'recording';
                    micButton.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5z"/>
                            <path d="M10 8V3a2 2 0 1 0-4 0v5a2 2 0 1 0 4 0z"/>
                            <path d="M6 6a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
                            <path d="M8 8a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
                            <path d="M10 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
                        </svg>
                        <span>Listening...</span>
                    `;
                } else if (SpeechModule.conversationMode) {
                    // Voice mode but waiting to restart listening or getting ready
                    micButton.className = 'conversation-waiting';
                    micButton.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5z"/>
                            <path d="M10 8V3a2 2 0 1 0-4 0v5a2 2 0 1 0 4 0z"/>
                        </svg>
                        <span>Thinking...</span>
                    `;
                } else {
                    // Voice mode but not in conversation - show start button
                    micButton.className = 'speak-mode';
                    micButton.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5z"/>
                            <path d="M10 8V3a2 2 0 1 0-4 0v5a2 2 0 1 0 4 0z"/>
                        </svg>
                        <span>Start Lesson</span>
                    `;
                }
            } else {
                // Text mode - show disabled state
                micButton.className = 'text-mode-disabled';
                micButton.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M13 8c0 .564-.094 1.107-.266 1.613l-.814-.814A4.02 4.02 0 0 0 12 8V7a.5.5 0 0 1 1 0v1zm-5 4c.818 0 1.578-.245 2.212-.667l.718.719a4.973 4.973 0 0 1-2.43.923V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 1 0v1a4 4 0 0 0 4 4zm3-9v4.879L5.158 2.037A3.001 3.001 0 0 1 11 3z"/>
                        <path d="M9.486 10.607 5 6.12V8a3 3 0 0 0 4.486 2.607zm-7.84-9.253 12 12 .708-.708-12-12-.708.708z"/>
                    </svg>
                    <span>Voice Disabled in Text Mode</span>
                `;
            }
        }
    }
};

// ============================================================================
// Chat Module
// ============================================================================
const ChatModule = {
    // Add message to conversation
    async addMessage(text, isUser, statusType = null) {
        // Add to conversation memory first
        if (isUser) {
            ConversationMemory.addMessage('user', text);
            
            // Check for user confirmation of understanding
            if (AppState.topicState.transitionPending) {
                const isConfirmation = ConversationMemory.isConfirmationOfUnderstanding(text);
                if (isConfirmation) {
                    AppState.topicState.userConfirmedUnderstanding = true;
                    AppState.conversationMemory.context.userConfirmedUnderstanding = true;
                    AppState.topicState.transitionPending = false;
                    console.log('✅ User confirmed understanding of current topic');
                }
            }
        } else {
            ConversationMemory.addMessage('assistant', text);
            
            // Check if this is a new topic or slide content presentation
            const isNewTopic = this._isNewTopicIntroduction(text);
            if (isNewTopic) {
                // Track the current topic
                const topicId = this._generateTopicId(text);
                // Ensure AppState.topicState and topicsCovered exist
                if (AppState.topicState && AppState.topicState.topicsCovered) {
                    AppState.topicState.currentTopic = topicId;
                    AppState.topicState.topicStartTime = Date.now();
                    AppState.conversationMemory.context.currentTopic = topicId;
                    AppState.conversationMemory.context.topicStartTime = Date.now();

                    // Add to topics covered
                    AppState.topicState.topicsCovered.add(topicId);
                    AppState.conversationMemory.context.topicsCovered.add(topicId);
                }
                
                console.log(`📊 New topic started: ${topicId}`);
            }
            
            // Check if this is asking for confirmation
            if (this._isAskingForConfirmation(text)) {
                AppState.topicState.transitionPending = true;
                AppState.conversationMemory.context.lastTransitionTime = Date.now();
                console.log('⏳ Waiting for user confirmation of understanding');
            }
        }

        const messageDiv = document.createElement('div');
        messageDiv.style.marginBottom = '10px';
        messageDiv.style.textAlign = isUser ? 'right' : 'left';
        
        const messageContent = document.createElement('div');
        messageContent.style.display = 'inline-block';
        messageContent.style.padding = '8px 12px';
        messageContent.style.borderRadius = isUser ? '15px 15px 5px 15px' : '15px 15px 15px 5px';
        messageContent.style.backgroundColor = isUser ? '#007bff' : '#e9ecef';
        messageContent.style.color = isUser ? 'white' : 'black';
        messageContent.style.maxWidth = '80%';
        messageContent.style.wordWrap = 'break-word';
        
        if (statusType === 'thinking') {
            messageContent.className = 'ai-thinking';
            messageContent.innerHTML = '🤔 AI is thinking<span class="thinking-dots"></span>';
            AppState.conversationState = 'thinking';
            AppState.currentStatusMessage = { messageDiv, messageContent };
        } else if (statusType === 'generating-speech') {
            messageContent.className = 'ai-generating-speech';
            messageContent.innerHTML = '🎙️ Generating speech<span class="thinking-dots"></span>';
            AppState.conversationState = 'generating-speech';
            AppState.currentStatusMessage = { messageDiv, messageContent };
        } else if (!isUser && statusType === 'typewriter') {
            messageContent.className = 'typewriter';
            messageContent.textContent = '';  // Start empty for typewriter effect
            
            // Start typewriter effect after the element is added to DOM
            setTimeout(() => {
                ChatModule.typewriterEffect(messageContent, text);
            }, 100);
        } else {
            messageContent.textContent = text;
            if (!isUser) {
                AppState.conversationState = 'ready';
                AppState.currentStatusMessage = null;
            }
        }
        
        messageDiv.appendChild(messageContent);
        
        // 🎙️ FIXED: Don't auto-expand chat in lesson voice mode
        const chatContainer = document.getElementById('chatContainer');
        const isVoiceMode = !chatContainer.classList.contains('expanded');
        const isLessonMode = window.lessonContext && window.lessonContext.isLessonMode;
        
        // Only auto-expand chat if:
        // 1. We're NOT in voice mode AND
        // 2. We're NOT in lesson mode (lessons default to voice) AND  
        // 3. We're NOT in voice conversation mode
        const shouldAutoExpand = !isVoiceMode && !isLessonMode && !SpeechModule.conversationMode;
        
        if (shouldAutoExpand) {
            // Make sure chat is visible for text mode in non-lesson contexts
            if (!chatContainer.classList.contains('expanded')) {
                UIControls.toggleChatWindow();
            }
        } else {
            console.log('🎤 Keeping chat collapsed - voice mode or lesson mode active');
        }
        
        document.getElementById('conversation').appendChild(messageDiv);
        document.getElementById('conversation').scrollTop = document.getElementById('conversation').scrollHeight;
        
        return { messageDiv, messageContent };
    },

    _isNewTopicIntroduction(text) {
        const topicIndicators = [
            "let's talk about",
            "let's discuss",
            "let's move on to",
            "let's look at",
            "let's explore",
            "let's go through",
            "let's examine",
            "let's review",
            "let's cover",
            "let's learn about",
            "let's understand",
            "let's dive into",
            "let's focus on",
            "let's analyze",
            "let's break down",
            "let's investigate",
            "let's consider",
            "let's study",
            "let's look into",
            "let's explore the concept of"
        ];
        
        return topicIndicators.some(indicator => text.toLowerCase().includes(indicator));
    },

    _isAskingForConfirmation(text) {
        const confirmationPhrases = [
            "does that make sense",
            "do you understand",
            "is that clear",
            "do you have any questions",
            "would you like me to explain",
            "shall we move on",
            "are you ready to proceed"
        ];
        
        return confirmationPhrases.some(phrase => text.toLowerCase().includes(phrase));
    },

    _generateTopicId(text) {
        // Generate a unique ID for the topic based on its content
        const timestamp = Date.now();
        const contentHash = text.substring(0, 50).replace(/[^a-z0-9]/gi, '').toLowerCase();
        return `${contentHash}_${timestamp}`;
    },

    // Clear current status message
    clearStatusMessage() {
        if (AppState.currentStatusMessage) {
            AppState.currentStatusMessage.messageDiv.remove();
            AppState.currentStatusMessage = null;
        }
    },

    // Update status message
    updateStatusMessage(newText, newClass = '') {
        if (AppState.currentStatusMessage) {
            AppState.currentStatusMessage.messageContent.innerHTML = newText;
            if (newClass) {
                AppState.currentStatusMessage.messageContent.className = newClass;
            }
        }
    },

    // Typewriter effect for AI responses
    typewriterEffect(element, text, speed = 30) {
        let index = 0;
        const conversationDiv = document.getElementById('conversation');
        
        function typeChar() {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
                
                // Auto-scroll to bottom as text appears
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
                
                setTimeout(typeChar, speed);
            } else {
                // Hide the blinking cursor when done
                element.classList.add('complete');
                AppState.conversationState = 'ready';
            }
        }
        
        typeChar();
    },
    
    // Handle form submission with improved TTS synchronization
    async handleChatSubmit(e) {
        e.preventDefault();
        
        const textInput = document.getElementById('text');
        const messageText = textInput.value.trim();
        
        if (!messageText) return;

        // Store user input in conversation memory
        AppState.lastUserInput = messageText;
        
        // Add user message to conversation
        await ChatModule.addMessage(messageText, true);
        
        // Clear input
        textInput.value = '';
        
        // Process the message
        await ChatModule.processMessage(messageText);
    },

    // Unified message processing for both chat and speech input
    async processMessage(messageText) {
        // FIXED: Remove local slide processing - let backend handle all commands
        // This prevents the AI thinking hang by ensuring all commands go through backend
        console.log('🎬 Processing message through backend (including slide commands):', messageText);
        
        // Step 1: Show "AI thinking..." while waiting for LLM response
        await ChatModule.addMessage('', false, 'thinking');
        
        try {
            // 🎓 LESSON CONTEXT ROUTING FIX: Check if we're in lesson mode
            let chatEndpoint = '/chat';  // Default endpoint
            
            // Check if lesson context is available
            if (window.lessonContext && window.lessonContext.isLessonMode && window.lessonContext.lessonId) {
                chatEndpoint = `/lesson/${window.lessonContext.lessonId}/chat`;
                console.log(`🎓 Using lesson chat endpoint: ${chatEndpoint}`);
            }
            
            // Enhance request with slide context for AI awareness
            const formData = new FormData();
            formData.append('text', messageText);
            
            // NEW: Add conversation history to provide context
            const recentContext = ConversationMemory.getRecentContext(10); // Get last 10 messages
            formData.append('conversation_history', JSON.stringify(recentContext));
            console.log('📚 Sending conversation history:', recentContext);
            
            // Add current slide index and context if available
            if (window.currentSlideData) {
                // *** Add the current slide index as 'current_slide' ***
                formData.append('current_slide', window.currentSlideData.index);

                // Optional: Keep the slide_context string for redundancy or other uses
                const slideContext = `[SLIDE_CONTEXT: Currently viewing slide ${window.currentSlideData.index + 1}/${window.currentSlideData.totalSlides}: "${window.currentSlideData.title}"]`;
                formData.append('slide_context', slideContext);

                console.log(`🎬 Adding slide data to AI request: Slide ${window.currentSlideData.index}, Context: ${slideContext}`);
                 // *** Add log here to confirm value being sent ***
                 console.log('Frontend sending current_slide:', window.currentSlideData.index);
            } else {
                 // If slide data isn't available, still send 0 as a default, but log a warning
                 formData.append('current_slide', 0);
                 console.warn('⚠️ window.currentSlideData not available, sending current_slide=0');
                  // *** Add log here to confirm default value being sent ***
                 console.log('Frontend sending default current_slide: 0');
            }
            
            // 🎓 Add lesson context for lesson-specific chats
            if (window.lessonContext && window.lessonContext.isLessonMode) {
                formData.append('lesson_id', window.lessonContext.lessonId);
                formData.append('lesson_title', window.lessonContext.lessonTitle || '');
                console.log(`🎓 Adding lesson context: ${window.lessonContext.lessonId}`);
            }
            
            // Get authentication token if available
            const authToken = localStorage.getItem('auth_token');
            const headers = {};
            
            if (authToken) {
                headers['Authorization'] = `Bearer ${authToken}`;
                console.log('🔐 Sending authenticated request');
            } else {
                console.log('👤 Sending anonymous request');
            }
            
            // Send request to backend
            const response = await fetch(chatEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: messageText,
                    current_slide: window.currentSlideData ? window.currentSlideData.index : 0,
                    conversation_history: recentContext,
                    slide_context: window.currentSlideData ? `[SLIDE_CONTEXT: Currently viewing slide ${window.currentSlideData.index + 1}/${window.currentSlideData.totalSlides}: "${window.currentSlideData.title}"]` : ''
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const data = await response.json();
            const aiResponse = data.response || 'Sorry, I could not process your request.';
            
            // Step 2: Determine mode and handle response appropriately
            await ChatModule.handleAIResponse(aiResponse);
            
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage = 'Sorry, there was an error processing your message.';
            await ChatModule.handleAIResponse(errorMessage, true);
        }
    },

    // Handle AI response based on current mode and TTS availability
    async handleAIResponse(aiResponse, isError = false) {
        const chatContainer = document.getElementById('chatContainer');
        const isVoiceMode = !chatContainer.classList.contains('expanded');
        
        // Clear the "AI thinking..." status
        ChatModule.clearStatusMessage();
        
        // FIXED: Always use TTS in voice mode with default settings
        const shouldUseTTS = isVoiceMode && !isError;
        
        if (shouldUseTTS) {
            // Voice mode with TTS using defaults
            await ChatModule.handleVoiceModeResponse(aiResponse);
        } else {
            // Chat mode or error - show typewriter immediately
            AppState.conversationState = 'ready';
            await ChatModule.addMessage(aiResponse, false, 'typewriter');
            
            if (isError) {
                console.log('📝 Error occurred - falling back to text display');
            }
        }
    },

    // Handle voice mode response with SIMPLIFIED OPTIMIZED APPROACH
    async handleVoiceModeResponse(text) {
        try {
            // Step 1: Show "AI thinking..." status with visual indicator
            const thinkingMessage = await ChatModule.addMessage('', false, 'thinking');
            
            // Get default TTS settings from backend - errors will propagate to outer catch
            const defaultTTSSettings = await TTSControls.getDefaultSettings();
            const selectedVoice = defaultTTSSettings.voice_id;
            const currentSpeed = defaultTTSSettings.speed;
            const currentTemperature = defaultTTSSettings.temperature;
            
            console.log('🎙️ TTS Settings retrieved successfully:', {
                voice: selectedVoice,
                speed: currentSpeed,
                temperature: currentTemperature
            });
            
            console.log('🤔 AI is thinking and generating speech...');
            console.log(`📏 Text length: ${text.length} characters`);
            console.log(`🎙️ Using TTS: Voice=${selectedVoice}, Speed=${currentSpeed}, Temp=${currentTemperature}`);
            
            // Step 2: Choose endpoint based on text length (AUTO-CHUNKING LOGIC)
            const MAX_STREAMING_LENGTH = 950; // Safe buffer under 1000 char limit
            const endpoint = text.length > MAX_STREAMING_LENGTH ? '/stream-chunked' : '/stream';
            
            console.log(`🎯 Using endpoint: ${endpoint} (text length: ${text.length})`);
            
            // Step 3: Update status to "Generating speech..."
            ChatModule.updateStatusMessage('🎙️ Generating speech<span class="thinking-dots"></span>', 'ai-generating-speech');
            
            // Step 4: OPTIMIZED APPROACH - Start TTS request with timeout
            const startTime = Date.now();
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    voice_id: selectedVoice,
                    speed: currentSpeed,
                    temperature: currentTemperature
                })
            });
            
            if (!response.ok) {
                throw new Error(`TTS failed: ${response.status}`);
            }
            
            const responseTime = Date.now() - startTime;
            console.log(`📡 TTS response received in ${responseTime}ms`);
            
            // Step 5: Check if chunking was used and update status
            const chunkCount = response.headers.get('X-Chunk-Count');
            if (chunkCount) {
                console.log(`📊 Response used ${chunkCount} chunks`);
            }
            
            // Step 6: Clear status, add text message, and play audio IMMEDIATELY
            ChatModule.clearStatusMessage();
            await ChatModule.addMessage(text, false, 'typewriter');
            
            // Step 7: SIMPLIFIED AUDIO PLAYBACK - No complex progressive streaming
            console.log('🎵 Converting response to audio blob...');
            const audioBlob = await response.blob();
            const conversionTime = Date.now() - startTime;
            console.log(`🎵 Audio ready in ${conversionTime}ms (${audioBlob.size} bytes)`);
            
            // Start the visualizer before playing audio
            if (window.ttsVisualizer && window.showVisualizer) {
                // Pass the desired dimensions from CSS
                const targetWidth = 160; // Match CSS width
                const targetHeight = 50; // Match CSS height
                window.showVisualizer(text, targetWidth, targetHeight);
            }
            
            // Play audio immediately
            await ChatModule.playAudioImmediately(audioBlob);
            
        } catch (error) {
            console.error('TTS generation failed:', error);
            
            // Clear any status messages
            ChatModule.clearStatusMessage();
            
            // Fall back to chat mode display with error indication
            console.log('🔄 TTS failed - falling back to text mode');
            AppState.conversationState = 'ready';
            await ChatModule.addMessage(text, false, 'typewriter');
            
            // Add a small note about the TTS failure
            setTimeout(async () => {
                await ChatModule.addMessage('[Voice synthesis temporarily unavailable]', false);
            }, 1000);
        }
    },

    // SIMPLIFIED: Immediate audio playback without complex streaming
    async playAudioImmediately(audioBlob) {
        console.log(`🎵 Playing audio immediately: ${audioBlob.size} bytes`);
        
        // Stop any currently playing audio
        if (AppState.currentAudioElement) {
            console.log('🔇 Stopping previous audio playback');
            AppState.currentAudioElement.pause();
            AppState.currentAudioElement.currentTime = 0;
            URL.revokeObjectURL(AppState.currentAudioElement.src);
            
            // Stop the visualizer if it's running
            if (window.ttsVisualizer) {
                window.ttsVisualizer.stop();
            }
        }
        
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        AppState.currentAudioElement = audio;
        AppState.isAISpeaking = true;
        AppState.conversationState = 'speaking';
        UIControls.updateButtonState();
        
        // Handle audio events
        audio.onended = () => {
            // Only proceed with normal cleanup if not interrupted
            if (!AppState.isInterrupted) {
                AppState.isAISpeaking = false;
                AppState.currentAudioElement = null;
                AppState.conversationState = 'ready';
                UIControls.updateButtonState();
                URL.revokeObjectURL(audioUrl);
                console.log('🔇 AI finished speaking');
                
                // Stop the visualizer
                if (window.ttsVisualizer) {
                    window.ttsVisualizer.stop();
                }
                
                // Notify speech module that AI finished speaking
                SpeechModule.onAIFinishedSpeaking();
            }
        };
        
        audio.onerror = (error) => {
            console.error('Audio playback error:', error);
            AppState.isAISpeaking = false;
            AppState.currentAudioElement = null;
            AppState.conversationState = 'ready';
            UIControls.updateButtonState();
            URL.revokeObjectURL(audioUrl);
            
            // Stop the visualizer on error
            if (window.ttsVisualizer) {
                window.ttsVisualizer.stop();
            }
        };
        
        // Start playback
        const playStartTime = Date.now();
        await audio.play();
        const playTime = Date.now() - playStartTime;
        console.log(`🎵 Audio playback started in ${playTime}ms`);
    }
};

// ============================================================================
// Audio Module
// ============================================================================
const AudioModule = {
    // Initialize audio playback
    initializeAudioPlayback() {
        if (!AppState.audioInitialized) {
            // Simple audio initialization for user gesture requirement
            const silentAudio = new Audio();
            silentAudio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQQAAAAAAA==';
            silentAudio.play().then(() => {
                AppState.audioInitialized = true;
                console.log('✅ Audio playback initialized');
            }).catch(() => {
                console.log('⚠️ Audio initialization failed - will retry on next interaction');
            });
        }
    },
    
    // Update feedback status
    updateFeedbackStatus() {
        const statusDiv = document.getElementById('feedbackStatus');
        if (!statusDiv) return;
        
        // Since AEC is disabled, show disabled status
        statusDiv.innerHTML = '🚫 AEC DISABLED: Speech recognition and echo cancellation disabled for debugging';
        statusDiv.style.backgroundColor = '#d4edda';
        statusDiv.style.borderColor = '#c3e6cb';
        statusDiv.style.color = '#155724';
    }
};

// ============================================================================
// TTS Control Module
// ============================================================================
const TTSControls = {
    // Default TTS settings for when admin UI is not available
    getDefaultSettings() {
        // Return a promise that resolves to the current settings from the backend
        return fetch('/tts/settings')
            .then(response => response.json());
    },
    
    // Initialize TTS settings
    async init() {
        // Check if TTS UI elements exist before initializing
        const hasTTSUI = document.getElementById('provider_select') !== null;
        
        if (!hasTTSUI) {
            console.log('🎙️ TTS UI not present on main page - voice mode will use default settings');
            const defaults = await this.getDefaultSettings();
            console.log('🎙️ Default TTS config: Voice=' + defaults.voice_id + ', Speed=' + defaults.speed + ', Temp=' + defaults.temperature);
            console.log('⚙️ To customize TTS settings, visit Admin Settings panel');
            return;
        }
        
        // Load providers
        await this.loadProviders();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load saved settings from backend
        await this.loadSavedSettings();
    },
    
    // Load TTS providers
    async loadProviders() {
        try {
            // Check if TTS UI elements exist on this page
            const providerSelect = document.getElementById('provider_select');
            if (!providerSelect) {
                console.log('🎙️ TTS provider UI not present on this page - skipping provider loading');
                return;
            }
            
            const response = await fetch('/tts/providers');
            const data = await response.json();
            
            providerSelect.innerHTML = '';
            
            // Iterate over the keys of data.providers
            Object.keys(data.providers).forEach(providerName => {
                const provider = data.providers[providerName];
                const option = document.createElement('option');
                option.value = providerName; // Use providerName as value
                option.textContent = provider.name;
                if (providerName === data.current_provider) { // Use data.current_provider
                    option.selected = true;
                    AppState.currentProvider = providerName; // Update AppState
                }
                providerSelect.appendChild(option);
            });
            
            // Update provider status and load voices for current provider
            if (data.current_provider) {
                await this.loadVoices(data.current_provider);
            }
            
        } catch (error) {
            console.error('Failed to load TTS providers:', error);
        }
    },
    
    // Load voices for a provider
    async loadVoices(providerId) {
        try {
            // Check if voice select element exists
            const voiceSelect = document.getElementById('voice_select');
            if (!voiceSelect) {
                console.log('🎙️ Voice select UI not present on this page - skipping voice loading');
                return;
            }
            
            const response = await fetch('/voices');
            const data = await response.json();
            
            voiceSelect.innerHTML = '<option value="" disabled>Choose a voice...</option>';
            
            if (data.voices_page && data.voices_page.length > 0) {
                data.voices_page.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.id;
                    option.textContent = voice.name;
                    voiceSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Failed to load voices:', error);
        }
    },
    
    // Set up event listeners
    setupEventListeners() {
        try {
            // Check if TTS UI elements exist before setting up listeners
            const providerSelect = document.getElementById('provider_select');
            const voiceSelect = document.getElementById('voice_select');
            const speedSlider = document.getElementById('speed');
            
            if (!providerSelect || !voiceSelect || !speedSlider) {
                console.log('🎙️ TTS controls not present on this page - skipping event listener setup');
                return;
            }
            
            // Provider change - with enhanced safety
            if (providerSelect && typeof providerSelect.addEventListener === 'function') {
                providerSelect.addEventListener('change', async (e) => {
                    try {
                        if (e.target && e.target.value) {
                            await this.loadVoices(e.target.value);
                        }
                    } catch (error) {
                        console.warn('⚠️ Error in provider change handler:', error);
                    }
                });
            }
            
            // Voice change - with enhanced safety
            if (voiceSelect && typeof voiceSelect.addEventListener === 'function') {
                voiceSelect.addEventListener('change', (e) => {
                    try {
                        if (e.target && e.target.value) {
                            AppState.currentVoice = e.target.value;
                            localStorage.setItem('selectedVoice', e.target.value);
                        }
                    } catch (error) {
                        console.warn('⚠️ Error in voice change handler:', error);
                    }
                });
            }
            
            // Speed change - with enhanced safety
            if (speedSlider && typeof speedSlider.addEventListener === 'function') {
                speedSlider.addEventListener('input', (e) => {
                    try {
                        if (e.target && e.target.value) {
                            const speedValue = e.target.value;
                            const speedValueDisplay = document.getElementById('speedValue');
                            if (speedValueDisplay && typeof speedValueDisplay.textContent !== 'undefined') {
                                speedValueDisplay.textContent = speedValue + 'x';
                            }
                            localStorage.setItem('speed', speedValue);
                        }
                    } catch (error) {
                        console.warn('⚠️ Error in speed change handler:', error);
                    }
                });
            }
        } catch (error) {
            console.warn('⚠️ Error setting up TTS event listeners:', error);
        }
    },
    
    // Load saved settings from backend
    async loadSavedSettings() {
        try {
            const settings = await this.getDefaultSettings();
            const providerSelect = document.getElementById('provider_select');
            const voiceSelect = document.getElementById('voice_select');
            const speedSlider = document.getElementById('speed');
            const temperatureSlider = document.getElementById('temperature');
            
            if (providerSelect) providerSelect.value = settings.provider;
            if (voiceSelect) voiceSelect.value = settings.voice_id;
            if (speedSlider) speedSlider.value = settings.speed;
            if (temperatureSlider) temperatureSlider.value = settings.temperature;
            
            console.log('✅ Loaded TTS settings from backend:', settings);
        } catch (error) {
            console.warn('⚠️ Error loading saved TTS settings:', error);
        }
    }
};

// ============================================================================
// Settings Module
// ============================================================================
const SettingsModule = {
    // Enhanced initialization function
    async init() {
        console.log('🚀 Initializing Enhanced SettingsModule...');
        
        try {
            // Load saved system prompt and apply it (this seems independent of the document list UI)
            // Removed localStorage prompt loading/applying to simplify
            // await this.loadAndApplySystemPrompt();
            
            // NOTE: Document upload and management functionality has been moved/removed.
            // The AI will now use lesson content directly from the database as knowledge base.
            console.log('📚 Document management features are disabled on this page.');
            
            // The checkKnowledgeBaseStatus might still be useful for debugging the primary knowledge source (lesson data), 
            // so keeping it for now, but its output might change based on backend modifications.
            await this.checkKnowledgeBaseStatus();
            
            console.log('✅ Enhanced SettingsModule initialization complete');
            
        } catch (error) {
            console.error('❌ Error during SettingsModule initialization:', error);
            SettingsModule.showFeedback('Error initializing settings: ' + error.message, 'error');
        }
    },

    // Enhanced updateSystemPrompt with better feedback
    async updateSystemPrompt() {
        const systemPromptTextarea = document.getElementById('systemPrompt');
        if (!systemPromptTextarea) {
            SettingsModule.showFeedback('System prompt textarea not found', 'error');
            return;
        }

        const systemPrompt = systemPromptTextarea.value.trim();

        try {
            console.log(`💾 Updating system prompt: ${systemPrompt.length} chars`);

            // Save to localStorage first
            localStorage.setItem('systemPrompt', systemPrompt);
            console.log('✅ System prompt saved locally');

            // Send to backend
            const response = await fetch('/system-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: systemPrompt,
                    // Include lesson_id
                    lesson_id: window.lessonContext ? window.lessonContext.lessonId : null
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ System prompt updated on server:', result);
                SettingsModule.showFeedback(`System prompt updated! (${result.prompt_length} characters)`, 'success');
            } else {
                const errorData = await response.json();
                console.error('❌ Server error:', errorData);
                SettingsModule.showFeedback('Failed to update system prompt: ' + (errorData.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('❌ Error updating system prompt:', error);
            SettingsModule.showFeedback('Error updating system prompt: ' + error.message, 'error');
        }
    },

    // NOTE: Document upload functionality is now disabled as the AI uses lesson data from the database as knowledge base.
    /*
    async uploadDocument() {
        const docName = document.getElementById('docName').value;
        const docContent = document.getElementById('docContent').value;

        if (!docName || !docContent) {
            alert('Please provide both document name and content');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('name', docName);
            formData.append('content', docContent);
            // Include lesson_id
            if (window.lessonContext && window.lessonContext.lessonId) {
                formData.append('lesson_id', window.lessonContext.lessonId);
            } else {
                alert('Lesson ID not available. Cannot upload document.');
                console.error('Lesson ID not available for document upload.');
                return;
            }

            const response = await fetch('/documents', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                alert('Document uploaded successfully!');
                document.getElementById('docName').value = '';
                document.getElementById('docContent').value = '';
                await this.loadDocuments();
            } else {
                alert('Failed to upload document');
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            alert('Error uploading document');
        }
    },
    */

    // NOTE: Document loading functionality is now disabled.
    /*
    async loadDocuments() {
        try {
            console.log('📚 Loading documents from server...');

            // Include lesson_id as a query parameter
            const lessonId = window.lessonContext ? window.lessonContext.lessonId : null;
            if (!lessonId) {
                console.warn('⚠️ Lesson ID not available. Cannot load documents.');
                SettingsModule.showFeedback('Lesson ID not available. Cannot load documents.', 'warning');
                return;
            }

            const response = await fetch(`/documents?lesson_id=${encodeURIComponent(lessonId)}`);

            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            const docList = document.getElementById('documentList');

            if (!docList) {
                console.warn('⚠️ Document list element not found');
                return;
            }

            // Clear existing content
            docList.innerHTML = '';

            if (data.documents && data.documents.length > 0) {
                console.log(`📄 Found ${data.documents.length} documents`);

                data.documents.forEach(docName => {
                    const docDiv = document.createElement('div');
                    docDiv.style.cssText = `
                        margin-bottom: 8px;
                        padding: 10px;
                        background: #f8f9fa;
                        border-radius: 6px;
                        border-left: 4px solid #007bff;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    `;

                    docDiv.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: #333; font-size: 14px;">${SettingsModule.escapeHtml(docName)}</strong>
                            <button onclick="SettingsModule.removeDocument('${SettingsModule.escapeHtml(docName)}')"
                                    style="background-color: #dc3545; color: white; border: none;
                                           padding: 4px 8px; border-radius: 3px; cursor: pointer;
                                           font-size: 12px; transition: background-color 0.2s;"
                                    onmouseover="this.style.backgroundColor='#c82333'"
                                    onmouseout="this.style.backgroundColor='#dc3545'">
                                Remove
                            </button>
                        </div>
                    `;
                    docList.appendChild(docDiv);
                });

                SettingsModule.showFeedback(`Loaded ${data.documents.length} documents`, 'success');
            } else {
                docList.innerHTML = '<em style="color: #666; font-style: italic;">No documents uploaded yet</em>';
                console.log('📄 No documents found');
            }
        } catch (error) {
            console.error('❌ Error loading documents:', error);
            SettingsModule.showFeedback('Error loading documents: ' + error.message, 'error');
        }
    },
    */

    // NOTE: Document removal functionality is now disabled.
    /*
    async removeDocument(docName) {
        if (!confirm(`Are you sure you want to remove "${docName}"?`)) {
            return;
        }

        try {
            // Include lesson_id as a query parameter
            const lessonId = window.lessonContext ? window.lessonContext.lessonId : null;
             if (!lessonId) {
                alert('Lesson ID not available. Cannot remove document.');
                console.error('Lesson ID not available for document removal.');
                return;
            }

            const response = await fetch(`/documents/${encodeURIComponent(docName)}?lesson_id=${encodeURIComponent(lessonId)}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                alert('Document removed successfully!');
                await this.loadDocuments();
            } else {
                alert('Failed to remove document');
            }
        } catch (error) {
            console.error('Error removing document:', error);
            alert('Error removing document');
        }
    },
    */

    // NOTE: Knowledge base status check might still be relevant for the primary knowledge source (lesson data), 
    // but the implementation here was likely tied to the separate document KB. 
    // Keeping the function definition but commenting out its likely unnecessary logic.
    async checkKnowledgeBaseStatus() {
        console.log('📊 Checking knowledge base status (for primary knowledge source)...');
        // The logic below was for the separate document KB. This should be implemented in the backend.
        /*
        try {
            // Include lesson_id as a query parameter
            const lessonId = window.lessonContext ? window.lessonContext.lessonId : null;
             if (!lessonId) {
                console.warn('⚠️ Lesson ID not available. Cannot check knowledge base status.');
                SettingsModule.showFeedback('Lesson ID not available. Cannot check knowledge base status.', 'warning');
                return null;
            }

            const response = await fetch(`/knowledge-base/status?lesson_id=${encodeURIComponent(lessonId)}`);

            if (response.ok) {
                const status = await response.json();
                console.log('📊 Knowledge base status:', status);

                // Show warning if there are consistency issues
                if (status.consistency_issues) {
                    console.warn('⚠️ Knowledge base consistency issues detected:', {
                        missing: status.documents.missing_from_memory,
                        extra: status.documents.extra_in_memory
                    });
                }

                return status;
            }
        } catch (error) {
            console.error('❌ Error checking knowledge base status:', error);
        }

        return null;
        */
    },

    // NOTE: Auto-refresh functionality for the document list is now disabled.
    /*
    setupAutoRefresh() {
        // Refresh documents every 30 seconds if the settings sidebar is open
        setInterval(() => {
            const sidebar = document.getElementById('settingsSidebar');
            // Only refresh if lessonId is available and sidebar is open
            if (window.lessonContext && window.lessonContext.lessonId && sidebar && !sidebar.classList.contains('collapsed')) {
                SettingsModule.loadDocuments();
            } else {
                console.log('⏰ Auto-refresh skipped: lessonId not available or sidebar closed.');
            }
        }, 30000);

        console.log('⏰ Auto-refresh set up (30s interval)');
    },
    */

    // Utility function to escape HTML
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    // Enhanced feedback system
    showFeedback(message, type = 'info') {
        // Create or update feedback element
        let feedbackEl = document.getElementById('settingsFeedback');
        
        if (!feedbackEl) {
            feedbackEl = document.createElement('div');
            feedbackEl.id = 'settingsFeedback';
            feedbackEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                z-index: 10000;
                max-width: 350px;
                opacity: 0;
                transition: opacity 0.3s ease;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-size: 14px;
                line-height: 1.4;
            `;
            document.body.appendChild(feedbackEl);
        }
        
        // Set color based on type
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        
        feedbackEl.style.backgroundColor = colors[type] || colors.info;
        if (type === 'warning') {
            feedbackEl.style.color = '#000';
        } else {
            feedbackEl.style.color = '#fff';
        }
        
        feedbackEl.textContent = message;
        feedbackEl.style.opacity = '1';
        
        // Auto-hide after 4 seconds (longer for error messages)
        const hideDelay = type === 'error' ? 6000 : 4000;
        setTimeout(() => {
            feedbackEl.style.opacity = '0';
            setTimeout(() => {
                if (feedbackEl.parentNode) {
                    feedbackEl.parentNode.removeChild(feedbackEl);
                }
            }, 300);
        }, hideDelay);
        
        console.log(`💬 Feedback (${type}): ${message}`);
    }
};

// ============================================================================
// Organic Flow Ring Visualizer Class
// ============================================================================


// ============================================================================
// Speech Recognition Module - VOICE INPUT
// ============================================================================
const SpeechModule = {
    recognition: null,
    isListening: false,
    isInitialized: false,
    conversationMode: false, // NEW: Continuous conversation mode
    autoRestartTimeout: null,
    
    // NEW: Speech validation settings (FIXED - More permissive for better user experience)
    speechValidation: {
        minConfidence: 0.3,          // Much more permissive - was 0.6
        minInterimConfidence: 0.2,   // Much more permissive - was 0.4  
        minSpeechDuration: 200,      // Much shorter - was 400ms
        maxNoSpeechRetries: 5,       // More retries - was 3
        currentNoSpeechCount: 0,     // Track consecutive failures
        speechStartTime: null,       // Track when speech started
        lastValidSpeech: null,       // Track last valid speech time
        backgroundNoiseThreshold: 1 // Allow single words - was 2
    },
    
    // Initialize speech recognition
    init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('⚠️ Speech Recognition not supported in this browser');
            return false;
        }
        
        try {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false; // Stop after each phrase
            this.recognition.interimResults = true;
            this.recognition.maxAlternatives = 1;
            this.recognition.lang = 'en-US';
            
            // Set up event handlers
            this.recognition.onstart = () => {
                console.log('🎤 Speech recognition started');
                this.isListening = true;
                AppState.isRecording = true;
                UIControls.updateButtonState();
            };
            
            this.recognition.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';
                let bestConfidence = 0;
                
                // Track when speech detection started
                if (!this.speechValidation.speechStartTime) {
                    this.speechValidation.speechStartTime = Date.now();
                }
                
                // Clear response timeout if user is speaking
                this.clearResponseTimeout();
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    const transcript = result[0].transcript;
                    const confidence = result[0].confidence || 1.0;
                    
                    bestConfidence = Math.max(bestConfidence, confidence);
                    
                    if (result.isFinal) {
                        // Apply validation to final results
                        if (this.isValidSpeech(transcript, confidence, true)) {
                            finalTranscript += transcript;
                            console.log(`🎤 Valid final speech: "${transcript}" (confidence: ${confidence.toFixed(2)})`);
                        } else {
                            console.log(`🔇 Rejected final speech: "${transcript}" (confidence: ${confidence.toFixed(2)}) - likely noise`);
                        }
                    } else {
                        // Show interim results if they meet minimum standards
                        if (this.isValidSpeech(transcript, confidence, false)) {
                            interimTranscript += transcript;
                        }
                    }
                }
                
                // Show interim results for user feedback
                if (interimTranscript) {
                    console.log(`🎤 Interim: "${interimTranscript}" (confidence: ${bestConfidence.toFixed(2)})`);
                }
                
                // Process final result if valid
                if (finalTranscript.trim()) {
                    this.speechValidation.currentNoSpeechCount = 0; // Reset failure count
                    this.speechValidation.lastValidSpeech = Date.now();
                    this.processSpeechInput(finalTranscript.trim());
                }
            };
            
            // NEW: Add speech validation method (IMPROVED with better debugging)
            this.isValidSpeech = (transcript, confidence, isFinal) => {
                const cleanTranscript = transcript.trim();
                const words = cleanTranscript.split(/\s+/).filter(word => word.length > 0);
                
                // Check confidence thresholds
                const minConfidence = isFinal ? 
                    this.speechValidation.minConfidence : 
                    this.speechValidation.minInterimConfidence;
                
                if (confidence < minConfidence) {
                    console.log(`🔇 Rejected confidence: ${confidence.toFixed(2)} < ${minConfidence} for "${cleanTranscript}"`);
                    return false;
                }
                
                // Check for minimum word count (filter out noise)
                if (words.length < this.speechValidation.backgroundNoiseThreshold) {
                    console.log(`🔇 Rejected word count: ${words.length} < ${this.speechValidation.backgroundNoiseThreshold} for "${cleanTranscript}"`);
                    return false;
                }
                
                // For final results, check speech duration
                if (isFinal && this.speechValidation.speechStartTime) {
                    const speechDuration = Date.now() - this.speechValidation.speechStartTime;
                    if (speechDuration < this.speechValidation.minSpeechDuration) {
                        console.log(`🔇 Rejected duration: ${speechDuration}ms < ${this.speechValidation.minSpeechDuration}ms for "${cleanTranscript}"`);
                        return false;
                    }
                }
                
                // Passed all validation
                console.log(`✅ Accepted speech: "${cleanTranscript}" (confidence: ${confidence.toFixed(2)}, words: ${words.length})`);
                return true;
            };
            
            this.recognition.onerror = (event) => {
                console.error('❌ Speech recognition error:', event.error);
                this.isListening = false;
                AppState.isRecording = false;
                this.speechValidation.speechStartTime = null; // Reset speech timing
                UIControls.updateButtonState();
                
                // Handle specific errors with smart backoff
                if (event.error === 'no-speech') {
                    this.speechValidation.currentNoSpeechCount++;
                    console.log(`🔇 No speech detected (${this.speechValidation.currentNoSpeechCount}/${this.speechValidation.maxNoSpeechRetries})`);
                    
                    // FIXED: More lenient restart conditions to prevent hanging
                    if (this.conversationMode && !AppState.isAISpeaking) {
                        
                        // Implement smart backoff for too many failures
                        if (this.speechValidation.currentNoSpeechCount >= this.speechValidation.maxNoSpeechRetries) {
                            console.log('⚠️ Too many no-speech detections, taking a longer break');
                            this.scheduleAutoRestart(6000); // Much longer delay to calm down
                            this.speechValidation.currentNoSpeechCount = 0; // Reset after long delay
                        } else {
                            // Use shorter delay to keep conversation flowing
                            this.scheduleAutoRestart(1000); // Reduced from 1500ms
                        }
                    } else {
                        console.log(`⚠️ Not restarting after no-speech - AI is busy (state: ${AppState.conversationState})`);
                    }
                } else if (event.error === 'not-allowed') {
                    console.error('❌ Microphone access denied');
                    alert('Microphone access denied. Please allow microphone access and refresh the page.');
                    this.stopConversation();
                } else if (event.error === 'audio-capture') {
                    console.log('🎤 Audio capture error - microphone may be busy');
                    // More aggressive restart for audio capture issues
                    if (this.conversationMode && !AppState.isAISpeaking) {
                        this.scheduleAutoRestart(1500); // Reduced delay
                    }
                } else if (event.error === 'aborted') {
                    console.log('🔇 Speech recognition was aborted - this is normal during manual stops');
                    // Don't restart on aborted - it was intentional
                } else {
                    // Other errors - be more aggressive with restart to prevent hanging
                    console.log(`⚠️ Unexpected speech error: ${event.error}`);
                    if (this.conversationMode && !AppState.isAISpeaking) {
                        this.scheduleAutoRestart(2000); // Reduced from 3000ms
                    }
                }
            };
            
            this.recognition.onend = () => {
                console.log('🔇 Speech recognition ended');
                this.isListening = false;
                AppState.isRecording = false;
                this.speechValidation.speechStartTime = null; // Reset speech timing
                UIControls.updateButtonState();
                
                // FIXED: Only schedule restart/timeout if AI is not busy
                if (this.conversationMode && !AppState.isAISpeaking) {
                    
                    // Don't restart if AI is thinking or generating speech
                    if (AppState.conversationState === 'thinking' || AppState.conversationState === 'generating-speech') {
                        console.log(`⚠️ Not restarting - AI is ${AppState.conversationState}`);
                        return;
                    }
                    
                    // Start timeout for automatic response if user pauses too long
                    this.startResponseTimeout();
                    
                    // Use normal delay if we had valid speech recently, longer if not
                    const timeSinceLastSpeech = this.speechValidation.lastValidSpeech ? 
                        Date.now() - this.speechValidation.lastValidSpeech : Infinity;
                    
                    const delay = timeSinceLastSpeech > 30000 ? 2000 : 800; // Longer delay if no speech for 30s
                    this.scheduleAutoRestart(delay);
                }
            };
            
            this.isInitialized = true;
            console.log('✅ Speech recognition initialized');
            return true;
            
        } catch (error) {
            console.error('❌ Speech recognition initialization failed:', error);
            return false;
        }
    },
    
    // Start conversation mode (continuous listening)
    async startConversation() {
        if (!this.isInitialized && !this.init()) {
            alert('Speech recognition is not available in this browser');
            return;
        }
        
        console.log('📞 Starting conversation mode with default voice (Sky)');
        this.conversationMode = true;
        
        // Initialize conversation memory only if it hasn't been initialized
        if (!AppState.conversationMemory.messages.length) {
            ConversationMemory.init(
                window.lessonContext?.lessonId,
                window.currentSlideData?.index
            );
            ConversationMemory.setMode('voice');
            
            // Wait for greeting to complete before starting to listen
            await this.triggerAICoachGreeting();
        } else {
            // Update mode for existing conversation
            ConversationMemory.setMode('voice');
            console.log('🔄 Continuing existing conversation in voice mode');
        }
        
        // Reset speech validation state for fresh start
        this.speechValidation.currentNoSpeechCount = 0;
        this.speechValidation.speechStartTime = null;
        this.speechValidation.lastValidSpeech = Date.now();
        
        // Only start listening after greeting is complete
        this.startListening();
    },
    
    // 🎬 NEW: Trigger AI coach greeting and introduction
    async triggerAICoachGreeting() {
        // NEW: Check if we've already greeted
        if (AppState.hasGreeted) {
            console.log('👋 Skipping greeting - already delivered');
            return;
        }

        // NEW: Check if a lesson welcome was recently shown (within last 5 seconds)
        const timeSinceWelcome = Date.now() - (window.lastLessonWelcomeTime || 0);
        if (timeSinceWelcome < 5000) { // 5 seconds
            console.log('👋 Skipping greeting - lesson welcome was recently shown');
            AppState.hasGreeted = true; // Mark as greeted to prevent future greetings
            return;
        }

        try {
            console.log('👋 Triggering AI Coach greeting...');
            
            // Show thinking message while waiting for greeting
            ChatModule.updateStatusMessage("AI Coach is thinking...");
            
            // Ensure lessonContext and lessonId are available
            if (!window.lessonContext || !window.lessonContext.lessonId) {
                console.warn('⚠️ Lesson context or lesson ID not available - cannot trigger AI coach greeting.');
                ChatModule.clearStatusMessage();
                await ChatModule.handleAIResponse("I cannot start the conversation because the lesson context is missing. Please ensure you are in a lesson.");
                return;
            }

            const lessonId = window.lessonContext.lessonId;
            const chatEndpoint = `/lesson/${encodeURIComponent(lessonId)}/chat`;
            console.log(`📞 Sending greeting request to: ${chatEndpoint}`);
            
            // NEW: Get conversation history for context
            const recentContext = ConversationMemory.getRecentContext(10);
            
            // Send special greeting trigger to backend
            const response = await fetch(chatEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: "START_AI_COACH_GREETING",
                    is_greeting_trigger: true,
                    conversation_history: recentContext, // NEW: Include conversation history
                    current_slide: window.currentSlideData?.index || 0
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                const greeting = data.response;
                
                // Clear thinking message and show greeting
                ChatModule.clearStatusMessage();
                await ChatModule.handleAIResponse(greeting);
                
                // NEW: Mark greeting as delivered
                AppState.hasGreeted = true;
                console.log('✅ AI Coach greeting delivered');
            } else {
                throw new Error(`Greeting request failed: ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Error triggering AI coach greeting:', error);
            
            // Show error message to user
            ChatModule.clearStatusMessage();
            await ChatModule.handleAIResponse("I apologize, but I'm having trouble starting our conversation. Please try refreshing the page or starting a new conversation.");
        }
    },
    
    // Stop conversation mode
    stopConversation() {
        console.log('📞 Ending conversation mode');
        this.conversationMode = false;
        this.clearAutoRestart();
        this.clearResponseTimeout();
        this.stopListening();
        
        // Reset validation state
        this.speechValidation.currentNoSpeechCount = 0;
        this.speechValidation.speechStartTime = null;
        
        // Reset conversation state
        AppState.conversationState = 'ready';
        AppState.lastUserInput = null;
        AppState.hasGreeted = false;  // NEW: Reset greeting state when conversation ends
    },
    
    // Schedule automatic restart of listening
    scheduleAutoRestart(delay = 1000) {
        this.clearAutoRestart();
        
        if (!this.conversationMode) {
            console.log('⚠️ Not scheduling auto-restart - not in conversation mode');
            return;
        }
        
        // FIXED: Don't restart if AI is busy thinking, generating speech, or speaking
        if (AppState.conversationState !== 'ready' && AppState.conversationState !== 'listening') {
            console.log(`⚠️ Not scheduling auto-restart - AI is busy (state: ${AppState.conversationState})`);
            return;
        }
        
        console.log(`⏱️ Scheduling auto-restart in ${delay}ms`);
        this.autoRestartTimeout = setTimeout(() => {
            console.log(`🔄 Auto-restart timeout triggered - conversationMode: ${this.conversationMode}, isAISpeaking: ${AppState.isAISpeaking}, isListening: ${this.isListening}, conversationState: ${AppState.conversationState}`);
            
            // Enhanced conditions check
            if (this.conversationMode && 
                !AppState.isAISpeaking && 
                !this.isListening &&
                (AppState.conversationState === 'ready' || AppState.conversationState === 'listening')) {
                console.log('🔄 Auto-restarting listening for conversation');
                this.startListening();
            } else {
                console.log('⚠️ Skipping auto-restart - conditions not met');
            }
        }, delay);
    },
    
    // Clear auto-restart timeout
    clearAutoRestart() {
        if (this.autoRestartTimeout) {
            clearTimeout(this.autoRestartTimeout);
            this.autoRestartTimeout = null;
        }
    },
    
    // Start listening for speech
    startListening() {
        if (!this.isInitialized && !this.init()) {
            alert('Speech recognition is not available in this browser');
            return;
        }
        
        if (this.isListening) {
            console.log('🎤 Already listening...');
            return;
        }
        
        // Don't listen if AI is speaking
        if (AppState.isAISpeaking) {
            console.log('🔇 Cannot listen while AI is speaking');
            return;
        }
        
        // FIXED: Don't listen if AI is busy thinking or generating speech
        if (AppState.conversationState === 'thinking' || AppState.conversationState === 'generating-speech') {
            console.log(`🔇 Cannot listen while AI is ${AppState.conversationState}`);
            return;
        }
        
        try {
            console.log('🎤 Thinking...');
            AppState.conversationState = 'listening';
            this.recognition.start();
            // Note: isListening will be set to true in the onstart event handler
        } catch (error) {
            console.error('❌ Failed to start speech recognition:', error);
            this.isListening = false;
            AppState.isRecording = false;
            AppState.conversationState = 'ready';
            UIControls.updateButtonState();
        }
    },
    
    // Stop listening
    stopListening() {
        if (this.recognition && this.isListening) {
            console.log('🛑 Stopping speech recognition');
            this.recognition.stop();
            this.isListening = false;
        }
        
        // Reset conversation state if we were listening
        if (AppState.conversationState === 'listening') {
            AppState.conversationState = 'ready';
        }
    },
    
    // Process speech input and send to chat
    async processSpeechInput(transcript) {
        console.log('📝 Processing speech input:', transcript);
        
        // Set conversation state to prevent auto-restarts while processing
        AppState.conversationState = 'thinking';
        
        // Store input in conversation memory
        AppState.lastUserInput = transcript;
        
        // Add user message to chat
        await ChatModule.addMessage(transcript, true);
        
        // Process through unified message handler
        await ChatModule.processMessage(transcript);
    },
    
    // Enhanced conversation timeout handling
    startResponseTimeout() {
        // Clear any existing timeout
        this.clearResponseTimeout();
        
        // Set a timeout to provide a response if user stops talking for too long
        AppState.responseTimeout = setTimeout(async () => {
            if (this.conversationMode && !AppState.isAISpeaking && !this.isListening) {
                console.log('⏰ User pause detected - providing contextual response');
                
                // Generate a contextual prompt based on the situation
                let contextualPrompt;
                if (AppState.lastUserInput) {
                    contextualPrompt = "I noticed you paused. Would you like me to continue with our conversation or is there something specific you'd like to discuss?";
                } else {
                    contextualPrompt = "I'm here and ready to help. What would you like to talk about?";
                }
                
                // Process as if it were a natural conversation continuation
                await ChatModule.processMessage("continue conversation");
            }
        }, 5000); // 5 second timeout for natural conversation flow
    },
    
    // Clear response timeout
    clearResponseTimeout() {
        if (AppState.responseTimeout) {
            clearTimeout(AppState.responseTimeout);
            AppState.responseTimeout = null;
        }
    },
    
    // NEW: Automatically restart listening after AI finishes speaking
    onAIFinishedSpeaking() {
        // Clear any response timeout since AI just finished speaking
        this.clearResponseTimeout();
        
        if (this.conversationMode && !this.isListening) {
            console.log('🎤 AI finished speaking, resuming conversation');
            console.log(`📊 State check - conversationMode: ${this.conversationMode}, isListening: ${this.isListening}, isAISpeaking: ${AppState.isAISpeaking}`);
            
            // Wait a bit longer after AI speech to allow natural conversation flow
            // This prevents immediate restarts and reduces the feedback loop
            this.scheduleAutoRestart(1000); // Increased from 500ms to 1000ms for better flow
        } else {
            console.log(`⚠️ Not restarting speech - conversationMode: ${this.conversationMode}, isListening: ${this.isListening}`);
        }
    },
    
    // NEW: Adjust speech sensitivity (FIXED with much more reasonable values)
    adjustSensitivity(level) {
        // level: 'low', 'medium', 'high'
        switch(level) {
            case 'low':
                this.speechValidation.minConfidence = 0.6;        // Conservative but reasonable
                this.speechValidation.minInterimConfidence = 0.4;
                this.speechValidation.minSpeechDuration = 300;    // Allow reasonably short speech
                this.speechValidation.backgroundNoiseThreshold = 2;  // Require 2+ words
                this.speechValidation.maxNoSpeechRetries = 3;
                console.log('🔇 Speech sensitivity set to LOW (less sensitive to noise)');
                break;
            case 'high':
                this.speechValidation.minConfidence = 0.1;        // Very permissive
                this.speechValidation.minInterimConfidence = 0.05;
                this.speechValidation.minSpeechDuration = 100;    // Very short allowed
                this.speechValidation.backgroundNoiseThreshold = 1;  // Single words OK
                this.speechValidation.maxNoSpeechRetries = 8;
                console.log('🎤 Speech sensitivity set to HIGH (very sensitive)');
                break;
            default: // medium - NEW BALANCED DEFAULTS
                this.speechValidation.minConfidence = 0.3;        // Reasonable threshold
                this.speechValidation.minInterimConfidence = 0.2;
                this.speechValidation.minSpeechDuration = 200;    // Short phrases OK
                this.speechValidation.backgroundNoiseThreshold = 1;  // Single words OK
                this.speechValidation.maxNoSpeechRetries = 5;
                console.log('🎯 Speech sensitivity set to MEDIUM (balanced - allows single words)');
        }
    },
    
    // NEW: Get speech detection statistics
    getSpeechStats() {
        return {
            consecutiveNoSpeech: this.speechValidation.currentNoSpeechCount,
            lastValidSpeech: this.speechValidation.lastValidSpeech,
            timeSinceLastSpeech: this.speechValidation.lastValidSpeech ? 
                Date.now() - this.speechValidation.lastValidSpeech : null,
            currentSettings: {
                minConfidence: this.speechValidation.minConfidence,
                minDuration: this.speechValidation.minSpeechDuration,
                noiseThreshold: this.speechValidation.backgroundNoiseThreshold
            }
        };
    }
};

// ============================================================================
// Test Functions (moved from global scope)
// ============================================================================
window.testTTS = async function() {
    console.log('Testing TTS...');
    
    // Use default settings if UI elements aren't available
    const defaultSettings = TTSControls.getDefaultSettings();
    const selectedVoice = defaultSettings.voice_id;
    const currentSpeed = defaultSettings.speed;
    
    if (!selectedVoice) {
        alert('No TTS voice available - please configure TTS in admin settings');
        return;
    }
    
    const testText = "Hello! This is a test of the text to speech system. How does this sound?";
    
    try {
        console.log(`🎙️ Testing TTS with voice: ${selectedVoice}, speed: ${currentSpeed}`);
        
        const response = await fetch('/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: testText,
                voice_id: selectedVoice,
                speed: currentSpeed
            })
        });
        
        if (response.ok) {
            console.log('✅ TTS synthesis successful');
            
            // Get the audio blob and play it
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                console.log('🔇 TTS test playback completed');
            };
            
            audio.onerror = (error) => {
                console.error('Audio playback error:', error);
                URL.revokeObjectURL(audioUrl);
                alert('Audio playback failed');
            };
            
            await audio.play();
            console.log('🎵 Playing TTS test audio...');
            
        } else {
            const errorData = await response.json();
            console.error('TTS test failed:', response.status, errorData);
            alert(`TTS test failed: ${errorData.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('TTS test error:', error);
        alert('TTS test error: ' + error.message);
    }
};

window.testChunking = function() {
    console.log('Testing chunking system...');
    alert('Chunking test functionality to be implemented');
};

window.testAEC = function() {
    console.log('🎤 Testing smart speech recognition...');
    
    if (!SpeechModule.isInitialized) {
        SpeechModule.init();
    }
    
    // Test speech recognition availability
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        console.log('✅ Speech Recognition API available');
        
        // Detailed state check including validation
        const status = {
            isAISpeaking: AppState.isAISpeaking,
            isRecording: AppState.isRecording,
            conversationMode: SpeechModule.conversationMode,
            speechIsListening: SpeechModule.isListening,
            speechInitialized: SpeechModule.isInitialized,
            currentProvider: document.getElementById('ttsProvider')?.value || 'Not selected'
        };
        
        const validation = SpeechModule.getSpeechStats();
        
        console.log('📊 Smart speech recognition state:', status);
        console.log('🎛️ Speech validation stats:', validation);
        
        // Button state check
        const micButton = document.getElementById('micButton');
        const buttonText = micButton?.textContent || 'Unknown';
        const buttonClass = micButton?.className || 'Unknown';
        
        console.log('🎛️ Button state:', { text: buttonText, class: buttonClass });
        
        alert(`🧠 Smart Speech Recognition Test:\n\n✅ Speech Recognition: Available\n\n📊 Current State:\n• Conversation Mode: ${status.conversationMode}\n• AI Speaking: ${status.isAISpeaking}\n• Recording: ${status.isRecording}\n• Actually Listening: ${status.speechIsListening}\n• TTS Provider: ${status.currentProvider}\n\n🎛️ Noise Filtering:\n• Min Confidence: ${validation.currentSettings.minConfidence}\n• Min Duration: ${validation.currentSettings.minDuration}ms\n• Noise Threshold: ${validation.currentSettings.noiseThreshold} words\n• Consecutive No-Speech: ${validation.consecutiveNoSpeech}\n\n🛠️ Anti-Loop Features:\n• Smart speech validation\n• Background noise filtering\n• Confidence thresholds\n• Duration requirements\n• Exponential backoff\n\n🎛️ Adjust sensitivity in TTS settings if needed!`);
    } else {
        console.error('❌ Speech Recognition not available');
        alert('❌ Speech Recognition not available in this browser.\n\nVoice input requires:\n• Chrome, Edge, or Safari\n• Secure connection (HTTPS or localhost)\n• Microphone permission');
    }
};

window.testInterruption = function() {
    console.log('Testing interruption...');
    alert('Interruption test functionality to be implemented');
};

// NEW: Speech sensitivity control functions
window.adjustSpeechSensitivity = function() {
    const sensitivityLevel = document.getElementById('sensitivityLevel').value;
    SpeechModule.adjustSensitivity(sensitivityLevel);
    
    const levelDescriptions = {
        'low': 'Low Sensitivity: Filters background noise, only clear speech',
        'medium': 'Medium Sensitivity: Balanced detection (recommended)',
        'high': 'High Sensitivity: Picks up quiet speech but may detect noise'
    };
    
    console.log(`🎛️ Sensitivity adjusted to: ${levelDescriptions[sensitivityLevel]}`);
};

window.showSpeechStats = function() {
    if (!SpeechModule.isInitialized) {
        alert('Speech module not initialized');
        return;
    }
    
    const stats = SpeechModule.getSpeechStats();
    const timeSinceLastSpeech = stats.timeSinceLastSpeech ? 
        Math.round(stats.timeSinceLastSpeech / 1000) : 'Never';
    
    alert(`🎤 Speech Recognition Statistics:\n\n` +
          `• Consecutive no-speech: ${stats.consecutiveNoSpeech}\n` +
          `• Time since last valid speech: ${timeSinceLastSpeech}s\n` +
          `• Min confidence: ${stats.currentSettings.minConfidence}\n` +
          `• Min duration: ${stats.currentSettings.minDuration}ms\n` +
          `• Noise threshold: ${stats.currentSettings.noiseThreshold} words\n\n` +
          `Check console for detailed logs.`);
    
    console.log('📊 Full speech recognition stats:', stats);
};

window.resetSpeechValidation = function() {
    if (SpeechModule.conversationMode) {
        SpeechModule.stopConversation();
        setTimeout(() => {
            SpeechModule.startConversation();
            console.log('🔄 Speech validation reset and conversation restarted');
        }, 1000);
    } else {
        SpeechModule.speechValidation.currentNoSpeechCount = 0;
        SpeechModule.speechValidation.speechStartTime = null;
        SpeechModule.speechValidation.lastValidSpeech = Date.now();
        console.log('🔄 Speech validation state reset');
    }
    
    alert('Speech validation reset! Try starting conversation again.');
};

window.switchProvider = async function() {
    // Check if TTS admin UI is available on this page
    const providerSelect = document.getElementById('provider_select');
    const voiceSelect = document.getElementById('voice_select');
    
    if (!providerSelect || !voiceSelect) {
        alert('Provider switching moved to Admin Settings panel.\n\nTo access advanced TTS settings:\n1. Click "Access Admin Settings" in the right sidebar\n2. Or visit /admin/settings directly');
        return;
    }
    
    const providerId = providerSelect.value;
    const voiceId = voiceSelect.value;
    
    try {
        const response = await fetch('/tts/provider', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: providerId
            })
        });
        
        if (response.ok) {
            AppState.currentProvider = providerId;
            alert('Provider switched successfully!');
        } else {
            alert('Failed to switch provider');
        }
    } catch (error) {
        console.error('Error switching provider:', error);
        alert('Error switching provider');
    }
};

// ============================================================================
// Main Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing CoCreate AI Coach...');
    
    // Make UI control functions globally available for HTML onclick handlers
    window.toggleSettingsSidebar = UIControls.toggleSettingsSidebar;
    window.toggleChatWindow = UIControls.toggleChatWindow;
    window.updateSystemPrompt = SettingsModule.updateSystemPrompt;
    window.uploadDocument = SettingsModule.uploadDocument;
    
    // 🎙️ NEW: Expose ChatModule globally for lesson templates
    window.ChatModule = ChatModule;
    
    // 🎙️ NEW: Add click handler for mic button to start conversation
    const micButton = document.getElementById('micButton');
    if (micButton) {
        micButton.addEventListener('click', () => {
            const chatContainer = document.getElementById('chatContainer');
            const isVoiceMode = !chatContainer.classList.contains('expanded');
            
            if (isVoiceMode && !SpeechModule.conversationMode) {
                console.log('🎤 Starting lesson from mic button click');
                // Initialize conversation memory if needed
                if (!AppState.conversationMemory.messages.length) {
                    ConversationMemory.init(
                        window.lessonContext?.lessonId,
                        window.currentSlideData?.index
                    );
                    ConversationMemory.setMode('voice');
                }
                SpeechModule.startConversation();
            }
        });
    }
    
    // 🎙️ NEW: Set up interrupt button
    const interruptButton = document.getElementById('interruptButton');
    if (interruptButton) {
        interruptButton.addEventListener('click', () => {
            if (AppState.isAISpeaking && AppState.currentAudioElement) {
                console.log('🛑 User interrupted AI speech');
                AppState.isInterrupted = true;  // Set interrupt flag
                AppState.currentAudioElement.pause();
                AppState.currentAudioElement.currentTime = 0;
                AppState.isAISpeaking = false;
                AppState.currentAudioElement = null;
                AppState.conversationState = 'ready';  // Reset conversation state
                UIControls.updateButtonState();
                
                // Resume conversation after interrupt if in conversation mode
                if (SpeechModule.conversationMode) {
                    // Reset interrupt flag after a short delay
                    setTimeout(() => {
                        AppState.isInterrupted = false;
                    }, 500);
                    SpeechModule.scheduleAutoRestart(300); // Very quick restart after interrupt
                }
            }
        });
    }
    
    // Initialize speech recognition
    SpeechModule.init();
    
    // Initialize speech sensitivity to medium (default)
    SpeechModule.adjustSensitivity('medium');
    
    // Initialize TTS controls
    await TTSControls.init();
    
    // Initialize chat form handler
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            ChatModule.handleChatSubmit(e);
        });
    }
    
    // Initialize enhanced settings module
    await SettingsModule.init();
    
    // Load documents (already called in SettingsModule.init, but keeping for compatibility)
    // await SettingsModule.loadDocuments();
    
    // Initialize audio on first user interaction
    document.addEventListener('click', () => {
        AudioModule.initializeAudioPlayback();
    }, { once: true });
    
    // 🎤 AUTO-START: Start voice conversation if page loads in voice mode
    const chatContainer = document.getElementById('chatContainer');
    const isVoiceMode = !chatContainer.classList.contains('expanded');
    const isLessonMode = window.lessonContext && window.lessonContext.isLessonMode;
    
    if (isVoiceMode && !isLessonMode) {
        // Only auto-start for non-lesson pages (lesson handles its own greeting)
        console.log('🎤 Page loaded in voice mode - auto-starting conversation');
        setTimeout(() => {
            SpeechModule.startConversation();
        }, 1000);
    } else if (isLessonMode) {
        console.log('🎓 Lesson mode detected - lesson will handle its own greeting');
    } else {
        console.log('📝 Page loaded in text mode');
    }
    
    console.log('✅ CoCreate AI Coach initialized successfully!');
});

// NEW: Conversation Memory Management
const ConversationMemory = {
    // Initialize conversation memory
    init(lessonId = null, currentSlide = null) {
        // Preserve existing mode if re-initializing
        const existingMode = AppState.conversationMemory?.metadata?.mode || 'text';
        const existingStartTime = AppState.conversationMemory?.metadata?.startTime || Date.now();
        const existingTotalTurns = AppState.conversationMemory?.metadata?.totalTurns || 0;
        const existingTopicsCovered = Array.from(AppState.conversationMemory?.context?.topicsCovered || []);

        AppState.conversationMemory = {
            messages: [],
            context: {
                lessonId,
                currentSlide,
                lastInteraction: AppState.conversationMemory?.context?.lastInteraction || null,
                currentTopic: AppState.conversationMemory?.context?.currentTopic || null,
                topicStartTime: AppState.conversationMemory?.context?.topicStartTime || null,
                slideContentPresented: new Set(AppState.conversationMemory?.context?.slideContentPresented || []), // Preserve slide content presented
                topicsCovered: new Set(existingTopicsCovered), // Use preserved topics covered
                userConfirmedUnderstanding: AppState.conversationMemory?.context?.userConfirmedUnderstanding || false // Preserve user confirmation
            },
            metadata: {
                startTime: existingStartTime,
                mode: existingMode,
                totalTurns: existingTotalTurns,
                topicsCovered: existingTopicsCovered // Keep as array for metadata summary if needed elsewhere
            }
        };
        console.log('🧠 Conversation memory initialized:', AppState.conversationMemory);
    },

    // Add a message to conversation memory
    addMessage(role, content) {
        // Ensure conversation memory is initialized before adding message
        if (!AppState.conversationMemory || !Array.isArray(AppState.conversationMemory.messages)) {
            console.warn('⚠️ Conversation memory not initialized when adding message. Initializing now.');
            // Attempt to re-initialize with available context
            const lessonId = window.lessonContext?.lessonId;
            const currentSlide = window.currentSlideData?.index;
            this.init(lessonId, currentSlide);
        }

        const message = {
            role,
            content,
            timestamp: Date.now()
        };
        AppState.conversationMemory.messages.push(message);
        AppState.conversationMemory.context.lastInteraction = message.timestamp;
        AppState.conversationMemory.metadata.totalTurns++;
        console.log('📝 Added message to conversation memory:', message);
    },

    // Get conversation history
    getHistory() {
        return AppState.conversationMemory.messages;
    },

    // Get recent context (last N messages)
    getRecentContext(n = 5) {
        return AppState.conversationMemory.messages.slice(-n);
    },

    // Update conversation mode
    setMode(mode) {
        AppState.conversationMemory.metadata.mode = mode;
        console.log(`🔄 Conversation mode set to: ${mode}`);
    },

    // Update slide context
    updateSlideContext(slideIndex) {
        AppState.conversationMemory.context.currentSlide = slideIndex;
        console.log(`📊 Updated slide context: ${slideIndex}`);
    },

    // Get conversation summary
    getSummary() {
        return {
            totalMessages: AppState.conversationMemory.messages.length,
            duration: Date.now() - AppState.conversationMemory.metadata.startTime,
            mode: AppState.conversationMemory.metadata.mode,
            currentSlide: AppState.conversationMemory.context.currentSlide
        };
    },

    isConfirmationOfUnderstanding(text) {
        const confirmationPhrases = [
            "yes", "yep", "yeah", "sure", "okay", "ok", "fine", "alright", "got it",
            "makes sense", "i understand", "i get it", "no questions", "no", "nope",
            "i see", "i see what you mean", "that's clear", "that makes sense",
            "i follow", "i'm following", "got that", "understood", "clear",
            "that's clear now", "i understand now", "i get it now"
        ];
        
        return confirmationPhrases.includes(text.toLowerCase().trim());
    },

    getTopicHistory() {
        return {
            currentTopic: AppState.conversationMemory.context.currentTopic,
            topicsCovered: Array.from(AppState.conversationMemory.context.topicsCovered),
            lastTransitionTime: AppState.conversationMemory.context.lastTransitionTime,
            userConfirmedUnderstanding: AppState.conversationMemory.context.userConfirmedUnderstanding
        };
    },

    clearTopicHistory() {
        AppState.topicState.currentTopic = null;
        AppState.topicState.topicStartTime = null;
        AppState.topicState.topicsCovered.clear();
        AppState.topicState.lastTransitionTime = null;
        AppState.topicState.transitionPending = false;
        AppState.topicState.userConfirmedUnderstanding = false;
        
        AppState.conversationMemory.context.currentTopic = null;
        AppState.conversationMemory.context.topicStartTime = null;
        AppState.conversationMemory.context.topicsCovered.clear();
        AppState.conversationMemory.context.lastTransitionTime = null;
        AppState.conversationMemory.context.userConfirmedUnderstanding = false;
        
        console.log('🗑️ Topic history cleared');
    }
};
