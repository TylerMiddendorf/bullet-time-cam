import QtQuick 2.15
import "../components"

Item {
    PlaceholderSurface {
        anchors.fill: parent
        showGrid: true
    }

    StatusHeader {
        anchors.left: parent.left
        anchors.right: parent.right
        title: "CAMERA PREVIEW DEMO"
        subtitle: "4 CAMERAS · USB"
        showBack: true
        onBack: bridge.navigate("ready")
    }

    Rectangle {
        x: 24
        y: 365
        width: 752
        height: 92
        radius: 16
        color: "#d9090c10"
        border.color: "#687078"

        Text {
            x: 26
            anchors.verticalCenter: parent.verticalCenter
            text: "STATIC DEMO\nNO PREVIEW TRANSPORT"
            color: "#aeb7c0"
            font.pixelSize: 14
            font.bold: true
            font.letterSpacing: 1.2
        }

        TouchButton {
            anchors.centerIn: parent
            width: 260
            height: 66
            label: "CAPTURE"
            enabled: bridge.canCapture
            onTapped: bridge.capture()
        }

        TouchButton {
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            width: 160
            height: 54
            label: "CONTROLS"
            onTapped: bridge.navigate("control")
        }
    }
}
