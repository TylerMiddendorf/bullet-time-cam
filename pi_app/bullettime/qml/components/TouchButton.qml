import QtQuick 2.15

Rectangle {
    id: control
    property string label: "BUTTON"
    property string accent: "#63adf2"
    property bool enabled: true
    property bool iconOnly: false
    signal tapped

    radius: 12
    color: enabled ? (tap.pressed ? "#244c72" : "#101820") : "#111317"
    border.width: 2
    border.color: enabled ? accent : "#3c4248"
    opacity: enabled ? 1.0 : 0.62

    Text {
        anchors.centerIn: parent
        width: parent.width - (control.iconOnly ? 8 : 24)
        text: control.label
        color: control.enabled ? "white" : "#89919a"
        font.pixelSize: control.iconOnly
            ? Math.floor(Math.min(control.width, control.height) * 0.72)
            : 20
        fontSizeMode: Text.Fit
        minimumPixelSize: control.iconOnly ? 1 : 12
        font.bold: true
        font.letterSpacing: control.iconOnly ? 0 : 2
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
    }

    MouseArea {
        id: tap
        anchors.fill: parent
        enabled: control.enabled
        onClicked: control.tapped()
    }
}
