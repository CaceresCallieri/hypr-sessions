/**
 * Background script for Hyprland Session Manager extension
 * Handles native messaging communication with Python session manager
 */

class HyprSessionsBackground {
    constructor() {
        this.nativePort = null;
        this.isConnected = false;
        this.debug = true; // Enable debug logging
        
        this.initializeNativeMessaging();
        this.setupMessageListeners();
    }
    
    debugLog(message, data = null) {
        if (this.debug) {
            console.log(`[HyprSessions Background] ${message}`, data || '');
        }
    }
    
    initializeNativeMessaging() {
        this.debugLog("Initializing native messaging connection");
        console.log("[Background] Attempting to connect to native host: hypr_sessions_host");
        
        try {
            this.nativePort = browser.runtime.connectNative("hypr_sessions_host");
            console.log("[Background] Native port created:", this.nativePort);
            console.log("[Background] Port error on creation:", this.nativePort?.error);
            
            this.nativePort.onMessage.addListener((message) => {
                this.debugLog("Received message from native host:", message);
                console.log("[Background] Native host response:", message);
                this.handleNativeMessage(message);
            });
            
            this.nativePort.onDisconnect.addListener(() => {
                this.debugLog("Native messaging disconnected");
                console.log("[Background] Native messaging disconnected");
                console.log("[Background] Port error object:", this.nativePort?.error);
                this.isConnected = false;
                this.nativePort = null;
                
                // Log any error
                if (browser.runtime.lastError) {
                    this.debugLog("Disconnect error:", browser.runtime.lastError.message);
                    console.error("[Background] Disconnect error:", browser.runtime.lastError.message);
                }
            });
            
            this.isConnected = true;
            this.debugLog("Native messaging connection established");
            console.log("[Background] Native messaging connection established");
            
            // Send initial ping to test connection
            this.sendPing();
            
        } catch (error) {
            this.debugLog("Failed to connect to native host:", error.message);
            console.error("[Background] Failed to connect to native host:", error.message);
            this.isConnected = false;
        }
    }
    
    sendPing() {
        this.debugLog("Sending ping to native host");
        console.log("[Background] Sending ping to native host");
        this.sendToNativeHost({
            action: "ping",
            timestamp: Date.now()
        });
    }
    
    sendToNativeHost(message) {
        console.log("[Background] sendToNativeHost called with:", message);
        console.log("[Background] Connection status - isConnected:", this.isConnected, "nativePort:", this.nativePort);
        
        if (!this.isConnected || !this.nativePort) {
            this.debugLog("Cannot send message - not connected to native host");
            console.log("[Background] Cannot send - not connected");
            return false;
        }
        
        try {
            this.debugLog("Sending to native host:", message);
            console.log("[Background] Posting message to native host:", message);
            this.nativePort.postMessage(message);
            console.log("[Background] Message posted successfully");
            return true;
        } catch (error) {
            this.debugLog("Error sending message:", error.message);
            console.error("[Background] Error sending message:", error.message);
            return false;
        }
    }
    
    handleNativeMessage(message) {
        this.debugLog("Processing native message:", message);
        
        const action = message.action || "unknown";
        
        switch (action) {
            case "capture_tabs":
                this.handleCaptureRequest(message);
                break;
                
            case "restore_tabs":
                this.handleRestoreRequest(message);
                break;
                
            default:
                this.debugLog(`Received response: ${message.status || message.error || 'unknown'}`);
        }
    }
    
    async handleCaptureRequest(message) {
        this.debugLog("Handling tab capture request");
        
        try {
            // Get all tabs in current window
            const tabs = await browser.tabs.query({currentWindow: true});
            
            const tabData = tabs.map(tab => ({
                id: tab.id,
                url: tab.url,
                title: tab.title,
                active: tab.active,
                pinned: tab.pinned,
                index: tab.index
            }));
            
            this.debugLog(`Captured ${tabData.length} tabs`);
            
            // Send tab data back to native host
            this.sendToNativeHost({
                action: "tabs_captured",
                session_name: message.session_name,
                tabs: tabData,
                timestamp: Date.now()
            });
            
        } catch (error) {
            this.debugLog("Error capturing tabs:", error.message);
            this.sendToNativeHost({
                action: "capture_error",
                error: error.message
            });
        }
    }
    
    async handleRestoreRequest(message) {
        this.debugLog("Handling tab restore request");
        
        try {
            const tabsToRestore = message.tabs || [];
            
            for (const tabInfo of tabsToRestore) {
                await browser.tabs.create({
                    url: tabInfo.url,
                    pinned: tabInfo.pinned || false,
                    active: false
                });
            }
            
            this.debugLog(`Restored ${tabsToRestore.length} tabs`);
            
            this.sendToNativeHost({
                action: "tabs_restored",
                session_name: message.session_name,
                count: tabsToRestore.length
            });
            
        } catch (error) {
            this.debugLog("Error restoring tabs:", error.message);
            this.sendToNativeHost({
                action: "restore_error", 
                error: error.message
            });
        }
    }
    
    setupMessageListeners() {
        // Listen for messages from content scripts or popup
        browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.debugLog("Received runtime message:", message);
            console.log("[Background] Received runtime message:", message);
            
            if (message.action === "get_connection_status") {
                console.log("[Background] Returning connection status:", this.isConnected);
                sendResponse({connected: this.isConnected});
            }
            
            if (message.action === "test_native_connection") {
                this.debugLog("Testing native connection via popup request");
                console.log("[Background] Testing native connection, current status:", this.isConnected);
                this.sendPing();
                sendResponse({testing: true, connected: this.isConnected});
            }
            
            return true; // Keep message channel open for async response
        });
    }
}

// Initialize background script
const hyprSessions = new HyprSessionsBackground();