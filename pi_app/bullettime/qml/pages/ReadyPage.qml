import QtQuick 2.15
import "../components"

Item {
    Rectangle { anchors.fill: parent; color: "black" }

    StatusHeader {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        title: "4 CAMERA RIG"
        subtitle: bridge.usbStatus === "error" ? "USB ERROR" : "USB READY"
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
                cameraState: bridge.cameraStates[index]
                compact: true
            }
        }
    }

    Text {
        id: readyTitle
        anchors.horizontalCenter: parent.horizontalCenter
        y: 145
        text: bridge.state === "ERROR" ? "ATTENTION" : "READY"
        color: bridge.state === "ERROR" ? "#ff6168" : "white"
        font.pixelSize: 76
        font.bold: true
        font.letterSpacing: 5
    }

    Text {
        anchors.top: readyTitle.bottom
        anchors.topMargin: -4
        anchors.horizontalCenter: parent.horizontalCenter
        width: 680
        horizontalAlignment: Text.AlignHCenter
        text: bridge.state === "ERROR" ? bridge.message : "4 CAMERAS CONNECTED"
        color: bridge.state === "ERROR" ? "#ff9196" : "#63adf2"
        font.pixelSize: bridge.state === "ERROR" ? 18 : 23
        font.bold: true
        font.letterSpacing: 2
        wrapMode: Text.WordWrap
    }

    TouchButton {
        x: 48
        y: 355
        width: 474
        height: 82
        label: "PRESS SHUTTER OR TAP TO CAPTURE"
        enabled: bridge.canCapture
        onTapped: bridge.capture()
    }

    TouchButton {
        x: 540
        y: 350
        width: 212
        height: 44
        label: "PREVIEW DEMO"
        onTapped: bridge.navigate("preview")
    }

    TouchButton {
        x: 540
        y: 404
        width: 212
        height: 44
        label: "UI CONCEPTS"
        accent: "#8f98a1"
        onTapped: bridge.navigate("control")
    }
}
