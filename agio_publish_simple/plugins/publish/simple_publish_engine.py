import logging

from agio.core.events import emit
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_publish_simple.publish_processing import get_publisher

logger = logging.getLogger(__name__)


class PublishEngineSimplePlugin(PublishEngineBasePlugin):
    name = 'simple_publish'

    def execute(self, **options):
        publish_result = []
        selected_instances = options.get('selected_instances')
        if selected_instances:
            logger.info('Selected instances: {}'.format(selected_instances))
        for inst_id, inst in self.instances.items():
            inst: PublishInstance
            if selected_instances:
                if inst.name not in selected_instances:
                    logger.info('Skip instance %s', inst.name)
                    continue
            publisher_cls = get_publisher(inst.product.type)
            publisher = publisher_cls(inst)
            published_files = publisher.publish(**options)
            if not published_files:
                raise Exception(f'No published files created with instance {inst}')
            publish_result.append({
                'instance': inst,
                'published_files': published_files
            })
        return publish_result