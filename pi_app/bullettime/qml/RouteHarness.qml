import QtQuick 2.15
import QtQuick.Window 2.15
import "pages"

Window {
    id: harnessWindow
    objectName: "routeHarness"
    width: 800
    height: 480
    visible: true
    color: "black"

    function argumentValue(prefix, fallback) {
        for (var index = 0; index < Qt.application.arguments.length; index++) {
            var argument = Qt.application.arguments[index]
            if (argument.indexOf(prefix) === 0)
                return argument.substring(prefix.length)
        }
        return fallback
    }

    QtObject {
        id: bridge
        property string route: harnessWindow.argumentValue("--route=", "ready")
        property string state: route === "progress" ? "LOADING" : "READY"
        property string message: route === "review" ? "CAMERA 4 UNAVAILABLE · 3 VIEWS SAVED" : ""
        property string usbStatus: "saved"
        property string capturePhase: "transferring"
        property var cameraStates: route === "progress"
            ? ["complete", "transferring", "transferring", "waiting"]
            : ["ready", "ready", "ready", route === "review" ? "error" : "ready"]
        property var connectedCameraIds: [1, 2, 3, 4]
        property var failedCameraIds: route === "review" ? [4] : []
        property int viewCount: route === "review" ? 3 : 4
        property int viewerViewCount: 4
        property string previewPlaceholder: Qt.resolvedUrl("../../../assets/ui/preview-placeholder.png")
        property string startupLogo: Qt.resolvedUrl("../../../assets/Logo_800x480.png")
        property string fixtureMedia: harnessWindow.argumentValue("--media=", previewPlaceholder)
        property string imageSource: fixtureMedia
        property int selectedLibraryIndex: 0
        property string catalogStatus: "ready"
        property string catalogMessage: "Fixture catalog"
        property bool fullscreen: false
        property bool canCapture: true
        property var libraryItems: [
            {"title": "20260718T175104Z_04b69c0b", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T171500Z_partial", "viewCount": 3, "partial": true, "thumbnail": fixtureMedia},
            {"title": "20260718T164500Z", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T160000Z", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T153000Z", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T150000Z", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T143000Z", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia}
        ]

        function capture() { return false }
        function navigate(nextRoute) { route = nextRoute; return true }
        function openLibraryItem(index) { selectedLibraryIndex = index; return true }
        function selectLibraryItem(index) { selectedLibraryIndex = index; return true }
        function framePresented() {}
    }

    QtObject { objectName: "startupLogo" }

    Loader {
        anchors.fill: parent
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

    Component { id: readyPage; ReadyPage {} }
    Component { id: progressPage; ProgressPage {} }
    Component { id: reviewPage; ReviewPage {} }
    Component { id: previewPage; PreviewPage {} }
    Component { id: controlPage; ControlCenterPage {} }
    Component { id: libraryPage; LibraryPage {} }
    Component { id: viewerPage; ViewerPage {} }
}
