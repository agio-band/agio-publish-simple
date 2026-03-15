import logging

from agio.core.events import emit
from agio_pipe.entities.version import AVersion
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_session import PublishSession
from agio_pipe.publish.tools.create_version import create_product_version
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
                published_files = publisher.publish(**inst_options)
                if not published_files:
                    raise Exception(f'No published files created with instance {instance}')
                processed.append([instance, published_files])
        except Exception:
            # TODO
            raise

        logger.info('Start creation versions...')
        created: list[tuple[AVersion, PublishInstance]] = []
        for instance, published_files in processed:
            try:
                version, files = create_product_version(
                    product_id=instance.product.id,
                    task_id=instance.task.id,
                    version=instance.version,
                    project_files=published_files,
                )
                instance.set_results(version, files)
                emit('pipe.publish.instance_processed',
                    {'instance': instance, 'session': self.session}
                )
                created.append((version, instance))
            except Exception:
                if created:
                    logger.error(
                        'Failed to create new version. Early created versions in current session will be deleted.')
                    for vers, inst in created:
                        logger.warning('DELETE VERSION: {}'.format(vers))
                        vers.delete()
                raise
        for vers, inst in created:
            emit('pipe.publish.version_created', {
                'version': vers,
                'instance': inst,
            })