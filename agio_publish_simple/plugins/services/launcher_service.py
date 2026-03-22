import logging
import os

from agio.core.plugins.base_service import ServicePlugin, make_action
from agio.tools import launching
from agio_pipe.entities.task import ATask

logger = logging.getLogger(__name__)


class SimpleLauncherService(ServicePlugin):
    name = 'simple_publish_service'

    @make_action(menu_name='task.launcher', app_name='front')
    def open_publisher_dialog(self, *args, task_id: str, **kwargs):
        task = ATask(task_id)
        logger.info(f'Start standalone publisher with task {task.entity.name}/{task.name}')

        if not task.project.workspace_launching_id:
            raise ValueError(f'Workspace not set for project "{task.project.name}"')
        cmd_args = [
            'pub',
            *args,
            '--task-id', task_id,
            '--ui',
        ]
        launching.exec_agio_command(
            args=cmd_args,
            workspace=task.project.workspace_launching_id,
            detached=os.name != 'nt',   # fix for windows
            non_blocking=os.name == 'nt',
            new_console=True,
        )


