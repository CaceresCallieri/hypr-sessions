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
    width: Config.sessions.cardWidth
    height: Config.sessions.cardHeight

    WlrLayershell.namespace: "sessions-ui"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.exclusionMode: ExclusionMode.Ignore
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

    HyprlandFocusGrab {
        active: true
        windows: [win]
        onCleared: win.close()
    }

    // Pop-in/pop-out state — drives card opacity and scale
    property bool showing: false

    function close() {
        if (!win.showing) return;
        win.showing = false;
    }

    // Root focus scope — handles global keys since PanelWindow is not an Item
    FocusScope {
        id: rootScope

        anchors.fill: parent
        focus: true

        // Content card fills the window (window IS the card now)
        ClippingRect {
            id: card

            readonly property var surface: Theme.matte(Theme.palette.m3surfaceContainerLow, 0.0)

            anchors.fill: parent
            radius: Theme.rounding.large
            color: card.surface.background

            // Pop-in/pop-out animation (matches Hyprland popin style)
            opacity: win.showing ? 1 : 0
            scale: win.showing ? 1 : 0.3
            transformOrigin: Item.Center

            Behavior on opacity {
                NumberAnimation {
                    duration: Theme.animDuration * 0.8
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.animCurveStandardDecel
                }
            }

            Behavior on scale {
                NumberAnimation {
                    id: scaleAnim
                    duration: Theme.animDuration * 0.8
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.animCurveOvershoot
                }
            }

            Component.onCompleted: win.showing = true

            // Quit after the close animation finishes
            Connections {
                target: scaleAnim
                function onRunningChanged() {
                    if (!scaleAnim.running && !win.showing)
                        Qt.quit();
                }
            }

            // Matte hairline border
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                radius: card.radius
                border.width: 1
                border.color: card.surface.border
            }

            Column {
                anchors.fill: parent
                anchors.margins: Theme.spacing.large

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
                win.close();
                event.accepted = true;
            } else if (event.key === Qt.Key_Q && event.modifiers & Qt.ControlModifier) {
                win.close();
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
