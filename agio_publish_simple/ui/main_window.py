import logging
import os
import re
import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from agio.core.workspaces import AWorkspaceManager
from agio.core.workspaces.resources import get_res
from agio.tools import paths
from agio.tools.launching import create_workspace_launch_context, LaunchContext
from agio_pipe.chips.publish_scene.default_standalone_scene import StandalonePublishScene
from agio_pipe.chips.publish_scene.export_container import ExportContainer
from agio.core.entities.product import AProduct
from agio.core.entities.product_type import AProductType
from agio.core.entities.task import ATask
from agio_publish_simple import __version__
from agio_publish_simple.ui import drop_widget

# 🗂️ 📦 📌
title1 = '''
<html><head/><body><p><span style=" font-size:12pt;">
 <span style="color: #999">Project:</span> {} / 
 <span style="color: #999">Entity:</span> {} / 
 <span style="color: #999">Task:</span> {}
</span></p></body></html>
'''
title2 = '''
<html><head/><body><p align="center"><span style=" font-size:12pt;">
Process logs
</span></p></body></html>
'''
title3 = '''
<html><head/><body><p align="center"><span style=" font-size:12pt;">
Publishing Done!
</span></p></body></html>
'''

logger = logging.getLogger(__name__)


class PublishDialog(QWidget):
    output_encoding = 'cp1251' if os.name == 'nt' else 'utf-8'
    def __init__(
            self,
            task,
            workfile_extensions=None,
            review_extensions=None,
            *args
        ):
        super().__init__(*args)
        self.task = task
        self.setWindowTitle(f'agio Simple Publisher v{__version__}')
        self.main_ly = QVBoxLayout(self)
        self.main_ly.setContentsMargins(-1, 0, -1, -1)
        self.stackedWidget = QStackedWidget()
        self.page = QWidget()
        self.main_ly_1 = QVBoxLayout(self.page)
        self.title1 = QLabel(title1.format(task.project.name, task.entity.name, task.name))
        self.title1.setAlignment(Qt.AlignCenter)
        self.main_ly_1.addWidget(self.title1)
        self.main_ly_1.addWidget(Line())

        self.drop_wd_1_ly = QVBoxLayout()
        self.drop_wd_1 = drop_widget.FileDropWidget(
            base_text='Drop Workfile Here',
            accepted_extensions=workfile_extensions,
            allow_multiple=False,
        )
        self.drop_wd_1.sourceChangedSignal.connect(self.on_source_changed)
        self.drop_wd_1_ly.addWidget(self.drop_wd_1)
        self.main_ly_1.addLayout(self.drop_wd_1_ly)
        self.drop_wd_2_ly = QVBoxLayout()
        self.drop_wd_2 = drop_widget.FileDropWidget(
            base_text='Drop Review Files Here',
            accepted_extensions=review_extensions,
            allow_sequence=True,
            allow_multiple=True,
            allow_directory=True,
        )
        self.drop_wd_2.sourceChangedSignal.connect(self.on_source_changed)
        self.drop_wd_2_ly.addWidget(self.drop_wd_2)
        self.main_ly_1.addLayout(self.drop_wd_2_ly)
        self.main_ly_1.addWidget(Line())

        self.horizontalLayout_2 = QHBoxLayout()
        self.help_btn = QPushButton('Help')

        self.horizontalLayout_2.addWidget(self.help_btn)
        self.horizontalLayout_2.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.start_btn = QPushButton('Start Publishing', clicked=self.on_start_publish)
        self.horizontalLayout_2.addWidget(self.start_btn)
        self.main_ly_1.addLayout(self.horizontalLayout_2)
        self.main_ly_1.setStretch(2, 1)
        self.main_ly_1.setStretch(3, 1)
        self.stackedWidget.addWidget(self.page)

        self.page_2 = QWidget()
        self.main_ly_2 = QVBoxLayout(self.page_2)
        self.title2 = QLabel(title2)

        self.main_ly_2.addWidget(self.title2)
        self.output_tb = OutputWidget(self.page_2)
        self.main_ly_2.addWidget(self.output_tb)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)
        self.cancel_btn = QPushButton('Cancel', clicked=self.on_cancel_publish)
        self.horizontalLayout.addWidget(self.cancel_btn)
        self.main_ly_2.addLayout(self.horizontalLayout)
        self.stackedWidget.addWidget(self.page_2)

        self.page_3 = QWidget()
        self.main_ly_3 = QVBoxLayout(self.page_3)
        self.title3 = QLabel(title3)
        self.main_ly_3.addWidget(self.title3)
        self.line_3 = QFrame(self.page_3)
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_ly_3.addWidget(self.line_3)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.report_tb = OutputWidget()
        scroll.setWidget(self.report_tb)
        self.report_tb.setOpenExternalLinks(False)
        self.report_tb.setOpenLinks(False)
        self.report_tb.setWordWrapMode(QTextOption.NoWrap)
        self.report_tb.anchorClicked.connect(self.on_report_link_clicked)
        self.main_ly_3.addWidget(scroll)
        self.line_4 = QFrame(self.page_3)
        self.line_4.setFrameShape(QFrame.Shape.HLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_ly_3.addWidget(self.line_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)
        self.restart_btn = QPushButton('Restart', clicked=self.on_reset)
        self.horizontalLayout_3.addWidget(self.restart_btn)
        self.close_btn = QPushButton('Close', clicked=self.close)
        self.horizontalLayout_3.addWidget(self.close_btn)
        self.main_ly_3.addLayout(self.horizontalLayout_3)
        self.main_ly_3.setStretch(2, 1)
        self.stackedWidget.addWidget(self.page_3)
        self.main_ly.addWidget(self.stackedWidget)
        self.resize(700, 420)

        self.stackedWidget.setCurrentIndex(0)
        self.apply_style()
        self.on_source_changed()
        self.process = None
        self.session_id = None

        # debug shortcuts
        QShortcut(QKeySequence("Alt+1"), self, activated=lambda: self.stackedWidget.setCurrentIndex(0))
        QShortcut(QKeySequence("Alt+2"), self, activated=lambda: self.stackedWidget.setCurrentIndex(1))
        QShortcut(QKeySequence("Alt+3"), self, activated=lambda: self.stackedWidget.setCurrentIndex(2))
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_scene)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_scene)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.on_reset)

    def on_source_changed(self):
        if self.drop_wd_1.get_source():
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(False)

    def on_report_link_clicked(self, url: QUrl):
        path = url.url()
        print('Open path', path)
        paths.open_path(path)

    def apply_style(self):
        css_file = get_res('publish-simple/style.css')
        if not css_file:
            logger.warning('No style file found Simple Publish UI')
            return
        self.setStyleSheet(Path(css_file).read_text(encoding='utf-8'))

    def set_workfile(self, paths: list):
        self.drop_wd_1.update_source(paths)

    def set_review(self, path_list):
        self.drop_wd_2.update_source(path_list)

    def on_start_publish(self):
        workfile = self.drop_wd_1.get_source()
        review_file = self.drop_wd_2.get_source()
        self.stackedWidget.setCurrentIndex(1)
        try:
            self.start_process(workfile, review_file)
        except Exception as e:
            traceback.print_exc()
            self.on_error(e)

    def on_cancel_publish(self):
        self.process: QProcess
        if self.process:
            self.process.kill()
            self.process.waitForFinished()
        self.output_tb.clear()
        self.stackedWidget.setCurrentIndex(0)

    def on_reset(self):
        self.output_tb.clear()
        self.stackedWidget.setCurrentIndex(0)
        self.drop_wd_1.reset()
        self.drop_wd_2.reset()
        self.on_source_changed()

    def show_report(self, result_data: dict):
        text = []
        projects = {}
        tasks = {}
        for inst in result_data['instances']:
            task_id = inst['task_id']
            task = tasks.get(task_id) or ATask(task_id)
            project = projects.get(task.project_id) or task.project
            tasks[task_id] = task
            projects[task.project_id] = project
            all_roots = project.get_roots()
            root = project.mount_root
            if not root:
                raise ValueError(f'No root named "projects". Existing: {all_roots}')
            new_version = inst['results']['new_version']
            published_files = [x['path'] for x in inst['results']['published_files']]
            if not published_files:
                text.append(f"<i>No published files found for {new_version['product']['name']} v{int(new_version['version'])}</i>")
            else:
                version_dir = Path(published_files[0]).parent.as_posix()
                text.append(f"<b><a href=\"{root}/{version_dir}\">{new_version['product']['name']}: v{int(new_version['version'])}</a></b>")
                for file in published_files:
                    text.append(f'<br> {root}/{file}')
            text.append('<br><br>')
        self.report_tb.setHtml(''.join(text))

    def start_process(self, workfile, review_file):
        scene_file = self.build_scene(workfile, review_file)

        ws_manager = AWorkspaceManager.current()
        ctx = create_workspace_launch_context(
            ws_manager=ws_manager,
            args=['-m', 'agio',
                  '-w', ws_manager.revision_id,
                  'pub',
                  scene_file,
                  ]
        )
        self.start_subprocess(ctx)

    def start_subprocess(self, ctx: LaunchContext, **kwargs):
        self.stackedWidget.setCurrentIndex(1)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_done)
        env = QProcessEnvironment.systemEnvironment()
        for k, v in ctx.envs.items():
            env.insert(k, v)
        self.process.setProcessEnvironment(env)
        self.process.setWorkingDirectory(ctx.workdir)
        self.output_tb.append('Exec command: ' + ' '.join(ctx.command))
        if ctx.workdir:
            self.output_tb.append(f'Workdir: {ctx.workdir}')
        self.process.errorOccurred.connect(lambda e: logger.error(f"Subprocess error {e}: {self.process.errorString()}"))
        self.process.start(ctx.command[0], ctx.command[1:])
        resp = self.process.waitForStarted()
        if not resp:
            logger.error(f"Failed to start: {self.process.errorString()}")
        else:
            logger.debug(f"Started: {self.process.state()}")

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        sys.stdout.write(data)
        sys.stdout.flush()
        self.output_tb.append(data)
        self._parse_output(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        sys.stderr.write(data)
        sys.stderr.flush()
        self.output_tb.append_error(data.strip().replace('\n', '<br>').replace(' ', '&nbsp;'))

    def process_done(self, exit_code, exit_status):
        print('Exit code:', exit_code)
        self.output_tb.append(f'Exit code: {exit_code}')
        if exit_code == 0:
            self.on_complete()

    def on_error(self, message):
        self.output_tb.append_error(message)

    def on_complete(self):
        self.stackedWidget.setCurrentIndex(2)
        if self.session_id:
            self.display_report(self.session_id)
        else:
            self.report_tb.setText('Publishing done!')

    def display_report(self, session_id):
        from agio_pipe.publish import publish_session
        session = publish_session.PublishSession(session_id=session_id)
        self.report_tb.append_success(f'Publishing session: {session.id}')
        for inst_id, inst in session.instances.items():
            self.report_tb.append(str(inst.name))

    def _parse_output(self, text: str):
        m = re.search(r'Publish Session ID: "([\w\-]+)"', text)
        if m:
            self.session_id = m.group(1)

    def get_product_type_id(self, name):
        product_type = AProductType.find(name)
        if not product_type:
            raise NameError(f'No product type named {name}')
        return product_type.id

    def build_scene(self, workfile, review_file, save_path: str = None):
        # TODO use only existing products! error if missing
        scene = StandalonePublishScene()

        default_options = {
            'publish_options': {
                'path_template_name': 'publish' # TODO get from settings
            }
        }

        workfile_product = AProduct.find(self.task.id, 'workfile', 'main')
        if not workfile_product:
            # required options fields:
            # - path_template_name
            workfile_product = AProduct.create(
                self.task.id, 'workfile', self.get_product_type_id('workfile'), 'main',
                fields=default_options
            )
        logger.debug('ADD Workfile %s %s %s', self.task, repr(workfile_product), workfile[0])
        scene.create_container('Workfile', self.task, workfile_product, workfile)

        if review_file:
            # review
            # required options fields:
            # - path_template_name
            # - burn_in_template_name
            review_product = AProduct.find(self.task.id, 'review', 'main')
            if not review_product:
                review_product = AProduct.create(
                    # частный случай когда продукт ссылается на таск, в общем случае там может быть любой entity
                    self.task.id, 'review', self.get_product_type_id('review'), 'main',
                    fields={
                        **default_options,
                        'burn_in_template_name': 'default'
                    }
                )
            opt = review_product.fields.get('publish_options') or {}
            if 'burn_in_template_name' not in opt:
                opt['burn_in_template_name'] = 'default'
                review_product.set_fields(publish_options=opt)
            logger.debug('ADD Review %s %s %s', self.task, repr(review_product), review_file[0])
            scene.create_container('Review', self.task, review_product, review_file)

            # thumbnail
            thumbnail_product = AProduct.find(self.task.id, 'thumbnail', 'main')
            if not thumbnail_product:
                # required options fields:
                # - path_template_name
                thumbnail_product = AProduct.create(
                    self.task.id, 'thumbnail', self.get_product_type_id('thumbnail'), 'main',
                    fields=default_options
                )
            logger.debug('Add Thumbnail %s %s %s', self.task, repr(thumbnail_product), review_file[0])
            scene.create_container('Thumbnail', self.task, thumbnail_product, review_file)
        if not save_path:
            save_path = tempfile.NamedTemporaryFile(delete=False, suffix='.json').name
        scene.save(save_path)
        return save_path

    def save_scene(self):
        workfile = self.drop_wd_1.get_source()
        review_file = self.drop_wd_2.get_source()
        if not any([workfile, review_file]):
            QMessageBox.critical(self,' Error', 'Select workfile or review file before saving')
            return
        dialog = QFileDialog()
        dialog.setNameFilter("*.json")
        dialog.setFileMode(QFileDialog.AnyFile)
        if dialog.exec():
            files = dialog.selectedFiles()
            if not files:
                return
            save_file = Path(files[0]).with_suffix('.json').as_posix()
            try:
                scene_file = self.build_scene(workfile, review_file, save_file)
                QMessageBox.information(self, 'Success', f'Saved to {scene_file}')
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(self, ' Error', str(e))

    def open_scene(self):
        dialog = QFileDialog()
        dialog.setNameFilter("*.json")
        dialog.setFileMode(QFileDialog.AnyFile)
        if dialog.exec():
            files = dialog.selectedFiles()
            if not files:
                return
            try:
                scene = StandalonePublishScene()
                scene.load(files[0])
                for cont in scene.containers.values():
                    cont: ExportContainer
                    if cont.get_product().type.name == 'workfile':
                        self.set_workfile(cont.get_sources())
                    elif cont.get_product().type.name == 'review':
                        self.set_review(cont.get_sources())
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(self, ' Error', str(e))


class OutputWidget(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._set_monospace_font()

        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self.on_link_clicked)

    def _set_monospace_font(self):
        self.document().setDefaultStyleSheet("p, div { margin: 0px; padding: 0px; }")
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.document().setDefaultFont(font)

    def _format_html(self, text):
        return text.strip().replace('\n', '<br>')

    def append_error(self, text):
        if text.strip():
            super().append(f"<span style='color:orange'>{self._format_html(text)}</span>")

    def append_success(self, text):
        if text.strip():
            super().append(f"<span style='color:green; font-weight:bold;'>{self._format_html(text)}</span>")

    def append(self, text):
        if text.strip():
            super().append(f"<span>{self._format_html(text)}</span>")

    def on_link_clicked(self, url: QUrl):
        link_str = url.toString()
        if url.scheme() in ["http", "https"]:
            QDesktopServices.openUrl(url)
        else:
            path = url.toLocalFile() if url.isLocalFile() else link_str
            if os.path.exists(path):
                folder = path if os.path.isdir(path) else os.path.dirname(path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
            else:
                QDesktopServices.openUrl(url)


class Line(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
