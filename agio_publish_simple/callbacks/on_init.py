from agio.core.events import callback
import logging
from agio.core.settings import get_local_settings
from agio.core.utils import launch_utils

logger = logging.getLogger(__name__)


@callback('agio_desk.app.before_launched')
def on_app_startup(event, payload):
    settings = get_local_settings()
    if not settings.get('agio_pipe.local_roots'):
        logger.info('No local roots configured')
        args = [
            'simple_settings',
        ]
        launch_utils.exec_agio_command(
            args=args,
            workspace=None,
            detached=False,
            new_console=False
        )
    else:
        logger.info('Local roots configured')
