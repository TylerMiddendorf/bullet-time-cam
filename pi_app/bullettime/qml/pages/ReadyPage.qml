import QtQuick 2.15
import "../components"

Item {
    Rectangle { anchors.fill: parent; color: "black" }

    StatusHeader {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        title: "4 CAMERA RIG"
        subtitle: bridge.storageConnected ? "USB CONNECTED" : "USB DISCONNECTED"
        subtitleColor: bridge.storageConnected ? "#67d884" : "#ff6168"
    }

    Row {
        anchors.top: header.bottom
        anchors.topMargin: 16
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 24
        Repeater {
            model: 4
            CameraBadge {
                cameraId: index + 1
                // Ready reports current connectivity. Per-capture states belong
                // on Progress and Review and may intentionally outlive a shot.
                cameraState: bridge.connectedCameraIds.indexOf(index + 1) >= 0
                    ? "ready"
                    : "disconnected"
                compact: true
            }
        }
    }

    Text {
        id: readyTitle
        x: 72
        y: 145
        width: 500
        horizontalAlignment: Text.AlignHCenter
        text: bridge.state === "ERROR" ? "ATTENTION" : "READY"
        color: bridge.state === "ERROR" ? "#ff6168" : "white"
        font.pixelSize: 76
        font.bold: true
        font.letterSpacing: 5
    }

    Text {
        anchors.top: readyTitle.bottom
        anchors.topMargin: -4
        x: 72
        width: 500
        horizontalAlignment: Text.AlignHCenter
        text: bridge.state === "ERROR" ? bridge.message : "4 CAMERAS CONNECTED"
        color: bridge.state === "ERROR" ? "#ff9196" : "#63adf2"
        font.pixelSize: bridge.state === "ERROR" ? 18 : 23
        font.bold: true
        font.letterSpacing: 2
        wrapMode: Text.WordWrap
    }

    StorageUsageCircle {
        objectName: "storageUsageCircle"
        x: 626
        y: 138
        width: 150
        height: 156
        connected: bridge.storageConnected
        fraction: bridge.storageUsedFraction
        availableText: bridge.storageAvailableText
    }

    TouchButton {
        objectName: "settingsButton"
        x: 48
        y: 355
        width: 82
        height: 82
        label: "\u2699"
        iconOnly: true
        accent: "#8f98a1"
        onTapped: bridge.navigate("control")
    }

    TouchButton {
        objectName: "libraryButton"
        x: 148
        y: 355
        width: 286
        height: 82
        label: "LIBRARY"
        onTapped: bridge.navigate("library")
    }

    TouchButton {
        objectName: "captureNavigationButton"
        x: 452
        y: 355
        width: 300
        height: 82
        label: "CAPTURE"
        onTapped: bridge.navigate("capture")
    }
}
