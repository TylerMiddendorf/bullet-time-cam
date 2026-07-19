import QtQuick 2.15

Item {
    id: badge
    property int cameraId: 1
    property string cameraState: "disconnected"
    property bool compact: false
    readonly property color stateColor: {
        if (cameraState === "error" || cameraState === "disconnected") return "#ff6168"
        if (cameraState === "complete" || cameraState === "ready") return "#67d884"
        if (cameraState === "waiting") return "#6d737a"
        return "#62b0f5"
    }

    width: compact ? 46 : 96
    height: compact ? 46 : 92

    Rectangle {
        id: ring
        anchors.horizontalCenter: parent.horizontalCenter
        width: badge.compact ? 38 : 54
        height: width
        radius: width / 2
        color: "#080b0f"
        border.width: 3
        border.color: badge.stateColor

        Text {
            anchors.centerIn: parent
            text: badge.cameraId
            color: "white"
            font.pixelSize: badge.compact ? 18 : 24
            font.bold: true
        }
    }

    Text {
        visible: !badge.compact
        anchors.top: ring.bottom
        anchors.topMargin: 8
        anchors.horizontalCenter: parent.horizontalCenter
        text: badge.cameraState.toUpperCase()
        color: badge.stateColor
        font.pixelSize: 12
        font.bold: true
        font.letterSpacing: 1.3
    }
}
