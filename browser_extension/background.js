/**
 * Clean Background script for Hyprland Session Manager extension
 * Focused solely on keyboard shortcut tab capture
 */

class HyprSessionsKeyboard {
	constructor() {
		this.debug = true;
		this.setupKeyboardCommands();
		this.debugLog("Hypr Sessions extension initialized (keyboard-only mode)");
	}

	debugLog(message, data = null) {
		if (this.debug) {
			const timestamp = new Date().toLocaleTimeString();
			console.log(`[${timestamp}] [HyprSessions] ${message}`, data || "");
		}
	}

	async setupKeyboardCommands() {
		this.debugLog("Setting up keyboard commands");

		if (!browser.commands) {
			console.error("[HyprSessions] Commands API not available");
			return;
		}

		// Register keyboard shortcut listener
		browser.commands.onCommand.addListener((command) => {
			this.debugLog(`Keyboard command received: ${command}`);

			if (command === "capture-tabs") {
				this.debugLog("Alt+U pressed - capturing current window tabs!");
				this.captureCurrentWindowTabs();
			}
		});

		// Verify command registration
		try {
			const commands = await browser.commands.getAll();
			const captureCommand = commands.find((cmd) => cmd.name === "capture-tabs");

			if (captureCommand) {
				this.debugLog(`Capture command registered: ${captureCommand.shortcut}`);
			} else {
				console.error("[HyprSessions] Capture command not found!");
			}
		} catch (error) {
			console.error("[HyprSessions] Error checking commands:", error);
		}

		this.debugLog("Keyboard commands setup complete");
	}

	async captureCurrentWindowTabs() {
		this.debugLog("=== TAB CAPTURE STARTED ===");

		try {
			// Get tabs from current window only
			const tabs = await browser.tabs.query({ currentWindow: true });
			this.debugLog(`Found ${tabs.length} tabs in current window`);

			// Extract clean tab data
			const tabData = tabs.map((tab, index) => {
				const cleanTab = {
					id: tab.id,
					url: tab.url,
					title: tab.title,
					active: tab.active,
					pinned: tab.pinned,
					index: tab.index,
					windowId: tab.windowId,
				};

				this.debugLog(`Tab ${index + 1}: ${cleanTab.title}`, cleanTab);
				return cleanTab;
			});

			// Create session data structure
			const sessionData = {
				timestamp: Date.now(),
				windowId: tabData[0]?.windowId || 0,
				tabCount: tabData.length,
				tabs: tabData,
				captureMethod: "keyboard_shortcut",
				keyboardShortcut: "Alt+U",
			};

			this.debugLog("Structured session data:", sessionData);

			// Save to downloads folder for hypr-sessions script to find
			await this.saveTabsFile(sessionData);

			this.debugLog("=== TAB CAPTURE COMPLETED ===");
			return sessionData;
		} catch (error) {
			console.error("[HyprSessions] Tab capture failed:", error);
			this.debugLog("Tab capture error:", error.message);
			return null;
		}
	}

	async saveTabsFile(sessionData) {
		try {
			// Create filename with timestamp for uniqueness
			const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
			const filename = `hypr-session-tabs-${timestamp}.json`;

			// Create downloadable blob
			const blob = new Blob([JSON.stringify(sessionData, null, 2)], {
				type: "application/json",
			});

			const url = URL.createObjectURL(blob);

			// Download file to Downloads folder
			await browser.downloads.download({
				url: url,
				filename: filename,
				saveAs: false,
			});

			this.debugLog(`Tab data saved to: ${filename}`);

			// Clean up blob URL
			URL.revokeObjectURL(url);
		} catch (error) {
			console.error("[HyprSessions] Failed to save tabs file:", error);
			throw error;
		}
	}
}

// Initialize clean extension
console.log("[HyprSessions] *** INITIALIZING CLEAN EXTENSION ***");
const hyprSessions = new HyprSessionsKeyboard();
console.log("[HyprSessions] *** EXTENSION READY ***");

