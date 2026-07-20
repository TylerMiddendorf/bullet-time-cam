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

    Rectangle {
        objectName: "controlReviewMedia"
        x: 18
        y: 78
        width: 500
        height: 290
        color: "#080b0f"
        border.color: "#38414a"

        Image {
            anchors.fill: parent
            anchors.margins: 2
            source: bridge.imageSource
            fillMode: Image.PreserveAspectFit
            visible: bridge.imageSource !== ""
        }

        Text {
            anchors.centerIn: parent
            text: "NO REVIEW IMAGE"
            color: "#aeb7c0"
            font.pixelSize: 16
            font.bold: true
            visible: bridge.imageSource === ""
        }
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
        width: 170
        height: 72
        label: "CAPTURE"
        onTapped: bridge.navigate("capture")
    }

    TouchButton {
        objectName: "cameraRecoveryButton"
        x: 198
        y: 386
        width: 250
        height: 72
        label: bridge.cameraRecoveryPending ? bridge.cameraRecoveryMessage : "RECONNECT CAMERAS"
        enabled: bridge.canRecoverCameras
        onTapped: bridge.recoverCameras()
    }

    TouchButton {
        objectName: "libraryButton"
        x: 458
        y: 386
        width: 156
        height: 72
        label: "LIBRARY"
        onTapped: bridge.navigate("library")
    }

    TouchButton {
        objectName: "homeButton"
        x: 624
        y: 386
        width: 158
        height: 72
        label: "\u2302"
        iconOnly: true
        iconScale: 1.0
        onTapped: bridge.navigate("ready")
    }
}
