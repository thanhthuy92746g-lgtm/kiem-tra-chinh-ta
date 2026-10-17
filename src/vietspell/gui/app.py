import sys
from collections import Counter

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QAction, QColor, QKeySequence, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QMainWindow, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QTextEdit,
    QToolBar, QVBoxLayout, QWidget)

from ..core.detector import CheckerConfig, SENSITIVITY_PRESETS
from ..core.legal import PROFILES
from ..core.ngram import NgramModel
from ..core.tokenizer import tokenize
from ..core.types import Issue
from ..paths import data_dir
from ..service import CheckCancelled, DocumentSession
from .theme import apply_theme

LEVELS = {"high": "Cao", "medium": "Vừa", "low": "Nhẹ"}
KINDS = {"format": "Biên tập", "document": "Định dạng Word", "element": "Thành phần thể thức", "diacritic": "Thiếu dấu", "capitalization": "Viết hoa", "abbrev": "Viết tắt", "unknown": "Âm tiết lạ", "context": "Ngữ cảnh", "confusion": "Nhầm lẫn", "fuzzy": "Gần giống ký tự"}


class NoticeBar(QFrame):
    filter_high = Signal()
    PALETTES = {"opened": ("#e8f1ff", "#173b65"), "running": ("#e8f1ff", "#173b65"),
                "clean": ("#e4f5ec", "#165437"), "light": ("#fff4d6", "#664500"),
                "issues": ("#ffe8e5", "#75271d"), "error": ("#ffe8e5", "#75271d")}

    def __init__(self):
        super().__init__()
        self.state = "opened"
        layout = QHBoxLayout(self)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.PlainText)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.button = QPushButton("Chỉ xem lỗi nặng")
        self.button.clicked.connect(self.filter_high)
        layout.addWidget(self.label, 1)
        layout.addWidget(self.button)
        self.show_notice("opened", "Mở một tệp Word (.docx) để bắt đầu. Tài liệu được xử lý hoàn toàn trên máy của bạn.")

    def show_notice(self, state, text, high_count=0):
        self.state = state
        background, foreground = self.PALETTES[state]
        self.setStyleSheet(f"NoticeBar {{background: {background}; border-radius: 7px;}} QLabel {{color: {foreground}; padding: 6px;}}")
        self.label.setText(text)
        self.button.setVisible(high_count > 0)
        self.button.setText(f"Chỉ xem {high_count} lỗi nặng")

    def completed(self, stats):
        high, medium, low = (stats.levels.get(k, 0) for k in ("high", "medium", "low"))
        tail = f"Đã soát {stats.words} từ trong {stats.paragraphs} đoạn."
        if stats.total == 0:
            self.show_notice("clean", "🎉 Không phát hiện lỗi nào trong phạm vi kiểm tra.\n"+tail)
        elif not high and not medium:
            self.show_notice("light", f"✅ Chỉ có {low} lỗi nhẹ — bạn có thể xem và cân nhắc bỏ qua.\n"+tail)
        else:
            most = ", ".join(f"{KINDS.get(k, k)} ({v})" for k, v in Counter(stats.kinds).most_common(3))
            self.show_notice("issues" if high else "light", f"⚠ Phát hiện {stats.total} lỗi: {high} mức cao, {medium} mức vừa, {low} mức nhẹ.\n"
                +(f"Nên xem {high} lỗi mức cao trước. " if high else "Hãy xem các gợi ý mức vừa trước. ")
                +"Bạn có thể chọn từng chỗ sửa trước khi xuất.\nNhiều nhất: "+most+". "+tail, high)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Độ nhạy soát lỗi")
        layout = QFormLayout(self)
        self.preset = QComboBox()
        self.preset.addItems(SENSITIVITY_PRESETS)
        self.preset.setCurrentIndex(1)
        layout.addRow("Mức dựng sẵn", self.preset)
        self.spins = {}
        for name, label in (("min_delta_confusion", "Ngưỡng nhầm lẫn"), ("min_delta_fuzzy", "Ngưỡng gần đúng"), ("min_delta_diacritic", "Ngưỡng khôi phục dấu"), ("context_threshold", "Cổng tìm theo ngữ cảnh")):
            box = QDoubleSpinBox()
            box.setRange(-10 if name == "context_threshold" else 0, 20)
            box.setSingleStep(0.1)
            box.setValue(getattr(config, name))
            self.spins[name] = box
            layout.addRow(label, box)
        self.preset.currentTextChanged.connect(self.apply_preset)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def apply_preset(self, label):
        for name, value in zip(("min_delta_confusion", "min_delta_fuzzy", "min_delta_diacritic"), SENSITIVITY_PRESETS[label]):
            self.spins[name].setValue(value)

    def config(self):
        return CheckerConfig(**{k: s.value() for k, s in self.spins.items()})


class CheckWorker(QThread):
    progress = Signal(int, int)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, session, profile, config, parent=None):
        super().__init__(parent)
        self.session, self.profile, self.config = session, profile, config

    def run(self):
        try:
            self.session.check(self.profile, self.config, self.progress.emit, self.isInterruptionRequested)
            self.completed.emit(self.session)
        except CheckCancelled:
            self.failed.emit("Đã dừng soát lỗi. Bạn có thể bấm F5 để chạy lại.")
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, model_dir=None):
        super().__init__()
        self.model_dir = model_dir or data_dir()
        self.session = None
        self.worker = None
        self.config = CheckerConfig()
        self.model_summary = ""
        self._close_when_done = False
        self.setWindowTitle("VietSpell · Soát Word ngoại tuyến")
        self.resize(1360, 850)
        toolbar = QToolBar("Tệp và soát lỗi")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.open_action = self.action(toolbar, "Mở tệp…", self.open_dialog, QKeySequence.Open)
        self.check_action = self.action(toolbar, "Soát lỗi (F5)", self.check, "F5")
        self.cancel_action = self.action(toolbar, "Dừng", self.cancel)
        self.cancel_action.setEnabled(False)
        self.accept_action = self.action(toolbar, "Chấp nhận tất cả", lambda: self.select_all(True))
        self.ignore_action = self.action(toolbar, "Bỏ qua tất cả", lambda: self.select_all(False))
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Loại văn bản: "))
        self.profile = QComboBox()
        for code, p in PROFILES.items():
            self.profile.addItem(p.title, code)
        toolbar.addWidget(self.profile)
        self.action(toolbar, "Độ nhạy…", self.settings)
        self.addToolBarBreak()
        exports = QToolBar("Xuất và lọc")
        exports.setMovable(False)
        self.addToolBar(exports)
        exports.addWidget(QLabel("Xuất dưới dạng: "))
        self.mode = QComboBox()
        for code, label in (("RED", "Chữ đỏ ở chỗ sửa"), ("TRACK", "Theo dõi thay đổi"), ("PLAIN", "Sửa giữ định dạng"), ("HIGHLIGHT", "Tô sáng mọi chỗ nghi vấn")):
            self.mode.addItem(label, code)
        exports.addWidget(self.mode)
        self.export_action = self.action(exports, "Xuất tệp…", self.export)
        self.report_action = self.action(exports, "Xuất báo cáo…", self.report)
        exports.addSeparator()
        exports.addWidget(QLabel("Mức độ: "))
        self.filter = QComboBox()
        self.filter.addItem("Tất cả", None)
        for code, name in LEVELS.items():
            self.filter.addItem(name, code)
        self.filter.currentIndexChanged.connect(self.filter_rows)
        exports.addWidget(self.filter)
        content = QWidget()
        layout = QVBoxLayout(content)
        self.notice = NoticeBar()
        self.notice.filter_high.connect(lambda: self.filter.setCurrentIndex(1))
        layout.addWidget(self.notice)
        self.model_notice = QLabel()
        self.model_notice.setWordWrap(True)
        self.model_notice.setTextFormat(Qt.PlainText)
        self.model_notice.setStyleSheet("color: #664500; padding: 6px;")
        layout.addWidget(self.model_notice)
        splitter = QSplitter()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Nội dung Word sẽ hiện ở đây. Tệp gốc luôn được giữ nguyên.")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Sửa?", "Từ nghi vấn", "Phương án thay thế", "Mức độ", "Loại lỗi"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 145)
        self.table.setColumnWidth(3, 65)
        self.table.setColumnWidth(4, 125)
        self.table.itemSelectionChanged.connect(self.jump_to_issue)
        splitter.addWidget(self.text)
        splitter.addWidget(self.table)
        splitter.setSizes([550, 750])
        layout.addWidget(splitter, 1)
        self.detail = QLabel("Chọn một lỗi để xem nguyên nhân và căn cứ.")
        self.detail.setTextFormat(Qt.PlainText)
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.detail)
        self.setCentralWidget(content)
        self.set_controls(False)
        try:
            from pathlib import Path
            with NgramModel(Path(self.model_dir) / "ngram.sqlite") as model:
                if model.meta.get("quality") == "demo":
                    self.model_notice.setText("MÔ HÌNH MẪU · Chỉ để thử chức năng. Cần huấn luyện ngữ liệu hỗn hợp trước khi soát văn bản thực tế.")
                else:
                    vocab = f"{model.vocab:,}".replace(",", ".")
                    self.model_summary = f"Mô hình ngoại tuyến · {vocab} âm tiết trong từ vựng. Hãy duyệt từng gợi ý theo ngữ cảnh trước khi xuất."
                    self.model_notice.setText(self.model_summary)
        except Exception as exc:
            self.notice.show_notice("error", f"Chưa nạp được mô hình ngôn ngữ: {exc}. Xem README để chuẩn bị data/.")

    def action(self, toolbar, label, callback, shortcut=None):
        action = QAction(label, self)
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        toolbar.addAction(action)
        return action

    def set_controls(self, checked):
        for action in (self.accept_action, self.ignore_action, self.export_action, self.report_action):
            action.setEnabled(checked)
        self.check_action.setEnabled(self.session is not None)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở tệp Word", "", "Word (*.docx)")
        if path:
            self.open_file(path)

    def open_file(self, path):
        try:
            session = DocumentSession(path, self.model_dir)
            self.session = session
            self.text.setPlainText(session.read.text)
            self.text.setExtraSelections([])
            self.table.setRowCount(0)
            self.detail.setText("Bấm Soát lỗi (F5) để kiểm tra.")
            self.set_controls(False)
            words = len(tokenize(session.read.text))
            self.notice.show_notice("opened", f"💡 Đã mở {session.path.name} — {len(session.read.blocks)} đoạn, {words} từ.\nBấm Soát lỗi (F5) để kiểm tra chính tả và thể thức.")
            self.setWindowTitle(f"{session.path.name} · VietSpell")
        except Exception as exc:
            self.notice.show_notice("error", f"Không mở được tệp: {exc}")

    def check(self):
        if self.session is None or self.worker is not None:
            return
        self.session.result = None
        self.table.setRowCount(0)
        self.text.setExtraSelections([])
        self.set_controls(False)
        self.open_action.setEnabled(False)
        self.check_action.setEnabled(False)
        self.profile.setEnabled(False)
        self.cancel_action.setEnabled(True)
        self.notice.show_notice("running", "⏳ Đang soát lỗi… 0%. Văn bản dài có thể mất vài phút, bạn chờ một chút nhé.")
        self.worker = CheckWorker(self.session, self.profile.currentData(), self.config, self)
        self.worker.progress.connect(self.progress)
        self.worker.completed.connect(self.completed)
        self.worker.failed.connect(lambda message: self.notice.show_notice("error", "Không hoàn tất soát lỗi: "+message))
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def progress(self, count, total):
        self.notice.show_notice("running", f"⏳ Đang soát lỗi… {round(100*count/max(1, total))}% · Đã xử lý {count}/{total} đoạn.\nVăn bản dài có thể mất vài phút, bạn chờ một chút nhé.")

    def completed(self, session):
        self.table.setRowCount(len(session.result.issues))
        highlights = []
        for row, issue in enumerate(session.result.issues):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable if issue.editable and "\n" not in issue.text else Qt.NoItemFlags)
            check.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, check)
            item = QTableWidgetItem(issue.text[:90] or "(toàn tài liệu)")
            item.setToolTip(issue.message+"\n"+issue.basis)
            self.table.setItem(row, 1, item)
            combo = QComboBox()
            if issue.editable and "\n" not in issue.text:
                combo.setEditable(True)
                combo.addItems([s.text for s in issue.suggestions])
            else:
                combo.addItem("— sửa trực tiếp trong Word —")
                combo.setEnabled(False)
            self.table.setCellWidget(row, 2, combo)
            self.table.setItem(row, 3, QTableWidgetItem(LEVELS[issue.severity]))
            self.table.setItem(row, 4, QTableWidgetItem(KINDS.get(issue.kind, issue.kind)))
            if issue.end > issue.start and len(highlights) < 1000:
                selection = QTextEdit.ExtraSelection()
                selection.cursor = self.cursor_for(issue.start, issue.end)
                selection.format.setBackground(QColor("#ffd7d0" if issue.severity == "high" else "#fff0bc"))
                highlights.append(selection)
        self.text.setExtraSelections(highlights)
        self.filter_rows()
        self.notice.completed(session.stats)
        self.model_notice.setText("\n".join(filter(None, [self.model_summary, *session.result.warnings])))
        self.statusBar().showMessage(f"{session.stats.paragraphs} đoạn · {session.stats.words} từ · {session.stats.total} lỗi · {session.stats.elapsed:.2f} giây")
        self.set_controls(True)

    def worker_finished(self):
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self.open_action.setEnabled(True)
        self.check_action.setEnabled(self.session is not None)
        self.profile.setEnabled(True)
        self.cancel_action.setEnabled(False)
        if self._close_when_done:
            self.close()

    def cancel(self):
        if self.worker:
            self.worker.requestInterruption()

    def closeEvent(self, event):
        if self.worker is not None:
            self._close_when_done = True
            self.worker.requestInterruption()
            event.ignore()
        else:
            event.accept()

    def select_all(self, checked):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def filter_rows(self):
        if self.session and self.session.result:
            for row, issue in enumerate(self.session.result.issues):
                self.table.setRowHidden(row, self.filter.currentData() not in {None, issue.severity})

    def cursor_for(self, start, end):
        # QTextCursor uses UTF-16 positions, Python uses Unicode code points.
        text = self.session.read.text
        cursor = self.text.textCursor()
        cursor.setPosition(len(text[:start].encode("utf-16-le"))//2)
        cursor.setPosition(len(text[:end].encode("utf-16-le"))//2, QTextCursor.KeepAnchor)
        return cursor

    def jump_to_issue(self):
        row = self.table.currentRow()
        if self.session and self.session.result and 0 <= row < len(self.session.result.issues):
            issue = self.session.result.issues[row]
            self.text.setTextCursor(self.cursor_for(issue.start, issue.end))
            self.text.ensureCursorVisible()
            self.detail.setText(issue.message+"\nCăn cứ: "+issue.basis)

    def export(self):
        if self.session is None or self.session.result is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất bản Word mới", str(self.session.path.with_stem(self.session.path.stem+"-da-soat")), "Word (*.docx)")
        if not path:
            return
        try:
            selections = []
            if self.mode.currentData() == "HIGHLIGHT":
                selections = self.session.highlight_selections()
            else:
                for row, issue in enumerate(self.session.result.issues):
                    if self.table.item(row, 0).checkState() == Qt.Checked:
                        selections.append((issue, self.table.cellWidget(row, 2).currentText()))
            self.session.export(path, selections, self.mode.currentData())
            self.notice.show_notice("opened", f"Đã xuất {len(selections)} chỗ được chọn vào {path}.\nTệp gốc được giữ nguyên; các lỗi định dạng cần chỉnh trực tiếp trong Word.")
        except Exception as exc:
            self.notice.show_notice("error", f"Không xuất được tệp: {exc}")

    def report(self):
        if self.session is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất báo cáo", "vietspell-report.json", "JSON (*.json)")
        if path:
            try:
                self.session.report(path)
                self.notice.show_notice("opened", "Đã lưu báo cáo: "+path)
            except Exception as exc:
                self.notice.show_notice("error", "Không lưu được báo cáo: "+str(exc))

    def settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.config()
            self.notice.show_notice("opened", "Đã đổi độ nhạy. Bấm F5 để soát lại với thiết lập mới.")


def run(model_dir=None):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    apply_theme(app)
    window = MainWindow(model_dir)
    window.show()
    return app.exec()
