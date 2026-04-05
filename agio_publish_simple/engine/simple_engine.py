import logging

from agio.core.events import emit
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_session import PublishSession
from agio_pipe.schemas.version import PublishedFileFull
from agio_publish_simple.publish_processing import get_publisher

logger = logging.getLogger(__name__)


class SimplePublishEngine:
    def __init__(self, session: PublishSession, **options):
        self.session = session

    def run(self, **options):
        publish_result = []
        selected_instances = options.get('selected_instances')
        if selected_instances:
            logger.info('Selected instances: {}'.format(selected_instances))
        instances = self.session.instances.values()
        if selected_instances:
            instances = [inst for inst in instances if inst.name in selected_instances]
        instances = [inst for inst in instances if inst.enabled]
        emit('pipe.publish.before_publish_processing', {'instances': instances}) # TODO
        self.do_publish(instances, **options)
        emit('pipe.publish.after_publish_processing', {'result': publish_result})  # TODO
        return publish_result

    def do_publish(self, instances: list[PublishInstance], **options):
        processed: list = []
        try:
            for instance in instances:
                instance: PublishInstance
                emit('pipe.publish.before_instance_processing', {'instances': instance, 'options': options}) # TODO
                publisher_cls = get_publisher(instance.product.type)
                publisher = publisher_cls(instance, options)
                inst_options = {
                    **instance.product.fields.get('publish_options', {}),
                    **instance.options,
                    **options,
                }
                published_files: list[PublishedFileFull] = publisher.publish(**inst_options)
                if not published_files:
                    raise Exception(f'No published files created with instance {instance}')
                instance.set_value('product_outputs', published_files)
                processed.append([instance, published_files])
        except Exception:
            # TODO
            raise
        logger.info('Start creation versions...')
        # Required event for create versions in DB!!!
        event = emit('pipe.publish.product_outputs_created', {'instances': instances})
        # versions = event.payload['versions']
