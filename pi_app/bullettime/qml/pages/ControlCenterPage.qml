import QtQuick 2.15
import "../components"

Item {
    Rectangle { anchors.fill: parent; color: "black" }

    StatusHeader {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        title: bridge.connectedCameraIds.length + "/4 CAMERAS READY"
        subtitle: "SETTINGS"
        showBack: true
        onBack: bridge.navigate("ready")
    }

    PlaceholderSurface {
        x: 18
        y: 78
        width: 500
        height: 290
    }

    Text {
        x: 540
        y: 82
        text: "SETTINGS"
        color: "#63adf2"
        font.pixelSize: 17
        font.bold: true
        font.letterSpacing: 2
    }

    Column {
        x: 536
        y: 112
        spacing: 10
        Repeater {
            model: ["EXPOSURE", "WHITE BALANCE", "SMOOTH MOTION", "AI INTERPOLATION"]
            SettingCard {
                width: 246
                height: 49
                label: modelData
                status: "V2 · DISABLED"
            }
        }
    }

    TouchButton {
        objectName: "captureNavigationButton"
        x: 18
        y: 386
        width: 500
        height: 72
        label: "CAPTURE"
        onTapped: bridge.navigate("capture")
    }

    TouchButton {
        objectName: "libraryButton"
        x: 536
        y: 386
        width: 246
        height: 72
        label: "LIBRARY"
        onTapped: bridge.navigate("library")
    }
}
