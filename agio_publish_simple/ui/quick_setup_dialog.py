import logging
import sys
import tempfile
from pathlib import Path

from agio.core.pkg.resources import get_res
from agio.core.settings import get_local_settings, save_local_settings
from agio.core.pkg import resources
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon

logger = logging.getLogger(__name__)


class QuickSetupDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_ly = QVBoxLayout(self)
        self.settings_gb = QGroupBox('Local Settings')
        self.form_ly = QFormLayout(self.settings_gb)
        self.projects_root_lb = QLabel("agio.drive Mount Point")
        self.form_ly.setWidget(0, QFormLayout.ItemRole.LabelRole, self.projects_root_lb)
        self.projects_root_le = QLineEdit(self.settings_gb)
        self.form_ly.setWidget(0, QFormLayout.ItemRole.FieldRole, self.projects_root_le)
        self.temp_lb = QLabel("Temp Dir")
        self.form_ly.setWidget(1, QFormLayout.ItemRole.LabelRole, self.temp_lb)
        self.temp_dir_le = QLineEdit(self.settings_gb)
        self.form_ly.setWidget(1, QFormLayout.ItemRole.FieldRole, self.temp_dir_le)
        self.main_ly.addWidget(self.settings_gb)
        self.save_btn = QPushButton('Save', clicked=self.save)
        self.main_ly.addWidget(self.save_btn)
        self.setWindowTitle('Quick Roots Settings')
        self.setWindowIcon(QIcon(resources.get_res('core/agio-icon.png')))
        self.resize(500, 160)
        self.init()

    def init(self):
        settings = self.load_settings()
        for root in settings:
            if root.name == 'projects':
                self.projects_root_le.setText(str(Path(root.path)))
            elif root.name == 'temp':
                self.temp_dir_le.setText(str(Path(root.path)))
        if not self.temp_dir_le.text():
            self.temp_dir_le.setText(tempfile.gettempdir())
        self.apply_style()

    def save(self):
        try:
            data = self.collect_data()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
            return
        self.save_settings(data)
        self.close()

    def apply_style(self):
        css_file = get_res('publish-simple/style.css')
        if not css_file:
            logger.warning('No style file found Simple Publish UI')
            return
        self.setStyleSheet(Path(css_file).read_text(encoding='utf-8'))

    def collect_data(self):
        if not self.projects_root_le.text().strip():
            raise Exception('No project root specified')
        projects_root = Path(self.projects_root_le.text())
        if not projects_root.exists():
            raise FileNotFoundError('Path not exists: {}'.format(projects_root))
        temp_dir = Path(self.temp_dir_le.text())
        temp_dir.mkdir(parents=True, exist_ok=True)

        data = {
            'agio_pipe.local_roots':[
                {'name': 'projects', 'path': projects_root.as_posix()},
                {'name': 'temp', 'path': temp_dir.as_posix()},
            ]
        }
        return data

    def load_settings(self):
        local_settings = get_local_settings()
        return local_settings.get('agio_pipe.local_roots')

    def save_settings(self, settings_data: dict):
        local_settings = get_local_settings()
        for pkg, values in settings_data.items():
            local_settings.set(pkg, values)
        save_local_settings(local_settings)


def show_dialog():
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = QuickSetupDialog()
    dialog.show()
    app.exec_()


if __name__ == '__main__':
    show_dialog()