import logging

from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_pipe.publish.publish_session import PublishSession
from agio_publish_simple.engine.simple_engine import SimplePublishEngine

logger = logging.getLogger(__name__)


class PublishEngineSimplePlugin(PublishEngineBasePlugin):
    name = 'simple_publish'
    open_ui_function = 'agio_publish_simple.ui.show_dialog'

    def start_publish(self, **options):
        engine = SimplePublishEngine(self.session)
        return engine.run(**options)
