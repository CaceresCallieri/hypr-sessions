import "../../components"
import "../../services"
import "../../config"
import QtQuick

Item {
    id: root

    // Search bar at top
    SearchBar {
        id: searchBar

        width: parent.width

        textInput.Keys.forwardTo: [keyHandler]
    }

    // Session list
    ListView {
        id: sessionList

        anchors.top: searchBar.bottom
        anchors.topMargin: Theme.spacing.small
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: keyboardHints.top
        anchors.bottomMargin: Theme.spacing.small

        model: SessionService.filteredSessions
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        highlightMoveDuration: 150

        // Sync selection with service
        currentIndex: SessionService.filteredSessions.indexOf(SessionService.selectedSession)
        onCurrentIndexChanged: {
            if (currentIndex >= 0 && currentIndex < count)
                SessionService.selectedSession = SessionService.filteredSessions[currentIndex];
        }

        delegate: SessionItem {
            required property string modelData
            width: sessionList.width
            sessionName: modelData
            isSelected: modelData === SessionService.selectedSession
        }

        // Empty state
        StyledText {
            anchors.centerIn: parent
            visible: sessionList.count === 0
            text: SessionService.searchQuery
                ? "No sessions match \"" + SessionService.searchQuery + "\""
                : (SessionService.archiveMode ? "No archived sessions" : "No sessions saved")
            color: Theme.palette.m3onSurfaceVariant
            font.pointSize: Theme.font.size.smaller
        }

        // Scroll wheel support
        WheelHandler {
            onWheel: event => {
                if (event.angleDelta.y > 0)
                    SessionService.selectPrevious();
                else if (event.angleDelta.y < 0)
                    SessionService.selectNext();
            }
        }
    }

    // Keyboard hints
    StyledText {
        id: keyboardHints

        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        font.pointSize: Theme.font.size.small
        color: Theme.palette.m3outline

        text: {
            if (SessionService.operationState !== "idle")
                return "Enter confirm  |  Esc cancel";
            const base = "Up/Down navigate  |  Enter restore  |  d delete";
            const archiveHint = SessionService.archiveMode
                ? "  |  Enter recover" : "";
            const extra = "  |  Ctrl+A archive  |  Ctrl+L clear";
            return base + archiveHint + extra;
        }
    }

    // Confirmation modal overlay
    ConfirmationModal {
        anchors.fill: parent
        visible: SessionService.operationState !== "idle"
    }

    // Keyboard handler — receives forwarded keys from SearchBar
    Item {
        id: keyHandler

        Keys.onPressed: event => {
            const hasCtrl = event.modifiers & Qt.ControlModifier;

            // Navigation
            if (event.key === Qt.Key_Up) {
                SessionService.selectPrevious();
                event.accepted = true;
            } else if (event.key === Qt.Key_Down) {
                SessionService.selectNext();
                event.accepted = true;
            }
            // Operations
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                if (SessionService.operationState === "confirming") {
                    SessionService.confirmOperation();
                } else if (SessionService.selectedSession) {
                    const type = SessionService.archiveMode ? "recover" : "restore";
                    SessionService.requestOperation(type);
                }
                event.accepted = true;
            } else if (event.key === Qt.Key_D && !hasCtrl) {
                if (SessionService.selectedSession && SessionService.operationState === "idle")
                    SessionService.requestOperation("delete");
                event.accepted = true;
            }
            // Ctrl shortcuts
            else if (hasCtrl) {
                if (event.key === Qt.Key_A) {
                    SessionService.archiveMode = !SessionService.archiveMode;
                    SessionService.ensureValidSelection();
                    event.accepted = true;
                } else if (event.key === Qt.Key_D) {
                    if (SessionService.selectedSession && SessionService.operationState === "idle")
                        SessionService.requestOperation("delete");
                    event.accepted = true;
                } else if (event.key === Qt.Key_L) {
                    SessionService.searchQuery = "";
                    searchBar.textInput.text = "";
                    event.accepted = true;
                }
            }
        }
    }

    // Keep search input focused
    onVisibleChanged: {
        if (visible)
            searchBar.textInput.forceActiveFocus();
    }
    onFocusChanged: {
        if (focus)
            searchBar.textInput.forceActiveFocus();
    }
}
