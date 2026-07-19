import QtQuick 2.15
import "../components"

Item {
    id: libraryPage
    readonly property int libraryPageSize: 6
    readonly property int libraryPageCount: Math.max(
        1, Math.ceil(bridge.libraryItems.length / libraryPageSize)
    )
    property int libraryPageIndex: 0

    function changeLibraryPage(offset) {
        var targetPage = Math.max(
            0, Math.min(libraryPageCount - 1, libraryPageIndex + offset)
        )
        libraryPageIndex = targetPage
        if (captureGrid.count > 0) {
            var targetIndex = Math.min(
                captureGrid.count - 1, targetPage * libraryPageSize
            )
            bridge.selectLibraryItem(targetIndex)
            captureGrid.positionViewAtIndex(targetIndex, GridView.Beginning)
        }
    }

    Rectangle { anchors.fill: parent; color: "black" }

    StatusHeader {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        title: "REMOVABLE MEDIA"
        subtitle: bridge.libraryItems.length + " CAPTURE SETS"
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
            spacing: 10
            Text {
                width: parent.width
                text: "REMOVABLE USB"
                color: "#63adf2"
                font.pixelSize: 17
                fontSizeMode: Text.Fit
                minimumPixelSize: 12
                font.bold: true
                font.letterSpacing: 1.5
                elide: Text.ElideRight
            }
            Text {
                width: parent.width
                text: "Published capture sets on the selected removable USB drive."
                color: "#aab2ba"
                font.pixelSize: 14
                lineHeight: 1.2
                wrapMode: Text.WordWrap
            }

            Rectangle {
                objectName: "storageUsageMetric"
                width: parent.width
                height: 116
                radius: 8
                color: "#111820"
                border.color: "#38414a"

                Text {
                    x: 10
                    y: 9
                    text: "USB STORAGE"
                    color: "#7f8891"
                    font.pixelSize: 10
                    font.bold: true
                    font.letterSpacing: 1
                }

                Row {
                    x: 10
                    y: 31
                    width: parent.width - 20
                    height: 48

                    Column {
                        width: parent.width / 2
                        spacing: 2
                        Text {
                            text: "USED"
                            color: "#7f8891"
                            font.pixelSize: 9
                            font.bold: true
                        }
                        Text {
                            width: 65
                            text: bridge.storageUsedText
                            color: "white"
                            font.pixelSize: 15
                            minimumPixelSize: 10
                            fontSizeMode: Text.Fit
                            font.bold: true
                        }
                    }

                    Column {
                        width: parent.width / 2
                        spacing: 2
                        Text {
                            text: "AVAILABLE"
                            color: "#7f8891"
                            font.pixelSize: 9
                            font.bold: true
                        }
                        Text {
                            width: 65
                            text: bridge.storageAvailableText
                            color: bridge.storageAvailableText === "UNAVAILABLE"
                                ? "#ff6168" : "#63adf2"
                            font.pixelSize: 15
                            minimumPixelSize: 8
                            fontSizeMode: Text.Fit
                            font.bold: true
                        }
                    }
                }

                Rectangle {
                    x: 10
                    y: 90
                    width: parent.width - 20
                    height: 8
                    radius: 4
                    color: "#303842"

                    Rectangle {
                        width: parent.width * bridge.storageUsedFraction
                        height: parent.height
                        radius: parent.radius
                        color: bridge.storageUsedFraction >= 0.9 ? "#ff6168" : "#63adf2"
                    }
                }
            }
        }
    }

    GridView {
        id: captureGrid
        x: 212
        y: 80
        width: 500
        height: 310
        clip: true
        cellWidth: 166
        cellHeight: 154
        model: bridge.libraryItems
        boundsBehavior: Flickable.StopAtBounds
        snapMode: GridView.SnapToRow
        highlightMoveDuration: 120
        currentIndex: bridge.selectedLibraryIndex
        onCountChanged: {
            libraryPage.libraryPageIndex = Math.min(
                libraryPage.libraryPageIndex,
                libraryPage.libraryPageCount - 1
            )
        }
        onMovementEnded: {
            var pageFromPosition = atYEnd
                ? libraryPage.libraryPageCount - 1
                : Math.round(contentY / (cellHeight * 2))
            libraryPage.libraryPageIndex = Math.max(
                0, Math.min(libraryPage.libraryPageCount - 1, pageFromPosition)
            )
        }
        delegate: Item {
            required property int index
            required property var modelData
            width: 158
            height: 144

            Rectangle {
                anchors.fill: parent
                radius: 8
                color: "#0b0f13"
                border.width: bridge.selectedLibraryIndex === index ? 3 : 1
                border.color: bridge.selectedLibraryIndex === index ? "#63adf2" : "#3d444a"
                clip: true

                Image {
                    anchors.fill: parent
                    anchors.bottomMargin: 30
                    source: modelData.thumbnail === "" ? bridge.previewPlaceholder : modelData.thumbnail
                    fillMode: Image.PreserveAspectCrop
                    opacity: modelData.thumbnail === "" ? 0.45 : 1.0
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 30
                    color: "#d9000000"
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 10
                        horizontalAlignment: Text.AlignHCenter
                        text: {
                            var title = String(modelData.title)
                            var separator = title.lastIndexOf("_")
                            var shortTitle = separator >= 0 ? title.substring(separator + 1) : title
                            return shortTitle.toUpperCase() + " · " + modelData.viewCount + " VIEWS"
                        }
                        color: modelData.partial ? "#ff7b80" : "white"
                        font.pixelSize: 11
                        font.bold: true
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: bridge.selectLibraryItem(index)
                }
            }
        }
    }

    Column {
        x: 726
        y: 80
        width: 56
        height: 310
        spacing: 8

        TouchButton {
            objectName: "libraryPageUp"
            width: parent.width
            height: 72
            label: "\u25B2"
            enabled: libraryPage.libraryPageIndex > 0
            onTapped: libraryPage.changeLibraryPage(-1)
        }

        Rectangle {
            width: parent.width
            height: 150
            radius: 8
            color: "#0d1116"
            border.color: "#38414a"

            Column {
                anchors.centerIn: parent
                spacing: 4
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "PAGE"
                    color: "#7f8891"
                    font.pixelSize: 10
                    font.bold: true
                    font.letterSpacing: 1
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: libraryPage.libraryPageIndex + 1
                    color: "white"
                    font.pixelSize: 20
                    font.bold: true
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "OF"
                    color: "#7f8891"
                    font.pixelSize: 10
                    font.bold: true
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: libraryPage.libraryPageCount
                    color: "#63adf2"
                    font.pixelSize: 20
                    font.bold: true
                }
            }
        }

        TouchButton {
            objectName: "libraryPageDown"
            width: parent.width
            height: 72
            label: "\u25BC"
            enabled: libraryPage.libraryPageIndex < libraryPage.libraryPageCount - 1
            onTapped: libraryPage.changeLibraryPage(1)
        }
    }

    Text {
        visible: bridge.libraryItems.length === 0
        x: 260
        y: 220
        text: bridge.catalogStatus === "loading"
            ? "REFRESHING REMOVABLE USB MEDIA"
            : (bridge.catalogMessage === "" ? "NO PUBLISHED CAPTURES" : bridge.catalogMessage)
        color: bridge.catalogStatus === "removed" || bridge.catalogStatus === "error"
            ? "#ff6168" : "#7f8891"
        font.pixelSize: 18
        font.bold: true
        font.letterSpacing: 1.5
    }

    Rectangle {
        visible: bridge.libraryItems.length > 0
            && bridge.catalogMessage !== ""
            && bridge.catalogStatus !== "loading"
        x: 212
        y: 342
        width: 500
        height: 48
        radius: 8
        color: bridge.catalogStatus === "ready" ? "#e0143320" : "#e03b1015"
        border.color: bridge.catalogStatus === "ready" ? "#58c98d" : "#ff6168"

        Text {
            anchors.fill: parent
            anchors.margins: 10
            text: bridge.catalogMessage
            color: "white"
            font.pixelSize: 14
            font.bold: true
            fontSizeMode: Text.Fit
            minimumPixelSize: 10
            elide: Text.ElideMiddle
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
    }

    TouchButton {
        x: 18
        y: 406
        width: 235
        height: 58
        label: "OPEN SELECTED"
        enabled: bridge.selectedLibraryIndex >= 0 && bridge.catalogStatus === "ready"
        onTapped: bridge.openLibraryItem(bridge.selectedLibraryIndex)
    }

    TouchButton {
        objectName: "deleteSelectedButton"
        x: 282
        y: 406
        width: 235
        height: 58
        label: bridge.catalogStatus === "deleting" ? "DELETING..." : "DELETE SELECTED"
        accent: "#ff6168"
        enabled: bridge.selectedLibraryIndex >= 0 && bridge.catalogStatus === "ready"
        onTapped: bridge.promptDeleteSelected()
    }

    TouchButton {
        x: 547
        y: 406
        width: 235
        height: 58
        label: "BACK TO CAMERA"
        onTapped: bridge.navigate("ready")
    }

    DeleteConfirmation { anchors.fill: parent }
}
