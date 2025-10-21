from agio.core.events import callback, AEvent
import logging
from agio.core.settings import load_default_settings
from agio.core.utils import launch_utils

logger = logging.getLogger(__name__)


@callback('agio_desk.app.before_launched')
def on_app_startup(event: AEvent):
    settings = load_default_settings()
    if not settings.get('agio_pipe.local_roots', None):
        logger.warning('No local roots configured')
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
        logger.debug('Local roots configured')
