pragma Singleton

import "../config"
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: root

    // === Session data ===
    property var sessions: []
    property var archivedSessions: []

    // === UI state ===
    property bool saveMode: false
    property bool archiveMode: false
    property string searchQuery: ""
    property string selectedSession: ""

    // === Operation state ===
    // operationState: "idle" | "confirming" | "executing" | "success" | "error"
    // operationType: "" | "restore" | "delete" | "recover" | "save"
    property string operationState: "idle"
    property string operationType: ""
    property string operationError: ""

    // === Computed: filtered sessions ===
    readonly property var filteredSessions: {
        const source = root.archiveMode ? root.archivedSessions : root.sessions;
        if (root.searchQuery === "")
            return source;
        const query = root.searchQuery.toLowerCase();
        return source.filter(name => name.toLowerCase().includes(query));
    }

    // === Navigation ===
    function selectNext(): void {
        const list = root.filteredSessions;
        if (list.length === 0) return;
        const idx = list.indexOf(root.selectedSession);
        root.selectedSession = list[(idx + 1) % list.length];
    }

    function selectPrevious(): void {
        const list = root.filteredSessions;
        if (list.length === 0) return;
        const idx = list.indexOf(root.selectedSession);
        root.selectedSession = list[(idx - 1 + list.length) % list.length];
    }

    function ensureValidSelection(): void {
        const list = root.filteredSessions;
        if (list.length === 0) {
            root.selectedSession = "";
            return;
        }
        if (list.indexOf(root.selectedSession) === -1)
            root.selectedSession = list[0];
    }

    // === Operation management ===
    function requestOperation(type: string): void {
        if (root.operationState !== "idle") return;
        if (root.selectedSession === "") return;
        root.operationType = type;
        root.operationState = "confirming";
    }

    function confirmOperation(): void {
        if (root.operationState !== "confirming") return;
        root.operationState = "executing";
        _executeOperation();
    }

    function cancelOperation(): void {
        root.operationState = "idle";
        root.operationType = "";
        root.operationError = "";
    }

    // === Backend communication ===
    function loadSessions(): void {
        _listProc.running = true;
    }

    function saveSession(name: string): void {
        root.operationType = "save";
        root.operationState = "executing";
        _saveProc.command = [Paths.cli, "save", name, "--json"];
        _saveProc.running = true;
    }

    // --- Internal ---

    function _executeOperation(): void {
        const session = root.selectedSession;
        const type = root.operationType;
        let cmd;

        if (type === "restore")
            cmd = [Paths.cli, "restore", session, "--json"];
        else if (type === "delete")
            cmd = [Paths.cli, "delete", session, "--json"];
        else if (type === "recover")
            cmd = [Paths.cli, "recover", session, "--json"];
        else
            return;

        _opProc.command = cmd;
        _opProc.running = true;
    }

    function _handleOperationResult(text: string, exitCode: int): void {
        try {
            const result = JSON.parse(text);
            if (result.success) {
                root.operationState = "success";
                _successTimer.restart();
                // Reload sessions after successful operation
                root.loadSessions();
            } else {
                root.operationError = result.messages?.[0]?.message ?? "Operation failed";
                root.operationState = "error";
            }
        } catch (e) {
            root.operationError = "Failed to parse backend response";
            root.operationState = "error";
        }
    }

    function _handleListResult(text: string, exitCode: int): void {
        try {
            const result = JSON.parse(text);
            if (result.success && result.data) {
                root.sessions = (result.data.active_sessions ?? []).map(s => s.name ?? s);
                root.archivedSessions = (result.data.archived_sessions ?? []).map(s => s.name ?? s);
                root.ensureValidSelection();
                console.log("SessionService: loaded", root.sessions.length, "active,",
                           root.archivedSessions.length, "archived sessions");
            } else {
                console.warn("SessionService: list failed:", result.messages?.[0]?.message);
            }
        } catch (e) {
            console.warn("SessionService: failed to parse list response:", e);
        }
    }

    function _handleSaveResult(text: string, exitCode: int): void {
        try {
            const result = JSON.parse(text);
            if (result.success) {
                root.operationState = "success";
                _successTimer.restart();
                root.loadSessions();
            } else {
                root.operationError = result.messages?.[0]?.message ?? "Save failed";
                root.operationState = "error";
            }
        } catch (e) {
            root.operationError = "Failed to parse backend response";
            root.operationState = "error";
        }
    }

    // === Processes ===

    // List sessions
    Process {
        id: _listProc
        command: [Paths.cli, "list", "--all", "--json"]
        stdout: StdioCollector {
            onStreamFinished: root._handleListResult(text, _listProc.exitCode)
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0)
                console.warn("SessionService: list command exited with", exitCode);
        }
    }

    // Operation execution (restore/delete/recover)
    Process {
        id: _opProc
        stdout: StdioCollector {
            onStreamFinished: root._handleOperationResult(text, _opProc.exitCode)
        }
    }

    // Save session
    Process {
        id: _saveProc
        stdout: StdioCollector {
            onStreamFinished: root._handleSaveResult(text, _saveProc.exitCode)
        }
    }

    // Auto-return timer after success
    Timer {
        id: _successTimer
        interval: Config.sessions.successAutoReturnMs
        onTriggered: root.cancelOperation()
    }

    // Operation timeout
    Timer {
        id: _timeoutTimer
        interval: Config.sessions.operationTimeoutMs
        running: root.operationState === "executing"
        onTriggered: {
            root.operationError = "Operation timed out";
            root.operationState = "error";
        }
    }

    // Load sessions on startup
    Component.onCompleted: root.loadSessions()
}
