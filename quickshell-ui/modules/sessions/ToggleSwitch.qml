import "../../components"
import "../../services"
import QtQuick

Row {
    id: root

    spacing: Theme.spacing.tiny

    Repeater {
        model: ["Browse", "Save"]

        ClippingRect {
            id: toggleItem

            required property string modelData
            required property int index

            property bool active: index === 0 ? !SessionService.saveMode : SessionService.saveMode

            width: 65
            height: 28
            radius: Theme.rounding.full
            color: active ? Theme.layer(Theme.palette.m3primary, 1) : "transparent"

            StyledText {
                anchors.centerIn: parent
                text: toggleItem.modelData
                font.pointSize: Theme.font.size.small
                font.weight: toggleItem.active ? Font.Medium : Font.Normal
                color: toggleItem.active ? Theme.palette.m3onPrimary : Theme.palette.m3onSurfaceVariant
            }

            StateLayer {
                onClicked: SessionService.saveMode = (toggleItem.index === 1)
            }
        }
    }
}
