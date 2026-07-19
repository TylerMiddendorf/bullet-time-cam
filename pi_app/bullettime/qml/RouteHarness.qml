import QtQuick 2.15
import QtQuick.Window 2.15
import "pages"

Window {
    id: harnessWindow
    objectName: "routeHarness"
    width: 800
    height: 480
    minimumWidth: 800
    maximumWidth: 800
    minimumHeight: 480
    maximumHeight: 480
    flags: Qt.FramelessWindowHint
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
        property string storageUsedText: "18.6 GB"
        property string storageAvailableText: "231.4 GB"
        property real storageUsedFraction: 0.0744
        property bool deleteConfirmationVisible: fixtureMedia === "confirm-delete"
        property string pendingDeleteTitle: "codex_delete_test_95961ff"
        property bool fullscreen: false
        property bool canCapture: true
        property var libraryItems: [
            {"title": "20260718T175104Z_04b69c0b", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T171500Z_a31c4f90", "viewCount": 3, "partial": true, "thumbnail": fixtureMedia},
            {"title": "20260718T164500Z_28c8b391", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T160000Z_d5a0082e", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T153000Z_b1c5e607", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T150000Z_83f10a9c", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia},
            {"title": "20260718T143000Z_091b6aa4", "viewCount": 4, "partial": false, "thumbnail": fixtureMedia}
        ]

        function capture() { return false }
        function navigate(nextRoute) { route = nextRoute; return true }
        function openLibraryItem(index) { selectedLibraryIndex = index; return true }
        function selectLibraryItem(index) { selectedLibraryIndex = index; return true }
        function promptDeleteSelected() {
            pendingDeleteTitle = libraryItems[selectedLibraryIndex].title
            deleteConfirmationVisible = true
            return true
        }
        function cancelDelete() { deleteConfirmationVisible = false }
        function confirmDelete() { deleteConfirmationVisible = false; return true }
        function framePresented() {}
    }

    QtObject { objectName: "startupLogo" }

    Loader {
        anchors.fill: parent
        sourceComponent: {
            if (bridge.route === "progress") return progressPage
            if (bridge.route === "review") return reviewPage
            if (bridge.route === "capture") return capturePage
            if (bridge.route === "control") return controlPage
            if (bridge.route === "library") return libraryPage
            if (bridge.route === "viewer") return viewerPage
            return readyPage
        }
    }

    Component { id: readyPage; ReadyPage {} }
    Component { id: progressPage; ProgressPage {} }
    Component { id: reviewPage; ReviewPage {} }
    Component { id: capturePage; CapturePage {} }
    Component { id: controlPage; ControlCenterPage {} }
    Component { id: libraryPage; LibraryPage {} }
    Component { id: viewerPage; ViewerPage {} }
}
