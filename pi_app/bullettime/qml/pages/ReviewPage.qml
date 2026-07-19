import QtQuick 2.15
import "../components"

Item {
    Image {
        id: resultImage
        anchors.fill: parent
        source: bridge.imageSource
        fillMode: Image.PreserveAspectCrop
        cache: false
    }

    Rectangle {
        anchors.fill: parent
        color: bridge.imageSource === "" ? "black" : "transparent"
    }

    Text {
        visible: bridge.imageSource === ""
        anchors.centerIn: parent
        text: "REVIEW UNAVAILABLE"
        color: "#ff6168"
        font.pixelSize: 34
        font.bold: true
    }

    StatusHeader {
        anchors.left: parent.left
        anchors.right: parent.right
        title: "LATEST CAPTURE"
        subtitle: bridge.usbStatus === "saved" ? "USB SAVED" : "USB STATUS"
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 150
        color: "#dc050709"

        Row {
            x: 22
            y: 14
            spacing: 18
            Repeater {
                model: 4
                Rectangle {
                    width: 48
                    height: 34
                    radius: 5
                    color: "#10151a"
                    border.width: 2
                    border.color: bridge.failedCameraIds.indexOf(index + 1) >= 0 ? "#ff6168" : "#67d884"
                    Text {
                        anchors.centerIn: parent
                        text: index + 1
                        color: parent.border.color
                        font.pixelSize: 19
                        font.bold: true
                    }
                }
            }
        }

        Text {
            x: 272
            y: 15
            width: 250
            text: bridge.viewCount > 0 ? bridge.viewCount + " VIEWS SAVED" : "CAPTURE SAVED"
            color: "white"
            font.pixelSize: 22
            font.bold: true
            font.letterSpacing: 2
            elide: Text.ElideRight
        }

        Text {
            x: 22
            y: 60
            width: 500
            text: bridge.message
            color: "#ff6168"
            font.pixelSize: 16
            font.bold: true
            wrapMode: Text.WordWrap
        }

        TouchButton {
            x: 540
            y: 16
            width: 238
            height: 54
            label: "NEXT CAPTURE"
            enabled: bridge.canCapture
            onTapped: bridge.capture()
        }

        TouchButton {
            x: 540
            y: 82
            width: 112
            height: 46
            label: "VIEWER"
            onTapped: bridge.navigate("viewer")
        }

        TouchButton {
            x: 666
            y: 82
            width: 112
            height: 46
            label: "MEDIA"
            onTapped: bridge.navigate("library")
        }
    }
}
