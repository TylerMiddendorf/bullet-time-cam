import QtQuick 2.15
import "../components"

Item {
    Rectangle { anchors.fill: parent; color: "black" }

    StatusHeader {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        title: "BULLET-TIME VIEWER"
        subtitle: bridge.imageSource === "" ? "NO MEDIA" : "DETACHED REVIEW"
        showBack: true
        onBack: bridge.navigate("library")
    }

    Image {
        x: 24
        y: 78
        width: 752
        height: 300
        source: bridge.imageSource === "" ? bridge.previewPlaceholder : bridge.imageSource
        fillMode: Image.PreserveAspectFit
        cache: false
    }

    Rectangle {
        visible: bridge.imageSource === ""
        x: 42
        y: 92
        width: 260
        height: 52
        radius: 8
        color: "#d9000000"
        border.color: "#63adf2"
        Text {
            anchors.centerIn: parent
            text: "PLACEHOLDER · DEMO"
            color: "white"
            font.pixelSize: 16
            font.bold: true
            font.letterSpacing: 1.5
        }
    }

    Rectangle {
        x: 24
        y: 392
        width: 752
        height: 68
        radius: 12
        color: "#10151a"
        border.color: "#414950"

        Text {
            x: 24
            anchors.verticalCenter: parent.verticalCenter
            text: "ANIMATION PLAYBACK"
            color: "white"
            font.pixelSize: 17
            font.bold: true
            font.letterSpacing: 1.5
        }

        Text {
            anchors.centerIn: parent
            text: bridge.imageSource === "" ? "NO MEDIA" : bridge.viewerViewCount + " CAPTURED VIEWS"
            color: "#63adf2"
            font.pixelSize: 16
            font.bold: true
        }

        TouchButton {
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            width: 178
            height: 48
            label: "BACK TO MEDIA"
            onTapped: bridge.navigate("library")
        }
    }
}
