import QtQuick 2.15

Rectangle {
    id: card
    property string label: "SETTING"
    property string status: "UNSUPPORTED"

    radius: 8
    color: "#0d1116"
    border.width: 1
    border.color: "#3b4249"
    opacity: 0.66

    Column {
        anchors.left: parent.left
        anchors.leftMargin: 18
        anchors.right: parent.right
        anchors.rightMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        spacing: 1

        Text {
            text: card.label
            color: "#a5adb5"
            font.pixelSize: 13
            font.bold: true
            font.letterSpacing: 1.0
        }
        Text {
            text: card.status
            color: "#ffb547"
            font.pixelSize: 10
            font.bold: true
        }
    }

    MouseArea {
        anchors.fill: parent
        enabled: false
    }
}
