import QtQuick 2.15

Rectangle {
    id: header
    property string title: "BULLET-TIME"
    property string subtitle: ""
    property bool showBack: false
    signal back

    color: "#070a0e"
    border.color: "#242b31"
    border.width: 1
    height: 64

    Image {
        id: logo
        x: showBack ? 68 : 18
        anchors.verticalCenter: parent.verticalCenter
        width: 66
        height: 44
        source: bridge.startupLogo
        fillMode: Image.PreserveAspectFit
    }

    Text {
        visible: header.showBack
        x: 20
        anchors.verticalCenter: parent.verticalCenter
        text: "‹"
        color: "white"
        font.pixelSize: 52
    }

    MouseArea {
        visible: header.showBack
        x: 0
        width: 64
        height: parent.height
        onClicked: header.back()
    }

    Text {
        x: logo.x + logo.width + 18
        anchors.verticalCenter: parent.verticalCenter
        text: header.title
        color: "white"
        font.pixelSize: 22
        font.bold: true
        font.letterSpacing: 2
    }

    Text {
        anchors.right: parent.right
        anchors.rightMargin: 22
        anchors.verticalCenter: parent.verticalCenter
        text: header.subtitle
        color: bridge.usbStatus === "error" ? "#ff6168" : "#67d884"
        font.pixelSize: 18
        font.bold: true
        font.letterSpacing: 1.5
    }
}
