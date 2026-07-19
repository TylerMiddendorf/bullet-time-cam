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
        title: "CAPTURE"
        subtitle: "4 CAMERAS \u00b7 USB"
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
            width: 190
            anchors.verticalCenter: parent.verticalCenter
            text: "STATIC PLACEHOLDER\nCAMERA VIEW NOT CONNECTED"
            color: "#aeb7c0"
            font.pixelSize: 12
            font.bold: true
            font.letterSpacing: 1.2
        }

        TouchButton {
            objectName: "captureButton"
            anchors.centerIn: parent
            width: 260
            height: 66
            label: "CAPTURE"
            enabled: bridge.canCapture
            onTapped: bridge.capture()
        }

        TouchButton {
            objectName: "settingsButton"
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            width: 160
            height: 54
            label: "SETTINGS"
            onTapped: bridge.navigate("control")
        }
    }
}
