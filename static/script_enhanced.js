// Enhanced SettingsModule with improved initialization and error handling
// Add these methods to the existing SettingsModule or replace the existing methods

const EnhancedSettingsModule = {
    
    // Enhanced initialization function
    async init() {
        console.log('🚀 Initializing Enhanced SettingsModule...');
        
        try {
            // Load saved system prompt and apply it
            await this.loadAndApplySystemPrompt();
            
            // Load documents from server
            await this.loadDocuments();
            
            // Set up auto-refresh for documents
            this.setupAutoRefresh();
            
            // Check knowledge base status
            await this.checkKnowledgeBaseStatus();
            
            console.log('✅ Enhanced SettingsModule initialization complete');
            
        } catch (error) {
            console.error('❌ Error during SettingsModule initialization:', error);
            this.showFeedback('Error initializing settings: ' + error.message, 'error');
        }
    },

    // Load and apply saved system prompt
    // Removed this function to simplify system prompt management
    // async loadAndApplySystemPrompt() {
    //     // Prevent this from running on admin pages to avoid overwriting database settings
    //     if (window.location.pathname.startsWith('/admin')) {
    //         console.log('🤖 Skipping localStorage prompt application on admin page.');
    //         return;
    //     }

    //     try {
    //         const savedSystemPrompt = localStorage.getItem('systemPrompt') || '';
    //         
    //         if (savedSystemPrompt) {
    //             console.log(`🤖 Loading saved system prompt: ${savedSystemPrompt.length} chars`);
    //             
    //             // Set in UI
    //             const systemPromptTextarea = document.getElementById('systemPrompt');
    //             if (systemPromptTextarea) {
    //                 systemPromptTextarea.value = savedSystemPrompt;
    //             }
    //             
    //             // Apply to backend
    //             const response = await fetch('/system-prompt', {
    //                 method: 'POST',
    //                 headers: { 'Content-Type': 'application/json' },
    //                 body: JSON.stringify({ prompt: savedSystemPrompt })
    //             });
    //             
    //             if (response.ok) {
    //                 const result = await response.json();
    //                 console.log('✅ System prompt applied successfully:', result);
    //             } else {
    //                 const errorData = await response.json();
    //                 console.warn('⚠️ Failed to apply saved system prompt to backend:', errorData);
    //             }
    //         } else {
    //             console.log('📝 No saved system prompt found');
    //         }
    //     } catch (error) {
    //         console.error('❌ Error loading system prompt:', error);
    //     }
    // },

    // Enhanced updateSystemPrompt with better feedback
    async updateSystemPrompt() {
        const systemPromptTextarea = document.getElementById('systemPrompt');
        if (!systemPromptTextarea) {
            this.showFeedback('System prompt textarea not found', 'error');
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
                body: JSON.stringify({ prompt: systemPrompt })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ System prompt updated on server:', result);
                this.showFeedback(`System prompt updated! (${result.prompt_length} characters)`, 'success');
            } else {
                const errorData = await response.json();
                console.error('❌ Server error:', errorData);
                this.showFeedback('Failed to update system prompt: ' + (errorData.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('❌ Error updating system prompt:', error);
            this.showFeedback('Error updating system prompt: ' + error.message, 'error');
        }
    },

    // Enhanced loadDocuments with better error handling
    async loadDocuments() {
        try {
            console.log('📚 Loading documents from server...');
            
            const response = await fetch('/documents');
            
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
                            <strong style="color: #333; font-size: 14px;">${this.escapeHtml(docName)}</strong>
                            <button onclick="EnhancedSettingsModule.removeDocument('${this.escapeHtml(docName)}')" 
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
                
                this.showFeedback(`Loaded ${data.documents.length} documents`, 'success');
            } else {
                docList.innerHTML = '<em style="color: #666; font-style: italic;">No documents uploaded yet</em>';
                console.log('📄 No documents found');
            }
        } catch (error) {
            console.error('❌ Error loading documents:', error);
            this.showFeedback('Error loading documents: ' + error.message, 'error');
        }
    },

    // Enhanced uploadDocument with better validation and feedback
    async uploadDocument() {
        const docNameInput = document.getElementById('docName');
        const docContentTextarea = document.getElementById('docContent');
        
        if (!docNameInput || !docContentTextarea) {
            this.showFeedback('Document form elements not found', 'error');
            return;
        }
        
        const docName = docNameInput.value.trim();
        const docContent = docContentTextarea.value.trim();
        
        // Client-side validation
        if (!docName) {
            this.showFeedback('Please enter a document name', 'warning');
            docNameInput.focus();
            return;
        }
        
        if (!docContent) {
            this.showFeedback('Please enter document content', 'warning');
            docContentTextarea.focus();
            return;
        }
        
        if (docName.length > 100) {
            this.showFeedback('Document name too long (max 100 characters)', 'warning');
            return;
        }
        
        if (docContent.length > 100000) {
            this.showFeedback('Document content too long (max 100KB)', 'warning');
            return;
        }
        
        // Check for invalid characters
        const invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|'];
        if (invalidChars.some(char => docName.includes(char))) {
            this.showFeedback('Document name contains invalid characters', 'warning');
            return;
        }
        
        try {
            console.log(`📝 Uploading document: ${docName} (${docContent.length} chars)`);
            
            const formData = new FormData();
            formData.append('name', docName);
            formData.append('content', docContent);
            
            const response = await fetch('/documents', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Document uploaded:', result);
                
                this.showFeedback(`Document "${docName}" uploaded successfully! (${result.content_length} chars)`, 'success');
                
                // Clear form
                docNameInput.value = '';
                docContentTextarea.value = '';
                
                // Refresh document list
                await this.loadDocuments();
                
                // Optionally refresh knowledge base status
                await this.checkKnowledgeBaseStatus();
                
            } else {
                const errorData = await response.json();
                console.error('❌ Upload failed:', errorData);
                this.showFeedback('Failed to upload document: ' + (errorData.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('❌ Error uploading document:', error);
            this.showFeedback('Error uploading document: ' + error.message, 'error');
        }
    },

    // Enhanced removeDocument with better confirmation and feedback
    async removeDocument(docName) {
        if (!docName) {
            this.showFeedback('Invalid document name', 'error');
            return;
        }
        
        if (!confirm(`Are you sure you want to remove the document "${docName}"?\n\nThis action cannot be undone.`)) {
            return;
        }
        
        try {
            console.log(`🗑️ Removing document: ${docName}`);
            
            const response = await fetch(`/documents/${encodeURIComponent(docName)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Document removed:', result);
                
                this.showFeedback(`Document "${docName}" removed successfully!`, 'success');
                
                // Refresh document list
                await this.loadDocuments();
                
                // Optionally refresh knowledge base status
                await this.checkKnowledgeBaseStatus();
                
            } else {
                const errorData = await response.json();
                console.error('❌ Remove failed:', errorData);
                this.showFeedback('Failed to remove document: ' + (errorData.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('❌ Error removing document:', error);
            this.showFeedback('Error removing document: ' + error.message, 'error');
        }
    },

    // Check knowledge base status for debugging
    async checkKnowledgeBaseStatus() {
        try {
            const response = await fetch('/knowledge-base/status');
            
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
    },

    // Refresh knowledge base manually
    async refreshKnowledgeBase() {
        try {
            console.log('🔄 Manually refreshing knowledge base...');
            
            const response = await fetch('/knowledge-base/refresh', {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Knowledge base refreshed:', result);
                this.showFeedback(`Knowledge base refreshed! ${result.new_document_count} documents loaded.`, 'success');
                
                // Refresh the document list too
                await this.loadDocuments();
                
            } else {
                const errorData = await response.json();
                console.error('❌ Refresh failed:', errorData);
                this.showFeedback('Failed to refresh knowledge base: ' + (errorData.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('❌ Error refreshing knowledge base:', error);
            this.showFeedback('Error refreshing knowledge base: ' + error.message, 'error');
        }
    },

    // Set up auto-refresh capabilities
    setupAutoRefresh() {
        // Refresh documents every 30 seconds if the settings sidebar is open
        setInterval(() => {
            const sidebar = document.getElementById('settingsSidebar');
            if (sidebar && !sidebar.classList.contains('collapsed')) {
                this.loadDocuments();
            }
        }, 30000);
        
        console.log('⏰ Auto-refresh set up (30s interval)');
    },

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

// Enhanced initialization - add this to your existing DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Enhanced CoCreate AI Coach Initialization...');
    
    // ... your existing initialization code ...
    
    // Initialize enhanced settings module
    try {
        await EnhancedSettingsModule.init();
    } catch (error) {
        console.error('❌ Error during enhanced initialization:', error);
    }
    
    console.log('✅ Enhanced Initialization Complete!');
});

// Make the enhanced module globally available
window.EnhancedSettingsModule = EnhancedSettingsModule;

// For backward compatibility, also update the existing SettingsModule
if (typeof SettingsModule !== 'undefined') {
    Object.assign(SettingsModule, EnhancedSettingsModule);
}

// Add refresh button to HTML (you can add this manually to your template)
function addRefreshButton() {
    const docListDiv = document.getElementById('documentList');
    if (docListDiv && !document.getElementById('refreshKnowledgeBaseBtn')) {
        const refreshBtn = document.createElement('button');
        refreshBtn.id = 'refreshKnowledgeBaseBtn';
        refreshBtn.textContent = '🔄 Refresh Knowledge Base';
        refreshBtn.style.cssText = `
            margin-top: 10px;
            padding: 8px 12px;
            background-color: #17a2b8;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        `;
        refreshBtn.onclick = () => EnhancedSettingsModule.refreshKnowledgeBase();
        
        docListDiv.parentNode.insertBefore(refreshBtn, docListDiv.nextSibling);
    }
}

// Call this after DOM is loaded
setTimeout(addRefreshButton, 1000);
