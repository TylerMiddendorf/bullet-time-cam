import QtQuick 2.15

Item {
    id: usage
    property bool connected: false
    property real fraction: 0.0
    property string availableText: "UNAVAILABLE"

    onConnectedChanged: ring.requestPaint()
    onFractionChanged: ring.requestPaint()

    Canvas {
        id: ring
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        width: 112
        height: 112

        onPaint: {
            var context = getContext("2d")
            var center = width / 2
            var radius = center - 9
            context.clearRect(0, 0, width, height)

            context.beginPath()
            context.lineWidth = 10
            context.strokeStyle = "#303842"
            context.arc(center, center, radius, 0, Math.PI * 2, false)
            context.stroke()

            if (usage.connected && usage.fraction > 0) {
                context.beginPath()
                context.lineWidth = 10
                context.lineCap = "round"
                context.strokeStyle = usage.fraction >= 0.9 ? "#ff6168" : "#63adf2"
                context.arc(
                    center,
                    center,
                    radius,
                    -Math.PI / 2,
                    -Math.PI / 2 + Math.PI * 2 * Math.min(1, usage.fraction),
                    false
                )
                context.stroke()
            }
        }

        Text {
            anchors.centerIn: parent
            text: usage.connected ? Math.round(usage.fraction * 100) + "%" : "--"
            color: usage.connected ? "white" : "#ff6168"
            font.pixelSize: 27
            font.bold: true
        }
    }

    Text {
        anchors.top: ring.bottom
        anchors.topMargin: 4
        anchors.horizontalCenter: parent.horizontalCenter
        text: usage.connected ? "USB CONNECTED" : "USB DISCONNECTED"
        color: usage.connected ? "#67d884" : "#ff6168"
        font.pixelSize: 12
        font.bold: true
        font.letterSpacing: 1
    }

    Text {
        anchors.top: ring.bottom
        anchors.topMargin: 24
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        text: usage.connected ? usage.availableText + " FREE" : "STORAGE UNAVAILABLE"
        color: "#8f98a1"
        font.pixelSize: 11
        minimumPixelSize: 8
        fontSizeMode: Text.Fit
        font.bold: true
        font.letterSpacing: 0.5
    }
}
