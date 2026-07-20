import QtQuick 2.15
import "../components"

Item {
    Rectangle {
        anchors.fill: parent
        color: "#080b0f"

        Image {
            objectName: "previewImage"
            x: 0
            y: 0
            width: 800
            height: 360
            source: bridge.previewSource
            fillMode: Image.PreserveAspectFit
            cache: false
            visible: bridge.previewAvailable
        }

        Text {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -50
            text: "WAITING FOR CAMERA PREVIEW"
            color: "#aeb7c0"
            font.pixelSize: 18
            font.bold: true
            font.letterSpacing: 1.5
            visible: !bridge.previewAvailable
        }

        Repeater {
            model: 2
            Rectangle {
                x: (index + 1) * 800 / 3
                y: 0
                width: 1
                height: 360
                color: "#55ffffff"
            }
        }

        Repeater {
            model: 2
            Rectangle {
                x: 0
                y: (index + 1) * 360 / 3
                width: 800
                height: 1
                color: "#55ffffff"
            }
        }
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
            text: bridge.previewAvailable
                  ? "PREVIEW CAMERA " + bridge.previewCameraId + "\n320 × 240 · ROTATING VIEWS"
                  : "PREVIEW STARTING\nWAITING FOR CAMERAS"
            color: "#aeb7c0"
            font.pixelSize: 12
            fontSizeMode: Text.Fit
            minimumPixelSize: 9
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
