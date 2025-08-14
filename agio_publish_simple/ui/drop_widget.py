from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QFrame, QFileDialog
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent
from typing import List, Optional
import sys
import os
import re


class FileDropWidget(QFrame):
    sourceChangedSignal = Signal()
    def __init__(self,
                 base_text="Drop File Here",
                 accepted_extensions=None,
                 allow_multiple=False,
                 allow_sequence=False
                 ):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.base_text = base_text
        self.accepted_extensions = accepted_extensions or []
        self.allow_multiple = allow_multiple
        self.allow_sequence = allow_sequence

        self.label = QLabel(base_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setAcceptDrops(True)
        self.setAutoFillBackground(True)
        self.setCursor(Qt.PointingHandCursor)

        self.reset()
        self.source = None

    def reset(self):
        self.setProperty("state", "default")
        self.style().unpolish(self)
        self.style().polish(self)
        self.label.setText(self.base_text)
        self.source = None

    def set_state(self, state):
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_source(self, source):
        self.source = source
        self.sourceChangedSignal.emit()

    def get_source(self):
        return self.source

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            try:
                self.check_input(file_paths)
                self.set_state("valid")
                event.acceptProposedAction()
            except Exception as e:
                self.set_state("error")
                self.label.setText(str(e))
                event.ignore()
                return
            # if not self.allow_multiple and len(urls) > 1:
            #     self.set_state("error")
            #     self.label.setText("Only one file allowed")
            #     event.ignore()
            #     return
            #
            # for url in urls:
            #     file_path = url.toLocalFile()
            #     if not self.is_extension_accepted(file_path):
            #         self.set_state("error")
            #         self.label.setText(f"Unsupported file: {os.path.basename(file_path)}")
            #         event.ignore()
            #         return
            #
            # self.set_state("valid")
            # event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.reset()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.update_source(file_paths)

    def update_source(self, paths):
        result_text = self.handle_files(paths)
        self.label.setText(str(result_text))
        self.set_state("default")

    def is_extension_accepted(self, file_path):
        return Path(file_path).suffix.lower() in self.accepted_extensions

    def handle_files(self, file_paths):
        """
        Get display string
        """
        self.set_source(file_paths)
        if seq := self.is_sequence_pattern(file_paths):
            return seq
        else:
            if len(file_paths) == 1:
                return Path(file_paths[0])
            else:
                return f'{file_paths[0]}\nTotal files:{len(file_paths)} files'

    def check_input(self, files):
        if self.is_sequence_pattern(files):
            if not self.allow_sequence:
                raise Exception("Sequence pattern not allowed")
        for file in files:
            if not self.is_extension_accepted(file):
                raise Exception(f'Unsupported file format {os.path.splitext(file)[-1]}')

    def is_sequence_pattern(self, file_list: List[str]) -> Optional[str]:
        """
        Возвращает паттерн файловой секвенции, если файлы имеют одинаковое имя и расширение,
        отличаясь только числовым суффиксом. Иначе возвращает None.

        Пример:
        ['render_001.exr', 'render_002.exr'] → 'render_*.exr'
        """
        if len(file_list) < 2:
            return None

        pattern = re.compile(r'^(.*?)(\d+)(\.[^.]+)$')

        parsed = []
        for file in file_list:
            basename = os.path.basename(file)
            match = pattern.match(basename)
            if not match:
                return None
            name, number, ext = match.groups()
            parsed.append((name, ext))
        dirname = Path(file_list[0]).parent.as_posix()
        print(dirname)
        base_name, base_ext = parsed[0]
        if all(name == base_name and ext == base_ext for name, ext in parsed):
            return f"{dirname}/{base_name}*{base_ext}"
        return None

    def mouseReleaseEvent(self, event, /):
        self.browse_files()
        super().mouseReleaseEvent(event)

    def browse_files(self):
        dialog = QFileDialog()
        ext_pattern = " ".join(f"*.{ext.strip('.')}" for ext in self.accepted_extensions)
        file_filter = f"Acceptable files ({ext_pattern})"
        dialog.setNameFilter(file_filter)
        if self.allow_multiple:
            dialog.setFileMode(QFileDialog.ExistingFiles)
        else:
            dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec():
            files = dialog.selectedFiles()
            if files:
                self.update_source(files)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Пример загрузки QSS стилей

    accepted_types = ['.txt', '.py', '.png']
    widget = FileDropWidget(
        base_text="Drop File Here",
        accepted_extensions=accepted_types,
        allow_multiple=True,
        allow_sequence=True
    )
    widget.setWindowTitle("File Drop Widget")
    widget.resize(300, 150)
    widget.show()

    sys.exit(app.exec())
