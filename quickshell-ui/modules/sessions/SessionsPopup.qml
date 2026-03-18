import "../../components"
import "../../services"
import "../../config"
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import QtQuick

PanelWindow {
    id: win

    color: "transparent"

    WlrLayershell.namespace: "sessions-ui"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.exclusionMode: ExclusionMode.Ignore
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

    anchors.top: true
    anchors.bottom: true
    anchors.left: true
    anchors.right: true

    HyprlandFocusGrab {
        active: true
        windows: [win]
        onCleared: Qt.quit()
    }

    // Root focus scope — handles global keys since PanelWindow is not an Item
    FocusScope {
        id: rootScope

        anchors.fill: parent
        focus: true

        // Dark scrim background — click to dismiss
        MouseArea {
            anchors.fill: parent
            onClicked: Qt.quit()

            StyledRect {
                anchors.fill: parent
                color: Qt.alpha(Theme.palette.m3shadow, 0.5)
            }
        }

        // Centered content card
        ClippingRect {
            id: card

            anchors.centerIn: parent
            width: Config.sessions.cardWidth
            height: Config.sessions.cardHeight
            radius: Theme.rounding.large
            color: Theme.layer(Theme.palette.m3surfaceContainerLow, 0)

            // Subtle border
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                radius: card.radius
                border.width: 1
                border.color: Qt.alpha(Theme.palette.m3outlineVariant, 0.3)
            }

            // Stop clicks on card from dismissing
            MouseArea {
                anchors.fill: parent
            }

            Column {
                anchors.fill: parent
                anchors.margins: Theme.padding.large

                // Header
                Row {
                    width: parent.width
                    spacing: Theme.spacing.normal

                    Column {
                        width: parent.width - toggleSwitch.width - parent.spacing

                        StyledText {
                            text: "Session Manager"
                            font.pointSize: Theme.font.size.large
                            font.weight: Font.Medium
                            color: Theme.palette.m3onSurface
                        }

                        StyledText {
                            text: {
                                const mode = SessionService.archiveMode ? "Archived" : "Active";
                                const count = SessionService.filteredSessions.length;
                                return mode + " Sessions (" + count + ")";
                            }
                            font.pointSize: Theme.font.size.small
                            color: Theme.palette.m3onSurfaceVariant
                        }
                    }

                    ToggleSwitch {
                        id: toggleSwitch
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Spacer
                Item { width: 1; height: Theme.spacing.normal }

                // Panel content area
                Item {
                    width: parent.width
                    height: parent.height - y

                    BrowsePanel {
                        anchors.fill: parent
                        visible: !SessionService.saveMode
                        focus: !SessionService.saveMode
                    }

                    SavePanel {
                        anchors.fill: parent
                        visible: SessionService.saveMode
                        focus: SessionService.saveMode
                    }
                }
            }
        }

        // Global keyboard shortcuts
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Escape) {
                if (SessionService.operationState !== "idle") {
                    SessionService.cancelOperation();
                    event.accepted = true;
                    return;
                }
                if (SessionService.searchQuery !== "") {
                    SessionService.searchQuery = "";
                    event.accepted = true;
                    return;
                }
                Qt.quit();
                event.accepted = true;
            } else if (event.key === Qt.Key_Q && event.modifiers & Qt.ControlModifier) {
                Qt.quit();
                event.accepted = true;
            } else if (event.key === Qt.Key_Tab) {
                SessionService.saveMode = !SessionService.saveMode;
                event.accepted = true;
            } else if (event.key === Qt.Key_Left && SessionService.saveMode) {
                SessionService.saveMode = false;
                event.accepted = true;
            } else if (event.key === Qt.Key_Right && !SessionService.saveMode) {
                SessionService.saveMode = true;
                event.accepted = true;
            }
        }
    }
}
