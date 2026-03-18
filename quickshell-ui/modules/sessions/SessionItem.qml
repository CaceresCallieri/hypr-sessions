import "../../components"
import "../../services"
import QtQuick

ClippingRect {
    id: root

    required property string sessionName
    required property bool isSelected

    height: 40
    radius: Theme.rounding.small
    color: isSelected ? Theme.layer(Theme.palette.m3secondaryContainer, 1) : "transparent"

    Row {
        anchors.fill: parent
        anchors.leftMargin: Theme.padding.normal
        anchors.rightMargin: Theme.padding.normal
        spacing: Theme.spacing.small

        MaterialIcon {
            anchors.verticalCenter: parent.verticalCenter
            text: SessionService.archiveMode ? "inventory_2" : "save"
            font.pointSize: Theme.font.size.normal
            fill: root.isSelected ? 1 : 0
            color: root.isSelected
                ? Theme.palette.m3onSecondaryContainer
                : Theme.palette.m3onSurfaceVariant
        }

        StyledText {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - parent.spacing - 24 // icon width
            text: root.sessionName
            elide: Text.ElideRight
            font.pointSize: Theme.font.size.smaller
            font.weight: root.isSelected ? Font.Medium : Font.Normal
            font.family: Theme.font.family.mono
            color: root.isSelected
                ? Theme.palette.m3onSecondaryContainer
                : Theme.palette.m3onSurface
        }
    }

    StateLayer {
        onClicked: {
            SessionService.selectedSession = root.sessionName;
            SessionService.requestOperation(SessionService.archiveMode ? "recover" : "restore");
        }
    }
}
