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
            x: 20
            width: 175
            anchors.verticalCenter: parent.verticalCenter
            text: "ANIMATION PLAYBACK"
            color: "white"
            font.pixelSize: 15
            fontSizeMode: Text.Fit
            minimumPixelSize: 11
            font.bold: true
            font.letterSpacing: 1.5
            elide: Text.ElideRight
        }

        Text {
            x: 195
            width: 220
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignHCenter
            text: bridge.imageSource === "" ? "NO MEDIA" : bridge.viewerViewCount + " CAPTURED VIEWS"
            color: "#63adf2"
            font.pixelSize: 15
            fontSizeMode: Text.Fit
            minimumPixelSize: 11
            font.bold: true
            elide: Text.ElideRight
        }

        TouchButton {
            objectName: "viewerDeleteButton"
            x: 425
            anchors.verticalCenter: parent.verticalCenter
            width: 145
            height: 48
            label: "DELETE"
            accent: "#ff6168"
            enabled: bridge.selectedLibraryIndex >= 0 && bridge.catalogStatus === "ready"
            onTapped: bridge.promptDeleteSelected()
        }

        TouchButton {
            x: 580
            anchors.verticalCenter: parent.verticalCenter
            width: 162
            height: 48
            label: "BACK TO MEDIA"
            onTapped: bridge.navigate("library")
        }
    }

    DeleteConfirmation { anchors.fill: parent }
}
