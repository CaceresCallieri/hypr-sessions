import "../../components"
import "../../services"
import QtQuick

// Overlay that appears on top of BrowsePanel during operations
ClippingRect {
    id: root

    radius: Theme.rounding.small
    color: Theme.matte(Theme.palette.m3surfaceContainer, 0.2).background

    // Operation configuration
    readonly property var opConfig: {
        const configs = {
            "restore": {
                icon: "play_arrow",
                confirmText: "Restore",
                executingText: "Restoring...",
                successText: "Session restored",
                color: Theme.palette.m3primary
            },
            "delete": {
                icon: "delete",
                confirmText: "Archive",
                executingText: "Archiving...",
                successText: "Session archived",
                color: Theme.palette.m3error
            },
            "recover": {
                icon: "restore",
                confirmText: "Recover",
                executingText: "Recovering...",
                successText: "Session recovered",
                color: Theme.palette.m3primary
            }
        };
        return configs[SessionService.operationType] ?? {
            icon: "", confirmText: "", executingText: "", successText: "", color: "transparent"
        };
    }

    Column {
        anchors.centerIn: parent
        spacing: Theme.spacing.larger
        width: parent.width - Theme.padding.large * 2

        // Icon
        MaterialIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.opConfig.icon
            font.pointSize: Theme.font.size.extraLarge
            fill: 1
            color: root.opConfig.color
        }

        // State-dependent content
        Column {
            width: parent.width
            spacing: Theme.spacing.small

            // Title
            StyledText {
                anchors.horizontalCenter: parent.horizontalCenter
                font.pointSize: Theme.font.size.larger
                font.weight: Font.Medium
                color: Theme.palette.m3onSurface

                text: {
                    const state = SessionService.operationState;
                    if (state === "confirming")
                        return root.opConfig.confirmText + " \"" + SessionService.selectedSession + "\"?";
                    if (state === "executing")
                        return root.opConfig.executingText;
                    if (state === "success")
                        return root.opConfig.successText;
                    if (state === "error")
                        return "Operation failed";
                    return "";
                }
            }

            // Subtitle / error message
            StyledText {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: text !== ""
                font.pointSize: Theme.font.size.smaller
                color: SessionService.operationState === "error"
                    ? Theme.palette.m3error
                    : Theme.palette.m3onSurfaceVariant

                text: {
                    const state = SessionService.operationState;
                    if (state === "confirming")
                        return "Press Enter to confirm, Esc to cancel";
                    if (state === "executing")
                        return "Please wait...";
                    if (state === "error")
                        return SessionService.operationError;
                    if (state === "success")
                        return "Returning automatically...";
                    return "";
                }
            }
        }

        // Action buttons (confirming state only)
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Theme.spacing.normal
            visible: SessionService.operationState === "confirming"

            // Cancel button
            ClippingRect {
                width: 90
                height: 34
                radius: Theme.rounding.full
                color: "transparent"

                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    radius: Theme.rounding.full
                    border.width: 1
                    border.color: Qt.alpha("#ffffff", Theme.matteConstants.borderOpacity)
                }

                StyledText {
                    anchors.centerIn: parent
                    text: "Cancel"
                    font.pointSize: Theme.font.size.smaller
                    color: Theme.palette.m3onSurface
                }

                StateLayer {
                    onClicked: SessionService.cancelOperation()
                }
            }

            // Confirm button
            ClippingRect {
                width: 90
                height: 34
                radius: Theme.rounding.full
                color: root.opConfig.color

                StyledText {
                    anchors.centerIn: parent
                    text: root.opConfig.confirmText
                    font.pointSize: Theme.font.size.smaller
                    font.weight: Font.Medium
                    color: SessionService.operationType === "delete"
                        ? Theme.palette.m3onSurface
                        : Theme.palette.m3onPrimary
                }

                StateLayer {
                    color: Theme.palette.m3onPrimary
                    onClicked: SessionService.confirmOperation()
                }
            }
        }

        // Retry button (error state only)
        ClippingRect {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: SessionService.operationState === "error"
            width: 90
            height: 34
            radius: Theme.rounding.full
            color: "transparent"

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                radius: Theme.rounding.full
                border.width: 1
                border.color: Qt.alpha("#ffffff", Theme.matteConstants.borderOpacity)
            }

            StyledText {
                anchors.centerIn: parent
                text: "Dismiss"
                font.pointSize: Theme.font.size.smaller
                color: Theme.palette.m3onSurface
            }

            StateLayer {
                onClicked: SessionService.cancelOperation()
            }
        }

        // Loading spinner (executing state)
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: SessionService.operationState === "executing"
            width: 24
            height: 24

            Rectangle {
                anchors.centerIn: parent
                width: 24
                height: 24
                radius: 12
                color: "transparent"
                border.width: 2
                border.color: root.opConfig.color

                RotationAnimation on rotation {
                    from: 0
                    to: 360
                    duration: 1000
                    loops: Animation.Infinite
                }

                // Partial arc effect
                Rectangle {
                    width: 12
                    height: 12
                    color: Theme.layer(Theme.palette.m3surfaceContainer, 1)
                    anchors.right: parent.right
                    anchors.top: parent.top
                }
            }
        }
    }
}
