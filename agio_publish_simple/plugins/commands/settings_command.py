import logging

from agio.core.plugins.base_command import AStartAppCommand
from agio.tools.qt import open_widget
from agio_publish_simple.ui import quick_setup_dialog

logger = logging.getLogger(__name__)


class SimplePublishCommand(AStartAppCommand):
    name = 'simple_settings_cmd'
    command_name = 'simple_settings'
    app_name = 'quick_settings'

    def execute(self, **kwargs):
        open_widget(quick_setup_dialog.QuickSetupDialog, app_name='agio Root Settings')


