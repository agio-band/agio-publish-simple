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
        instances = self.instances.values()
        if selected_instances:
            instances = [inst for inst in instances if inst.name in selected_instances]
        emit('pipe.publish.before_publish_processing', {'instances': instances})
        for inst_id, inst in self.instances.items():
            inst: PublishInstance
            emit('pipe.publish.before_instance_processing', {'instances': inst})
            if not inst.enabled:
                continue
            publisher_cls = get_publisher(inst.product.type)
            publisher = publisher_cls(inst, options)
            published_files = publisher.publish(**options)
            if not published_files:
                raise Exception(f'No published files created with instance {inst}')
            instance_result = {
                'instance': inst,
                'published_files': published_files
            }
            emit('pipe.publish.instance_processed', instance_result)
            publish_result.append(instance_result)
        emit('pipe.publish.after_publish_processing', {'result': publish_result})
        return publish_result
