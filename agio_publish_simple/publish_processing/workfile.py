import logging

from agio_pipe.exceptions import PublishError
from agio_pipe.schemas.version import PublishedFileFull
from agio_publish_simple.publish_processing._base import PublishProcessingBase

logger = logging.getLogger(__name__)


class PublishProcessingWorkfile(PublishProcessingBase):
    product_type = "workfile"
    publish_filename = "workfile"

    def execute(self, **options):
        if not self.instance.sources:
            raise PublishError(detail=f'No sources files in instance {self.instance}')
        if len(self.instance.sources) > 1:
            raise PublishError(detail=f'Multiple sources files in instance not allowed {self.instance.sources}')
        # get one single file and publish to project
        work_file = self.instance.sources[0]
        full_path, rel_path = self.get_save_path(work_file)
        logger.info('Workfile save path %s', rel_path)
        self.copy_file_to(work_file, full_path)
        file = PublishedFileFull(
            path=full_path,
            relative_path=rel_path,
        )
        return [file]