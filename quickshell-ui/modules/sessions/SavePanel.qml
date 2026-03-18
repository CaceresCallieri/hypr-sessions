import "../../components"
import "../../services"
import "../../config"
import QtQuick

Item {
    id: root

    property string savedName: ""

    Column {
        anchors.centerIn: parent
        width: parent.width - Theme.padding.large * 2
        spacing: Theme.spacing.larger

        // Icon
        MaterialIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            text: {
                const state = SessionService.operationState;
                if (SessionService.operationType !== "save") return "add_circle";
                if (state === "success") return "check_circle";
                if (state === "error") return "error";
                if (state === "executing") return "hourglass_top";
                return "add_circle";
            }
            font.pointSize: Theme.font.size.extraLarge
            fill: 1
            color: {
                const state = SessionService.operationState;
                if (SessionService.operationType !== "save") return Theme.palette.m3primary;
                if (state === "success") return Theme.palette.m3primary;
                if (state === "error") return Theme.palette.m3error;
                return Theme.palette.m3primary;
            }
        }

        // Title
        StyledText {
            anchors.horizontalCenter: parent.horizontalCenter
            font.pointSize: Theme.font.size.larger
            font.weight: Font.Medium
            color: Theme.palette.m3onSurface

            text: {
                const state = SessionService.operationState;
                if (SessionService.operationType !== "save" || state === "idle")
                    return "Save Current Session";
                if (state === "executing") return "Saving...";
                if (state === "success") return "Session saved";
                if (state === "error") return "Save failed";
                return "Save Current Session";
            }
        }

        // Input area (idle state)
        Column {
            width: parent.width
            spacing: Theme.spacing.small
            visible: SessionService.operationType !== "save" || SessionService.operationState === "idle"

            // Session name input
            ClippingRect {
                width: parent.width
                height: 40
                radius: Theme.rounding.small
                color: Theme.layer(Theme.palette.m3surfaceContainer, 1)

                TextInput {
                    id: nameInput

                    anchors.fill: parent
                    anchors.leftMargin: Theme.padding.normal
                    anchors.rightMargin: Theme.padding.normal
                    verticalAlignment: TextInput.AlignVCenter
                    clip: true

                    color: Theme.palette.m3onSurface
                    selectedTextColor: Theme.palette.m3onPrimary
                    selectionColor: Theme.palette.m3primary
                    font.family: Theme.font.family.mono
                    font.pointSize: Theme.font.size.smaller

                    Keys.onReturnPressed: _triggerSave()
                    Keys.onEnterPressed: _triggerSave()

                    // Placeholder
                    StyledText {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: !nameInput.text && !nameInput.activeFocus
                        text: "Enter session name..."
                        color: Theme.palette.m3outline
                        font.pointSize: Theme.font.size.smaller
                    }
                }
            }

            // Save button
            ClippingRect {
                width: parent.width
                height: 36
                radius: Theme.rounding.full
                color: nameInput.text.trim() ? Theme.palette.m3primary : Theme.layer(Theme.palette.m3surfaceContainerHigh, 1)

                StyledText {
                    anchors.centerIn: parent
                    text: "Save Session"
                    font.pointSize: Theme.font.size.smaller
                    font.weight: Font.Medium
                    color: nameInput.text.trim() ? Theme.palette.m3onPrimary : Theme.palette.m3outline
                }

                StateLayer {
                    disabled: !nameInput.text.trim()
                    color: Theme.palette.m3onPrimary
                    onClicked: _triggerSave()
                }
            }
        }

        // Status area (executing/success/error)
        Column {
            width: parent.width
            spacing: Theme.spacing.small
            visible: SessionService.operationType === "save" && SessionService.operationState !== "idle"

            StyledText {
                anchors.horizontalCenter: parent.horizontalCenter
                font.pointSize: Theme.font.size.smaller
                color: SessionService.operationState === "error"
                    ? Theme.palette.m3error
                    : Theme.palette.m3onSurfaceVariant

                text: {
                    const state = SessionService.operationState;
                    if (state === "executing") return "Saving workspace data...";
                    if (state === "success") return "Returning automatically...";
                    if (state === "error") return SessionService.operationError;
                    return "";
                }
            }

            // Retry/dismiss button (error state)
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
                    border.color: Theme.palette.m3outline
                }

                StyledText {
                    anchors.centerIn: parent
                    text: "Retry"
                    font.pointSize: Theme.font.size.smaller
                    color: Theme.palette.m3onSurface
                }

                StateLayer {
                    onClicked: {
                        SessionService.cancelOperation();
                        // Restore the name for retry
                        nameInput.text = root.savedName;
                    }
                }
            }
        }
    }

    // Keyboard hints
    StyledText {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        font.pointSize: Theme.font.size.small
        color: Theme.palette.m3outline
        text: "Enter save  |  Tab browse  |  Esc quit"
    }

    function _triggerSave(): void {
        const name = nameInput.text.trim();
        if (!name) return;
        root.savedName = name;
        nameInput.text = "";
        SessionService.saveSession(name);
    }

    // Focus input when panel becomes visible
    onVisibleChanged: {
        if (visible)
            nameInput.forceActiveFocus();
    }
    onFocusChanged: {
        if (focus && (SessionService.operationType !== "save" || SessionService.operationState === "idle"))
            nameInput.forceActiveFocus();
    }
}
