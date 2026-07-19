import QtQuick 2.15
import QtQuick.Window 2.15
import "pages"

Window {
    id: mainWindow
    width: 800
    height: 480
    minimumWidth: 800
    maximumWidth: 800
    minimumHeight: 480
    maximumHeight: 480
    visible: true
    visibility: bridge.fullscreen ? Window.FullScreen : Window.Windowed
    color: "black"
    title: "Bullet-Time Camera"

    Loader {
        anchors.fill: parent
        active: bridge.state !== "STARTING"
        sourceComponent: {
            if (bridge.route === "progress") return progressPage
            if (bridge.route === "review") return reviewPage
            if (bridge.route === "preview") return previewPage
            if (bridge.route === "control") return controlPage
            if (bridge.route === "library") return libraryPage
            if (bridge.route === "viewer") return viewerPage
            return readyPage
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: bridge.state === "STARTING"
        color: "black"
        Image {
            anchors.fill: parent
            source: bridge.startupLogo
            fillMode: Image.PreserveAspectFit
        }
    }

    onFrameSwapped: bridge.framePresented()

    Component { id: readyPage; ReadyPage {} }
    Component { id: progressPage; ProgressPage {} }
    Component { id: reviewPage; ReviewPage {} }
    Component { id: previewPage; PreviewPage {} }
    Component { id: controlPage; ControlCenterPage {} }
    Component { id: libraryPage; LibraryPage {} }
    Component { id: viewerPage; ViewerPage {} }
}
