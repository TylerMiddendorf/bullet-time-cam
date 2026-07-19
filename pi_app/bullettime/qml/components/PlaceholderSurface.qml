import QtQuick 2.15

Item {
    id: surface
    property bool showGrid: false

    clip: true

    Image {
        anchors.fill: parent
        source: bridge.previewPlaceholder
        fillMode: Image.PreserveAspectCrop
    }

    Rectangle {
        anchors.fill: parent
        color: "#19000000"
    }

    Repeater {
        model: surface.showGrid ? 2 : 0
        Rectangle {
            x: (index + 1) * surface.width / 3
            width: 1
            height: surface.height
            color: "#80ffffff"
        }
    }

    Repeater {
        model: surface.showGrid ? 2 : 0
        Rectangle {
            y: (index + 1) * surface.height / 3
            width: surface.width
            height: 1
            color: "#80ffffff"
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 14
        width: 238
        height: 52
        radius: 8
        color: "#d9000000"
        border.color: "#63adf2"

        Column {
            anchors.centerIn: parent
            spacing: 1
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "PREVIEW PLACEHOLDER"
                color: "white"
                font.pixelSize: 16
                font.bold: true
                font.letterSpacing: 1.6
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "DEMO"
                color: "#63adf2"
                font.pixelSize: 13
                font.bold: true
                font.letterSpacing: 2
            }
        }
    }
}
