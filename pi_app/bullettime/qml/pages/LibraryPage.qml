import QtQuick 2.15
import "../components"

Item {
    Rectangle { anchors.fill: parent; color: "black" }

    StatusHeader {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        title: "SESSION MEDIA"
        subtitle: "READ ONLY · " + bridge.libraryItems.length + " ITEMS"
        showBack: true
        onBack: bridge.navigate("control")
    }

    Rectangle {
        x: 18
        y: 80
        width: 178
        height: 310
        radius: 10
        color: "#0d1116"
        border.color: "#38414a"

        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 14
            Text {
                text: "THIS SESSION"
                color: "#63adf2"
                font.pixelSize: 17
                font.bold: true
                font.letterSpacing: 1.5
            }
            Text {
                width: parent.width
                text: "Published capture sets on the selected removable USB drive. Media is never changed or deleted."
                color: "#aab2ba"
                font.pixelSize: 14
                lineHeight: 1.2
                wrapMode: Text.WordWrap
            }
        }
    }

    Grid {
        x: 212
        y: 80
        columns: 3
        spacing: 12
        Repeater {
            model: bridge.libraryItems
            Rectangle {
                width: 182
                height: 144
                radius: 8
                color: "#0b0f13"
                border.width: bridge.selectedLibraryIndex === index ? 3 : 1
                border.color: bridge.selectedLibraryIndex === index ? "#63adf2" : "#3d444a"
                clip: true

                Image {
                    anchors.fill: parent
                    anchors.bottomMargin: 30
                    source: modelData.thumbnail
                    fillMode: Image.PreserveAspectCrop
                    opacity: 1.0
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 30
                    color: "#d9000000"
                    Text {
                        anchors.centerIn: parent
                        text: modelData.title + " · " + modelData.viewCount + " VIEWS"
                        color: modelData.partial ? "#ff7b80" : "white"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: bridge.selectLibraryItem(index)
                }
            }
        }
    }

    Text {
        visible: bridge.libraryItems.length === 0
        x: 260
        y: 220
        text: bridge.catalogStatus === "loading"
            ? "REFRESHING REMOVABLE USB MEDIA"
            : (bridge.catalogMessage === "" ? "NO PUBLISHED CAPTURES" : bridge.catalogMessage)
        color: bridge.catalogStatus === "removed" ? "#ff6168" : "#7f8891"
        font.pixelSize: 18
        font.bold: true
        font.letterSpacing: 1.5
    }

    TouchButton {
        x: 18
        y: 406
        width: 370
        height: 58
        label: "OPEN SELECTED"
        enabled: bridge.selectedLibraryIndex >= 0 && bridge.catalogStatus !== "loading"
        onTapped: bridge.openLibraryItem(bridge.selectedLibraryIndex)
    }

    TouchButton {
        x: 412
        y: 406
        width: 370
        height: 58
        label: "BACK TO CAMERA"
        onTapped: bridge.navigate("ready")
    }
}
