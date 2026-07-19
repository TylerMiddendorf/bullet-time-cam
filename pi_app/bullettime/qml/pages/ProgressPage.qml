import QtQuick 2.15
import "../components"

Item {
    Rectangle { anchors.fill: parent; color: "black" }

    Text {
        anchors.top: parent.top
        anchors.topMargin: 20
        anchors.horizontalCenter: parent.horizontalCenter
        text: "CREATING BULLET-TIME"
        color: "white"
        font.pixelSize: 25
        font.bold: true
        font.letterSpacing: 5
    }

    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 70
        width: 190
        height: 190
        radius: 95
        color: "#090d12"
        border.width: 8
        border.color: bridge.capturePhase === "building" ? "#ffb547" : "#63adf2"

        Image {
            anchors.centerIn: parent
            width: 125
            height: 125
            source: bridge.startupLogo
            fillMode: Image.PreserveAspectFit
        }

        RotationAnimation on rotation {
            from: 0
            to: 360
            duration: 1800
            loops: Animation.Infinite
            running: true
        }
    }

    Row {
        x: 145
        y: 275
        spacing: 54
        Repeater {
            model: 4
            CameraBadge {
                cameraId: index + 1
                cameraState: bridge.cameraStates[index]
            }
        }
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 394
        spacing: 34
        Repeater {
            model: ["CAPTURING", "TRANSFERRING", "BUILDING ANIMATION"]
            Rectangle {
                width: 220
                height: 36
                radius: 18
                color: {
                    var active = (bridge.capturePhase === "capturing" && index === 0)
                        || (bridge.capturePhase === "transferring" && index === 1)
                        || (bridge.capturePhase === "building" && index === 2)
                    return active ? "#243e55" : "#101317"
                }
                border.color: color === "#243e55" ? "#63adf2" : "#383d42"
                Text {
                    anchors.centerIn: parent
                    text: modelData
                    color: parent.color === "#243e55" ? "#72bdff" : "#747b82"
                    font.pixelSize: 13
                    font.bold: true
                    font.letterSpacing: 1.5
                }
            }
        }
    }

    Text {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 14
        anchors.horizontalCenter: parent.horizontalCenter
        text: "KEEP CAMERA STEADY"
        color: "#63adf2"
        font.pixelSize: 16
        font.bold: true
        font.letterSpacing: 4
    }
}
