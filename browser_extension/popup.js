/**
 * Popup script for Hyprland Session Manager extension
 * Provides UI for testing connection and manual operations
 */

class HyprSessionsPopup {
    constructor() {
        console.log("[Popup] HyprSessionsPopup constructor called");
        this.statusElement = document.getElementById('status');
        this.testButton = document.getElementById('test-connection');
        this.captureButton = document.getElementById('capture-tabs');
        
        console.log("[Popup] Elements found:", {
            status: this.statusElement,
            testButton: this.testButton, 
            captureButton: this.captureButton
        });
        
        this.setupEventListeners();
        this.checkConnectionStatus();
    }
    
    setupEventListeners() {
        this.testButton.addEventListener('click', () => {
            this.testConnection();
        });
        
        this.captureButton.addEventListener('click', () => {
            this.captureCurrentTabs();
        });
    }
    
    async checkConnectionStatus() {
        console.log("[Popup] Checking connection status...");
        try {
            const response = await browser.runtime.sendMessage({
                action: "get_connection_status"
            });
            
            console.log("[Popup] Connection status response:", response);
            this.updateConnectionStatus(response.connected);
        } catch (error) {
            console.error("[Popup] Error checking connection:", error);
            this.updateConnectionStatus(false);
        }
    }
    
    updateConnectionStatus(connected) {
        console.log("[Popup] Updating connection status:", connected);
        if (connected) {
            this.statusElement.textContent = "Connected to native host";
            this.statusElement.className = "status connected";
            this.captureButton.disabled = false;
            console.log("[Popup] Status updated to CONNECTED");
        } else {
            this.statusElement.textContent = "Not connected to native host";
            this.statusElement.className = "status disconnected"; 
            this.captureButton.disabled = true;
            console.log("[Popup] Status updated to DISCONNECTED");
        }
    }
    
    async testConnection() {
        console.log("[Popup] Test connection button clicked");
        this.testButton.textContent = "Testing...";
        this.testButton.disabled = true;
        
        try {
            console.log("[Popup] Sending test_native_connection message to background");
            // Send a ping via background script
            const response = await browser.runtime.sendMessage({
                action: "test_native_connection"
            });
            
            console.log("[Popup] Test connection response:", response);
            
            // Check connection status after test
            setTimeout(() => {
                console.log("[Popup] Rechecking connection status after test");
                this.checkConnectionStatus();
                this.testButton.textContent = "Test Connection";
                this.testButton.disabled = false;
            }, 1000);
            
        } catch (error) {
            console.error("[Popup] Error testing connection:", error);
            this.testButton.textContent = "Test Connection";
            this.testButton.disabled = false;
        }
    }
    
    async captureCurrentTabs() {
        this.captureButton.textContent = "Capturing...";
        this.captureButton.disabled = true;
        
        try {
            const tabs = await browser.tabs.query({currentWindow: true});
            
            console.log(`Found ${tabs.length} tabs to capture:`, tabs);
            
            // For demo purposes, just log the tabs
            // In actual use, this would be triggered by the Python script
            
            this.captureButton.textContent = `Captured ${tabs.length} tabs`;
            
            setTimeout(() => {
                this.captureButton.textContent = "Capture Current Tabs";
                this.captureButton.disabled = false;
            }, 2000);
            
        } catch (error) {
            console.error("Error capturing tabs:", error);
            this.captureButton.textContent = "Capture Current Tabs";
            this.captureButton.disabled = false;
        }
    }
}

// Initialize popup when DOM is loaded
console.log("[Popup] popup.js script loaded");

document.addEventListener('DOMContentLoaded', () => {
    console.log("[Popup] DOM loaded, initializing popup");
    new HyprSessionsPopup();
});

// Also try immediate initialization in case DOMContentLoaded already fired
if (document.readyState === 'loading') {
    console.log("[Popup] Document still loading, waiting for DOMContentLoaded");
} else {
    console.log("[Popup] Document already loaded, initializing immediately");
    new HyprSessionsPopup();
}