"""Run a bounded QML first-frame smoke and emit machine-readable evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from pi_app.qt_validation.headless import qt_environment, sha256_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qml", type=Path, required=True, help="root QML file")
    parser.add_argument("--platform", choices=("offscreen", "wayland"), default="offscreen")
    parser.add_argument("--timeout-ms", type=int, default=5000)
    parser.add_argument("--required-object", default="startupLogo")
    parser.add_argument("--screenshot", type=Path)
    return parser


def _emit(report: dict[str, Any]) -> int:
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 100 <= args.timeout_ms <= 60_000:
        return _emit({"status": "FAIL", "errors": ["timeout must be between 100 and 60000 ms"]})
    qml_path = args.qml.resolve()
    if not qml_path.is_file():
        return _emit({"status": "FAIL", "errors": [f"QML file not found: {qml_path}"]})

    os.environ.update(qt_environment(args.platform))
    try:
        from PySide6.QtCore import QObject, QTimer, QUrl, qInstallMessageHandler
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtQml import QQmlApplicationEngine
    except ImportError as exc:
        return _emit({"status": "FAIL", "errors": [f"PySide6 import failed: {exc}"]})

    messages: list[str] = []

    def message_handler(message_type, context, message):
        del context
        if (
            "Warning" in str(message_type)
            or "Critical" in str(message_type)
            or "Fatal" in str(message_type)
        ):
            messages.append(message)

    qInstallMessageHandler(message_handler)
    application = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    engine = QQmlApplicationEngine()
    report: dict[str, Any] = {
        "status": "FAIL",
        "platform": args.platform,
        "qml": str(qml_path),
        "root_object_count": 0,
        "frame_swapped": False,
        "required_object": args.required_object,
        "required_object_found": False,
        "errors": [],
    }

    def finish_error(error: str) -> None:
        report["errors"].append(error)
        application.exit(1)

    QTimer.singleShot(args.timeout_ms, lambda: finish_error("QML smoke timed out"))
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    roots = engine.rootObjects()
    report["root_object_count"] = len(roots)
    if not roots:
        report["errors"].append("QML engine returned zero root objects")
        if messages:
            report["errors"].extend(messages)
        return _emit(report)

    root = roots[0]
    required = root.findChild(QObject, args.required_object)
    report["required_object_found"] = required is not None
    if required is None:
        report["errors"].append(f"required object not found: {args.required_object}")

    frame_signal = getattr(root, "frameSwapped", None)
    if frame_signal is None:
        report["errors"].append("root object has no frameSwapped signal")
        return _emit(report)

    def on_frame_swapped() -> None:
        report["frame_swapped"] = True
        report["width"] = int(root.width())
        report["height"] = int(root.height())
        if (report["width"], report["height"]) != (800, 480):
            report["errors"].append(
                f"root is {report['width']}x{report['height']}; expected 800x480"
            )
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            image = root.grabWindow()
            if not image.save(str(args.screenshot), "PNG"):
                report["errors"].append("failed to save first-frame screenshot")
            else:
                report["screenshot"] = str(args.screenshot)
                report["screenshot_sha256"] = sha256_file(args.screenshot)
        report["errors"].extend(messages)
        if not report["errors"]:
            report["status"] = "PASS"
        application.exit(0 if report["status"] == "PASS" else 1)

    frame_signal.connect(on_frame_swapped)
    application.exec()
    return _emit(report)


if __name__ == "__main__":
    raise SystemExit(main())
