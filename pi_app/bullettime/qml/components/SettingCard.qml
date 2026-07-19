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

    Text {
        anchors.left: parent.left
        anchors.leftMargin: 18
        anchors.verticalCenter: parent.verticalCenter
        text: card.label
        color: "#a5adb5"
        font.pixelSize: 15
        font.bold: true
        font.letterSpacing: 1.2
    }

    Text {
        anchors.right: parent.right
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        text: card.status
        color: "#ffb547"
        font.pixelSize: 11
        font.bold: true
    }

    MouseArea {
        anchors.fill: parent
        enabled: false
    }
}
