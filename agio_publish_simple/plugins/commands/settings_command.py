import logging

from agio.core.plugins.base_command import AStartAppCommand
from agio.tools.qt import main_app, center_on_screen
from agio_publish_simple.ui import quick_setup_dialog

logger = logging.getLogger(__name__)


class SimplePublishCommand(AStartAppCommand):
    name = 'simple_settings_cmd'
    command_name = 'simple_settings'
    app_name = 'quick_settings'

    def execute(self, **kwargs):
        with main_app() as app:
            dialog = quick_setup_dialog.QuickSetupDialog()
            center_on_screen(dialog, app)
            dialog.show()


