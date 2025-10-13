import logging

from agio.core.plugins.base_service import ServicePlugin, make_action
from agio.core.utils import launch_utils
from agio_pipe.entities.task import ATask

logger = logging.getLogger(__name__)


class SimpleLauncherService(ServicePlugin):
    name = 'simple_publish'

    def execute(self, **kwargs):
        pass

    @make_action(menu_name='task.launcher', app_name='front')
    def open_publisher_dialog(self, *args, task_id: str, **kwargs):
        logger.info(f'Start standalone publisher with task {task_id}')
        project = ATask(task_id).project
        if not project.workspace_id:
            raise ValueError(f'Workspace not set for project "{project.name}"')
        cmd_args = [
            'pub',
            *args,
            '--task-id', task_id,
            '--ui',
        ]
        launch_utils.exec_agio_command(
            args=cmd_args,
            workspace=project.workspace_id,
            detached=True
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