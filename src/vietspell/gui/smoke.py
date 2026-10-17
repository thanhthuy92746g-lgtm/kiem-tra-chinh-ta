"""Explicit developer smoke check, also available in the packaged GUI."""
import json
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .app import MainWindow
from .theme import apply_theme


def run_smoke(file, model_dir=None, screenshot=None, report_path=None, timeout_ms=30000, profile="HC-ND30"):
    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    window = MainWindow(model_dir)
    window.show()
    window.open_file(file)
    window.profile.setCurrentIndex(window.profile.findData(profile))
    if window.session is None:
        window.close()
        return 2
    window.check()
    poll, timeout = QTimer(), QTimer()
    timeout.setSingleShot(True)
    code = [2]
    expired = [False]

    def finished():
        if window.worker is not None:
            return
        payload = {"passed": False, "timed_out": expired[0], "profile": profile}
        if window.session.result is not None and not expired[0]:
            actual = {(i.text, i.suggestions[0].text) for i in window.session.result.issues if i.editable}
            if profile == "DANG-HD05":
                rules = {i.rule_id for i in window.session.result.issues}
                passed = {"PARTY_NUMBER_FORMAT", "ELEMENT_BOLD_POSITION", "ELEMENT_SIZE_RECIPIENTS"} <= rules
            else:
                passed = {("an", "ăn"), (".", "?"), ("di", "đi")} <= actual
            payload.update({"passed": passed, "findings": window.table.rowCount(),
                            "required_corrections_present": passed})
            code[0] = 0 if payload["passed"] else 1
            if screenshot:
                window.grab().save(str(screenshot))
        if report_path:
            Path(report_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        poll.stop()
        timeout.stop()
        window.close()
        app.quit()

    def expire():
        expired[0] = True
        window.cancel()
        # Keep the event loop alive until the worker finishes; never destroy a live QThread.

    poll.timeout.connect(finished)
    timeout.timeout.connect(expire)
    poll.start(50)
    timeout.start(timeout_ms)
    app.exec()
    return code[0]
