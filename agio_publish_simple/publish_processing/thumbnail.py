import logging
import tempfile

from PIL import Image

from agio_pipe.exceptions import PublishError
from agio_pipe.schemas.version import PublishedFileFull
from agio_publish_simple.publish_processing.review import PublishProcessingReview

logger = logging.getLogger(__name__)


class PublishProcessThumbnail(PublishProcessingReview):
    product_type = "thumbnail"
    publish_filename = "thumbnail"

    def execute(self, **options):
        if self.is_no_file_mode:
            if self.instance.sources:
                thumbnail_file = self.instance.sources[0]
            else:
                raise PublishError("No sources specified for thumbnail")
        else:
            seq = self.extract_sequence(self.instance.sources, max_files=1)
            thumbnail_file = seq[0]
            thumbnail_file = self.to_rgb(thumbnail_file)
        full_path, rel_path = self.get_save_path(thumbnail_file)
        self.copy_file_to(thumbnail_file, full_path)
        file = PublishedFileFull(
            orig_path=thumbnail_file,
            publish_path=full_path,
        )
        return [file]

    def to_rgb(self, file_path: str):
        tmp_tile = tempfile.mktemp(suffix=".png")
        Image.open(file_path).convert('RGB').save(tmp_tile, 'PNG')
        return tmp_tile