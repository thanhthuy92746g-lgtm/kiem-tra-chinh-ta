from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

COLORS = {"ink": "#182b3a", "paper": "#ffffff", "muted": "#435768", "accent": "#126b63"}


def apply_theme(app):
    app.setStyle("Fusion")
    hints = app.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme(Qt.ColorScheme.Light)
    palette = QPalette()
    roles = {QPalette.Window: "#f3f6f8", QPalette.WindowText: COLORS["ink"],
             QPalette.Base: COLORS["paper"], QPalette.AlternateBase: "#f0f5f5",
             QPalette.Text: COLORS["ink"], QPalette.Button: "#edf3f4",
             QPalette.ButtonText: COLORS["ink"], QPalette.Highlight: COLORS["accent"],
             QPalette.HighlightedText: "#ffffff", QPalette.ToolTipBase: "#ffffff",
             QPalette.ToolTipText: COLORS["ink"], QPalette.PlaceholderText: COLORS["muted"]}
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#657585"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#657585"))
    app.setPalette(palette)
    app.setStyleSheet("""
        QWidget { font-family: 'Segoe UI', sans-serif; font-size: 13px; }
        QMainWindow { background: #f3f6f8; }
        QToolBar { spacing: 7px; padding: 8px; border: none; }
        QToolButton, QPushButton { padding: 7px 12px; border-radius: 5px; }
        QPushButton:focus, QToolButton:focus { border: 1px solid #126b63; }
        QTextEdit, QTableWidget { border: 1px solid #d6e1e7; border-radius: 6px; }
        QHeaderView::section { background: #e9f0f3; padding: 8px; border: none; font-weight: 600; }
        QComboBox { min-height: 27px; padding: 2px 5px; }
        QStatusBar { color: #435768; padding: 4px; }
    """)
