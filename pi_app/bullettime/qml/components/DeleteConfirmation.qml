import QtQuick 2.15

Rectangle {
    id: confirmation
    objectName: "deleteConfirmation"
    visible: bridge.deleteConfirmationVisible
    z: 100
    color: "#f20a0d11"

    MouseArea { anchors.fill: parent }

    Rectangle {
        anchors.centerIn: parent
        width: 620
        height: 310
        radius: 16
        color: "#15191e"
        border.width: 3
        border.color: "#ff6168"

        Text {
            x: 30
            y: 28
            width: 560
            text: "DELETE CAPTURE SET?"
            color: "#ff7b80"
            font.pixelSize: 28
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
        }

        Text {
            x: 36
            y: 82
            width: 548
            text: bridge.pendingDeleteTitle
            color: "white"
            font.pixelSize: 18
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideMiddle
        }

        Text {
            x: 46
            y: 124
            width: 528
            text: "This permanently deletes the original JPEG images, animation GIF, and manifest from the removable USB drive. This cannot be undone."
            color: "#c5cbd1"
            font.pixelSize: 17
            lineHeight: 1.25
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }

        TouchButton {
            objectName: "cancelDeleteButton"
            x: 30
            y: 234
            width: 265
            height: 56
            label: "CANCEL"
            onTapped: bridge.cancelDelete()
        }

        TouchButton {
            objectName: "confirmDeleteButton"
            x: 325
            y: 234
            width: 265
            height: 56
            label: "DELETE PERMANENTLY"
            accent: "#ff6168"
            onTapped: bridge.confirmDelete()
        }
    }
}
