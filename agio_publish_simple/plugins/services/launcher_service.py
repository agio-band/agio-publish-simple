import logging

from agio.core.plugins.base_service import ServicePlugin, make_action
from agio.core.utils import launch_utils

logger = logging.getLogger(__name__)


class SimpleLauncherService(ServicePlugin):
    name = 'simple_publish'

    def execute(self, **kwargs):
        pass

    @make_action(menu_name='task.launcher', app_name='front')
    def open_publisher_dialog(self, *args, task_id: str, **kwargs):
        logger.info(f'Start standalone publisher with task {task_id}')
        workspace_id = None # ATask(task_id).project.workspace_id
        args = [
            'pub',
            *args,
            '--task_id', task_id,
            '--ui',
        ]
        launch_utils.exec_agio_command(
            args=args,
            workspace=workspace_id,
        )


    @make_action(label='Settings',
                 menu_name='tray.main_menu',
                 app_name='desk',
                 )
    def login(self, *args, **kwargs):
        # from agio_publish_simple.ui import quick_setup_dialog
        #
        # self.dialog = quick_setup_dialog.QuickSetupDialog()
        # self.dialog.show()
        args = [
            'simple_settings',
        ]
        launch_utils.exec_agio_command(
            args=args,
            workspace=None,
            detached=False,
            new_console=False
        )