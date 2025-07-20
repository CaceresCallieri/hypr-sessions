/**
 * Content script for Hyprland Session Manager extension
 * Handles page-specific data capture (scroll position, form data, etc.)
 */

class HyprSessionsContent {
    constructor() {
        this.debug = true;
        this.setupMessageListener();
    }
    
    debugLog(message, data = null) {
        if (this.debug) {
            console.log(`[HyprSessions Content] ${message}`, data || '');
        }
    }
    
    setupMessageListener() {
        // Listen for messages from background script
        browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.debugLog("Received message:", message);
            
            if (message.action === "capture_page_state") {
                const pageState = this.capturePageState();
                sendResponse(pageState);
            }
            
            if (message.action === "restore_page_state") {
                this.restorePageState(message.state);
                sendResponse({success: true});
            }
            
            return true; // Keep message channel open
        });
        
        this.debugLog("Content script initialized for:", window.location.href);
    }
    
    capturePageState() {
        this.debugLog("Capturing page state");
        
        const state = {
            url: window.location.href,
            title: document.title,
            scrollX: window.scrollX,
            scrollY: window.scrollY,
            timestamp: Date.now()
        };
        
        // Capture form data if present
        const forms = document.querySelectorAll('form');
        if (forms.length > 0) {
            state.forms = this.captureFormData(forms);
        }
        
        this.debugLog("Captured page state:", state);
        return state;
    }
    
    captureFormData(forms) {
        const formData = [];
        
        forms.forEach((form, index) => {
            const inputs = form.querySelectorAll('input, textarea, select');
            const formInputs = [];
            
            inputs.forEach(input => {
                // Only capture non-sensitive form data
                if (input.type !== 'password' && input.type !== 'hidden') {
                    formInputs.push({
                        name: input.name,
                        id: input.id,
                        type: input.type,
                        value: input.value,
                        checked: input.checked
                    });
                }
            });
            
            if (formInputs.length > 0) {
                formData.push({
                    index: index,
                    action: form.action,
                    method: form.method,
                    inputs: formInputs
                });
            }
        });
        
        return formData;
    }
    
    restorePageState(state) {
        this.debugLog("Restoring page state:", state);
        
        // Restore scroll position
        if (state.scrollX !== undefined && state.scrollY !== undefined) {
            window.scrollTo(state.scrollX, state.scrollY);
        }
        
        // Restore form data
        if (state.forms) {
            this.restoreFormData(state.forms);
        }
    }
    
    restoreFormData(formData) {
        const forms = document.querySelectorAll('form');
        
        formData.forEach(savedForm => {
            const form = forms[savedForm.index];
            if (!form) return;
            
            savedForm.inputs.forEach(savedInput => {
                let input = null;
                
                // Try to find input by name first, then by id
                if (savedInput.name) {
                    input = form.querySelector(`[name="${savedInput.name}"]`);
                } else if (savedInput.id) {
                    input = form.querySelector(`#${savedInput.id}`);
                }
                
                if (input && input.type === savedInput.type) {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = savedInput.checked;
                    } else {
                        input.value = savedInput.value;
                    }
                }
            });
        });
    }
}

// Initialize content script
const hyprSessionsContent = new HyprSessionsContent();