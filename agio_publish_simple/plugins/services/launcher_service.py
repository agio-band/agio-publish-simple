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
            # detached=True,
            # new_console=True
        )


