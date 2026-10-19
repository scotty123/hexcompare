"""HexCompare 0.1.2 — PyQt6 desktop UI."""
import sys
from html import escape
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget, QHeaderView,
)
from core import compare, load_binary, load_intel_hex

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HexCompare 0.1.2")
        self.resize(1250, 720)
        self.data = [None, None]
        self.paths = [None, None]
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        bar = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Intel HEX", "Binary"])
        self.mode.currentIndexChanged.connect(self.reset)
        bar.addWidget(self.mode)
        for i in range(2):
            button = QPushButton(f"Open file {i + 1}")
            button.clicked.connect(lambda _=False, index=i: self.open_file(index))
            bar.addWidget(button)
        self.differences_only = QCheckBox("Only differing blocks")
        self.differences_only.setChecked(True)
        self.differences_only.toggled.connect(self.refresh)
        bar.addWidget(self.differences_only)
        bar.addWidget(QLabel('Diff layout:'))
        self.diff_layout = QComboBox()
        self.diff_layout.addItems(['Side by side', 'Stacked'])
        self.diff_layout.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.diff_layout)
        layout.addLayout(bar)
        self.paths_label = QLabel("Choose two files.")
        layout.addWidget(self.paths_label)
        self.summary = QLabel("")
        layout.addWidget(self.summary)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Address", "File 1 HEX", "File 2 HEX", "File 1 ASCII", "File 2 ASCII"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.table)

    def reset(self):
        self.data = [None, None]
        self.paths = [None, None]
        self.paths_label.setText("Choose two files.")
        self.refresh()

    def open_file(self, index):
        filters = "Intel HEX (*.hex *.ihx *.ihex);;All files (*)" if self.mode.currentIndex() == 0 else "All files (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", filters)
        if not path:
            return
        try:
            loaded = load_intel_hex(path) if self.mode.currentIndex() == 0 else load_binary(path)
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.critical(self, "Invalid file", str(exc))
            return
        self.data[index] = loaded
        self.paths[index] = path
        self.paths_label.setText("   |   ".join(
            f"File {i + 1}: {Path(p).name if p else '—'}" for i, p in enumerate(self.paths)
        ))
        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        if any(d is None for d in self.data):
            self.summary.setText("Select two files to compare.")
            return
        left, right = self.data
        result = compare(left, right)
        self.summary.setText(
            f"Changed: {len(result.changed):,}    Modified: {result.modified:,}    "
            f"Added: {result.added:,}    Removed: {result.removed:,}    "
            f"Identical: {result.identical:,}    Changed blocks: {len(result.blocks):,}"
        )
        blocks = result.blocks if self.differences_only.isChecked() else tuple(
            sorted({address // 16 * 16 for address in left.keys() | right.keys()})
        )
        changed = set(result.changed)
        stacked = self.diff_layout.currentIndex() == 1
        self.table.setColumnCount(4 if stacked else 5)
        self.table.setHorizontalHeaderLabels(
            ['Address', 'File', 'HEX', 'ASCII'] if stacked else
            ['Address', 'File 1 HEX', 'File 2 HEX', 'File 1 ASCII', 'File 2 ASCII']
        )
        self.table.setUpdatesEnabled(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        if stacked:
            widths = [105, 75, 490, 185]
        else:
            widths = [105, 490, 490, 185, 185]
        for col, width in enumerate(widths):
            header.resizeSection(col, width)
        try:
            self.table.setRowCount(len(blocks) * (2 if stacked else 1))
            for row, start in enumerate(blocks):
                if not stacked:
                    self.table.setItem(row, 0, QTableWidgetItem(f"{start:08X}"))
                for side, memory in enumerate((left, right)):
                    hex_values, ascii_values = [], []
                    for address in range(start, start + 16):
                        byte = memory.get(address)
                        h = f"{byte:02X}" if byte is not None else "--"
                        c = escape(chr(byte)) if byte is not None and 32 <= byte <= 126 else ("." if byte is not None else "&nbsp;")
                        if address in changed:
                            h = f'<span style="color:#e02020;font-weight:bold">{h}</span>'
                            c = f'<span style="color:#e02020;font-weight:bold">{c}</span>'
                        hex_values.append(h)
                        ascii_values.append(c)
                    target_row = row * 2 + side if stacked else row
                    if stacked:
                        self.table.setItem(target_row, 0, QTableWidgetItem(f'{start:08X}'))
                        self.table.setItem(target_row, 1, QTableWidgetItem(f'File {side + 1}'))
                    for column, content in ((2 if stacked else side + 1, "&nbsp;".join(hex_values)), (3 if stacked else side + 3, "".join(ascii_values))):
                        widget = QTextBrowser()
                        widget.setFrameShape(QTextBrowser.Shape.NoFrame)
                        widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                        widget.setStyleSheet("background:transparent;border:0;padding:0")
                        widget.setHtml(
                            '<div style="font-family:Consolas,monospace;font-size:10pt;white-space:nowrap">'
                            + content + "</div>"
                        )
                        self.table.setCellWidget(target_row, column, widget)
                    self.table.setRowHeight(target_row, 28)
        finally:
            self.table.setUpdatesEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
