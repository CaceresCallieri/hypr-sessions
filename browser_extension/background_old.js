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
        this.setupKeyboardCommands();
        this.startTriggerFileWatcher();
    }
    
    debugLog(message, data = null) {
        if (this.debug) {
            console.log(`[HyprSessions Background] ${message}`, data || '');
        }
    }
    
    async setupKeyboardCommands() {
        this.debugLog("Setting up keyboard commands");
        console.log("[Background] Setting up keyboard commands");
        
        // Check if commands API is available
        if (!browser.commands) {
            console.error("[Background] browser.commands API not available");
            return;
        }
        
        console.log("[Background] browser.commands API is available");
        
        // Try to get all registered commands to verify our command exists
        try {
            const commands = await browser.commands.getAll();
            console.log("[Background] All registered commands:", commands);
            
            const captureCommand = commands.find(cmd => cmd.name === "capture-tabs");
            if (captureCommand) {
                console.log("[Background] Found capture-tabs command:", captureCommand);
                console.log("[Background] Command shortcut:", captureCommand.shortcut);
            } else {
                console.error("[Background] capture-tabs command NOT found in registered commands");
            }
        } catch (error) {
            console.error("[Background] Error getting commands:", error);
        }
        
        // Listen for keyboard shortcuts
        browser.commands.onCommand.addListener((command) => {
            console.log("[Background] *** KEYBOARD COMMAND RECEIVED ***:", command);
            console.log("[Background] Command type:", typeof command);
            console.log("[Background] Command length:", command.length);
            this.debugLog(`Keyboard command received: ${command}`);
            
            if (command === "capture-tabs") {
                console.log("[Background] *** ALT+U DETECTED - CAPTURING TABS! ***");
                this.debugLog("Capture tabs shortcut activated!");
                this.captureCurrentWindowTabs();
            } else {
                console.log("[Background] Unknown command received:", command);
            }
        });
        
        console.log("[Background] Keyboard command listener registered successfully");
        
        // Add a test to verify the listener is working
        setTimeout(() => {
            console.log("[Background] Keyboard command setup completed - listener should be active");
        }, 1000);
    }
    
    async captureCurrentWindowTabs() {
        console.log("[Background] === KEYBOARD SHORTCUT TAB CAPTURE STARTED ===");
        this.debugLog("Starting keyboard shortcut tab capture");
        
        try {
            // Get all tabs in current window
            const tabs = await browser.tabs.query({currentWindow: true});
            console.log("[Background] Raw tabs data:", tabs);
            
            console.log(`[Background] Found ${tabs.length} tabs in current window:`);
            
            // Log each tab with detailed information
            tabs.forEach((tab, index) => {
                console.log(`[Background] Tab ${index + 1}:`, {
                    id: tab.id,
                    url: tab.url,
                    title: tab.title,
                    active: tab.active,
                    pinned: tab.pinned,
                    index: tab.index,
                    windowId: tab.windowId
                });
            });
            
            // Create structured tab data
            const tabData = tabs.map(tab => ({
                id: tab.id,
                url: tab.url,
                title: tab.title,
                active: tab.active,
                pinned: tab.pinned,
                index: tab.index,
                windowId: tab.windowId
            }));
            
            console.log("[Background] Structured tab data:", tabData);
            console.log("[Background] === KEYBOARD SHORTCUT TAB CAPTURE COMPLETED ===");
            
            this.debugLog(`Successfully captured ${tabData.length} tabs via keyboard shortcut`);
            
            return tabData;
            
        } catch (error) {
            console.error("[Background] Error capturing tabs via keyboard shortcut:", error);
            this.debugLog("Error in keyboard shortcut tab capture:", error.message);
            return [];
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
            
            // Create tab session data
            const tabSessionData = {
                session_name: message.session_name,
                timestamp: Date.now(),
                tabs: tabData,
                browser_type: "zen"
            };
            
            // Save tab data to downloads folder (accessible to extensions)
            const filename = `${message.session_name}-tabs.json`;
            const blob = new Blob([JSON.stringify(tabSessionData, null, 2)], {
                type: 'application/json'
            });
            
            // Use downloads API to save file
            const url = URL.createObjectURL(blob);
            await browser.downloads.download({
                url: url,
                filename: filename,
                saveAs: false
            });
            
            this.debugLog(`Tab data saved to: ${filename}`);
            
            // Send confirmation back to native host
            this.sendToNativeHost({
                action: "tabs_captured",
                session_name: message.session_name,
                tabs: tabData,
                filename: filename,
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
    
    startTriggerFileWatcher() {
        this.debugLog("Starting trigger file watcher");
        
        // Poll for trigger files every 2 seconds
        setInterval(() => {
            this.checkForTriggerFiles();
        }, 2000);
    }
    
    async checkForTriggerFiles() {
        try {
            // Get all downloads to check for trigger files
            const downloads = await browser.downloads.search({
                filename: ".hypr-capture-*.trigger",
                exists: true
            });
            
            for (const download of downloads) {
                if (download.filename.includes('.hypr-capture-') && download.filename.endsWith('.trigger')) {
                    this.debugLog(`Found trigger file: ${download.filename}`);
                    await this.processTriggerFile(download);
                }
            }
        } catch (error) {
            // Silently ignore errors - downloads API might not find pattern matches
        }
    }
    
    async processTriggerFile(download) {
        try {
            // Extract session name from filename
            const filename = download.filename;
            const match = filename.match(/\.hypr-capture-(.+)\.trigger$/);
            if (!match) return;
            
            const sessionName = match[1];
            this.debugLog(`Processing trigger for session: ${sessionName}`);
            
            // Capture tabs for this session
            await this.handleCaptureRequest({
                session_name: sessionName,
                action: "capture_tabs"
            });
            
            // Remove the trigger file
            await browser.downloads.removeFile(download.id);
            this.debugLog(`Cleaned up trigger file: ${filename}`);
            
        } catch (error) {
            this.debugLog(`Error processing trigger file: ${error.message}`);
        }
    }
}

// Initialize background script with debugging
console.log("[Background] *** INITIALIZING HYPR SESSIONS EXTENSION ***");
console.log("[Background] Browser API available:", typeof browser !== 'undefined');
console.log("[Background] Commands API available:", typeof browser?.commands !== 'undefined');

const hyprSessions = new HyprSessionsBackground();

console.log("[Background] *** EXTENSION INITIALIZATION COMPLETE ***");