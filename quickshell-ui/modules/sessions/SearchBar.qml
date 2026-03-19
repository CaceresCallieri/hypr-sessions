import "../../components"
import "../../services"
import QtQuick

ClippingRect {
    id: root

    property alias textInput: input

    function clear(): void {
        input.text = "";
    }

    height: 36
    radius: Theme.rounding.small
    color: Theme.matte(Theme.palette.m3surfaceContainer, 0.4).background

    Row {
        anchors.fill: parent
        anchors.leftMargin: Theme.padding.normal
        anchors.rightMargin: Theme.padding.normal
        spacing: Theme.spacing.small

        MaterialIcon {
            anchors.verticalCenter: parent.verticalCenter
            text: "search"
            font.pointSize: Theme.font.size.normal
            color: Theme.palette.m3onSurfaceVariant
        }

        TextInput {
            id: input

            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - parent.spacing - 24 // icon width
            clip: true

            color: Theme.palette.m3onSurface
            selectedTextColor: Theme.palette.m3onPrimary
            selectionColor: Theme.palette.m3primary
            font.family: Theme.font.family.sans
            font.pointSize: Theme.font.size.smaller

            onTextChanged: SessionService.searchQuery = text

            // Placeholder
            StyledText {
                anchors.verticalCenter: parent.verticalCenter
                visible: !input.text && !input.activeFocus
                text: "Search sessions..."
                color: Theme.palette.m3outline
                font.pointSize: Theme.font.size.smaller
            }
        }
    }
}
