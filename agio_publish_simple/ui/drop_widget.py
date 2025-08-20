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
                 allow_sequence=False,
                 allow_directory=False
                 ):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.base_text = base_text
        self.accepted_extensions = accepted_extensions or []
        self.allow_multiple = allow_multiple
        self.allow_sequence = allow_sequence
        self.allow_directory = allow_directory

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

        self._last_valid_source = None
        self._last_valid_label = base_text

    def reset(self):
        self.setProperty("state", "default")
        self.style().unpolish(self)
        self.style().polish(self)
        self.label.setText(self.base_text)
        self.source = None
        self._last_valid_source = None
        self._last_valid_label = self.base_text

    def set_state(self, state):
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_source(self, source, label_text=None):
        self.source = source
        self._last_valid_source = source
        if label_text is not None:
            self._last_valid_label = label_text
        else:
            self._last_valid_label = self.label.text()
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
                # показываем ошибку
                self.set_state("error")
                self.label.setText(str(e))
                event.ignore()
                return
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        if self.property("state") == "error":
            self.set_state("default")
            self.label.setText(self._last_valid_label)
            self.source = self._last_valid_source
        else:
            if self._last_valid_source is None:
                self.reset()
            else:
                self.set_state("default")
                self.label.setText(self._last_valid_label)
                self.source = self._last_valid_source

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.update_source(file_paths)

    def update_source(self, paths):
        result_text = self.handle_files(paths)
        self.label.setText(str(result_text))
        self.set_source(paths, str(result_text))
        self.set_state("default")

    def is_extension_accepted(self, file_path):
        if Path(file_path).is_dir():
            return self.allow_directory
        return Path(file_path).suffix.lower() in self.accepted_extensions

    def handle_files(self, file_paths):
        """
        Get display string
        """
        if len(file_paths) == 1 and Path(file_paths[0]).is_dir():
            file_paths = [x for x in Path(file_paths[0]).iterdir() if x.is_file()]
        if seq := self.is_sequence_pattern(file_paths):
            self.set_source(file_paths, seq)
            return seq
        else:
            if len(file_paths) == 1:
                self.set_source(file_paths[0], Path(file_paths[0]).name)
                return Path(file_paths[0])
            else:
                txt = f'{file_paths[0]}\nTotal files:{len(file_paths)} files'
                self.set_source(file_paths, txt)
                return txt

    def check_input(self, files):
        if len(files) == 1 and Path(files[0]).is_dir():
            if not self.allow_directory:
                raise Exception("Directory not allowed")
            return

        if self.is_sequence_pattern(files):
            if not self.allow_sequence:
                raise Exception("Sequence pattern not allowed")

        for file in files:
            if not self.is_extension_accepted(file):
                raise Exception(f'Unsupported file format {os.path.splitext(file)[-1]}')

    def is_sequence_pattern(self, file_list: List[str]) -> Optional[str]:
        file_list = [Path(x) for x in file_list if Path(x).is_file()]
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
        if ext_pattern:
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

    accepted_types = ['.txt', '.py', '.png']
    widget = FileDropWidget(
        base_text="Drop File Here",
        accepted_extensions=accepted_types,
        allow_multiple=True,
        allow_sequence=True,
        allow_directory=True
    )
    widget.setWindowTitle("File Drop Widget")
    widget.resize(300, 150)
    widget.show()

    sys.exit(app.exec())
