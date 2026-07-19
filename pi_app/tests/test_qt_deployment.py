import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class QtDeploymentContractTests(unittest.TestCase):
    def test_debian_qt_packages_exclude_effects_and_multimedia(self):
        requirements = (REPO_ROOT / "pi_app" / "system-requirements.txt").read_text(
            encoding="utf-8"
        )
        for package in (
            "python3-pyside6.qtquick",
            "qml6-module-qtquick-controls",
            "qml6-module-qtquick-layouts",
            "qml6-module-qtqml-workerscript",
            "qt6-wayland",
        ):
            self.assertIn(package, requirements.splitlines())
        self.assertNotIn("effects", requirements.lower())
        self.assertNotIn("multimedia", requirements.lower())

    def test_installer_keeps_rollback_and_service_forces_wayland(self):
        installer = (REPO_ROOT / "pi_app" / "scripts" / "install_boot_experience.sh").read_text(
            encoding="utf-8"
        )
        service = (REPO_ROOT / "pi_app" / "systemd" / "bullet-time-ui.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("python3-tk", installer)
        self.assertIn("x11-apps", installer)
        self.assertIn("Environment=QT_QPA_PLATFORM=wayland", service)
        self.assertNotIn("Environment=DISPLAY=", service)

    def test_verifier_loads_qt_qml_and_checks_wayland(self):
        verifier = (REPO_ROOT / "pi_app" / "scripts" / "verify_boot_experience.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("from PySide6 import QtCore, QtGui, QtQml, QtQuick", verifier)
        self.assertIn("verify_qml", verifier)
        self.assertIn("QT_QPA_PLATFORM=wayland", verifier)
        self.assertIn("Xwayland is not running", verifier)

    def test_first_frame_and_metrics_use_window_frame_swaps(self):
        qml = (REPO_ROOT / "pi_app" / "bullettime" / "qml" / "Main.qml").read_text(encoding="utf-8")
        runtime = (REPO_ROOT / "pi_app" / "bullettime" / "qt_ui.py").read_text(encoding="utf-8")
        self.assertIn("onFrameSwapped: bridge.framePresented()", qml)
        self.assertIn('objectName: "startupLogo"', qml)
        self.assertIn('first_frame["callback"] = start_runtime', runtime)
        self.assertIn("bridge.setParent(engine)", runtime)
        self.assertIn("receiver.automatic_run_completed.is_set()", runtime)
        self.assertIn("QTimer.singleShot(1000, app.quit)", runtime)
        self.assertNotIn("QtMultimedia", qml + runtime)


if __name__ == "__main__":
    unittest.main()
